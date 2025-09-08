# Engine.py

import random
import os
from config import DEFAULT_TEAM_STRENGTH, HOME_ADVANTAGE_BONUS, PREDICTION_LOG_PATH

class PredictionEngine:
    def __init__(self):
        self.team_strength = {
            "real madrid": 90,
            "barcelona": 88,
            "psg": 85,
            "manchester united": 87,
            "manchester city": 92,
            "chelsea": 80,
            "liverpool": 86,
            "arsenal": 83,
            "bayern munich": 90,
            "juventus": 84,
            "inter milan": 82,
            "ac milan": 81,
            "napoli": 80,
            "marseille": 78,
            "ajax": 79,
            "benfica": 77,
            "porto": 76
        }

    def predict(self, team1, team2, home_team=None):
        team1 = team1.lower().strip()
        team2 = team2.lower().strip()

        strength1 = self.team_strength.get(team1, DEFAULT_TEAM_STRENGTH)
        strength2 = self.team_strength.get(team2, DEFAULT_TEAM_STRENGTH)

        # Bonus domicile
        if home_team:
            if home_team.lower() == team1:
                strength1 += HOME_ADVANTAGE_BONUS
            elif home_team.lower() == team2:
                strength2 += HOME_ADVANTAGE_BONUS

        # Simulation des scores
        score1 = max(0, int(random.gauss(strength1 / 20, 1)))
        score2 = max(0, int(random.gauss(strength2 / 20, 1)))

        prediction = f"{team1.title()} {score1} - {score2} {team2.title()}"
        self.log_prediction(team1, team2, prediction)
        return prediction

    def log_prediction(self, team1, team2, prediction):
        # Créer le dossier data/ s'il n'existe pas
        os.makedirs(os.path.dirname(PREDICTION_LOG_PATH), exist_ok=True)
        try:
            with open(PREDICTION_LOG_PATH, "a", encoding="utf-8") as file:
                file.write(f"{team1} vs {team2} → {prediction}\n")
        except Exception as e:
            print(f"⚠ Erreur lors de l'enregistrement de la prédiction: {e}")