#!/bin/bash
# lms-auto-load-dual.sh : Automatisme de démarrage persistant LM Studio Multi-GPU (Spécial Vitesse & Parallélisme)
# Garantit un débit maximal et l'exécution instantanée sans attente.

set -e
export PATH="$HOME/.lmstudio/bin:$PATH"

LM_URL="http://127.0.0.1:1234"

# Attente de la disponibilité de LM Studio (max 30s)
for i in {1..30}; do
    if curl -fsS "$LM_URL/v1/models" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

if ! curl -fsS "$LM_URL/v1/models" >/dev/null 2>&1; then
    echo "[lms-dual-load] LM Studio non disponible sur $LM_URL." >&2
    exit 1
fi

# 1. Chargement Modèle 1 (qwen/qwen3.5-9b sur RTX 3080 - High Speed Contexte 4096 / Parallel 4)
if ! lms ps 2>/dev/null | grep -q "qwen/qwen3.5-9b"; then
    echo "[lms-dual-load] Chargement Haute Vitesse Modèle 1 (qwen/qwen3.5-9b)..."
    lms load qwen/qwen3.5-9b -c 4096 --parallel 4 --gpu max -y || true
fi

# 2. Chargement Modèle 2 (hermes-2-pro-mistral-7b sur RTX 2060 - High Speed Contexte 4096 / Parallel 4)
if ! lms ps 2>/dev/null | grep -q "hermes-2-pro-mistral-7b"; then
    echo "[lms-dual-load] Chargement Haute Vitesse Modèle 2 (hermes-2-pro-mistral-7b)..."
    lms load hermes-2-pro-mistral-7b -c 4096 --parallel 4 --gpu max -y || true
fi

echo "[lms-dual-load] Chargement bi-GPU Haute Vitesse vérifié."
