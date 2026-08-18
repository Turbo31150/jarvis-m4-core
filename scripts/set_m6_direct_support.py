import json
import os

config_path = "/home/pamerys/.openclaw/openclaw.json"

if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        data = json.load(f)
    
    # Provider M6 branché en câble direct (MODE SECOUR / TAMPON INTÉGRAL EN PREMIER)
    p1_m6_direct = {
        "name": "m6-direct-cable-primary-buffer",
        "api": "ollama",
        "baseUrl": "http://10.42.0.230:11434",
        "models": ["qwen2.5:1.5b", "gemma3:4b", "deepseek-r1:7b"],
        "timeout_ms": 5000,
        "priority": 1,
        "role": "tampon_principal_mode_secour_cable_direct",
        "interface": "enxf8e43b9b67d4",
        "target_ip": "10.42.0.230"
    }

    # Provider secondaire : M4 demonte le 2026-08-06, renvoye sur le hub de cascade
    p2 = {
        "name": "secondary-qwen-m4",
        "api": "openai-completions",
        "baseUrl": "http://127.0.0.1:18800/v1",
        "models": ["qwen/qwen3.5-9b", "openai/gpt-oss-20b"],
        "timeout_ms": 3000,
        "priority": 2
    }

    # Backup LM Studio M1
    p3 = {
        "name": "m1-lmstudio-heavy",
        "api": "openai-completions",
        "baseUrl": "http://127.0.0.1:1234/v1",
        "models": ["qwen3.5-27b-claude-distill"],
        "timeout_ms": 15000,
        "priority": 3
    }
    
    data["providers"] = [p1_m6_direct, p2, p3]
    data["m6_mode_secour_active"] = True
    data["m6_cable_interface"] = "10.42.0.230"

    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    print("MODE SECOUR ACTIF : M6 (10.42.0.230 - câble direct) passe en PRIORITÉ 1 (tampon principal) !")
