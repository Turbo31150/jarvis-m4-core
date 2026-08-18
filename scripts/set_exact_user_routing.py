import json
import os

config_path = "/home/pamerys/.openclaw/openclaw.json"

routing_config = {
    "primary_node": "M1-Hub",
    "primary_address": "http://192.168.0.10:11235",
    "primary_endpoint": "http://192.168.0.10:11235/v1",
    "primary_model": "qwen/qwen3.5-9b",
    "default_model": "qwen/qwen3.5-9b",
    "fast_model": "qwen/qwen3.5-9b",
    "providers": [
        {
            "name": "m1-primary-qwen35",
            "api": "openai-completions",
            "baseUrl": "http://192.168.0.10:11235/v1",
            "models": ["qwen/qwen3.5-9b", "openai/gpt-oss-20b", "text-embedding-nomic-embed-text-v1.5"],
            "timeout_ms": 3000,
            "priority": 1
        },
        {
            "name": "m1-lmstudio-heavy",
            "api": "openai-completions",
            "baseUrl": "http://127.0.0.1:1234/v1",
            "models": ["qwen3.5-27b-claude-distill", "qwen3.5-35b"],
            "timeout_ms": 15000,
            "priority": 2
        },
        {
            "name": "m6-ollama-backup",
            "api": "ollama",
            "baseUrl": "http://10.42.0.230:11434",
            "models": ["gemma3:4b", "deepseek-r1:7b"],
            "timeout_ms": 12000,
            "priority": 3
        }
    ]
}

with open(config_path, 'w') as f:
    json.dump(routing_config, f, indent=2)

print("ALIGNEMENT PARFAIT : Modèle qwen/qwen3.5-9b + Adresse http://192.168.0.10:11235 + M1 verrouillés !")
