import json
import os

config_path = "/home/pamerys/.openclaw/openclaw.json"

if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        data = json.load(f)
    
    data["primary_node"] = "M1"
    data["primary_address"] = "http://127.0.0.1:1234"
    data["primary_endpoint"] = "http://127.0.0.1:1234/v1"
    data["primary_model"] = "qwen3.5-27b-claude-distill"
    
    providers = data.get("providers", [])
    m1_provider = {
        "name": "primary-m1-leader",
        "api": "openai-completions",
        "baseUrl": "http://127.0.0.1:1234/v1",
        "models": ["qwen3.5-27b-claude-distill", "qwen3.5-35b", "glm-4.7-flash"],
        "timeout_ms": 15000,
        "priority": 1
    }
    
    providers = [p for p in providers if p.get("name") != "primary-m1-leader"]
    providers.insert(0, m1_provider)
    data["providers"] = providers

    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)
    print("Nœud Leader M1 (127.0.0.1:1234) configuré comme NŒUD PRINCIPAL ABSOLU du cluster !")
