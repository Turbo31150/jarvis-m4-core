#!/usr/bin/env bash
# m6-watch.sh — etat du noeud GPU distant M6, en une page.
# Extrait de ttx : l imbrication de guillemets dans tmux rendait la fenetre
# M6 impossible a creer (elle sautait en silence le 20/08).
#
# Deux routes vers la MEME machine (hostname 'turbo') :
#   - cable direct ASIX 10.42.0.230  -> 1,4 ms quand il tient
#   - Tailscale        100.112.114.32 -> ~0,5 a 10 s, toujours debout
M6_DIRECT="10.42.0.230"
M6_TS="100.112.114.32"

echo "════════ M6 — NOEUD GPU DISTANT ════════"

printf 'cable direct %-16s : ' "$M6_DIRECT"
if ping -c1 -W2 "$M6_DIRECT" >/dev/null 2>&1; then
  echo "VIVANT (1,4 ms)"
  URL="http://$M6_DIRECT:1234"
else
  echo "MORT"
  URL="http://$M6_TS:1234"
fi

printf 'tailscale    %-16s : ' "$M6_TS"
if curl -sf --max-time 20 "http://$M6_TS:1234/api/v0/models" >/dev/null 2>&1; then
  echo "VIVANT"
else
  echo "MUET"
fi

echo
echo "── modeles sur $URL ──"
curl -s --max-time 25 "$URL/api/v0/models" 2>/dev/null | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin).get("data", [])
except Exception:
    print("  pas de reponse exploitable")
    sys.exit(0)
charges = sum(1 for m in data if m.get("state") == "loaded")
print(f"  {charges} charge(s) sur {len(data)} declare(s)")
for m in data:
    ident = m.get("id", "?")
    etat = m.get("state", "?")
    print("    %-44s %s" % (ident, etat))
' 2>/dev/null || echo "  injoignable"

echo
echo "── vectorisation bibliotheque ──"
RESTE=$(timeout 20 sqlite3 "$HOME/jarvis/board/board.db" \
        "SELECT COUNT(*) FROM chunks WHERE embedding IS NULL;" 2>/dev/null || echo "?")
TOTAL=$(timeout 20 sqlite3 "$HOME/jarvis/board/board.db" \
        "SELECT COUNT(*) FROM chunks;" 2>/dev/null || echo "?")
echo "  $RESTE chunk(s) sans vecteur sur $TOTAL"
