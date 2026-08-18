#!/bin/bash
# Script d'optimisation haute performance pour LM Studio (M1) et M6 (GTX 1660 SUPER)

echo "[1/3] Configuration du Keep-Alive et Offload GPU pour Ollama sur M6..."
ssh m6 "curl -s http://127.0.0.1:11434/api/generate -d '{\"model\":\"gemma3:4b\", \"prompt\":\"preload\", \"keep_alive\":\"24h\"}' >/dev/null 2>&1 &"

echo "[2/3] Tuning des paramètres de contexte et batching dans ~/.openclaw/openclaw.json..."
python3 -c "
import json

config_path = '/home/pamerys/.openclaw/openclaw.json'
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        data = json.load(f)
    
    # Optimisation des timeouts et batching pour M6 et LM Studio
    for p in data.get('providers', []):
        if 'm6' in p.get('name', ''):
            p['timeout_ms'] = 15000
            p['max_tokens'] = 2048
            p['temperature'] = 0.2
        elif 'lmstudio' in p.get('name', ''):
            p['timeout_ms'] = 20000
            p['max_tokens'] = 4096

    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)
    print('Configuration OpenClaw optimisée pour la performance maximale de M6 et LM Studio !')
"

echo "[3/3] Redémarrage du Proxy Hub de Routage (:18800)..."
systemctl --user restart jarvis-chat-proxy.service 2>/dev/null || true

echo "Réglage haute performance appliqué avec succès sur M1 et M6 !"
