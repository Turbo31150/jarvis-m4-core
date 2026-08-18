#!/usr/bin/env bash
# jarvis-cockpit — ouvre les CLI de l'écosystème comme fenêtres tmux de la
# session où tourne déjà Claude Code, pour les avoir côte à côte plutôt qu'en
# terminaux séparés.
#
#   jarvis-cockpit.sh            # monte les fenêtres manquantes
#   jarvis-cockpit.sh --status   # dit ce qui répond, n'ouvre rien
#
# Les secrets viennent du coffre sops et ne transitent ni par la ligne de
# commande (visible dans ps) ni par un fichier sur disque : ils sont écrits
# dans /dev/shm, sourcés, puis effacés dans la foulée.
set -u

SESSION="${JARVIS_COCKPIT_SESSION:-claude-code}"
VAULT="$HOME/jarvis/secrets-vault/secrets.enc.env"

sonde() {
  printf '%-12s ' "$1"
  shift
  if timeout "${TIMEOUT:-20}" "$@" >/dev/null 2>&1; then
    echo "répond"
  else
    echo "muet"
  fi
}

if [[ "${1:-}" == "--status" ]]; then
  echo "— CLI de l'écosystème —"
  sonde agy agy -p "ok"
  sonde openclaw openclaw --version
  sonde gemini gemini --version
  sonde tmux tmux -V
  echo
  echo "— session tmux $SESSION —"
  tmux list-windows -t "$SESSION" 2>/dev/null || echo "  session absente"
  exit 0
fi

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Session tmux '$SESSION' absente. Rien ouvert." >&2
  exit 1
fi

# Une fenêtre par outil. On ne recrée pas ce qui existe déjà : relancer le
# cockpit deux fois ne doit pas empiler des doublons.
ouvre() {
  local nom="$1" cmd="$2"
  if tmux list-windows -t "$SESSION" -F '#W' 2>/dev/null | grep -qx "$nom"; then
    echo "  $nom : déjà ouverte"
    return
  fi
  tmux new-window -d -t "$SESSION" -n "$nom" "$cmd"
  echo "  $nom : ouverte"
}

echo "Cockpit sur la session '$SESSION' :"

ouvre agy      "agy; exec bash"
ouvre openclaw "openclaw; exec bash"

# Gemini exige une clé ; sans elle la fenêtre s'ouvrirait sur une erreur d'auth.
if [[ -r "$VAULT" ]] && command -v sops >/dev/null 2>&1; then
  ENVF="/dev/shm/.jarvis-cockpit-$$"
  ( umask 077; sops -d "$VAULT" > "$ENVF" 2>/dev/null )
  if grep -q '^GEMINI_API_KEY=' "$ENVF" 2>/dev/null; then
    ouvre gemini "set -a; . '$ENVF'; set +a; rm -f '$ENVF'; gemini; exec bash"
  else
    rm -f "$ENVF"
    echo "  gemini : pas de GEMINI_API_KEY dans le coffre, non ouverte"
  fi
else
  echo "  gemini : coffre illisible, non ouverte"
fi

# Veille board : la dette vectorielle et la part de JSON brut, rafraîchies.
ouvre board "watch -n 60 \"sqlite3 'file:\$HOME/jarvis/board/board.db?mode=ro' \
\\\"SELECT (SELECT COUNT(*) FROM chunks WHERE embedding IS NULL) AS dette, \
(SELECT COUNT(*) FROM chunks WHERE embedding IS NULL AND text NOT LIKE '{%' AND text NOT LIKE '[%') AS utile;\\\"\""

echo
tmux list-windows -t "$SESSION" -F '  #I: #W'
echo
echo "Basculer : Ctrl-b puis le numéro de fenêtre."
