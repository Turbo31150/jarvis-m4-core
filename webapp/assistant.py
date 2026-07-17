# assistant.py — barre latérale IA (brique B1), 0-token via ai_local.
# Logique captée de Mochii, reconstruite native : cascade cache→cluster→cloud→Ollama
# local (garde thermique 82°C déjà dans ai_local), persona = préfixe système,
# backend renvoyé (transparence). Aucune IA facturée au runtime.
from flask import jsonify, request
import ai_local

PERSONAS = {
    "standard": "",
    "demarches": "Tu es un assistant expert des démarches administratives françaises. Réponds clairement et cite l'organisme ou le formulaire compétent quand c'est pertinent.",
    "falc": "Réponds en FALC (Facile À Lire et à Comprendre) : phrases courtes, mots simples, une idée par phrase.",
    "mediateur": "Tu es un médiateur bienveillant. Rassure, explique pas à pas, sans jargon.",
    "senior": "Tu t'adresses à une personne peu à l'aise avec le numérique. Explique très simplement, une étape à la fois.",
}


def register(app):
    @app.route("/api/assistant", methods=["POST"])
    def api_assistant():
        data = request.get_json(force=True) or {}
        prompt = (data.get("prompt") or "").strip()
        persona = data.get("persona", "standard")
        if not prompt:
            return jsonify({"error": "prompt vide"}), 400
        if len(prompt) > 8000:  # garde-fou anti-pollution (aligné sur le labo)
            return jsonify({"error": "prompt trop long (max 8000)"}), 422
        system = PERSONAS.get(persona) or None
        try:
            res = ai_local.generate(prompt, system=system, cache=True, max_tokens=900)
        except Exception:
            return jsonify({"error": "IA locale indisponible, réessaie plus tard"}), 503
        return jsonify(
            {
                "texte": res.get("text", ""),
                "backend": res.get("backend"),
                "cached": res.get("cached", False),
                "persona": persona,
            }
        )

    @app.route("/api/backends", methods=["GET"])
    def api_backends():
        # État de la cascade (cluster/cloud/ollama + température) — transparence.
        return jsonify(ai_local.backend_status())
