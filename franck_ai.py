# franck_ai.py

import sys
import io
import logging
import requests
import json
import os
import re
import spacy
from urllib.parse import quote
from allsport_connector import get_live_scores, get_countries, get_leagues_by_country, get_teams_by_league
from engine import PredictionEngine
from api_connector import get_team_info
from utils.team_form import get_team_form
from utils.head_to_head import get_head_to_head
from config import (
    RAPID_API_KEY, RAPID_API_HOST, WIKIPEDIA_LANG,
    DEFAULT_TEAM_STRENGTH, HOME_ADVANTAGE_BONUS, DICTIONARY_PATH
)

# Forcer l'encodage UTF-8 pour la console (Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration des logs
logging.basicConfig(level=logging.INFO)

# Header User-Agent obligatoire pour Wikipedia
WIKI_HEADERS = {
    "User-Agent": "FranckAI Bot/1.0 (contact@franckai.example.com) - Projet educatif"
}

def safe_quote(text):
    """Nettoie et encode un texte pour l'utiliser dans une URL."""
    if not isinstance(text, str):
        text = str(text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return quote(text.strip())

class Franck:
    def __init__(self):
        self.personnalité = "Expert du football, direct, loyal à Franck"
        self.mémoire = []
        self.historique_predictions = []
        self.historique_interactions = []
        self.base_connaissances = self._charger_connaissances()
        self.clubs = [
            "real madrid", "barcelona", "psg", "manchester united", "manchester city",
            "chelsea", "liverpool", "arsenal", "bayern munich", "juventus", "inter milan",
            "ac milan", "napoli", "marseille", "ajax", "benfica", "porto"
        ]
        self.prévision = PredictionEngine()

        # Charger le modèle spaCy
        try:
            self.nlp = spacy.load("fr_core_news_md")
            logging.info("✅ Modèle spaCy chargé avec succès.")
        except Exception as e:
            logging.error(f"❌ Erreur de chargement de spaCy : {e}")
            self.nlp = None

    # =============================
    # 📚 Base de connaissances évolutive
    # =============================

    def _charger_connaissances(self):
        if os.path.exists(DICTIONARY_PATH):
            with open(DICTIONARY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print(f"⚠️ Fichier {DICTIONARY_PATH} non trouvé. Démarrage avec connaissances vides.")
            return {}

    def _sauvegarder_connaissances(self):
        os.makedirs(os.path.dirname(DICTIONARY_PATH), exist_ok=True)
        with open(DICTIONARY_PATH, "w", encoding="utf-8") as f:
            json.dump(self.base_connaissances, f, ensure_ascii=False, indent=2)

    def ajouter_connaissance(self, question, reponse):
        self.base_connaissances[question.lower()] = reponse
        self._sauvegarder_connaissances()

    def chercher_connaissance(self, question):
        return self.base_connaissances.get(question.lower())

    # =============================
    # 🔄 Enregistrement des interactions
    # =============================

    def enregistrer_interaction(self, question, reponse, validée=False):
        self.historique_interactions.append({
            "question": question,
            "reponse": reponse,
            "validee": validée
        })

    def corriger_reponse(self, question, nouvelle_reponse):
        self.ajouter_connaissance(question, nouvelle_reponse)
        for interaction in self.historique_interactions:
            if interaction["question"] == question:
                interaction["validee"] = True
                interaction["reponse"] = nouvelle_reponse

    # =============================
    # 🧠 Analyse sémantique
    # =============================

    def analyser_question(self, question):
        if not self.nlp:
            return {"question": question, "entites": [], "mots_cles": [], "intention": "générale"}

        doc = self.nlp(question)
        entites = [ent.text for ent in doc.ents]
        mots_cles = [token.lemma_ for token in doc if token.pos_ in ["VERB", "NOUN"]]
        intention = self.detecter_intention(doc)

        return {
            "question": question,
            "entites": entites,
            "mots_cles": mots_cles,
            "intention": intention
        }

    def detecter_intention(self, doc):
        question_text = doc.text.lower()
        if "qui a fondé" in question_text or "créé" in question_text or "créer" in question_text:
            return "fondateur"
        elif "parle-moi de" in question_text or "présente" in question_text or "c'est quoi" in question_text:
            return "description"
        elif "gagné" in question_text or "score" in question_text or "résultat" in question_text:
            return "résultat"
        elif ("plus titré" in question_text or
              "record" in question_text or
              "meilleur" in question_text or
              "plus de" in question_text or
              "combien de" in question_text or
              "statistique" in question_text or
              "classement" in question_text or
              "seria a" in question_text):
            return "statistique"
        else:
            return "générale"

    # =============================
    # 🌐 Recherche sur Wikipedia
    # =============================

    def chercher_sur_wikipedia(self, question):
        """Cherche un article Wikipedia correspondant à la question."""
        joueurs_connus = {
            "rodrigo goes": "Rodrigo (footballer, born 1991)",
            "rodrigo": "Rodrigo (footballer, born 1991)",
            "neymar": "Neymar",
            "mbappe": "Kylian Mbappé",
            "messi": "Lionel Messi",
            "ronaldo": "Cristiano Ronaldo",
        }

        question_lower = question.lower()
        for joueur, titre_officiel in joueurs_connus.items():
            if joueur in question_lower:
                return titre_officiel

        url = "https://fr.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": f"{question} football",
            "utf8": 1
        }

        try:
            response = requests.get(url, params=params, headers=WIKI_HEADERS, timeout=10)
            if response.status_code != 200:
                return None

            data = response.json()
            if data.get("query", {}).get("search"):
                for result in data["query"]["search"]:
                    title = result["title"]
                    if any(kw in title.lower() for kw in ["football", "joueur", "attaquant", "milieu", "défenseur", "gardien"]):
                        return title
                return data["query"]["search"][0]["title"]
        except Exception as e:
            logging.error(f"❌ Erreur Wikipedia search : {e}")
        return None

    def resume_wikipedia(self, titre):
        """Récupère le résumé d'un article Wikipedia."""
        if not titre:
            return "Titre invalide."

        titre_encode = safe_quote(titre.replace(' ', '_'))
        url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{titre_encode}"

        try:
            response = requests.get(url, headers=WIKI_HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("extract", "Résumé introuvable.")
            else:
                return "Résumé introuvable."
        except Exception as e:
            logging.error(f"❌ Erreur Wikipedia summary : {e}")
            return "Erreur lors de la récupération du résumé."

    # =============================
    # 🚀 Point d'entrée principal
    # =============================

    def repondre_statistique(self, question):
        """Répond aux questions de type statistique (records, classements, etc.)."""
        question_lower = question.lower()

        # Base de données manuelle de records (à enrichir)
        statistiques = {
            "club le plus titré de l'histoire de la liga": "🏆 Le Real Madrid est le club le plus titré de l'histoire de la Liga, avec 36 titres (au 2025). Le FC Barcelone est 2e avec 27 titres.",
            "club le plus titré de l'histoire de la seria a": "🏆 La Juventus de Turin est le club le plus titré de l'histoire de la Serie A, avec 36 titres (au 2025). L'Inter Milan et l'AC Milan suivent avec 19 titres chacun.",
            "meilleur buteur de l'histoire de la liga": "⚽ Lionel Messi est le meilleur buteur de l'histoire de la Liga, avec 474 buts pour le FC Barcelone.",
            "club le plus titré d'europe": "🌍 Le Real Madrid est le club le plus titré d'Europe, avec 15 titres en Ligue des champions.",
            "gardien avec le plus de clean sheets": "🧤 Jan Oblak (Atlético Madrid) détient le record de clean sheets par saison en Liga (27 en 2015-2016)."
        }

        # Recherche approximative
        for key, value in statistiques.items():
            if key in question_lower:
                return value

        # Fallback : recherche sur Wikipedia
        titre = self.chercher_sur_wikipedia(question)
        if titre:
            resume = self.resume_wikipedia(titre)
            return f"Selon Wikipedia : {resume}"

        return "Je n'ai pas encore cette statistique dans ma base de données."

    def operer(self, message):
        message_lower = message.lower()

        # ✅ 1. Scores en direct → PRIORITAIRE
        if "scores en direct" in message_lower:
            matches = get_live_scores()
            if matches:
                reponse = "⚽ MATCHS EN DIRECT :\n"
                for match in matches[:5]:  # 5 premiers matchs
                    home = match["event_home_team"]
                    away = match["event_away_team"]
                    score = f"{match['event_final_result']}"
                    reponse += f"- {home} {score} {away}\n"
                return reponse
            else:
                return "Aucun match en direct pour l’instant."

        # ✅ 2. Liste des pays
        elif "pays supportés" in message_lower or "pays disponibles" in message_lower:
            pays = get_countries()
            if pays:
                reponse = "🌍 PAYS SUPPORTÉS :\n"
                for p in pays[:10]:  # 10 premiers pays
                    reponse += f"- {p['country_name']}\n"
                reponse += f"... et {len(pays) - 10} autres."
                return reponse
            else:
                return "Impossible de récupérer la liste des pays."

        # ✅ 3. Ligues d'un pays
        elif "ligues en" in message_lower:
            pays_nom = message_lower.replace("ligues en ", "").strip().title()
            ligues = get_leagues_by_country(pays_nom)
            if ligues:
                reponse = f"🏆 LIGUES EN {pays_nom.upper()} :\n"
                for ligue in ligues[:5]:
                    reponse += f"- {ligue['league_name']}\n"
                return reponse
            else:
                return f"Aucune ligue trouvée pour {pays_nom}."

        # ✅ 4. Autres intentions (statistique, description, etc.)
        analyse = self.analyser_question(message)
        if analyse["intention"] == "statistique":
            reponse = self.repondre_statistique(message)
            self.ajouter_connaissance(message, reponse)
            self.enregistrer_interaction(message, reponse)
            return reponse

        # ✅ 5. Recherche Wikipedia (fallback)
        reponse_connue = self.chercher_connaissance(message)
        if reponse_connue:
            self.enregistrer_interaction(message, reponse_connue, validée=True)
            return reponse_connue

        titre = self.chercher_sur_wikipedia(message)
        if titre:
            resume = self.resume_wikipedia(titre)
            self.ajouter_connaissance(message, resume)
            self.enregistrer_interaction(message, resume)
            return resume

        return "Je n’ai pas trouvé d’information pertinente sur cette question."

    # =============================
    # ⚽ Anciennes méthodes (compatibilité)
    # =============================

    def apprendre_club(self, nom_club):
        return self.operer(f"Présente-moi {nom_club}")

    def predict_match(self, message):
        if " vs " not in message.lower():
            return "Format incorrect. Utilise : <Équipe1> vs <Équipe2>"
        parts = message.split(" vs ")
        if len(parts) != 2:
            return "Format incorrect."
        team1, team2 = parts[0].strip(), parts[1].strip()
        return self.operer(f"Prédire le match entre {team1} et {team2}")

    def afficher_historique_prédictions(self, nombre_lignes=None):
        if not self.historique_predictions:
            return "Aucune prédiction enregistrée."
        lignes = self.historique_predictions[-nombre_lignes:] if nombre_lignes else self.historique_predictions
        return "\n".join(lignes)

    def analyse_match(self, team1_name, team2_name, home_team=None):
        return self.operer(f"Analyser le match {team1_name} vs {team2_name}")
        def predict_score(self, team1_name, team2_name, home_team=None):
        """
        Prédit le score d'un match futur entre deux équipes.
        """
        team1_id = self.get_team_id(team1_name)
        team2_id = self.get_team_id(team2_name)

        # Récupérer les forces de base
        force1 = self.prévision.team_strength.get(team1_name.lower(), DEFAULT_TEAM_STRENGTH)
        force2 = self.prévision.team_strength.get(team2_name.lower(), DEFAULT_TEAM_STRENGTH)

        # Bonus domicile
        if home_team and home_team.lower() == team1_name.lower():
            force1 += HOME_ADVANTAGE_BONUS
        elif home_team and home_team.lower() == team2_name.lower():
            force2 += HOME_ADVANTAGE_BONUS

        # Récupérer la forme récente
        forme1 = get_team_form(team1_id)
        forme2 = get_team_form(team2_id)
        force1 += forme1.get("bonus", 0)
        force2 += forme2.get("bonus", 0)

        # Récupérer les stats H2H
        h2h = get_head_to_head(team1_id, team2_id)
        force1 += h2h.get("bonus_team1", 0)
        force2 += h2h.get("bonus_team2", 0)

        # Calculer les buts probables (base 1.0, ajusté par la force)
        buts_team1 = max(0, round((force1 / 80) * 1.5))
        buts_team2 = max(0, round((force2 / 80) * 1.5))

        # Ajustement aléatoire léger pour le réalisme
        import random
        buts_team1 += random.randint(-1, 1)
        buts_team2 += random.randint(-1, 1)
        buts_team1 = max(0, buts_team1)
        buts_team2 = max(0, buts_team2)

        score = f"{buts_team1}-{buts_team2}"

        # Générer une explication tactique
        explication = ""
        if buts_team1 > buts_team2:
            explication = f"{team1_name.title()} devrait dominer grâce à sa forme récente et son effectif offensif."
        elif buts_team2 > buts_team1:
            explication = f"{team2_name.title()} a l'avantage tactique et une défense solide."
        else:
            explication = "Match serré — les deux équipes ont des forces équilibrées."

        return {
            "score": score,
            "explication": explication,
            "details": {
                "team1": team1_name,
                "team2": team2_name,
                "force1": force1,
                "force2": force2,
                "forme1": forme1.get("performance_percent", 0),
                "forme2": forme2.get("performance_percent", 0)
            }
        }
    def get_team_id(self, team_name):
        info = get_team_info(team_name)
        return info["id"] if info else None

    def chercher_club_en_ligne(self, nom_club):
        return self.operer(f"Parle-moi de {nom_club}")