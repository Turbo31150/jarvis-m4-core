#!/usr/bin/env bash
# Cockpit tmux JARVIS — un volet par backend, tout visible d'un coup d'œil.
#
# Volets :
#   0 forge      production en cours (ollama-cloud, déporté)
#   1 backends   santé LM Studio M6 / Ollama local / Rémi, rafraîchie
#   2 agy        Antigravity CLI, prêt à recevoir une question
#   3 shell      libre
#
# Usage : bash cockpit-tmux.sh        (crée ou rattache)
#         tmux attach -t jarvis       (rattacher plus tard)
#         Ctrl-b puis o               (passer d'un volet à l'autre)
set -uo pipefail

SESSION=jarvis
JV="$HOME/jarvis"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  exec tmux attach -t "$SESSION"
fi

# — volet 0 : la forge
tmux new-session -d -s "$SESSION" -n cockpit \
  "tail -f '$JV/data/forge-run.log'"

# — volet 1 : santé des backends. Une inférence réelle est la SEULE preuve
#   qu'un nœud LM Studio sert : lms ps, lms status et /v1/models peuvent tous
#   les trois être verts pendant que le GPU est tombé du bus (constaté le 14/08).
tmux split-window -t "$SESSION:0" -h "watch -n 30 -t '
echo \"── LM Studio M6 (10.42.0.230:1234)\"
curl -s -m 5 http://10.42.0.230:1234/api/v0/models 2>/dev/null | python3 -c \"
import sys,json
try:
  for m in json.load(sys.stdin)[\\\"data\\\"]: print(f\\\"  {m.get(\\\"state\\\"):11} {m.get(\\\"id\\\")}\\\")
except: print(\\\"  injoignable\\\")\" 2>/dev/null
echo \"  preuve reelle :\"
curl -s -m 12 http://10.42.0.230:1234/v1/chat/completions -H \"Content-Type: application/json\" \
  -d \"{\\\"model\\\":\\\"qwen/qwen3.5-9b\\\",\\\"messages\\\":[{\\\"role\\\":\\\"user\\\",\\\"content\\\":\\\"<think></think>ok\\\"}],\\\"max_tokens\\\":5}\" 2>/dev/null | head -c 120
echo
echo \"── Ollama local\"
curl -s -m 4 http://127.0.0.1:11434/api/ps 2>/dev/null | head -c 150
echo
echo \"── Remi (Tailscale)\"
curl -s -o /dev/null -w \"  http %{http_code}\n\" -m 5 http://100.113.121.61:11434/api/tags 2>/dev/null
echo \"── Machine\"
free -m | awk \"NR==2{printf \\\"  RAM %d%%\\\\n\\\",\\\$3*100/\\\$2}\"
cat /sys/class/thermal/thermal_zone*/temp | sort -rn | head -1 | awk \"{printf \\\"  CPU %d C\\\\n\\\",\\\$1/1000}\"
'"

# — volet 2 : agy (Antigravity CLI), déjà dans le bon dossier
tmux split-window -t "$SESSION:0.0" -v -c "$JV" \
  "echo 'agy prêt — ex : agy -p \"ta question\" --effort medium'; exec bash"

# — volet 3 : shell libre
tmux split-window -t "$SESSION:0.1" -v -c "$JV" "exec bash"

tmux select-layout -t "$SESSION:0" tiled
tmux select-pane -t "$SESSION:0.2"
exec tmux attach -t "$SESSION"
