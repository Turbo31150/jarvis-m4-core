#!/usr/bin/env bash
# jarvis-tmux-server.sh — monte la session tmux permanente "jarvis" (uid 1000).
# Idempotent : relance uniquement les fenetres absentes, ne tue rien qui tourne.
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
SESSION=jarvis
BIN="$HOME/jarvis/bin"

fenetre_vivante() {  # $1 = nom de fenetre
  tmux list-panes -t "$SESSION:$1" -F '#{pane_dead}' 2>/dev/null | grep -qx 0
}

assurer() {  # $1 = nom de fenetre, $2 = commande
  if fenetre_vivante "$1"; then
    echo "  = $1 deja vivant"
  else
    tmux kill-window -t "$SESSION:$1" 2>/dev/null
    tmux new-window -d -t "$SESSION" -n "$1" "$2"
    echo "  + $1 lance"
  fi
}

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux new-session -d -s "$SESSION" -n link-watch "$BIN/m6-link-watch.sh"
  echo "  + session $SESSION creee (link-watch)"
else
  assurer link-watch "$BIN/m6-link-watch.sh"
fi
assurer board-keepwarm "$BIN/board-keepwarm.sh"
# Passerelle OpenAI -> agy : donne au board un second backend de chat
# (Gemini/Claude/GPT-OSS), independant de M6 et bien plus rapide.
assurer agy-shim "python3 $BIN/agy-openai-shim.py ${AGY_SHIM_PORT:-18811}"

tmux list-windows -t "$SESSION" -F '  session=#{session_name} fenetre=#{window_name} panes=#{window_panes}'
