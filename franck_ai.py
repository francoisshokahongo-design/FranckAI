# franck_ai.py

import sys
import io
import logging
import requests
import json
import os
import re
import spacy  # ← Intégré pour la compréhension sémantique
from urllib.parse import quote
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

def build_search_url(query):
    """Construit une URL de recherche Wikipedia propre et sécurisée."""
    encoded_query = safe_quote(query)
    return f"https://fr.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&format=json"

def build_summary_url(title):
    """Construit une URL de résumé Wikipedia propre et sécurisée."""
    encoded_title = safe_quote(title)
    return f"https://fr.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"  # ← ESPACES SUPPRIMÉS

class Franck:
    def __init__(self):
        self.personnalité = "Expert du football, direct, loyal à Franck"
        self.mémoire = []
        self.historique_predictions = []
        self.clubs = [
            "real madrid", "barcelona", "psg", "manchester united", "manchester city",
            "chelsea", "liverpool", "arsenal", "bayern munich", "juventus", "inter milan",
            "ac milan", "napoli", "marseille", "ajax", "benfica", "porto"
        ]
        self.prévision = PredictionEngine()
        self.connaissances = self._charger_connaissances()

        # Charger le modèle spaCy pour la compréhension sémantique
        try:
            self.nlp = spacy.load("fr_core_news_md")
            logging.info("✅ Modèle spaCy chargé avec succès.")
        except Exception as e:
            logging.error(f"❌ Erreur de chargement de spaCy : {e}")
            self.nlp = None

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
            json.dump(self.connaissances, f, ensure_ascii=False, indent=2)

    def apprendre_club(self, nom_club):
        nom_club_lower = nom_club.lower()
        if nom_club_lower in self.connaissances:
            return f"Je connais déjà {nom_club}. Voici ce que je sais : {self.connaissances[nom_club_lower]['définition']}"
        else:
            description = self.chercher_club_en_ligne(nom_club)
            self.connaissances[nom_club_lower] = {
                "définition": description,
                "tactique": "À compléter.",
                "transfert": "À compléter.",
                "performance": "À compléter."
            }
            self._sauvegarder_connaissances()
            self.clubs.append(nom_club_lower)
            return description

    def predict_match(self, message):
        if " vs " not in message.lower():
            return "Format incorrect. Utilise : <Équipe1> vs <Équipe2>"

        parts = message.split(" vs ")
        if len(parts) != 2:
            return "Format incorrect."

        team1 = parts[0].strip()
        team2 = parts[1].strip()

        resultat = self.analyse_match(team1, team2)
        self.historique_predictions.append(f"{team1} vs {team2} → {resultat}")
        return resultat

    def afficher_historique_prédictions(self, nombre_lignes=None):
        if not self.historique_predictions:
            return "Aucune prédiction enregistrée."
        lignes = self.historique_predictions[-nombre_lignes:] if nombre_lignes else self.historique_predictions
        return "\n".join(lignes)

    def detect_intention(self, doc):
        """Détecte l'intention de la question à partir du doc spaCy."""
        if any(token.lemma_ == "créer" for token in doc):
            return "question_fondation"
        elif any(token.lemma_ == "gagner" for token in doc):
            return "question_résultat"
        elif any(token.lemma_ == "jouer" for token in doc):
            return "question_match"
        else:
            return "question_générale"

    def operer(self, message):
        """Traite une question libre de l'utilisateur avec compréhension sémantique."""
        # Si spaCy n'est pas disponible, fallback sur l'ancien comportement
        if not self.nlp:
            return self._operer_fallback(message)

        try:
            # Traiter la question avec spaCy
            doc = self.nlp(message)

            # Détecter l'intention
            intention = self.detect_intention(doc)

            # Extraire les entités nommées (clubs, joueurs, etc.)
            entites = [ent.text.lower() for ent in doc.ents if ent.label_ in ["ORG", "PERSON"]]

            # Répondre selon l'intention et les entités détectées
            if intention == "question_fondation" and entites:
                return self.repondre_fondation(entites[0])
            elif intention == "question_résultat" and entites:
                return self.repondre_resultat(entites[0])
            elif intention == "question_match" and len(entites) >= 2:
                return self.analyse_match(entites[0], entites[1])
            else:
                # Fallback : recherche générale
                return self.chercher_club_en_ligne(message)

        except Exception as e:
            logging.error(f"Erreur spaCy : {e}")
            return self._operer_fallback(message)

    def _operer_fallback(self, message):
        """Ancien comportement de operer() — fallback si spaCy échoue."""
        message_lower = message.lower()
        for club in self.clubs:
            if club in message_lower:
                if club in self.connaissances:
                    return self.connaissances[club]["définition"]
                else:
                    return self.chercher_club_en_ligne(club)

        try:
            termes = [
                f"{message} football",
                f"football {message}",
                f"club de {message}",
                message
            ]

            for terme in termes:
                search_url = build_search_url(terme)
                try:
                    resp = requests.get(search_url, headers=WIKI_HEADERS, timeout=5)
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    results = data.get("query", {}).get("search", [])
                    for result in results:
                        title = result["title"]
                        if any(kw in title.lower() for kw in ["fc", "football", "club", "équipe"]):
                            summary_url = build_summary_url(title)
                            resp2 = requests.get(summary_url, headers=WIKI_HEADERS, timeout=5)
                            if resp2.status_code == 200:
                                page_data = resp2.json()
                                summary = page_data.get("extract", "Résumé non disponible.")
                                return f"Selon Wikipedia ({title}) : {summary}"
                except Exception:
                    continue

            return "Je ne sais pas. Essaye d’être plus précis."

        except Exception as e:
            return f"Je ne sais pas. (Erreur: {e})"

    def repondre_fondation(self, entite):
        """Répond à une question sur la fondation d'un club."""
        if entite in self.connaissances:
            return self.connaissances[entite]["définition"]
        else:
            return self.chercher_club_en_ligne(entite)

    def repondre_resultat(self, entite):
        """Répond à une question sur les résultats d'un club."""
        info = get_team_info(entite)
        if info:
            forme = get_team_form(info.get("id"))
            if forme and forme.get("performance_percent"):
                return f"Récemment, {entite.title()} a {forme['performance_percent']:.1f}% de victoires."
        return f"Je cherche les derniers résultats de {entite}..."

    def analyse_match(self, team1_name, team2_name, home_team=None):
        team1_id = self.get_team_id(team1_name)
        team2_id = self.get_team_id(team2_name)
        moteur = self.prévision

        force1 = moteur.team_strength.get(team1_name.lower(), DEFAULT_TEAM_STRENGTH)
        force2 = moteur.team_strength.get(team2_name.lower(), DEFAULT_TEAM_STRENGTH)

        if home_team and home_team.lower() == team1_name.lower():
            force1 += HOME_ADVANTAGE_BONUS
        elif home_team and home_team.lower() == team2_name.lower():
            force2 += HOME_ADVANTAGE_BONUS

        forme1 = get_team_form(team1_id)
        forme2 = get_team_form(team2_id)
        force1 += forme1.get("bonus", 0)
        force2 += forme2.get("bonus", 0)

        h2h = get_head_to_head(team1_id, team2_id)
        force1 += h2h.get("bonus_team1", 0)
        force2 += h2h.get("bonus_team2", 0)

        if force1 > force2:
            return f"📊 Analyse: {team1_name.title()} est favori ({force1} vs {force2})"
        elif force2 > force1:
            return f"📊 Analyse: {team2_name.title()} est favori ({force2} vs {force1})"
        else:
            return f"📊 Analyse: Match équilibré ({force1} vs {force2})"

    def get_team_id(self, team_name):
        info = get_team_info(team_name)
        return info["id"] if info else None