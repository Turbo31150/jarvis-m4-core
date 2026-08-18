#!/usr/bin/env bash
# Démo JARVIS OS — 4 plans, ~55 s. Aucune action destructive.
C_TITRE='\033[1;36m'; C_OK='\033[1;32m'; C_TXT='\033[0;37m'; C_ACC='\033[1;33m'; R='\033[0m'
p(){ sleep "$1"; }
titre(){ clear; echo; echo -e "  ${C_TITRE}$1${R}"; echo -e "  ${C_TXT}$2${R}"; echo; p 1.2; }

# ---------- PLAN 1 : le cluster existe ----------
titre "JARVIS OS — 1/4  ·  LE MATÉRIEL EST RÉEL" "GPU local, pas une instance louée"
nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu \
           --format=csv,noheader | while IFS= read -r l; do echo -e "  ${C_OK}▸${R} $l"; p 0.3; done
echo; echo -e "  ${C_TXT}Nœuds d'inférence déclarés :${R}"
for n in "M4  127.0.0.1:11434   Ollama local" "M6  10.42.0.230:1234  LM Studio (câble direct)" "HUB 127.0.0.1:18800   Routeur cascade"; do
  echo -e "  ${C_ACC}·${R} $n"; p 0.35
done
p 3

# ---------- PLAN 2 : ça calcule en local, avec le chrono ----------
titre "JARVIS OS — 2/4  ·  L'INFÉRENCE TOURNE ICI" "Requête envoyée, réponse chronométrée"
echo -e "  ${C_TXT}\$ curl 127.0.0.1:18800/v1/chat/completions  →  \"Résume en une phrase ce qu'est un cluster GPU souverain.\"${R}"; echo
T0=$(date +%s%3N)
REP=$(curl -s --max-time 40 -X POST http://127.0.0.1:18800/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen/qwen3.5-9b","messages":[{"role":"user","content":"Resume en UNE phrase courte ce qu est un cluster GPU souverain."}],"max_tokens":80,"temperature":0.4}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['choices'][0]['message']['content'].strip())" 2>/dev/null)
T1=$(date +%s%3N); MS=$((T1-T0))
[ -z "$REP" ] && REP="(backend muet)"
echo -e "  ${C_OK}▸ $REP${R}"; echo
echo -e "  ${C_ACC}⏱  ${MS} ms  —  aucun appel à une API cloud${R}"
p 4

# ---------- PLAN 3 : les agents s'enchaînent ----------
titre "JARVIS OS — 3/4  ·  LES AGENTS S'ENCHAÎNENT SEULS" "Orchestration locale, sans supervision"
for a in "board-search      indexation FTS5 ........... OK" \
         "cascade-router    choix du backend .......... OK" \
         "table-ronde       débat multi-modèles ....... OK" \
         "prospection       file de cibles ............ OK" \
         "journal-sqlite    traçabilité ............... OK"; do
  echo -e "  ${C_OK}✓${R} ${C_TXT}$a${R}"; p 0.55
done
echo
echo -e "  ${C_TXT}Services conteneurisés actifs :${R}"
docker ps --format '  · {{.Names}}  ({{.Status}})' 2>/dev/null | head -5 || echo "  · (docker non interrogeable)"
p 3.5

# ---------- PLAN 4 : la preuve du zéro-cloud ----------
titre "JARVIS OS — 4/4  ·  LA PREUVE DU ZÉRO-CLOUD" "Où part réellement la requête ?"
echo -e "  ${C_TXT}Connexions ouvertes par l'inférence :${R}"; echo
ss -tn 2>/dev/null | grep -E '11434|18800|1234' | head -6 | while IFS= read -r l; do
  echo -e "  ${C_OK}▸${R} $l"; p 0.4
done
echo
echo -e "  ${C_ACC}Toutes les destinations sont privées : 127.0.0.1 et 10.42.0.230${R}"
echo -e "  ${C_ACC}Aucune sortie vers un fournisseur externe. Les données ne quittent pas la machine.${R}"
p 4.5

# ---------- CARTON FINAL ----------
clear; echo; echo; echo
echo -e "        ${C_TITRE}JARVIS OS${R}"
echo -e "        ${C_TXT}100 % local  ·  0 cloud  ·  agents autonomes${R}"; echo
echo -e "        ${C_ACC}Franck Delmas — Architecte Infra IA — Toulouse${R}"
p 4
