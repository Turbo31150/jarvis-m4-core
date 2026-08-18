#!/usr/bin/env bash
# stop_protocol.sh — HOOK STOP "balanceur cahier des charges" (PROTOCOLE ZERO-TOKEN)
# Demande Turbo: "a chaque arret tu balance la commande cahier des charges +
#   audit/deepresearch mots-cles todolist -> cascade CLI+balises HTML ->
#   sortie plan mode cascade maximale -> sauvegarde des combinaisons (ajout valeur)
#   -> serie decomposee pour execution immediate."
# NON-BLOQUANT (exit 0 toujours), anti-boucle (garde 90s), 0 token IA.
set +e
AD="$HOME/jarvis/.actions"
LOCK=/tmp/jarvis_stop_protocol.lock
LOG="$AD/logs/stop_protocol.log"; mkdir -p "$AD/logs"

# --- anti-boucle: 1 exec / 90s max ---
if [ -f "$LOCK" ]; then
  last=$(cat "$LOCK" 2>/dev/null || echo 0)
  now=$(date +%s)
  [ $((now - last)) -lt 90 ] && exit 0
fi
date +%s > "$LOCK"

# --- 1) capture auto de la combinaison de session (ajout valeur) ---
# lit les mots-cles depuis le dernier prompt (transcript via stdin JSON si fourni)
KW=""
STDIN_JSON=$(timeout 0.5 cat 2>/dev/null)
if [ -n "$STDIN_JSON" ]; then
  KW=$(printf '%s' "$STDIN_JSON" | python3 -c "import sys,json
try:
  d=json.load(sys.stdin); print(d.get('prompt','') or d.get('last_user','') )
except: pass" 2>/dev/null | tr -cd 'a-zA-Z0-9 éèàùçâêîôû_-' | head -c 200)
fi
if [ -n "$KW" ]; then
  python3 "$AD/ag.py" "$KW" --save >>"$LOG" 2>&1
fi

# --- 2) FEEDBACK : clôt le cycle du tour dans action_feedback ---
# Le cahier des charges complet est un cycle en 5 temps :
#   demande → action → log → scoring → feedback
# Les quatre premiers existaient déjà (ag.py --save, session_command_log,
# serie_weights) mais le cycle n'était jamais FERMÉ : rien n'enregistrait le
# résultat du tour, donc le scoring ne pouvait pas apprendre. Cette étape écrit
# une ligne de feedback par tour, en lecture/écriture bornée (busy_timeout), sans
# jamais faire échouer le hook.
# Identité du terminal appelant. Le hook tourne HORS tty (`tty` répond « pas un
# tty ») et `$TTY` n'est pas défini : écrire os.environ['TTY'] produisait une seule
# valeur « claude-code » pour tout le monde, alors que les 15 000 lignes déjà en base
# portent de vrais pts/0…pts/6. Avec 6 sessions Claude simultanées, un feedback non
# attribué est un feedback inutilisable — on remonte donc la chaîne des parents
# jusqu'au premier ancêtre qui possède un tty.
detect_tty() {
  local pid="$PPID" tty_val="" i=0
  while [ -n "$pid" ] && [ "$pid" != "1" ] && [ $i -lt 8 ]; do
    tty_val=$(ps -o tty= -p "$pid" 2>/dev/null | tr -d ' ')
    case "$tty_val" in
      pts/*|tty*) echo "$tty_val"; return 0 ;;
    esac
    pid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
    i=$((i + 1))
  done
  echo "detached"
}
TTY_ID="$(detect_tty)"
UID_NUM="$(id -u 2>/dev/null || echo '?')"

if [ -n "$KW" ]; then
  python3 - "$KW" "$TTY_ID" "$UID_NUM" <<'PY' >>"$LOG" 2>&1
import os, sqlite3, sys
kw = (sys.argv[1] or "").strip()[:120]
tty = sys.argv[2] or "detached"
uid = sys.argv[3] or "?"
db = os.path.expanduser("~/jarvis/jarvis_master.db")
try:
    c = sqlite3.connect(db, timeout=8)
    c.execute("PRAGMA busy_timeout=8000")
    # `serie` = l'intention du tour ; `state` = observé (le hook ne sait pas si
    # l'action a réussi, il ne prétend donc pas 'ok' — c'est 'tour' et le scoring
    # agrège les hits, jamais un succès supposé).
    c.execute(
        "INSERT INTO action_feedback (tty, serie, backend, state, score) VALUES (?,?,?,?,?)",
        (tty, kw, f"stop-protocol/uid{uid}", "tour", 0.0),
    )
    c.commit(); c.close()
    print(f"[feedback] {tty} uid={uid} ← {kw[:60]}")
except Exception as e:
    print(f"[feedback] non écrit : {e}")
PY
fi

# --- 3) balance le rappel cahier des charges — JSON systemMessage (VISIBLE en chat) ---
TOTAL=$(python3 -c "import json;print(json.load(open('$AD/INDEX.json'))['total_actions'])" 2>/dev/null || echo '?')
COMBOS=$(ls "$AD"/cli_sequences/combo_*.json 2>/dev/null | wc -l | tr -d ' ')
# Compteurs réels du cycle, lus en RO : un cahier des charges qui affiche des
# chiffres inventés ne vaut rien. Sans base joignable, on affiche « ? ».
CYCLE=$(python3 - <<'PY' 2>/dev/null || echo "log ? · score ? · retour ?"
import os, sqlite3
db = os.path.expanduser("~/jarvis/jarvis_master.db")
try:
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
    c.execute("PRAGMA busy_timeout=5000")
    q = lambda s: c.execute(s).fetchone()[0]
    log = q("SELECT COUNT(*) FROM session_command_log")
    sc = q("SELECT COUNT(*) FROM serie_weights")
    fb = q("SELECT COUNT(*) FROM action_feedback")
    top = c.execute(
        "SELECT serie, weight FROM serie_weights ORDER BY weight DESC, hits DESC LIMIT 1"
    ).fetchone()
    c.close()
    tete = f" · tête {top[0][:22]} {top[1]:.2f}" if top else ""
    print(f"log {log} · score {sc} · retour {fb}{tete}")
except Exception:
    print("log ? · score ? · retour ?")
PY
)
MSG="📋 CAHIER DES CHARGES ZERO-TOKEN | ${TOTAL} actions · ${COMBOS} combos | CYCLE demande→action→log→scoring→feedback : ${CYCLE} | session ${TTY_ID} uid${UID_NUM} | ag.py \"mots-clés\" [--save|--exec] · capture_html.py <id> <url> · nav.py plan <réseau> · Loi: capture 1× → usage ∞ 0 token"
python3 -c "import json,sys;print(json.dumps({'systemMessage':sys.argv[1],'suppressOutput':True}))" "$MSG"
exit 0
