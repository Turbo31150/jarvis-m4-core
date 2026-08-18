#!/usr/bin/env bash
# jarvis-mirra — CLI auto-detect plateformes Mirra + audit cohérence + dispatch
#
# Usage:
#   jarvis-mirra status           # statut OAuth + chiffres gonflés détectés
#   jarvis-mirra audit            # cohérence claims vs réalité (cluster, GitHub)
#   jarvis-mirra slides           # régénère 6 slides reply LinkedIn (PIL local)
#   jarvis-mirra publish-li FILE  # publie texte sur LinkedIn via Path E
#   jarvis-mirra detect-plugins   # liste outils/MCP/skills auto-détectés
#   jarvis-mirra help

set -euo pipefail

ROUTE_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS_DIR="$(cd "$ROUTE_DIR/.." && pwd)"
JARVIS_ROOT="$HOME/jarvis"

# IDs Mirra (source-of-truth)
ACC_IG="a8bf4841-a64b-4d75-b752-0b992f0678b0"
ACC_THREADS="4d5081d0-0955-4c87-9901-312296b3f532"
ACC_TIKTOK="6667a068-2084-4261-9830-cb74d690fd7b"
ACC_YT="070f4cb3-d6fb-4d9c-82e8-3958ac66489f"

# Chiffres gonflés à détecter dans personas
INFLATED_PATTERNS=("1000+ agents" "12 GPUs" "P95 18ms" "835 Domino" "99.9% uptime")
TRUE_NUMBERS=("250+ agents" "10 GPUs" "P95 cible <50ms" "boucle Domino en cours de fix")

cmd="${1:-help}"

