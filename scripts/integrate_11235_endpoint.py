import json
import os

config_path = "/home/pamerys/.openclaw/openclaw.json"
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        data = json.load(f)
    
    # Ajout/Mise à jour du provider 10.42.0.1:11235 (M4 Hub)
    m4_provider = {
        "name": "m4-hub-11235",
        "api": "openai-completions",
        "baseUrl": "http://10.42.0.1:11235/v1",
        "models": ["qwen/qwen3.5-9b", "openai/gpt-oss-20b"],
        "timeout_ms": 5000
    }
    
    providers = data.get("providers", [])
    # Remplacer ou ajouter
    providers = [p for p in providers if p.get("name") != "m4-hub-11235"]
    providers.append(m4_provider)
    data["providers"] = providers

    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)
    print("Endpoint http://10.42.0.1:11235 intégré avec succès dans OpenClaw Hub !")
