#!/usr/bin/env bash
# jarvis-s9-bridge.sh — implante JARVIS OS dans le Galaxy S9.
#
# Publie les services JARVIS de M1 sur le loopback DU TÉLÉPHONE via `adb reverse`.
# Pourquoi pas une IP ? Le sous-réseau du partage USB est randomisé par Android à
# chaque activation, et sans root on ne peut pas figer de route côté S9. Le tunnel
# adb donne au téléphone une adresse invariante — 127.0.0.1 — quel que soit le réseau.
#
# Idempotent : re-poser un reverse existant est sans effet. Conçu pour être rejoué
# au branchement (udev) et périodiquement (timer).
set -uo pipefail

S9_SERIAL="${S9_SERIAL:-4357514238453498}"
ADB="${ADB:-/usr/bin/adb}"
export HOME="${ADB_HOME:-/home/pamerys}"

# port:description — le port est identique des deux côtés pour rester lisible.
SERVICES=(
  "8899:widget planning (ce que le système fait)"
  "18800:hub LLM unifié (OpenAI-compat, cascade failover)"
  "18801:dashboard JARVIS"
  "9742:API gateway JARVIS"
  "1234:LM Studio M1 (qwen3.5-9b, gpt-oss-20b)"
  "11434:Ollama local"
  "8770:lumen/neo"
)

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*"; logger -t jarvis-s9-bridge -- "$*"; }

[ -x "$ADB" ] || { log "adb absent"; exit 0; }

for _ in $(seq 1 15); do
  [ "$("$ADB" -s "$S9_SERIAL" get-state 2>/dev/null)" = "device" ] && break
  sleep 1
done
[ "$("$ADB" -s "$S9_SERIAL" get-state 2>/dev/null)" = "device" ] || { log "S9 absent — rien à implanter"; exit 0; }

posed=0 skipped=0
for entry in "${SERVICES[@]}"; do
  port="${entry%%:*}"
  desc="${entry#*:}"
  # Ne publier que ce qui écoute réellement : un reverse vers un port mort
  # renverrait des refus de connexion à l'app et masquerait la vraie panne.
  if ss -ltn "( sport = :$port )" 2>/dev/null | grep -q LISTEN; then
    if "$ADB" -s "$S9_SERIAL" reverse "tcp:$port" "tcp:$port" >/dev/null 2>&1; then
      posed=$((posed+1))
    else
      log "échec reverse tcp:$port ($desc)"
    fi
  else
    skipped=$((skipped+1))
  fi
done

log "implantation : $posed service(s) publiés sur 127.0.0.1 du S9, $skipped hors service ignoré(s)"
exit 0
