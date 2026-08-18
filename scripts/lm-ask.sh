#!/usr/bin/env bash
# lm-ask.sh — inférence rapide sur le cluster local (LM Studio puis Ollama).
#
# Prompt attendu en ARGUMENT ($1). Lit aussi stdin si aucun argument n'est
# fourni, parce que des appelants historiques font `echo "$p" | lm-ask.sh`.
#
# TROIS BUGS CORRIGÉS ICI (2026-07-29) :
#
#  1. Le prompt était interpolé DIRECTEMENT dans le JSON :
#       "content": "'"$PROMPT"'"
#     Tout prompt contenant un guillemet, un backslash ou un retour ligne
#     produisait du JSON invalide → réponse vide, en silence. C'est pourquoi
#     les prompts d'audit (tableaux markdown, backticks, accents) échouaient
#     systématiquement. Le JSON est désormais construit par python json.dumps.
#
#  2. Un prompt vide était REMPLACÉ par « Vérification rapide de santé du
#     système ». Le modèle répondait donc fidèlement à une question que
#     personne n'avait posée — d'où des rapports d'audit entiers parlant du
#     Gestionnaire des tâches Windows. Un prompt vide est maintenant une
#     ERREUR (exit 2), jamais une substitution silencieuse.
#
#  3. La clé API LM Studio était en clair dans le fichier. Elle est lue depuis
#     l'environnement (LM_API_KEY) ; la valeur en dur est retirée.

set -uo pipefail

PROMPT="${1:-}"
if [ -z "$PROMPT" ] && [ ! -t 0 ]; then PROMPT="$(cat)"; fi

if [ -z "${PROMPT// /}" ]; then
  echo "lm-ask.sh: prompt vide — rien n'est envoyé au modèle." >&2
  echo "usage: lm-ask.sh \"<prompt>\"   |   echo \"<prompt>\" | lm-ask.sh" >&2
  exit 2
fi

# 2026-08-14 : LM Studio n'existe pas sur M4 (~/.lmstudio/models vide). Le seul
# serveur LM Studio du parc est M6, joignable par câble ethernet direct sur
# 10.42.0.230:1234 (lien 1 Gbps, RTT 1,4 ms) — mesuré, 4 modèles servis.
LM_HOST="${LM_HOST:-http://10.42.0.230:1234}"
OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
LM_MODEL="${LM_MODEL:-qwen/qwen3.5-9b}"
OLLAMA_MODEL="${OLLAMA_MODEL:-gemma3:4b}"

# Corps JSON construits par python : échappement correct garanti.
build_body() { # $1 = lmstudio|ollama
  PROMPT="$PROMPT" LM_MODEL="$LM_MODEL" OLLAMA_MODEL="$OLLAMA_MODEL" \
  python3 -c '
import json, os, sys
p = os.environ["PROMPT"]
if sys.argv[1] == "lmstudio":
    # qwen3.5-9b part en reasoning-runaway sur /v1/chat/completions : le
    # content revient vide ou tronqué à un mot, tout le budget passant dans
    # reasoning_content. Parade vérifiée (identique à bin/jarvis-agent et
    # cli/biblio_filler.py) : /v1/completions avec <think></think> pré-fermé.
    print(json.dumps({
        "model": os.environ["LM_MODEL"],
        "prompt": ("<|im_start|>user\n" + p + "<|im_end|>\n"
                   "<|im_start|>assistant\n<think></think>\n\n"),
        "temperature": 0.2,
        "max_tokens": 900,
        "stop": ["<|im_end|>"],
    }))
else:
    print(json.dumps({
        "model": os.environ["OLLAMA_MODEL"],
        "prompt": p,
        # keep_alive -1 gardait le modele resident A VIE : le llama-server
        # restait a ~380 % CPU sans aucun client, 22 min apres la fin du run,
        # machine a 94 degres. TTL 5 min = assez pour enchainer les agents,
        # pas assez pour squatter la machine.
        "keep_alive": "5m",
        "stream": False,
    }))
' "$1"
}

extract() { # $1 = lmstudio|ollama  (lit le JSON de réponse sur stdin)
  python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit()
if sys.argv[1] == "lmstudio":
    print(((d.get("choices") or [{}])[0]).get("text", "").strip())
else:
    print(d.get("response", "").strip())
' "$1" 2>/dev/null
}

# 1. LM Studio (OpenAI-compat)
# 2026-08-15 : --max-time 180 était trop court. Mesuré sur M6 : un prompt d'audit
# de 6 000 caractères met 2 min 06. Au moindre dépassement on retombait sur le
# fallback Ollama en CPU pur (-ngl 0), qui a poussé le M4 à 94 °C. 600 s laisse
# M6 finir au lieu de brûler le CPU local.
RES=$(build_body lmstudio | curl -s --connect-timeout 3 --max-time 600 \
  "$LM_HOST/v1/completions" \
  -H "Content-Type: application/json" \
  ${LM_API_KEY:+-H "Authorization: Bearer $LM_API_KEY"} \
  --data-binary @- 2>/dev/null | extract lmstudio)

if [ -n "${RES// /}" ]; then
  echo "$RES"
  exit 0
fi

# 2. Fallback Ollama
RES=$(build_body ollama | curl -s --connect-timeout 3 --max-time 180 \
  "$OLLAMA_URL/api/generate" \
  -H "Content-Type: application/json" \
  --data-binary @- 2>/dev/null | extract ollama)

if [ -n "${RES// /}" ]; then
  echo "$RES"
  exit 0
fi

# Aucun backend n'a répondu : on le DIT, on ne fabrique pas de texte.
echo "lm-ask.sh: aucun backend n'a répondu (LM Studio $LM_HOST · Ollama $OLLAMA_URL)." >&2
exit 1
