# registre.py — lecteur de la bibliothèque de commandes rapides (registre partagé).
# Table de routage DÉCLARATIVE : expose les commandes routables côté prof + le
# mapping tâche→modèle + les règles de dispatch. Ne projette AUCUN secret
# (le bloc `secrets` du registre ne contient que des références). Lecture seule.
import json
import os

from flask import jsonify

_PATH = os.environ.get(
    "REGISTRY_PATH", "/home/pamerys/jarvis/scripts/mochii-commandes-rapides.json"
)


def register(app):
    @app.route("/api/registre", methods=["GET"])
    def api_registre():
        try:
            with open(_PATH, encoding="utf-8") as f:
                reg = json.load(f)
        except Exception:
            return jsonify({"error": "registre indisponible"}), 503
        cmds = [
            {
                "id": c["id"],
                "balises": c.get("balises"),
                "description": c.get("description"),
                "backend": c.get("backend"),
                "domino": c.get("domino"),
                "route": c["routes"]["prof"],
            }
            for c in reg.get("commandes", [])
            if c.get("routes", {}).get("prof") and c["routes"]["prof"] != "n/a"
        ]
        return jsonify(
            {
                "emplacement": "prof",
                "modeles": reg.get("modeles_locaux", {}).get("task_modele", {}),
                "dispatch": reg.get("dispatch", {}).get("regles", []),
                "commandes": cmds,
            }
        )
