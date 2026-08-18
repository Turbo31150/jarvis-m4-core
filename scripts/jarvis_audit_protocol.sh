#!/usr/bin/env bash
# =============================================================================
# PROTOCOLE D'AUDIT JARVIS — reproductible, 0-token, déterministe, READ-ONLY
# Rejoue les 3 audits de session (Système / Containers+n8n / cmdlib / Git / LLM).
# NE MODIFIE AUCUN SERVICE. Régénère docs/holding/AUDIT_COMPLET.md (horodaté).
# Verdict global : VERT / ORANGE / ROUGE  →  code retour 0 / 1 / 2.
#
# Usage : bash scripts/jarvis_audit_protocol.sh
# =============================================================================
set -uo pipefail   # PAS -e : un check qui échoue ne doit jamais tuer la cascade.

# -----------------------------------------------------------------------------
# Constantes / chemins
# -----------------------------------------------------------------------------
REPO_DIR="${JARVIS_REPO:-/home/pamerys/jarvis}"
N8N_DB="${N8N_DB:-$HOME/.n8n/database.sqlite}"
OUT_MD="$REPO_DIR/docs/holding/AUDIT_COMPLET.md"
TS="$(date '+%Y-%m-%d %H:%M:%S')"
TS_FILE="$(date '+%Y%m%d_%H%M%S')"

# Seuils
ZOMBIE_THRESHOLD=10
GPU_TEMP_WARN=80
GPU_TEMP_CRIT=90
JV_EXPECTED=24
LMS_EXPECTED_MODELS=4
ERR_RATE_WARN=20      # % taux d'erreur n8n FRAIS → ORANGE
ERR_RATE_CRIT=50      # % taux d'erreur n8n FRAIS → ROUGE

# Endpoints réseau (probes flaky → multi-essai)
LMS_URL="http://127.0.0.1:1234/v1/models"
PROXY_URL="http://127.0.0.1:18800/health"
GATEWAY_URL="http://127.0.0.1:9742/"
N8N_HEALTHZ="http://127.0.0.1:5678/healthz"

# Niveau global : 0=VERT 1=ORANGE 2=ROUGE (monotone croissant)
GLOBAL=0
# Buffers de rapport (Markdown)
REPORT=""
ANOMALIES=""

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
sev() { # $1 = niveau (0/1/2) → escalade le verdict global
  [ "$1" -gt "$GLOBAL" ] && GLOBAL="$1"
}
add()  { REPORT+="$1"$'\n'; }       # ligne au rapport
anom() { ANOMALIES+="- $1"$'\n'; }  # anomalie priorisée
lvltxt() { case "$1" in 0) echo "🟢 VERT";; 1) echo "🟡 ORANGE";; 2) echo "🔴 ROUGE";; esac; }

# Probe HTTP avec multi-essai : 3 tentatives espacées de 2s.
# $1=url  $2=label  → echo le body (1ère réussite) ; rc=0 ok / 1 down.
probe_retry() {
  local url="$1" label="$2" body rc i
  for i in 1 2 3; do
    body="$(curl -s -m 4 "$url" 2>/dev/null)"; rc=$?
    if [ $rc -eq 0 ] && [ -n "$body" ]; then
      echo "$body"; return 0
    fi
    [ $i -lt 3 ] && sleep 2
  done
  return 1
}

# Probe HTTP code-only avec multi-essai. $1=url → echo code, rc selon 2xx.
probe_code_retry() {
  local url="$1" code i
  for i in 1 2 3; do
    code="$(curl -s -m 4 -o /dev/null -w '%{http_code}' "$url" 2>/dev/null)"
    if [ "$code" = "200" ]; then echo "$code"; return 0; fi
    [ $i -lt 3 ] && sleep 2
  done
  echo "${code:-000}"; return 1
}

