import json
import os

config_path = "/home/pamerys/.openclaw/openclaw.json"

if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        data = json.load(f)
    
    data["primary_address"] = "http://127.0.0.1:1234"
    data["primary_endpoint"] = "http://127.0.0.1:1234/v1"
    data["primary_model"] = "qwen/qwen3.5-9b"
    
    # Ajouter/Mettre à jour le provider
    providers = data.get("providers", [])
    m4_lan_provider = {
        "name": "primary-m4-lan",
        "api": "openai-completions",
        "baseUrl": "http://127.0.0.1:1234/v1",
        "models": ["qwen/qwen3.5-9b", "openai/gpt-oss-20b"],
        "timeout_ms": 3000,
        "priority": 1
    }
    
    providers = [p for p in providers if p.get("name") != "primary-m4-lan"]
    providers.insert(0, m4_lan_provider)
    data["providers"] = providers

    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)
    print("Adresse Principale mise à jour avec succès vers http://127.0.0.1:1234 !")
