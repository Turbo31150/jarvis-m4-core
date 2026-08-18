import json
import os

config_path = "/home/pamerys/.openclaw/openclaw.json"

primary_config = {
    "primary_model": "qwen/qwen3.5-9b",
    "primary_address": "http://10.42.0.1:11235",
    "primary_endpoint": "http://10.42.0.1:11235/v1",
    "default_model": "qwen/qwen3.5-9b",
    "fast_model": "qwen/qwen3.5-9b",
    "providers": [
        {
            "name": "primary-qwen-m4",
            "api": "openai-completions",
            "baseUrl": "http://10.42.0.1:11235/v1",
            "models": ["qwen/qwen3.5-9b"],
            "timeout_ms": 3000,
            "priority": 1
        },
        {
            "name": "m1-lmstudio",
            "api": "openai-completions",
            "baseUrl": "http://127.0.0.1:1234/v1",
            "models": ["qwen/qwen3.5-9b", "qwen3.5-35b"],
            "timeout_ms": 10000,
            "priority": 2
        },
        {
            "name": "ollama-m6",
            "api": "ollama",
            "baseUrl": "http://10.42.0.230:11434",
            "models": ["gemma3:4b", "deepseek-r1:7b"],
            "timeout_ms": 12000,
            "priority": 3
        }
    ]
}

with open(config_path, 'w') as f:
    json.dump(primary_config, f, indent=2)

print("CONFIRMATION : Modèle Principal et Adresse Principale verrouillés avec succès !")