# =============================================================================
# CASCADE D'AUDIT
# =============================================================================
echo "=== PROTOCOLE D'AUDIT JARVIS — $TS (read-only) ==="
add "# AUDIT COMPLET JARVIS OS — $TS (régénéré par jarvis_audit_protocol.sh)"
add ""
add "> Audit **READ-ONLY** reproductible · aucun service modifié · cascade déterministe 0-token."
add "> Source : \`scripts/jarvis_audit_protocol.sh\` · détail historique : AUDIT_CONTAINERS_N8N.md, AUDIT_GITHUB_ARCHI.md, AUDIT_CMDLIB_COMMANDE.md."
add ""

# -----------------------------------------------------------------------------
# 1) SYSTÈME
# -----------------------------------------------------------------------------
echo "[1/6] Système…"
S_LVL=0
FAILED_SYS="$(systemctl --failed --no-legend --plain 2>/dev/null | awk '{print $1}' | grep -c . || true)"
FAILED_USR="$(systemctl --user --failed --no-legend --plain 2>/dev/null | awk '{print $1}' | grep -c . || true)"
FAILED_SYS="${FAILED_SYS:-0}"; FAILED_USR="${FAILED_USR:-0}"
[ "$FAILED_SYS" -gt 0 ] && { S_LVL=2; anom "P1 · $FAILED_SYS service(s) systemd **system** en échec : $(systemctl --failed --no-legend --plain 2>/dev/null | awk '{print $1}' | paste -sd, -)"; }
[ "$FAILED_USR" -gt 0 ] && { sev 1; [ "$S_LVL" -lt 1 ] && S_LVL=1; anom "P2 · $FAILED_USR service(s) systemd **user** en échec : $(systemctl --user --failed --no-legend --plain 2>/dev/null | awk '{print $1}' | paste -sd, -)"; }

read -r MEM_TOTAL MEM_USED MEM_FREE < <(free -m | awk '/^Mem:/{print $2,$3,$4}')
read -r SWAP_TOTAL SWAP_USED < <(free -m | awk '/^Swap:/{print $2,$3}')
LOAD="$(awk '{print $1}' /proc/loadavg)"
NCPU="$(nproc)"
MEM_PCT=$(( MEM_TOTAL>0 ? MEM_USED*100/MEM_TOTAL : 0 ))
SWAP_PCT=0; [ "${SWAP_TOTAL:-0}" -gt 0 ] && SWAP_PCT=$(( SWAP_USED*100/SWAP_TOTAL ))
[ "$MEM_PCT" -ge 90 ]  && { [ "$S_LVL" -lt 1 ] && S_LVL=1; anom "P2 · RAM à ${MEM_PCT}% (${MEM_USED}/${MEM_TOTAL} MiB)"; }
[ "$SWAP_PCT" -ge 50 ] && { [ "$S_LVL" -lt 1 ] && S_LVL=1; anom "P2 · Swap à ${SWAP_PCT}% (${SWAP_USED}/${SWAP_TOTAL} MiB)"; }
# load > 2x ncpu = pression
if awk "BEGIN{exit !($LOAD > $NCPU*2)}"; then [ "$S_LVL" -lt 1 ] && S_LVL=1; anom "P2 · Load $LOAD > 2× cœurs ($NCPU)"; fi

ZOMBIES="$(ps -eo stat= 2>/dev/null | grep -c '^Z' || true)"; ZOMBIES="${ZOMBIES:-0}"
[ "$ZOMBIES" -ge "$ZOMBIE_THRESHOLD" ] && { [ "$S_LVL" -lt 1 ] && S_LVL=1; anom "P2 · $ZOMBIES zombies (seuil $ZOMBIE_THRESHOLD)"; }
DSTATE="$(ps -eo stat= 2>/dev/null | grep -c '^D' || true)"; DSTATE="${DSTATE:-0}"
[ "$DSTATE" -gt 0 ] && add "- ℹ️ $DSTATE process en D-state (I/O uninterruptible)"

