#!/usr/bin/env bash
# Surveille la fenêtre active et auto-configure le mode Lumen
# Fonctionne en tâche de fond, sans page ouverte

API="http://127.0.0.1:8788/api/control"
LAST_MODE=""
INTERVAL=3

log() { echo "[$(date +%H:%M:%S)] $*"; }

# Détection DISPLAY robuste si non défini ou invalide
_detect_display() {
  for disp in :0 :1 :2; do
    if DISPLAY="$disp" xdotool getactivewindow > /dev/null 2>&1; then
      export DISPLAY="$disp"
      return 0
    fi
  done
  return 1
}
if [ -z "$DISPLAY" ] || ! xdotool getactivewindow > /dev/null 2>&1; then
  _detect_display && log "DISPLAY auto-détecté: $DISPLAY" || log "WARN: aucun serveur X trouvé"
fi

detect_mode_from_window() {
  local wname
  wname=$(xdotool getactivewindow getwindowname 2>/dev/null | tr '[:upper:]' '[:lower:]')
  local wclass
  wclass=$(xdotool getactivewindow getwindowclassname 2>/dev/null | tr '[:upper:]' '[:lower:]')

  if echo "$wname $wclass" | grep -qE "terminal|konsole|alacritty|kitty|tilix|gnome-terminal"; then
    echo "research"
  elif echo "$wname $wclass" | grep -qE "code|cursor|sublime|vim|neovim|emacs|jetbrains"; then
    echo "document"
  elif echo "$wname $wclass" | grep -qE "meet|teams|zoom|discord|slack|visio|webex"; then
    echo "meeting"
  elif echo "$wname $wclass" | grep -qE "libreoffice|writer|calc|impress|word|excel|docs"; then
    echo "document"
  elif echo "$wname $wclass" | grep -qE "translate|deepl|reverso|linguee"; then
    echo "translation"
  elif echo "$wname $wclass" | grep -qE "lumen|transcri"; then
    echo "classroom"  # fenêtre Lumen elle-même
  elif echo "$wname $wclass" | grep -qE "chrome|firefox|brave|edge|safari|chromium"; then
    echo "auto"  # browser: mode auto (détecte selon contenu)
  else
    echo "auto"
  fi
}

log "Lumen Context Watcher démarré (PID $$)"
log "Auto-configure le mode selon la fenêtre active (intervalle: ${INTERVAL}s)"

while true; do
  # Seulement si Lumen backend actif
  if ! curl -sf --max-time 1 "${API}/status" > /dev/null 2>&1; then
    sleep 10; continue
  fi

  MODE=$(detect_mode_from_window)

  if [ "$MODE" != "$LAST_MODE" ] && [ -n "$MODE" ]; then
    RESULT=$(curl -sf -X POST "${API}/mode" \
      -H "Content-Type: application/json" \
      -d "{\"taskMode\":\"$MODE\"}" 2>/dev/null)
    log "Fenêtre changée → mode: $MODE"
    LAST_MODE="$MODE"
  fi

  sleep "$INTERVAL"
done
