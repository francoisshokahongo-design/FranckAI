# utils/head_to_head.py

class HeadToHead:
    def __init__(self, team1_name, team2_name):
        self.team1_name = team1_name
        self.team2_name = team2_name
        self.matches = []  # Liste des résultats: 'Team1', 'Team2', 'Draw'

    def add_match_result(self, result):
        """Ajoute le résultat d'un match entre les deux équipes."""
        if result not in ['Team1', 'Team2', 'Draw']:
            raise ValueError("Résultat doit être 'Team1', 'Team2' ou 'Draw'")
        self.matches.append(result)

    def get_record(self):
        """Retourne le bilan des confrontations."""
        team1_wins = self.matches.count('Team1')
        team2_wins = self.matches.count('Team2')
        draws = self.matches.count('Draw')
        return {
            self.team1_name: team1_wins,
            self.team2_name: team2_wins,
            'Draws': draws,
            'Total': len(self.matches)
        }

    def calculate_bonuses(self):
        """
        Calcule les bonus pour chaque équipe selon leur domination historique.
        """
        if not self.matches:
            return {"bonus_team1": 0, "bonus_team2": 0}

        total = len(self.matches)
        team1_wins = self.matches.count('Team1')
        team2_wins = self.matches.count('Team2')

        win_rate_team1 = team1_wins / total
        win_rate_team2 = team2_wins / total

        bonus_team1 = 4 if win_rate_team1 > 0.6 else 2 if win_rate_team1 > 0.4 else 0
        bonus_team2 = 4 if win_rate_team2 > 0.6 else 2 if win_rate_team2 > 0.4 else 0

        return {
            "bonus_team1": bonus_team1,
            "bonus_team2": bonus_team2,
            "record": self.get_record()
        }


def get_head_to_head(team1_id, team2_id):
    """
    Simule la récupération des stats H2H via les IDs des équipes.
    """
    simulated_h2h = {
        (1, 2): {"team1_name": "Real Madrid", "team2_name": "Barcelona", "results": ['Team1', 'Team2', 'Team1', 'Draw', 'Team1']},
        (1, 3): {"team1_name": "Real Madrid", "team2_name": "PSG", "results": ['Team1', 'Team2', 'Draw']},
        (2, 4): {"team1_name": "Barcelona", "team2_name": "Manchester City", "results": ['Team2', 'Team2', 'Draw', 'Team1']},
        (3, 4): {"team1_name": "PSG", "team2_name": "Manchester City", "results": ['Team2', 'Team2', 'Team1']},
        (5, 6): {"team1_name": "Bayern Munich", "team2_name": "Chelsea", "results": ['Team1', 'Draw', 'Team1', 'Team2']},
        (6, 7): {"team1_name": "Chelsea", "team2_name": "Juventus", "results": ['Draw', 'Team2', 'Team1']},
    }

    h2h_data = simulated_h2h.get((team1_id, team2_id)) or simulated_h2h.get((team2_id, team1_id))

    if not h2h_data:
        h2h = HeadToHead(f"Team_{team1_id}", f"Team_{team2_id}")
        h2h.matches = ['Draw', 'Draw']
    else:
        h2h = HeadToHead(h2h_data["team1_name"], h2h_data["team2_name"])
        h2h.matches = h2h_data["results"]

    return h2h.calculate_bonuses()