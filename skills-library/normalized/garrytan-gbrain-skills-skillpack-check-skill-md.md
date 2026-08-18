---
{
  "name": "skillpack-check",
  "source": "https://skillsmp.com/creators/garrytan/gbrain/skills-skillpack-check",
  "repository": "https://github.com/garrytan/gbrain/tree/master/skills/skillpack-check",
  "author": "garrytan",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:31:12+00:00",
  "verified": false,
  "quality_score": 91,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "bffb755b1c177357546fc48635944cb0033c33e61ed7eed75064210204c83877"
}
---

# Résumé
Run `gbrain skillpack-check` to produce an agent-readable JSON health report
for the gbrain install. Wraps `gbrain doctor` + `gbrain apply-migrations
--list` so a host agent (your OpenClaw's morning-briefing, any OpenClaw cron)
can see at a glance whether the skillpack needs attention.

Use when the user asks "is gbrain healthy?", when a cron fires a morning
check, or proactively when something seems off (jobs not running, brain
not updating, autopilot silent).

# Source originale
- SkillsMP : https://skillsmp.com/creators/garrytan/gbrain/skills-skillpack-check
- Dépôt    : https://github.com/garrytan/gbrain/tree/master/skills/skillpack-check

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
