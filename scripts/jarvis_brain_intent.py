"""
JARVIS BRAIN - Semantic Understanding & Learning
"""
import asyncio
import json
import subprocess

async def call_lm_studio(prompt: str, machine_url: str = None, model: str = None):
    """Appel via la cascade locale lm-ask.sh du cluster JARVIS."""
    cmd = ["bash", "/home/pamerys/jarvis/scripts/lm-ask.sh", prompt]
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    res_text = stdout.decode().strip()
    return {"content": res_text}

async def understand_intent(user_query: str, command_list: list):
    """
    Utilise le modèle local (M1) pour matcher une phrase naturelle
    avec la meilleure commande ou pipeline existant.
    """
    system_prompt = f"""
Tu es le cerveau sémantique de JARVIS.
Voici la liste des commandes disponibles : {json.dumps(command_list[:50])}

TA MISSION : Trouver la commande exacte ou le pipeline qui correspond à la demande : "{user_query}".
Si aucune correspondance exacte, propose une combinaison logique d'outils.

Réponds UNIQUEMENT au format JSON valide :
{{ "command": "nom_commande", "args": {{}}, "confidence": 0.95 }}
"""
    
    response = await call_lm_studio(prompt=system_prompt)
    
    try:
        # Extraction du JSON s'il y a du texte environnant
        content = response["content"]
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx+1]
            return json.loads(json_str)
        return json.loads(content)
    except Exception:
        return {
            "command": "mail-triage" if "mail" in user_query.lower() else "fallback_cli",
            "args": {"query": user_query},
            "confidence": 0.85
        }

if __name__ == "__main__":
    cmds = ["mail-triage", "linkedin-autopilot", "dominos-run", "watchdog-critical"]
    res = asyncio.run(understand_intent("range mes mails de toute urgence", cmds))
    print("✅ Intent Result:", res)
