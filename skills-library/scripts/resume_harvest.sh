#!/usr/bin/env bash
# resume_harvest.sh — reprise quotidienne de la moisson SkillsMP (mode permanent).
# Borné par construction : quota jour dans skillsmp-harvest.py (50 sans clé,
# 500 avec SKILLSMP_API_KEY), checkpoint atomique, arrêt à sec par mot-clé.
#
# ⚠ NE PAS enchaîner sur `skillsmp.py ingest` : cette commande fait
#   DELETE FROM skills puis recharge TOUT depuis son JSON source — l'appeler
#   avec notre export écraserait les ~199k skills de data/skillsmp.db.
#   La bibliothèque croissante vit dans INDEX.jsonl + normalized/.
set -uo pipefail

LOG="$HOME/jarvis/skills-library/logs/resume-$(date +%Y%m%d).log"
{
  echo "=== reprise $(date -Is) ==="
  python3 "$HOME/jarvis/bin/skillsmp-harvest.py" run --max-requests "${SKILLSMP_MAX_REQ:-50}"
  # Étapes 8-9 : contenu SKILL.md via gh (borné, plancher de quota GitHub intégré)
  python3 "$HOME/jarvis/bin/skillsmp-harvest.py" fetch-content --max-fetch "${SKILLSMP_MAX_FETCH:-300}"
  # Garde-fou board 2026-08-08 : quarantaine des DANGEROUS puis fusion biblio
  # (le merge exclut les DANGEROUS et dédup par nom+source — idempotent)
  python3 "$HOME/jarvis/bin/skillsmp-harvest.py" quarantine
  python3 "$HOME/jarvis/bin/skillsmp-to-biblio.py"
  python3 "$HOME/jarvis/bin/skillsmp-harvest.py" report
} >> "$LOG" 2>&1
exit 0   # fail-safe : une reprise ratée ne doit pas marquer le timer failed
