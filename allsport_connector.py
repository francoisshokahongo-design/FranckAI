# allsport_connector.py

import requests
from config import ALLSPORT_API_KEY

ALLSPORT_BASE_URL = "https://apiv2.allsportsapi.com/football"

def get_countries():
    """Récupère la liste des pays pris en charge par AllSport API."""
    url = f"{ALLSPORT_BASE_URL}/?met=Countries&APIkey={ALLSPORT_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") == 1:
                return data["result"]
            else:
                print(f"❌ Erreur API AllSport : {data.get('message', 'Inconnue')}")
        else:
            print(f"❌ Erreur HTTP : {response.status_code}")
    except Exception as e:
        print(f"💥 Erreur : {e}")
    return []

def get_leagues_by_country(country_name):
    """Récupère les ligues d'un pays."""
    url = f"{ALLSPORT_BASE_URL}/?met=Leagues&countryName={country_name}&APIkey={ALLSPORT_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") == 1:
                return data["result"]
        else:
            print(f"❌ Erreur HTTP : {response.status_code}")
    except Exception as e:
        print(f"💥 Erreur : {e}")
    return []

def get_teams_by_league(league_id):
    """Récupère les équipes d'une ligue."""
    url = f"{ALLSPORT_BASE_URL}/?met=Teams&leagueId={league_id}&APIkey={ALLSPORT_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") == 1:
                return data["result"]
        else:
            print(f"❌ Erreur HTTP : {response.status_code}")
    except Exception as e:
        print(f"💥 Erreur : {e}")
    return []

def get_live_scores():
    """Récupère les matchs en direct."""
    url = f"{ALLSPORT_BASE_URL}/?met=Fixtures&matchLive=1&APIkey={ALLSPORT_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") == 1:
                return data["result"]
        else:
            print(f"❌ Erreur HTTP : {response.status_code}")
    except Exception as e:
        print(f"💥 Erreur : {e}")
    return []