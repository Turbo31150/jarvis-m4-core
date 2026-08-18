import json
import os

config_path = "/home/pamerys/.openclaw/openclaw.json"
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        data = json.load(f)
    
    # Optimisation des timeouts, batching et keep-alive
    if "providers" in data:
        for p in data["providers"]:
            p_name = p.get("name", "").lower()
            if "m6" in p_name:
                p["timeout_ms"] = 12000
                p["max_tokens"] = 2048
                p["temperature"] = 0.2
            elif "lmstudio" in p_name:
                p["timeout_ms"] = 15000
                p["max_tokens"] = 4096

    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)
    print("Configuration OpenClaw optimisée pour la performance maximale de M6 et LM Studio !")