# GPU (nvidia-smi) — non bloquant si absent
GPU_LINE="(nvidia-smi indisponible)"
if command -v nvidia-smi >/dev/null 2>&1; then
  GPU_INFO="$(nvidia-smi --query-gpu=index,temperature.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null)"
  if [ -n "$GPU_INFO" ]; then
    GPU_LINE=""
    while IFS=',' read -r gi gt gmu gmt; do
      gt="$(echo "$gt"|tr -d ' ')"; gi="$(echo "$gi"|tr -d ' ')"
      gmu="$(echo "$gmu"|tr -d ' ')"; gmt="$(echo "$gmt"|tr -d ' ')"
      GPU_LINE+="GPU$gi ${gt}°C ${gmu}/${gmt}MiB · "
      if   [ "${gt:-0}" -ge "$GPU_TEMP_CRIT" ]; then S_LVL=2; anom "P1 · GPU$gi à ${gt}°C (≥ ${GPU_TEMP_CRIT}°C critique)";
      elif [ "${gt:-0}" -ge "$GPU_TEMP_WARN" ]; then [ "$S_LVL" -lt 1 ] && S_LVL=1; anom "P2 · GPU$gi à ${gt}°C (≥ ${GPU_TEMP_WARN}°C)"; fi
    done <<< "$GPU_INFO"
  fi
fi
sev "$S_LVL"
add ""
add "## 1. Système — $(lvltxt "$S_LVL")"
add ""
add "| Métrique | Valeur |"
add "|---|---|"
add "| Services failed (system / user) | $FAILED_SYS / $FAILED_USR |"
add "| RAM | ${MEM_USED}/${MEM_TOTAL} MiB (${MEM_PCT}%) |"
add "| Swap | ${SWAP_USED:-0}/${SWAP_TOTAL:-0} MiB (${SWAP_PCT}%) |"
add "| Load (1m) / cœurs | $LOAD / $NCPU |"
add "| Zombies / D-state | $ZOMBIES (seuil $ZOMBIE_THRESHOLD) / $DSTATE |"
add "| GPU | ${GPU_LINE%· } |"

# -----------------------------------------------------------------------------
# 2) CONTAINERS
# -----------------------------------------------------------------------------
echo "[2/6] Containers…"
C_LVL=0
if command -v docker >/dev/null 2>&1 && docker ps >/dev/null 2>&1; then
  JV_COUNT="$(docker ps --format '{{.Names}}' | grep -c '^jv-' || true)"; JV_COUNT="${JV_COUNT:-0}"
  UNHEALTHY="$(docker ps --filter health=unhealthy --format '{{.Names}}' | grep -c . || true)"; UNHEALTHY="${UNHEALTHY:-0}"
  RESTARTING="$(docker ps --filter status=restarting --format '{{.Names}}' | grep -c . || true)"; RESTARTING="${RESTARTING:-0}"
  # restart-loop : RestartCount élevé sur containers up
  LOOP=0
  while read -r name; do
    [ -z "$name" ] && continue
    rc="$(docker inspect "$name" --format '{{.RestartCount}}' 2>/dev/null || echo 0)"
    [ "${rc:-0}" -ge 3 ] && { LOOP=$((LOOP+1)); anom "P1 · restart-loop $name (RestartCount=$rc)"; }
  done < <(docker ps --format '{{.Names}}' | grep '^jv-')
  JVNET="$(docker network ls --format '{{.Name}}' | grep -c '^jvnet-' || true)"; JVNET="${JVNET:-0}"

  [ "$JV_COUNT" -lt "$JV_EXPECTED" ] && { [ "$C_LVL" -lt 1 ] && C_LVL=1; anom "P2 · $JV_COUNT/$JV_EXPECTED containers jv-* up (manquants)"; }
  [ "$UNHEALTHY"  -gt 0 ] && { C_LVL=2; anom "P1 · $UNHEALTHY container(s) unhealthy : $(docker ps --filter health=unhealthy --format '{{.Names}}'|paste -sd, -)"; }
  [ "$RESTARTING" -gt 0 ] && { C_LVL=2; anom "P1 · $RESTARTING container(s) en restarting"; }
  [ "$LOOP" -gt 0 ] && C_LVL=2
