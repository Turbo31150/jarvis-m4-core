#!/usr/bin/env bash
# cascade-cli.sh — commandes courtes de la cascade CLI JARVIS (à SOURCER, pas exécuter)
# Charge: ask / askf / askc / askr / askq / askw / cascade
# Réf protocole: ~/jarvis/audit/CAHIER_CHARGES_CASCADE_CLI.md §3
# 0 token API Anthropic — tout passe par le cluster local + Gemini (Google One).

_CASCADE_DIR="$HOME/jarvis/scripts"
_CASCADE_DOC="$HOME/jarvis/audit/CAHIER_CHARGES_CASCADE_CLI.md"

_cascade_guard() {  # $1 = script attendu
  if [ ! -f "$_CASCADE_DIR/$1" ]; then
    echo "cascade: $_CASCADE_DIR/$1 introuvable" >&2; return 1
  fi
}

# Niveau auto — routeur intelligent (classe la tâche + fallback)
ask()  { local b="$HOME/.local/bin/jarvis-ask"; [ -x "$b" ] || b="$_CASCADE_DIR/jarvis-ask.sh"; bash "$b" --auto "$@"; }

# Niveau 1 — texte court (parallèle M1+M2+OL1, 1er non-vide)
askf() { _cascade_guard lm-ask.sh || return 1; bash "$_CASCADE_DIR/lm-ask.sh" "$@"; }

# Niveau 2 — code routinier (--big = qwen3.5-9b M1 + qwen2.5-coder:7b M2)
askc() { _cascade_guard lm-ask.sh || return 1; bash "$_CASCADE_DIR/lm-ask.sh" --big "$@"; }

# Niveau 3 — reasoning (deepseek-r1 sur M1+M2)
askr() { _cascade_guard lm-ask.sh || return 1; bash "$_CASCADE_DIR/lm-ask.sh" --reason "$@"; }

# Niveau 4 — quorum local : reason puis big (tu arbitres)
askq() {
  _cascade_guard lm-ask.sh || return 1
  echo "── [reason] ──"; bash "$_CASCADE_DIR/lm-ask.sh" --reason "$@"
  echo "── [big] ──";    bash "$_CASCADE_DIR/lm-ask.sh" --big "$@"
}

# Niveau 5 — web / gros contexte (gemini pro→flash→antigravity→lm-ask)
askw() { _cascade_guard gemini-ask.sh || return 1; bash "$_CASCADE_DIR/gemini-ask.sh" "$@"; }

# Aide — protocole de cascade
cascade() {
  cat <<'EOF'
CASCADE CLI JARVIS — router au backend le moins cher (0 token API) :
  ask  "<q>"   → routeur AUTO (classe fast/code/reason/web + fallback)   [recommandé]
  askf "<q>"   → 1. texte court / résumé / extract        (cluster fast)
  askc "<q>"   → 2. code / refactor / doc                 (--big)
  askr "<q>"   → 3. reasoning / debug logique             (deepseek-r1)
  askq "<q>"   → 4. quorum local (reason + big, tu tranches)
  askw "<q>"   → 5. recherche web / gros contexte         (gemini)
  (6. archi / debug critique → Opus, manuel)
EOF
  [ -f "$_CASCADE_DOC" ] && echo "Doc complète: $_CASCADE_DOC"
}
