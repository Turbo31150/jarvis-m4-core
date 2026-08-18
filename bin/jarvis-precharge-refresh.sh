#!/usr/bin/env bash
# Rafraichit le prechargement unifie : miroir -> index -> TSV -> moteur `bloc`.
# Idempotent : deux passages consecutifs laissent exactement le meme etat.
# 0 token, 0 inference.
#
# 2026-08-18 — ajout de l'etape 0 (resync du miroir). Sans elle, le rafraichissement
# horaire reconstruisait l'index a partir d'un miroir fige : l'index restait
# "frais" au sens de la date de build tout en servant un corpus vieux de plusieurs
# jours, sans le moindre signal. Un index perime qui se declare a jour est pire
# qu'un index absent.
set -euo pipefail

PRECHARGE="$HOME/jarvis/bin/jarvis-precharge.py"
BLOC="$HOME/.claude/bin/bloc"
MIROIR="$HOME/m1-sync/bibliotheque-vivante"
TEMOIN="$MIROIR/lib/BLOCS-INDEX.tsv"
JOURNAL="$HOME/jarvis/logs/precharge.log"
M1_HOTE="${M1_HOTE:-100.112.114.32}"
SYNC_MAX_H="${SYNC_MAX_H:-6}"     # au-dela, le miroir est considere perime
mkdir -p "$(dirname "$JOURNAL")"

trace() { printf '%s %s\n' "$(date -Is)" "$*" | tee -a "$JOURNAL"; }

trace "=== rafraichissement du prechargement ==="

# --- 0. miroir : resync si perime ET M1 joignable (jamais bloquant) ---------
if [ ! -d "$MIROIR" ]; then
    trace "ERREUR miroir absent : $MIROIR — creer puis lancer '$BLOC sync'"
    exit 1
fi
age_h=$(( ( $(date +%s) - $(stat -c%Y "$TEMOIN" 2>/dev/null || echo 0) ) / 3600 ))
if [ "$age_h" -ge "$SYNC_MAX_H" ]; then
    if timeout 5 bash -c "</dev/tcp/${M1_HOTE}/22" 2>/dev/null; then
        trace "miroir perime (${age_h}h >= ${SYNC_MAX_H}h) — resync depuis M1"
        # `bloc sync` enchaine rsync + build ; on ne garde que le rsync ici,
        # le build definitif a lieu plus bas avec les TSV a jour.
        if ! timeout 300 "$BLOC" sync >>"$JOURNAL" 2>&1; then
            trace "AVERTISSEMENT resync M1 en echec — on poursuit sur le miroir existant (${age_h}h)"
        fi
        # Les series et l'index des agents vivent en local, pas sur M1 :
        # --ignore-existing pour ne jamais ecraser un fichier venu de M1.
        rsync -a --ignore-existing "$HOME/labo/bibliotheque/lib/"    "$MIROIR/lib/"    2>/dev/null || true
        rsync -a --ignore-existing "$HOME/labo/bibliotheque/series/" "$MIROIR/series/" 2>/dev/null || true
    else
        trace "AVERTISSEMENT miroir perime (${age_h}h) et M1 injoignable — index reconstruit sur corpus VIEUX"
    fi
else
    trace "miroir frais (${age_h}h < ${SYNC_MAX_H}h) — pas de resync"
fi

# --- 1. disque -> index local ----------------------------------------------
python3 "$PRECHARGE" build  2>&1 | tee -a "$JOURNAL"
# --- 2. index -> TSV au schema de `bloc` -----------------------------------
python3 "$PRECHARGE" export 2>&1 | tee -a "$JOURNAL"
# --- 3. TSV -> moteur de recherche unifie ----------------------------------
"$BLOC" build 2>&1 | tail -5 | tee -a "$JOURNAL"
# --- 4. controle de fraicheur : journalise a CHAQUE tick ---------------------
# Sans cette etape, une panne reste invisible jusqu'a ce que quelqu'un la cherche.
# C'est exactement ainsi que le board est reste muet du 13 au 17/08. Non bloquant :
# un composant mort ne doit pas empecher l'index de se reconstruire.
trace "--- fraicheur ---"
python3 "$PRECHARGE" fraicheur 2>&1 | tee -a "$JOURNAL" || true

trace "=== termine ==="