else
  C_LVL=2; JV_COUNT=0; UNHEALTHY="n/a"; RESTARTING="n/a"; JVNET="n/a"; LOOP="n/a"
  anom "P1 · Docker indisponible (daemon down ou non installé)"
fi
sev "$C_LVL"
add ""
add "## 2. Containers — $(lvltxt "$C_LVL")"
add ""
add "| Métrique | Valeur |"
add "|---|---|"
add "| Containers jv-* up | $JV_COUNT / $JV_EXPECTED |"
add "| Unhealthy | $UNHEALTHY |"
add "| Restarting | $RESTARTING |"
add "| Restart-loop (RestartCount≥3) | $LOOP |"
add "| Réseaux jvnet-* | $JVNET |"

# -----------------------------------------------------------------------------
# 3) n8n  (historique 24h VS frais depuis restart container)
# -----------------------------------------------------------------------------
echo "[3/6] n8n…"
N_LVL=0
N8N_HTTP="$(probe_code_retry "$N8N_HEALTHZ")"; N8N_HZ_RC=$?
[ $N8N_HZ_RC -ne 0 ] && { N_LVL=2; anom "P1 · n8n /healthz = $N8N_HTTP (DOWN après 3 essais)"; }

WF_ACTIVE="n/a"; WF_TOTAL="n/a"
ERR24=0; OK24=0; RATE24=0
ERRF=0; OKF=0; RATEF=0
N8N_START="?"
if [ -r "$N8N_DB" ] && command -v sqlite3 >/dev/null 2>&1; then
  read -r WF_TOTAL WF_ACTIVE < <(sqlite3 "$N8N_DB" "SELECT count(*),COALESCE(sum(active),0) FROM workflow_entity;" 2>/dev/null | awk -F'|' '{print $1, $2}')
  WF_TOTAL="${WF_TOTAL:-n/a}"; WF_ACTIVE="${WF_ACTIVE:-n/a}"
  # 24h (historique — startedAt en UTC, datetime('now') aussi → cohérent)
  ERR24="$(sqlite3 "$N8N_DB" "SELECT count(*) FROM execution_entity WHERE status='error' AND startedAt>=datetime('now','-24 hours');" 2>/dev/null || echo 0)"
  OK24="$(sqlite3  "$N8N_DB" "SELECT count(*) FROM execution_entity WHERE status='success' AND startedAt>=datetime('now','-24 hours');" 2>/dev/null || echo 0)"
  ERR24="${ERR24:-0}"; OK24="${OK24:-0}"
  TOT24=$((ERR24+OK24)); [ "$TOT24" -gt 0 ] && RATE24=$(( ERR24*100/TOT24 ))
  # FRAIS : on borne sur le démarrage RÉEL du container n8n (distinction historique vs frais)
  if command -v docker >/dev/null 2>&1; then
    RAW_START="$(docker inspect jv-front-n8n --format '{{.State.StartedAt}}' 2>/dev/null)"
    if [ -n "$RAW_START" ]; then
      # normalise ISO8601 → 'YYYY-MM-DD HH:MM:SS' UTC pour comparaison sqlite
      N8N_START="$(date -u -d "$RAW_START" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "$RAW_START")"
    fi
  fi
  if [ "$N8N_START" != "?" ]; then
    ERRF="$(sqlite3 "$N8N_DB" "SELECT count(*) FROM execution_entity WHERE status='error' AND startedAt>='$N8N_START';" 2>/dev/null || echo 0)"
    OKF="$(sqlite3  "$N8N_DB" "SELECT count(*) FROM execution_entity WHERE status='success' AND startedAt>='$N8N_START';" 2>/dev/null || echo 0)"
  else
    # fallback : dernière heure
    ERRF="$(sqlite3 "$N8N_DB" "SELECT count(*) FROM execution_entity WHERE status='error' AND startedAt>=datetime('now','-1 hours');" 2>/dev/null || echo 0)"
    OKF="$(sqlite3  "$N8N_DB" "SELECT count(*) FROM execution_entity WHERE status='success' AND startedAt>=datetime('now','-1 hours');" 2>/dev/null || echo 0)"
  fi
  ERRF="${ERRF:-0}"; OKF="${OKF:-0}"
  TOTF=$((ERRF+OKF)); [ "$TOTF" -gt 0 ] && RATEF=$(( ERRF*100/TOTF ))
  # Le verdict n8n se base sur le taux FRAIS (post-restart), PAS sur l'historique.
  if   [ "$RATEF" -ge "$ERR_RATE_CRIT" ]; then N_LVL=2; anom "P1 · n8n taux d'erreur FRAIS ${RATEF}% (≥${ERR_RATE_CRIT}%) — $ERRF err / $TOTF exéc depuis restart";
  elif [ "$RATEF" -ge "$ERR_RATE_WARN" ]; then [ "$N_LVL" -lt 1 ] && N_LVL=1; anom "P2 · n8n taux d'erreur FRAIS ${RATEF}% (≥${ERR_RATE_WARN}%) — $ERRF err / $TOTF exéc depuis restart"; fi
