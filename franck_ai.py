# franck_ai.py

import sys
import io
import logging
import requests
import json
import os
import re
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
    # Supprimer tout caractère non-ASCII pour éviter les problèmes
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return quote(text.strip())

def build_search_url(query):
    """Construit une URL de recherche Wikipedia propre et sécurisée."""
    encoded_query = safe_quote(query)
    return f"https://fr.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&format=json"

def build_summary_url(title):
    """Construit une URL de résumé Wikipedia propre et sécurisée."""
    encoded_title = safe_quote(title)
    return f"https://fr.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"

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

    def operer(self, message):
        message_lower = message.lower()
        for club in self.clubs:
            if club in message_lower:
                if club in self.connaissances:
                    return self.connaissances[club]["définition"]
                else:
                    return self.chercher_club_en_ligne(club)

        # Dernier recours : Wikipedia via API REST — VERSION SÉCURISÉE
        try:
            termes = [
                f"{message} football",
                f"football {message}",
                f"club de {message}",
                message
            ]

            for terme in termes:
                search_url = build_search_url(terme)
                logging.info(f"🔍 Requête Wikipedia : {search_url}")

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
                except Exception as e:
                    logging.error(f"Erreur lors de la recherche '{terme}': {e}")
                    continue

            raise Exception("Aucun résultat pertinent trouvé")

        except Exception as e:
            return f"Je ne sais pas. Essaye d’être plus précis. (Erreur: {e})"

    def chercher_club_en_ligne(self, nom_club):
        traductions = {
            "barcelone": "barcelona",
            "réal madrid": "real madrid",
            "psg": "paris saint-germain",
            "manchester united": "manchester united",
            "manchester city": "manchester city",
            "bayern": "bayern munich"
        }
        nom_club = traductions.get(nom_club.lower(), nom_club)

        # 1️⃣ Essayer d'abord via SportMonks (api_connector)
        info = get_team_info(nom_club)
        if info:
            description = (
                f"{info['name']} est basé en {info['country']}. "
                f"Fondé en {info['founded']}, son stade est {info['stadium']}."
            )
            self.connaissances[nom_club.lower()] = {
                "définition": description,
                "tactique": "Tactique à compléter.",
                "transfert": "Transferts à compléter.",
                "performance": "Performance à compléter."
            }
            self._sauvegarder_connaissances()
            return description

        # 2️⃣ Si SportMonks échoue, essayer via RapidAPI (api-football)
        url = f"https://api-football-v1.p.rapidapi.com/v3/teams?search={nom_club}"
        headers = {
            "X-RapidAPI-Key": RAPID_API_KEY,
            "X-RapidAPI-Host": RAPID_API_HOST
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()

            if data.get("response"):
                club = data["response"][0]["team"]
                description = (
                    f"{club['name']} est basé à {club.get('country', 'pays inconnu')}. "
                    f"Fondé en {club.get('founded', 'année inconnue')}, "
                    f"son stade est {club['venue'].get('name', 'stade inconnu')}."
                )
                self.connaissances[nom_club.lower()] = {
                    "définition": description,
                    "tactique": "Tactique à compléter.",
                    "transfert": "Transferts à compléter.",
                    "performance": "Performance à compléter."
                }
                self._sauvegarder_connaissances()
                return description
            else:
                logging.info(f"ℹ️ Aucun résultat via RapidAPI pour '{nom_club}'")

        except Exception as e:
            logging.error(f"❌ Erreur RapidAPI pour '{nom_club}': {e}")

        # 3️⃣ DERNIER RECOURS : WIKIPEDIA via API REST (PLUS FIABLE)
        try:
            # Liste des titres à essayer, du plus spécifique au plus général
            titres_a_tester = [
                f"FC {nom_club.title()}",
                f"{nom_club.title()} FC",
                f"Futbol Club {nom_club.title()}",
                f"{nom_club.title()} (football)",
                f"{nom_club.title()} football club",
                f"Club de {nom_club.title()}",
                nom_club.title()
            ]

            for titre in titres_a_tester:
                api_url = build_summary_url(titre)
                logging.info(f"📖 Test résumé : {api_url}")

                try:
                    resp = requests.get(api_url, headers=WIKI_HEADERS, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        # Vérifier que c'est bien un club de football
                        if "description" in data and "football" in data.get("description", "").lower():
                            summary = data.get("extract", "Résumé non disponible.")
                            description = f"Selon Wikipedia ({data.get('title', titre)}) : {summary}"
                            self.connaissances[nom_club.lower()] = {
                                "définition": description,
                                "tactique": "Tactique à compléter.",
                                "transfert": "Transferts à compléter.",
                                "performance": "Performance à compléter."
                            }
                            self._sauvegarder_connaissances()
                            logging.info(f"✅ Wikipedia API : page '{data.get('title')}' utilisée pour '{nom_club}'")
                            return description
                        else:
                            logging.info(f"ℹ️ Page '{titre}' non pertinente (pas liée au football).")
                            continue
                    elif resp.status_code == 404:
                        continue
                except Exception as e:
                    logging.error(f"Erreur sur '{titre}': {e}")
                    continue

            # Si rien ne marche, essayer une recherche libre
            search_term = f"{nom_club} football"
            search_url = build_search_url(search_term)
            resp = requests.get(search_url, headers=WIKI_HEADERS, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("query", {}).get("search", [])
                for result in results:
                    title = result["title"]
                    if any(kw in title.lower() for kw in ["fc", "football", "club"]):
                        summary_url = build_summary_url(title)
                        resp2 = requests.get(summary_url, headers=WIKI_HEADERS, timeout=5)
                        if resp2.status_code == 200:
                            page_data = resp2.json()
                            summary = page_data.get("extract", "Résumé non disponible.")
                            description = f"Selon Wikipedia ({title}) : {summary}"
                            self.connaissances[nom_club.lower()] = {
                                "définition": description,
                                "tactique": "Tactique à compléter.",
                                "transfert": "Transferts à compléter.",
                                "performance": "Performance à compléter."
                            }
                            self._sauvegarder_connaissances()
                            logging.info(f"✅ Wikipedia API (recherche) : page '{title}' utilisée pour '{nom_club}'")
                            return description

            raise Exception("Aucune page pertinente trouvée")

        except Exception as e:
            return f"Je n'ai trouvé aucune info fiable sur '{nom_club}' sur Wikipedia. (Erreur: {e})"

    def analyse_match(self, team1_name, team2_name, home_team=None):
        team1_id = self.get_team_id(team1_name)
        team2_id = self.get_team_id(team2_name)
        moteur = self.prévision  # ← Utilise l'instance existante

        force1 = moteur.team_strength.get(team1_name.lower(), DEFAULT_TEAM_STRENGTH)
        force2 = moteur.team_strength.get(team2_name.lower(), DEFAULT_TEAM_STRENGTH)

        if home_team and home_team.lower() == team1_name.lower():
            force1 += HOME_ADVANTAGE_BONUS
        elif home_team and home_team.lower() == team2_name.lower():
            force2 += HOME_ADVANTAGE_BONUS

        forme1 = get_team_form(team1_id)
        forme2 = get_team_form(team2_id)
        force1 += forme1["bonus"]
        force2 += forme2["bonus"]

        h2h = get_head_to_head(team1_id, team2_id)
        force1 += h2h["bonus_team1"]
        force2 += h2h["bonus_team2"]

        if force1 > force2:
            return f"📊 Analyse: {team1_name.title()} est favori ({force1} vs {force2})"
        elif force2 > force1:
            return f"📊 Analyse: {team2_name.title()} est favori ({force2} vs {force1})"
        else:
            return f"📊 Analyse: Match équilibré ({force1} vs {force2})"

    def get_team_id(self, team_name):
        info = get_team_info(team_name)
        return info["id"] if info else None