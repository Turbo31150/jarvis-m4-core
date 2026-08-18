#!/usr/bin/env bash
# netlify-oauth.sh — pont app-OAuth Netlify -> access_token (flux out-of-band).
# Le secret est lu depuis .secrets/netlify-oauth.env (gitignored, 600) — jamais affiché.
#
#   netlify-oauth.sh authorize        # imprime l'URL à ouvrir dans le navigateur
#   netlify-oauth.sh token <CODE>     # échange le code OOB -> access_token (stocké + exporté CLI)
set -uo pipefail
JARVIS="${JARVIS_HOME:-$HOME/jarvis}"
ENVF="$JARVIS/.secrets/netlify-oauth.env"
[ -f "$ENVF" ] || { echo "FAIL: $ENVF introuvable"; exit 1; }
# shellcheck disable=SC1090
set -a; . "$ENVF"; set +a
CID="${NETLIFY_OAUTH_CLIENT_ID:?}"; SEC="${NETLIFY_OAUTH_CLIENT_SECRET:?}"
RURI="${NETLIFY_OAUTH_REDIRECT_URI:-urn:ietf:wg:oauth:2.0:oob}"

case "${1:-}" in
  authorize)
    # encoder le redirect_uri
    enc=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=''))" "$RURI")
    echo "Ouvre cette URL, autorise, puis copie le CODE affiché :"
    echo "https://app.netlify.com/authorize?response_type=code&client_id=${CID}&redirect_uri=${enc}"
    echo "Ensuite : $0 token <CODE>"
    ;;
  token)
    CODE="${2:?usage: token <CODE>}"
    resp=$(curl -s --max-time 30 -X POST "https://api.netlify.com/oauth/token" \
      -d "grant_type=authorization_code" -d "client_id=${CID}" \
      -d "client_secret=${SEC}" -d "code=${CODE}" -d "redirect_uri=${RURI}")
    tok=$(echo "$resp" | python3 -c "import json,sys;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
    if [ -z "$tok" ]; then echo "FAIL échange token. Réponse: $resp"; exit 1; fi
    # stocker le token au coffre + config CLI Netlify
    echo "NETLIFY_AUTH_TOKEN=$tok" > "$JARVIS/.secrets/netlify-token.env"; chmod 600 "$JARVIS/.secrets/netlify-token.env"
    python3 - "$tok" <<'PY'
import json,os,sys
p=os.path.expanduser("~/.config/netlify/config.json")
d={}
try: d=json.load(open(p))
except Exception: pass
d.setdefault("users",{}); d["userId"]=d.get("userId","oauth")
# Netlify CLI lit aussi NETLIFY_AUTH_TOKEN ; on garde le token au coffre comme source de vérité.
json.dump(d,open(p,"w"),indent=2)
print("config CLI mise à jour")
PY
    echo "✅ access_token obtenu et stocké (.secrets/netlify-token.env, 600)."
    echo "Utilise la CLI ainsi :  export \$(grep -v '^#' $JARVIS/.secrets/netlify-token.env) && netlify status"
    ;;
  *) echo "Usage: $0 {authorize|token <CODE>}";;
esac