else
  [ "$N_LVL" -lt 1 ] && N_LVL=1; anom "P2 · n8n DB illisible ($N8N_DB) — métriques workflows/exécutions indisponibles"
fi
sev "$N_LVL"
add ""
add "## 3. n8n — $(lvltxt "$N_LVL")"
add ""
add "| Métrique | Valeur |"
add "|---|---|"
add "| Webhook /healthz | HTTP $N8N_HTTP |"
add "| Workflows actifs | $WF_ACTIVE / $WF_TOTAL |"
add "| Exéc 24h (historique) | ✅ $OK24 / ❌ $ERR24 → taux ${RATE24}% |"
add "| Exéc FRAIS (depuis restart $N8N_START UTC) | ✅ $OKF / ❌ $ERRF → taux ${RATEF}% |"
add ""
add "> Distinction clé : le taux **24h** peut être pollué par des erreurs **antérieures** au dernier restart du container (ex. bug historique déjà corrigé). Le verdict n8n se fonde sur le taux **FRAIS** (exécutions depuis le démarrage réel du container)."

# -----------------------------------------------------------------------------
# 4) cmdlib (PostgreSQL — container détecté DYNAMIQUEMENT)
# -----------------------------------------------------------------------------
echo "[4/6] cmdlib…"
D_LVL=0
PG="n/a"; PG_HEALTH="n/a"; CMD_N="n/a"; HOLD_N="n/a"; SER_N="n/a"
if command -v docker >/dev/null 2>&1 && docker ps >/dev/null 2>&1; then
  PG="$(docker ps --format '{{.Names}} {{.Image}}' | awk '/postgres/{print $1; exit}')"
  if [ -n "$PG" ]; then
    PG_HEALTH="$(docker inspect "$PG" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' 2>/dev/null)"
    COUNTS="$(docker exec "$PG" psql -U cmduser -d cmdlib -tAc \
      "SELECT (SELECT count(*) FROM commands),(SELECT count(*) FROM holding_index),(SELECT count(*) FROM library_series);" 2>/dev/null)"
    if [ -n "$COUNTS" ]; then
      CMD_N="$(echo "$COUNTS"|cut -d'|' -f1)"; HOLD_N="$(echo "$COUNTS"|cut -d'|' -f2)"; SER_N="$(echo "$COUNTS"|cut -d'|' -f3)"
    else
      [ "$D_LVL" -lt 1 ] && D_LVL=1; anom "P2 · cmdlib : requête psql sans retour (DB pas prête ?) sur $PG"
    fi
    [ "$PG_HEALTH" = "unhealthy" ] && { D_LVL=2; anom "P1 · container PG $PG unhealthy"; }
  else
    [ "$D_LVL" -lt 1 ] && D_LVL=1; anom "P2 · aucun container postgres détecté (docker ps | postgres)"
  fi
