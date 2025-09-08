# api_connector.py

import requests
from config import SPORTMONKS_API_KEY, SPORTMONKS_BASE_URL

def get_team_info(nom_club):
    """
    Récupère les informations d'une équipe via l'API SportMonks.
    Retourne un dictionnaire ou None si non trouvé.
    """
    url = f"{SPORTMONKS_BASE_URL}/teams"
    params = {
        "api_token": SPORTMONKS_API_KEY,
        "search": nom_club
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("data"):
            team = data["data"][0]
            return {
                "id": team["id"],
                "name": team["name"],
                "country": team["country"]["name"],
                "founded": team.get("founded"),
                "stadium": team.get("venue", {}).get("name", "Inconnu")
            }
        else:
            print(f"ℹ️ Aucun résultat pour '{nom_club}' dans l'API SportMonks.")
            return None

    except Exception as e:
        print(f"❌ Erreur API Sportmonks: {e}")
        return None