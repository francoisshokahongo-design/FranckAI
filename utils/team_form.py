# utils/team_form.py

class TeamForm:
    def __init__(self, team_name):
        self.team_name = team_name
        self.results = []  # Liste des résultats (ex: 'W', 'D', 'L')

    def add_result(self, result):
        """Ajoute un résultat à l'historique de l'équipe."""
        if result in ['W', 'D', 'L']:
            self.results.append(result)
        else:
            raise ValueError("Résultat doit être 'W' (Win), 'D' (Draw) ou 'L' (Loss)")

    def get_form(self):
        """Retourne les 5 derniers résultats."""
        return self.results[-5:]

    def calculate_performance(self):
        """Calcule le pourcentage de victoires."""
        if not self.results:
            return 0
        wins = self.results.count('W')
        return (wins / len(self.results)) * 100

    def calculate_bonus(self):
        """
        Calcule un bonus basé sur la performance récente.
        """
        perf = self.calculate_performance()
        if perf >= 80:
            return 5
        elif perf >= 60:
            return 3
        elif perf >= 40:
            return 1
        else:
            return 0


def get_team_form(team_id):
    """
    Simule la récupération de la forme d'une équipe via son ID.
    """
    simulated_data = {
        1: {"name": "Real Madrid", "results": ['W', 'W', 'D', 'W', 'W']},
        2: {"name": "Barcelona", "results": ['L', 'W', 'W', 'D', 'W']},
        3: {"name": "PSG", "results": ['W', 'L', 'W', 'W', 'D']},
        4: {"name": "Manchester City", "results": ['W', 'W', 'W', 'W', 'D']},
        5: {"name": "Bayern Munich", "results": ['L', 'W', 'L', 'W', 'W']},
        6: {"name": "Chelsea", "results": ['L', 'L', 'D', 'W', 'L']},
        7: {"name": "Juventus", "results": ['W', 'D', 'W', 'L', 'W']},
    }

    team_data = simulated_data.get(team_id)

    if not team_data:
        team_form = TeamForm(f"Team_{team_id}")
        team_form.results = ['D', 'D', 'D']
    else:
        team_form = TeamForm(team_data["name"])
        team_form.results = team_data["results"]

    return {
        "team_name": team_form.team_name,
        "last_5": team_form.get_form(),
        "performance_percent": team_form.calculate_performance(),
        "bonus": team_form.calculate_bonus()
    }