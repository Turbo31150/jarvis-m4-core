#!/usr/bin/env bash
# =============================================================================
# RECONFIGURATION TOTALE DE M6 POUR MODE TAMPON INTÉGRAL & PROCESSEUR PRÉ-MÂCHAGE
# =============================================================================
set -uo pipefail

echo "⚡ 1. RECONFIGURATION DU SERVICES OLLAMA & DÉCONGESTION VRAM SUR M6 (10.42.0.230)..."
ssh -o ConnectTimeout=5 turbo@10.42.0.230 "bash -s" << 'REMOTE_CMD'
  # Ajustement des limites système et variables d'environnement Ollama
  sudo mkdir -p /etc/systemd/system/ollama.service.d/
  cat << 'SYSCONF' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
Environment="OLLAMA_KEEP_ALIVE=-1"
SYSCONF
  sudo systemctl daemon-reload
  sudo systemctl restart ollama
  echo "✅ Service Ollama débridé sur M6 (Parallel=4, KeepAlive=-1)."
REMOTE_CMD

echo "⚡ 2. INJECTION DES RÈGLES DE ROUTAGE TAMPON EXCLUSIF DANS LA CONFIGURATION CENTRALISÉE..."
python3 -c "
import json

config_path = '/home/pamerys/.openclaw/openclaw.json'
try:
    with open(config_path, 'r') as f:
        data = json.load(f)

    # Reconfiguration complète de M6 comme processeur de pré-mâchage exclusif
    data['m6_dedicated_buffer_mode'] = True
    data['m6_role'] = 'PREPROCESSOR_TAMPO_EXCLUSIF'
    data['m6_parallel_slots'] = 4
    data['m6_direct_ip'] = '10.42.0.230'
    data['m6_cable_interface'] = 'enxf8e43b9b67d4'

    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)
    print('✅ Registre OpenClaw mis à jour avec le rôle M6 processeur exclusif.')
except Exception as e:
    print('Erreur json:', e)
"

echo "⚡ 3. VERROUILLAGE DE LA PIPELINE SINGLE REQUEST EN TÊTE D'EXÉCUTION DU NŒUD M6..."
python3 /home/pamerys/jarvis/scripts/set_m6_direct_support.py

echo "================================================================="
echo "🎉 CAHIER DES CHARGES DE RECONFIGURATION TOTALE DE M6 APPLIQUÉ !"
echo "================================================================="
