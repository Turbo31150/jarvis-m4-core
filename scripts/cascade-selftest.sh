#!/usr/bin/env bash
# cascade-selftest.sh — tests déterministes de la cascade CLI (anti-régression, 0 appel LLM)
# Usage: bash cascade-selftest.sh [--live]   (--live ajoute 1 appel cluster réel léger)
# Sortie: PASS/FAIL par check + code retour (0 = tout vert).

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS=0; FAIL=0
ok()   { printf "  ✅ %s\n" "$1"; PASS=$((PASS+1)); }
ko()   { printf "  ❌ %s\n" "$1"; FAIL=$((FAIL+1)); }
chk()  { if eval "$2" >/dev/null 2>&1; then ok "$1"; else ko "$1"; fi; }

echo "── 1. Syntaxe des scripts cascade ──"
for s in lm-ask.sh gemini-ask.sh gemini-smart.sh jarvis-ask.sh cascade-cli.sh; do
  chk "syntaxe $s" "bash -n '$DIR/$s'"
done

echo "── 2. Commandes chargées (7 fonctions) ──"
source "$DIR/cascade-cli.sh" 2>/dev/null
for fn in ask askf askc askr askq askw cascade; do
  chk "fonction $fn définie" "declare -F $fn"
done

echo "── 3. Garde-fous sécurité / stabilité ──"
# 3a. lm-ask : --big NE charge PAS un 35b sur M1 (M1=9b max → anti-freeze)
chk "lm-ask MODEL_BIG ≤ 9b (pas de 35b)" "! grep -q 'MODEL_BIG=\"qwen/qwen3.5-35b' '$DIR/lm-ask.sh'"
# 3b. gemini-smart : aucun --yolo hard-codé (anti prompt-injection)
chk "gemini-smart sans --yolo hard-codé" "! grep -qE 'gemini --prompt.*--yolo --model' '$DIR/gemini-smart.sh'"
# 3c. gemini-smart : YOLO_FLAG conditionnel présent
chk "gemini-smart YOLO_FLAG conditionnel" "grep -q 'YOLO_FLAG' '$DIR/gemini-smart.sh'"

echo "── 4. Classification routeur (dry, sans LLM) ──"
classify() {  # reproduit la logique de jarvis-ask.sh --auto
  local low="${1,,}" MODE="auto"
  if   echo "$low" | grep -qE "recherche|cherche.+(web|internet|en ligne)|actualit|derni[èe]re version|news|sur internet|google"; then MODE=web
  elif echo "$low" | grep -qE "refactor|impl[ée]ment|écris? (une|un|le|la)? ?(fonction|classe|script|code)|debug|corrige le code|\bcode\b|python|bash|typescript|sql\b"; then MODE=code
  elif echo "$low" | grep -qE "pourquoi|analyse|raisonn|compare|explique|logique|d[ée]montre|stratégie|architecture"; then MODE=reason
  elif [[ ${#1} -gt 500 ]]; then MODE=web; else MODE=fast; fi
  echo "$MODE"
}
chk "classe 'résume X' → fast"            "[ \"\$(classify 'résume ce texte')\" = fast ]"
chk "classe 'écris une fonction' → code"  "[ \"\$(classify 'écris une fonction python')\" = code ]"
chk "classe 'cherche sur internet' → web" "[ \"\$(classify 'cherche sur internet les news')\" = web ]"

if [[ "${1:-}" == "--live" ]]; then
  echo "── 5. Appel cluster réel (léger) ──"
  out="$(timeout 90 bash "$DIR/lm-ask.sh" 'dis OK' 2>/dev/null)"
  [ -n "${out// }" ] && ok "lm-ask répond ($(echo "$out"|head -c 30)…)" || ko "lm-ask vide (cluster down/cold ?)"
fi

echo "── BILAN : $PASS PASS / $FAIL FAIL ──"
[ "$FAIL" -eq 0 ]
