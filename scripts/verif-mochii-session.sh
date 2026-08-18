#!/usr/bin/env bash
# verif-mochii-session.sh — automatisation de VÉRIFICATION (idempotente, sûre) de la
# session "capture Mochii → outils 0-token souverains" (prof + labo).
# NE contient AUCUNE commande destructive : pas de kill, pas de restart, pas de commit/push,
# pas d'inférence lourde (anti-surchauffe). Rejouable autant de fois qu'on veut.
set -uo pipefail

LABO="/home/pamerys/labo/passcerfa-app/.claude/worktrees/passcerfa-affiliation"
PROF="/home/pamerys/jarvis/webapp"
REG="/home/pamerys/jarvis/scripts/mochii-commandes-rapides.json"
PASS=0; FAIL=0
ok(){ echo "  ✅ $1"; PASS=$((PASS+1)); }
ko(){ echo "  ❌ $1"; FAIL=$((FAIL+1)); }

echo "==================================================================="
echo " VÉRIFICATION SESSION MOCHII — $(hostname) — GPU $(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader 2>/dev/null)°C"
echo "==================================================================="

echo "── 1. LABO : tests backend (node:test, 0 inférence) ──"
if [ -d "$LABO" ]; then
  ( cd "$LABO" && node --test tests/assistant.test.js tests/registry.test.js tests/partners.test.js >/tmp/labo_back.txt 2>&1 )
  grep -q "# fail 0" /tmp/labo_back.txt && ok "backend labo (assistant+registry+partners) tous verts" || ko "backend labo : voir /tmp/labo_back.txt"
else ko "worktree labo introuvable ($LABO)"; fi

echo "── 2. LABO : tests front (vitest jsdom) ──"
if [ -d "$LABO/frontend" ]; then
  # cible uniquement les tests présents sur la branche courante ; verdict = code de sortie (robuste ANSI)
  FRONT_TESTS=""
  for f in assistant-sidebar partner-selector; do
    [ -f "$LABO/frontend/src/tests/$f.test.ts" ] && FRONT_TESTS="$FRONT_TESTS src/tests/$f.test.ts"
  done
  if [ -n "$FRONT_TESTS" ]; then
    ( cd "$LABO/frontend" && npx vitest run $FRONT_TESTS >/tmp/labo_front.txt 2>&1 )
    [ $? -eq 0 ] && ok "front labo verts ($FRONT_TESTS )" || ko "front labo : voir /tmp/labo_front.txt"
  else ko "aucun test front ciblé présent sur cette branche"; fi
else ko "frontend labo introuvable"; fi

echo "── 3. PROF : routes live (curl localhost, 0 inférence) ──"
systemctl --user is-active jarvis-webapp >/dev/null 2>&1 && ok "service jarvis-webapp actif" || ko "jarvis-webapp inactif"
code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:7777/api/backends 2>/dev/null); [ "$code" = "200" ] && ok "/api/backends 200" || ko "/api/backends = $code"
nb=$(curl -s http://127.0.0.1:7777/api/registre 2>/dev/null | python3 -c "import json,sys;print(len(json.load(sys.stdin).get('commandes',[])))" 2>/dev/null)
[ -n "$nb" ] && ok "/api/registre OK ($nb commandes)" || ko "/api/registre KO"
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:7777/api/assistant -H 'Content-Type: application/json' -d '{"prompt":""}' 2>/dev/null); [ "$code" = "400" ] && ok "/api/assistant validation (vide→400)" || ko "/api/assistant = $code"
grep -q "fetch('/api/assistant'" "$PROF/index.html" && ok "onglet index.html recâblé sur /api/assistant" || ko "onglet pas recâblé"

echo "── 4. SANTÉ cascade locale (lecture seule) ──"
curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && ok "Ollama local (11434) répond" || ko "Ollama local KO"
t=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader 2>/dev/null); [ -n "$t" ] && { [ "$t" -lt 82 ] && ok "GPU $t°C (< seuil 82)" || echo "  ⚠️ GPU $t°C ≥ 82 (différer l'inférence)"; }

echo "── 5. GARDE-FOUS sécurité (0 fuite de secret) ──"
python3 -c "import json;json.load(open('$REG'));print('ok')" >/dev/null 2>&1 && ok "registre JSON valide" || ko "registre JSON invalide"
if grep -rql "882c2c3e" "$LABO" "$PROF" "$REG" 2>/dev/null; then ko "VALEUR DE CLÉ trouvée dans le code (FUITE)"; else ok "aucune valeur de clé dans le code/registre"; fi
[ -f /home/pamerys/.config/ollama/cloud.env ] && [ "$(stat -c '%a' /home/pamerys/.config/ollama/cloud.env)" = "600" ] && ok "clé cloud stockée chmod 600" || echo "  ℹ️ clé cloud absente ou perms != 600"

echo "==================================================================="
echo " RÉSULTAT : $PASS OK / $FAIL KO"
echo "==================================================================="
[ "$FAIL" -eq 0 ]
