# app.py

from flask import Flask, render_template, request, jsonify
from franck_ai import Franck
import os

# Créer le dossier data/ si nécessaire
os.makedirs("data", exist_ok=True)

# Initialiser FranckAI
franck = Franck()

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_message = request.form.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Message vide"}), 400

    # Gestion des commandes spéciales
    if user_message.lower() in ["quitter", "exit", "stop"]:
        response = "Merci d’avoir utilisé FranckAI ⚽ À bientôt !"
    elif user_message.lower().startswith("ajoute club "):
        club = user_message[12:].strip()
        response = franck.apprendre_club(club)
    elif " vs " in user_message.lower():
        try:
            response = franck.predict_match(user_message)
        except Exception as e:
            response = f"Erreur de prédiction : {e}"
    elif user_message.lower() == "historique":
        response = franck.afficher_historique_prédictions()
    elif user_message.lower().startswith("historique "):
        try:
            n = int(user_message.split(" ")[1])
            response = franck.afficher_historique_prédictions(nombre_lignes=n)
        except ValueError:
            response = "Format incorrect. Utilise 'historique 5' par exemple."
    else:
        try:
            response = franck.operer(user_message)
        except Exception as e:
            response = f"Je n’ai pas compris. Erreur : {e}"

    return jsonify({"response": response})

if __name__ == "__main__":
    print("\n✅ FranckAI est prêt !")
    print("➡️  En local : http://127.0.0.1:5000")
    print("ℹ️  Le message 'development server' est normal — tu es en mode test.\n")

    # Masquer le warning de Werkzeug
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Lancer en mode debug uniquement en local
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))