else
  [ "$D_LVL" -lt 1 ] && D_LVL=1; anom "P2 · Docker indisponible → cmdlib non vérifiable"
fi
sev "$D_LVL"
add ""
add "## 4. cmdlib (PostgreSQL) — $(lvltxt "$D_LVL")"
add ""
add "| Métrique | Valeur |"
add "|---|---|"
add "| Container PG (détecté dynamiquement) | $PG |"
add "| Health | $PG_HEALTH |"
add "| Table commands | $CMD_N |"
add "| Table holding_index | $HOLD_N |"
add "| Table library_series | $SER_N |"

# -----------------------------------------------------------------------------
# 5) GIT
# -----------------------------------------------------------------------------
echo "[5/6] Git…"
G_LVL=0
BRANCH="n/a"; AHEAD=0; BEHIND=0; DIRTY=0; ORIGIN_URL="n/a"
if git -C "$REPO_DIR" rev-parse --git-dir >/dev/null 2>&1; then
  BRANCH="$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null)"
  DIRTY="$(git -C "$REPO_DIR" status --porcelain 2>/dev/null | grep -c . || true)"; DIRTY="${DIRTY:-0}"
  ORIGIN_URL="$(git -C "$REPO_DIR" remote get-url origin 2>/dev/null || echo 'none')"
  UP="$(git -C "$REPO_DIR" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo '')"
  if [ -n "$UP" ]; then
    read -r BEHIND AHEAD < <(git -C "$REPO_DIR" rev-list --left-right --count "$UP...HEAD" 2>/dev/null | awk '{print $1, $2}')
    BEHIND="${BEHIND:-0}"; AHEAD="${AHEAD:-0}"
  fi
  # Alerte si origin ≠ jarvis-core (anomalie connue : origin=sql-backups)
  case "$ORIGIN_URL" in
    *jarvis-core*) : ;;
    none) [ "$G_LVL" -lt 1 ] && G_LVL=1; anom "P2 · pas de remote 'origin' configuré" ;;
    *) [ "$G_LVL" -lt 1 ] && G_LVL=1; anom "P1 · remote 'origin' ≠ jarvis-core (=$ORIGIN_URL) → \`git push origin\` viserait le mauvais dépôt" ;;
  esac
  [ "${AHEAD:-0}" -gt 0 ] && { [ "$G_LVL" -lt 1 ] && G_LVL=1; anom "P2 · $AHEAD commit(s) local(aux) non poussé(s) sur $BRANCH"; }
  [ "${DIRTY:-0}" -gt 0 ] && { [ "$G_LVL" -lt 1 ] && G_LVL=1; anom "P2 · $DIRTY fichier(s) non commité(s)"; }
else
  G_LVL=2; anom "P1 · $REPO_DIR n'est pas un dépôt git"
fi
sev "$G_LVL"
add ""
add "## 5. Git — $(lvltxt "$G_LVL")"
add ""
add "| Métrique | Valeur |"
add "|---|---|"
add "| Branche | $BRANCH |"
add "| Ahead / Behind upstream | $AHEAD / $BEHIND |"
add "| Fichiers non commités | $DIRTY |"
add "| Remote origin | $ORIGIN_URL |"

# -----------------------------------------------------------------------------
# 6) LLM (probes flaky → multi-essai 3×/2s)
# -----------------------------------------------------------------------------
echo "[6/6] LLM…"
L_LVL=0
# LMS :1234
LMS_BODY="$(probe_retry "$LMS_URL" "LMS")"; LMS_RC=$?
LMS_MODELS=0
if [ $LMS_RC -eq 0 ]; then
  LMS_MODELS="$(echo "$LMS_BODY" | grep -o '"id"' | wc -l | tr -d ' ')"
  [ "${LMS_MODELS:-0}" -lt "$LMS_EXPECTED_MODELS" ] && { [ "$L_LVL" -lt 1 ] && L_LVL=1; anom "P2 · LMS :1234 expose $LMS_MODELS modèle(s) (< $LMS_EXPECTED_MODELS attendus)"; }
