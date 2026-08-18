#!/usr/bin/env bash
# audit-cascade-auto — relance `jarvis-audit.sh cascade` sur le DERNIER rapport.
#
# Le §9 du protocole veut une ré-itération périodique (« après 2 semaines
# d'actions »). `do_cascade` sait la faire mais exige `--previous <rapport>` :
# il fallait donc retrouver le dernier rapport à la main, ce qui condamnait la
# ré-itération à rester manuelle. Ce script est ce chaînon.
#
# Garde-fous AVANT de lancer (une cascade appelle le LLM, donc chauffe) :
# charge, RAM, GPU — mêmes seuils que cascade-micro-actions.py.

set -uo pipefail

RUNS="${AUDIT_RUNS:-/home/pamerys/jarvis/audit/runs}"
AUDIT="${AUDIT_BIN:-/home/pamerys/jarvis/scripts/jarvis-audit.sh}"
LOG="${AUDIT_LOG:-/home/pamerys/jarvis/logs/audit-cascade-auto.log}"
VERROU="/tmp/audit-cascade-auto.lock"
CHARGE_MAX=12
RAM_MAX=92
GPU_MAX=84

j() { echo "$(date '+%F %T') $*" | tee -a "$LOG"; }

# Verrou NON bloquant : deux cascades simultanées produiraient deux addendums
# concurrents sur le même rapport. `flock -n` échoue tout de suite plutôt que
# d'empiler des instances en attente — un timer qui se déclenche plus vite que
# le travail ne dure fabrique sinon une file infinie.
exec 9>"$VERROU"
flock -n 9 || { j "SKIP — cascade déjà en cours"; exit 0; }

# --- garde-fous
charge=$(awk '{printf "%.0f", $1}' /proc/loadavg)
ram=$(awk '/MemTotal/{t=$2} /MemAvailable/{a=$2} END{printf "%.0f", 100-100*a/t}' /proc/meminfo)
gpu=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader 2>/dev/null | sort -rn | head -1)
gpu=${gpu:-0}

if [ "$charge" -ge "$CHARGE_MAX" ] || [ "$ram" -ge "$RAM_MAX" ] || [ "$gpu" -ge "$GPU_MAX" ]; then
  j "BLOQUÉ — charge ${charge} · RAM ${ram}% · GPU ${gpu}°C (seuils ${CHARGE_MAX}/${RAM_MAX}/${GPU_MAX})"
  exit 0   # exit 0 VOLONTAIRE : un report n'est pas une panne, sinon le
           # OnFailure du timer alerterait à chaque machine chargée.
fi

# --- dernier rapport. `ls -t` sur le contenu, PAS sur les dossiers : un run
# interrompu laisse un dossier récent SANS AUDIT_DEEP_REPORT.md, et cascader
# sur un rapport absent produit un addendum vide sans rien signaler.
PREV="$(ls -t "$RUNS"/*/AUDIT_DEEP_REPORT.md 2>/dev/null | head -1)"
if [ -z "$PREV" ] || [ ! -s "$PREV" ]; then
  j "AUCUN rapport précédent exploitable dans $RUNS — rien à cascader"
  exit 0
fi

age_j=$(( ( $(date +%s) - $(stat -c %Y "$PREV") ) / 86400 ))
# trigger_days vient du YAML (workflows.cascade), pas d'une constante : le
# timer systemd tire les 1er et 15, mais si un audit complet a ete relance a
# la main entre-temps, cascader dessus produirait un addendum vide.
MIN_J=$(python3 -c "import yaml;print((yaml.safe_load(open('/home/pamerys/jarvis/AUDIT_CONFIG.yaml')).get('workflows') or {}).get('cascade',{}).get('trigger_days',14))" 2>/dev/null || echo 14)
if [ "$age_j" -lt "$MIN_J" ]; then
  j "SKIP — dernier rapport vieux de ${age_j} j < trigger_days=${MIN_J}"
  exit 0
fi
j "cascade sur $PREV (${age_j} j) — charge ${charge} · RAM ${ram}% · GPU ${gpu}°C"

if timeout "${AUDIT_TIMEOUT:-3600}" bash "$AUDIT" cascade --previous "$PREV" >>"$LOG" 2>&1; then
  ADD="$(ls -t "$RUNS"/*/AUDIT_ADDENDUM.md 2>/dev/null | head -1)"
  j "OK — addendum : ${ADD:-?}"
else
  rc=$?
  j "ÉCHEC rc=$rc (voir $LOG)"
  exit "$rc"
fi
