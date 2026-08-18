#!/usr/bin/env bash
# SERIE: admin-audit — audit 0-token d'un dossier/fichier de démarche admin (complet/manquant, RGPD, prochaine action) via cascade IA locale
set -uo pipefail
SRC="${1:?usage: lib.sh run admin-audit <fichier|dossier> [fichier_sortie]}"
[ -e "$SRC" ] || { echo "⛔ introuvable: $SRC"; exit 1; }
OUTDIR="$HOME/labo/_admin-prive"; mkdir -p "$OUTDIR"
base=$(basename "$SRC" | tr ' /' '__' | tr -cd 'A-Za-z0-9_.' | cut -c1-50)
OUT="${2:-$OUTDIR/audit-$base.md}"

# Rassemble le texte : fichier seul, ou tous les .md/.txt/.json d'un dossier (tronqué ~12k car)
if [ -d "$SRC" ]; then
  CONTENT=$(find "$SRC" -maxdepth 2 -type f \( -iname '*.md' -o -iname '*.txt' -o -iname '*.json' \) -print0 2>/dev/null \
            | xargs -0 -r awk 'FNR==1{print "\n===== "FILENAME" ====="}{print}' 2>/dev/null | head -c 12000)
else
  CONTENT=$(head -c 12000 "$SRC")
fi
[ -n "${CONTENT:-}" ] || { echo "⛔ aucun texte exploitable dans $SRC"; exit 1; }

PROMPT="Tu es assistant administratif. Audite le dossier/document de démarche administrative ci-dessous.
Rends en Markdown, français, factuel:
1) De quoi il s'agit (1-2 puces).
2) Ce qui est COMPLET (✅).
3) Ce qui MANQUE ou à corriger (❌/⏳) — précis.
4) Risques RGPD / pièces sensibles.
5) PROCHAINE action concrète (1-3 puces priorisées).
N'invente aucune donnée; si une info manque écris 'à vérifier'.

=== CONTENU ===
$CONTENT"

echo "🔎 Audit 0-token de: $SRC"
RES=$(curl -s -m 120 -X POST http://127.0.0.1:8788/api/cluster/orchestrate \
  -H 'Content-Type: application/json' \
  -d "$(python3 -c 'import json,sys;print(json.dumps({"content":sys.argv[1],"profile":"speed"}))' "$PROMPT")" 2>/dev/null \
  | python3 -c 'import sys,json
try:
 j=json.load(sys.stdin); print((j.get("content") or j.get("response") or j.get("text") or "").strip())
except Exception: pass' 2>/dev/null)

if [ -z "${RES:-}" ]; then
  echo "   (cascade :8788 muette → repli ol1-ask.sh, cold-load possible ~180s)"
  RES=$(bash "$HOME/jarvis/scripts/ol1-ask.sh" "$PROMPT" 2>/dev/null)
fi
[ -z "${RES:-}" ] && { echo "⛔ aucune réponse (cluster + OL1 down)"; exit 2; }

{ echo "# Audit admin — $base"; echo "_source: ${SRC}_"; echo; echo "$RES"; } > "$OUT"
echo "✅ écrit: $OUT"
