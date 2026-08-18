#!/usr/bin/env bash
# Alimente la bibliothèque vivante avec l'inventaire RÉEL du disque :
# skills, agents et CLI. Déterministe, 0 token, relançable.
#
# Format imposé par BLOCS-INDEX.tsv : nom<TAB>source<TAB>danger<TAB>bloc
#   🟢 sûr (lecture / invocation)  🟠 modifie  🔴 destructif
set -uo pipefail

LIB="$HOME/labo/bibliotheque/lib"
IDX="$LIB/BLOCS-INDEX.tsv"
mkdir -p "$LIB"

emit() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4"; }

# --- skills : invocables via l'outil Skill, donc sans effet de bord direct ---
{
  printf 'nom\tsource\tdanger\tbloc\n'
  for d in "$HOME"/.claude/skills/*/ "$HOME"/jarvis/.claude/skills/*/; do
    [ -d "$d" ] || continue
    n=$(basename "$d")
    # La description du frontmatter rend le bloc utile au routage par intention.
    desc=$(grep -m1 '^description:' "$d/SKILL.md" 2>/dev/null | cut -c14- | cut -c1-160)
    emit "$n" "skill-live" "🟢" "Skill: $n${desc:+ — $desc}"
  done
} > "$LIB/skill-live-blocs.tsv"

# --- agents Claude : frontmatter name + description ---
{
  printf 'nom\tsource\tdanger\tbloc\n'
  for f in "$HOME"/.claude/agents/*.md; do
    [ -f "$f" ] || continue
    n=$(basename "$f" .md)
    desc=$(grep -m1 '^description:' "$f" 2>/dev/null | cut -c14- | cut -c1-160)
    emit "$n" "agent-live" "🟢" "Agent tool subagent_type=$n${desc:+ — $desc}"
  done
  # --- agents OpenClaw : un répertoire par agent ---
  for d in "$HOME"/.openclaw/agents/*/; do
    [ -d "$d" ] || continue
    n=$(basename "$d")
    emit "$n" "agent-openclaw-live" "🟢" "invoke_agent $n  # MCP jarvis-agents"
  done
} > "$LIB/agent-live-blocs.tsv"

# --- CLI : scripts exécutables → 🟠 (ils agissent sur le système) ---
{
  printf 'nom\tsource\tdanger\tbloc\n'
  for f in "$HOME"/jarvis/cli/*.py "$HOME"/jarvis/bin/*; do
    [ -f "$f" ] && [ -x "$f" -o "${f##*.}" = "py" ] || continue
    n=$(basename "$f")
    case "$f" in
      *.py) emit "${n%.py}" "cli-live" "🟠" "python3 $f" ;;
      *)    emit "$n"       "cli-live" "🟠" "bash $f" ;;
    esac
  done
} > "$LIB/cli-live-blocs.tsv"

# --- fusion : on retire les anciennes lignes de ces sources avant de réinjecter,
#     sinon chaque passe empilerait des doublons.
TMP=$(mktemp)
awk -F'\t' 'NR==1 || ($2 != "skill-live" && $2 != "agent-live" && $2 != "agent-openclaw-live" && $2 != "cli-live")' "$IDX" > "$TMP"
for s in skill-live agent-live cli-live; do
  tail -n +2 "$LIB/$s-blocs.tsv" >> "$TMP"
done
mv "$TMP" "$IDX"

echo "skills : $(($(wc -l < "$LIB/skill-live-blocs.tsv") - 1))"
echo "agents : $(($(wc -l < "$LIB/agent-live-blocs.tsv") - 1))"
echo "cli    : $(($(wc -l < "$LIB/cli-live-blocs.tsv") - 1))"
echo "INDEX  : $(wc -l < "$IDX") lignes"