else
  L_LVL=2; anom "P1 · LMS :1234 DOWN (3 essais échoués)"
fi
# Proxy :18800/health
PROXY_BODY="$(probe_retry "$PROXY_URL" "proxy")"; PROXY_RC=$?
PROXY_STATUS="down"
if [ $PROXY_RC -eq 0 ]; then
  echo "$PROXY_BODY" | grep -q '"status"[[:space:]]*:[[:space:]]*"ok"' && PROXY_STATUS="ok" || PROXY_STATUS="degraded"
  [ "$PROXY_STATUS" != "ok" ] && { [ "$L_LVL" -lt 1 ] && L_LVL=1; anom "P2 · proxy :18800 status=$PROXY_STATUS"; }
else
  [ "$L_LVL" -lt 1 ] && L_LVL=1; anom "P2 · proxy :18800/health injoignable (3 essais)"
fi
# Gateway :9742 (flaky historique hook .85 → multi-essai)
GW_BODY="$(probe_retry "$GATEWAY_URL" "gateway")"; GW_RC=$?
GW_STATE="down"
if [ $GW_RC -eq 0 ]; then GW_STATE="up"; else
  [ "$L_LVL" -lt 1 ] && L_LVL=1; anom "P2 · gateway :9742 injoignable (3 essais — faux négatif possible, non bloquant)"
fi
# lm-ask 1 essai (best-effort, non bloquant)
LMASK="skip"
if [ -x "$REPO_DIR/scripts/lm-ask.sh" ]; then
  if timeout 30 "$REPO_DIR/scripts/lm-ask.sh" "ping" >/dev/null 2>&1; then LMASK="ok"; else LMASK="ko (non bloquant)"; fi
fi
sev "$L_LVL"
add ""
add "## 6. LLM — $(lvltxt "$L_LVL")"
add ""
add "| Probe (multi-essai 3×/2s) | État |"
add "|---|---|"
add "| LMS :1234 | $([ $LMS_RC -eq 0 ] && echo "up · $LMS_MODELS modèles" || echo DOWN) |"
add "| Proxy :18800/health | $PROXY_STATUS |"
add "| Gateway :9742 | $GW_STATE |"
add "| lm-ask.sh (1 essai) | $LMASK |"

# =============================================================================
# VERDICT GLOBAL + ÉCRITURE
# =============================================================================
VERDICT="$(lvltxt "$GLOBAL")"
add ""
add "---"
add ""
add "## VERDICT GLOBAL : $VERDICT"
add ""
add "| Domaine | Verdict |"
add "|---|---|"
add "| Système | $(lvltxt "$S_LVL") |"
add "| Containers | $(lvltxt "$C_LVL") |"
add "| n8n | $(lvltxt "$N_LVL") |"
add "| cmdlib | $(lvltxt "$D_LVL") |"
add "| Git | $(lvltxt "$G_LVL") |"
add "| LLM | $(lvltxt "$L_LVL") |"
add ""
if [ -n "$ANOMALIES" ]; then
  add "## Anomalies détectées"
  add ""
  add "$ANOMALIES"
else
  add "## Anomalies détectées"
  add ""
  add "_Aucune._"
fi
add ""
add "_Régénéré le $TS par \`scripts/jarvis_audit_protocol.sh\` (read-only, 0-token)._"

mkdir -p "$(dirname "$OUT_MD")"
printf '%s' "$REPORT" > "$OUT_MD"

# Sortie console
echo
echo "================== RAPPORT ($OUT_MD) =================="
printf '%s' "$REPORT"
echo "======================================================="
echo
echo "VERDICT GLOBAL : $VERDICT"

exit "$GLOBAL"