print_header() { printf "\n\033[1;36m=== %s ===\033[0m\n" "$1"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m⚠\033[0m %s\n" "$1"; }
err()  { printf "  \033[31m✗\033[0m %s\n" "$1"; }

cmd_status() {
  print_header "Mirra MCP status"
  if claude mcp list 2>/dev/null | grep -q "mirra.*Connected"; then
    ok "MCP mirra connected"
  else
    err "MCP mirra not connected — claude mcp add mirra ..."
    return 1
  fi
  print_header "Chrome CDP :9222"
  if curl -s --max-time 2 http://localhost:9222/json/version >/dev/null 2>&1; then
    ok "Chrome CDP alive"
    li_tabs=$(curl -s http://localhost:9222/json | grep -c "linkedin.com/feed" || echo 0)
    if [ "$li_tabs" -gt 0 ]; then ok "LinkedIn tab loggué"; else warn "0 tab LinkedIn loggué"; fi
  else
    warn "Chrome CDP :9222 down (Path A/E LinkedIn KO)"
  fi
  print_header "JARVIS-CDP service :9108"
  curl -s --max-time 2 http://127.0.0.1:9108/ -o /dev/null -w "  HTTP %{http_code}\n" 2>/dev/null || warn "jarvis-cdp service down"
}

cmd_audit() {
  print_header "Audit cohérence claims marketing vs réalité"

  # M1 GPU réels
  gpus_m1=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | wc -l)
  ok "M1 GPUs détectés : $gpus_m1 (claim courant : 6)"

  # Domino loop status
  domino_log="/home/pamerys/Workspaces/jarvis-linux/logs/domino-engine.log"
  if [ -f "$domino_log" ]; then
    recent_crashes=$(tail -200 "$domino_log" | grep -c "service_crash" || echo 0)
    recent_success=$(tail -200 "$domino_log" | grep -ic "success\|completed" || echo 0)
    if [ "$recent_success" -eq 0 ] && [ "$recent_crashes" -gt 10 ]; then
      err "Domino boucle stérile : $recent_crashes service_crash / 0 succès (claim '835 chaînes' = invalide)"
    else
      ok "Domino : $recent_success succès / $recent_crashes crashes"
    fi
  fi

  # jarvis.db integrity
  jdb="$HOME/jarvis/data/jarvis.db"
  if [ -f "$jdb" ]; then
    if sqlite3 "$jdb" "PRAGMA integrity_check;" 2>&1 | grep -q "ok"; then
      ok "jarvis.db integrity OK"
    else
      err "jarvis.db CORROMPUE (Rowid out of order) — sqlite3 .recover requis"
    fi
  fi

  # GitHub repos publics
  pub_count=$(gh api users/Turbo31150/repos --paginate -q '.[] | select(.private==false) | .name' 2>/dev/null | wc -l)
  ok "GitHub repos publics : $pub_count (claim '106 repos' inclut privés)"

  # Whisper device
  if pgrep -af "whisper" | grep -q "cuda"; then
    ok "Whisper sur CUDA"
  else
    warn "Whisper sur CPU (claim '<300ms' non garanti)"
  fi
}

cmd_slides() {
  print_header "Génération 6 slides réponse LinkedIn (PIL local — anti quota AI)"
  python3 "$ROUTE_DIR/gen_slides.py"
}

cmd_publish_li() {
  local txt_file="${2:-}"
  [ -z "$txt_file" ] && { err "Usage: jarvis-mirra publish-li FILE.txt"; return 2; }
  [ ! -f "$txt_file" ] && { err "File not found: $txt_file"; return 3; }
  print_header "Publication LinkedIn via Path E (linkedin_publisher.py + fallback iframe JS)"
  warn "Path E nécessite Claude Code session active (claude-in-chrome MCP)"
  echo "  Texte à publier : $txt_file ($(wc -c < "$txt_file") bytes)"
  echo ""
  echo "  → Demande à Claude :"
  echo "    'Publie le contenu de $txt_file sur LinkedIn via Path E'"
  echo ""
  echo "  Path E procédure stockée dans :"
  echo "    ~/.claude/skills/mirra-omnichannel-publish/SKILL.md"
}

cmd_detect_plugins() {
  print_header "Auto-détection MCPs / Skills / Outils JARVIS"

  printf "\n\033[1mMCP servers connectés :\033[0m\n"
  claude mcp list 2>/dev/null | grep -E "Connected|✓" | sed 's/^/  /' | head -20

  printf "\n\033[1mSkills disponibles (locaux) :\033[0m\n"
  for d in ~/.claude/skills ~/jarvis/.claude/skills; do
    [ -d "$d" ] && find "$d" -maxdepth 2 -name "SKILL.md" 2>/dev/null | while read f; do
      name=$(basename "$(dirname "$f")")
      printf "  \033[32m✓\033[0m %s\n" "$name"
    done
  done | head -20

  printf "\n\033[1mScripts JARVIS auto-publish :\033[0m\n"
  for s in \
    "$HOME/jarvis/automation/linkedin_publisher.py" \
    "$ROUTE_DIR/gen_slides.py" \
    "$ROUTE_DIR/route.sh"; do
    [ -f "$s" ] && ok "$(basename "$s") ($(stat -c %s "$s" 2>/dev/null) bytes)"
  done

  printf "\n\033[1mPersonas Mirra connectées (4) :\033[0m\n"
  echo "  Instagram : $ACC_IG"
  echo "  Threads   : $ACC_THREADS"
  echo "  TikTok    : $ACC_TIKTOK"
  echo "  YouTube   : $ACC_YT"
}

cmd_help() {
  cat <<EOF
\033[1;36mjarvis-mirra\033[0m — CLI auto-détection Mirra + audit cohérence + Path E LinkedIn

USAGE :
  jarvis-mirra status              Statut OAuth + Chrome CDP + JARVIS-CDP
  jarvis-mirra audit               Cohérence claims marketing vs réalité (GPU, Domino, DB, Whisper, GitHub)
  jarvis-mirra slides              Régénère 6 slides Instagram réponse LinkedIn (PIL local, bypass quota)
  jarvis-mirra publish-li FILE     Procédure publication LinkedIn Path E (assistant requis)
  jarvis-mirra detect-plugins      Liste MCPs/skills/scripts auto-détectés
  jarvis-mirra help

REFERENCES :
  Skill omnichannel : ~/.claude/skills/mirra-omnichannel-publish/SKILL.md (Path E inclus)
  Route gen slides  : $ROUTE_DIR/gen_slides.py
  Backup pipeline   : ~/jarvis/.claude/skills/run-jarvis-n8n-backup/driver.sh

PERSONAS (mise à jour 2026-05-28 honnête) :
  YouTube  ✅ chiffres réels
  TikTok   ✅ chiffres réels
  IG/Threads (180 agents/6 GPUs) — à harmoniser si tu veux

EOF
}

case "$cmd" in
  status)         cmd_status ;;
  audit)          cmd_audit ;;
  slides)         cmd_slides ;;
  publish-li)     cmd_publish_li "$@" ;;
  detect-plugins) cmd_detect_plugins ;;
  help|--help|-h|"") cmd_help ;;
  *) err "Unknown command: $cmd"; cmd_help; exit 2 ;;
esac
