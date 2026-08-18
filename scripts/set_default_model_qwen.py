import json
import os

config_path = "/home/pamerys/.openclaw/openclaw.json"
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        data = json.load(f)
    
    data["default_model"] = "qwen/qwen3.5-9b"
    data["fast_model"] = "qwen/qwen3.5-9b"
    
    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)
    print("qwen/qwen3.5-9b configuré comme modèle par défaut et prioritaire absolu !")
