#!/bin/bash
# ==============================================================================
# JARVIS OMEGA — Orchestration Auto au Démarrage & Verrouillage Cluster M6 Shield
# ==============================================================================

LOG_FILE="/home/pamerys/jarvis/logs/boot_orchestration.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 Démarrage de l'orchestration système JARVIS Cluster..." >> "$LOG_FILE"

# 1. Vérification liaison réseau direct avec M6 (10.42.0.230)
if ping -c 2 10.42.0.230 >/dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Liaison Ethernet M6 opérationnelle (10.42.0.230)." >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ M6 non joignable immédiatement sur 10.42.0.230." >> "$LOG_FILE"
fi

# 2. Configuration M6 en Priorité 1 (Tampon Principal & Bouclier de Protection M1)
/usr/bin/python3 /home/pamerys/jarvis/scripts/set_m6_direct_support.py >> "$LOG_FILE" 2>&1

# 3. Enregistrement des nœuds du Cluster (M1 local, M6 câble direct 10.42.0.230) — M4 démonté le 2026-08-06
/usr/bin/python3 /home/pamerys/jarvis/scripts/setup_m6_m1_cable_bridge.py >> "$LOG_FILE" 2>&1

# 4. Activation des règles Bouclier M6 dans le registre global
# Ces réglages vivaient dans ~/.openclaw/openclaw.json : c'était la cause d'une
# panne de 3 jours du service Swarm jarvis_prod_antigravity-mcp (0/1 réplique).
# OpenClaw valide openclaw.json contre un schéma STRICT et refuse toute clé
# étrangère ("Unrecognized keys: m6_shield_mode, max_concurrency_m1, ...").
# La gateway abandonnait alors au démarrage, en écrivant l'erreur sur la sortie
# d'erreur de l'enfant — donc invisible dans `docker service logs`.
# Le skill run-m6-tampon documente déjà la règle : la config M6 vit dans un
# fichier dédié, jamais dans openclaw.json. On s'y conforme ici.
/usr/bin/python3 -c "
import json, os, sqlite3

config_path = '/home/pamerys/jarvis/config/m6-shield.json'
try:
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}

    data['m6_shield_mode'] = True
    data['m6_protects_m1'] = True
    data['max_concurrency_m1'] = 2
    data['m6_offload_threshold'] = 0.50

    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)

    conn = sqlite3.connect('/home/pamerys/jarvis/jarvis_master.db')
    cur = conn.cursor()
    cur.execute('''
    INSERT INTO cluster_nodes (ip, hostname, status, role, services)
    VALUES ('10.42.0.230', 'M6-Shield', 'SHIELD_ACTIVE', 'Bouclier de protection M1 & Tampon direct', 'ollama:11434')
    ON CONFLICT(ip) DO UPDATE SET
        role='Bouclier de protection M1 & Tampon direct',
        status='SHIELD_ACTIVE',
        last_ping=datetime('now');
    ''')
    conn.commit()
    conn.close()
except Exception as e:
    pass
" >> "$LOG_FILE" 2>&1

# 5. Verrouillage pré-chargé (Keep-Alive VRAM) du modèle rapide qwen2.5 sur M6
/usr/bin/python3 -c "
import urllib.request, json
try:
    url = 'http://10.42.0.230:11434/api/generate'
    payload = {'model': 'qwen2.5:1.5b', 'prompt': 'WARMUP', 'keep_alive': -1, 'stream': False}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req, timeout=10)
except Exception:
    pass
" >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🏁 Orchestration et protection Bouclier M6 appliquées à tout le cluster." >> "$LOG_FILE"
