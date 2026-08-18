#!/usr/bin/env bash
# skill-detect — Scan exhaustif skills + hooks JARVIS

set -uo pipefail
mode="${1:-text}"

echo "═══ SKILLS ═══"
for d in ~/.claude/skills ~/jarvis/.claude/skills; do
  [ -d "$d" ] || continue
  find "$d" -maxdepth 3 -name "SKILL.md" 2>/dev/null | while read f; do
    name=$(basename "$(dirname "$f")")
    lines=$(wc -l < "$f" 2>/dev/null)
    printf "  · %-50s [%d lignes]\n" "$name" "$lines"
  done
done

# Plugin skills (read-only)
plugin_root=~/.claude/plugins/cache
if [ -d "$plugin_root" ]; then
  echo ""
  echo "═══ PLUGIN SKILLS (cache) ═══"
  find "$plugin_root" -maxdepth 5 -name "SKILL.md" 2>/dev/null | while read f; do
    name=$(basename "$(dirname "$f")")
    plugin=$(echo "$f" | awk -F/ '{print $7}')
    printf "  · %-30s [plugin: %s]\n" "$name" "$plugin"
  done | head -30
fi

echo ""
echo "═══ HOOKS settings.json ═══"
jq -r '.hooks | keys[]?' ~/.claude/settings.json 2>/dev/null | while read evt; do
  count=$(jq ".hooks.\"$evt\" | length" ~/.claude/settings.json 2>/dev/null)
  printf "  · %-25s [%s configs]\n" "$evt" "$count"
done

echo ""
echo "═══ HOOK SCRIPTS ═══"
find ~/.claude/hooks -maxdepth 1 -name "*.sh" 2>/dev/null | while read f; do
  name=$(basename "$f")
  size=$(stat -c %s "$f" 2>/dev/null)
  printf "  · %-40s [%d bytes]\n" "$name" "$size"
done
