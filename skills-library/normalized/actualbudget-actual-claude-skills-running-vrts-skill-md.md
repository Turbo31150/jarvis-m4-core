---
id: actualbudget-actual-claude-skills-running-vrts-skill-md
name: "running-vrts"
author: "actualbudget"
repository: "https://github.com/actualbudget/actual/tree/master/.claude/skills/running-vrts"
skill_url: "https://skillsmp.com/creators/actualbudget/actual/claude-skills-running-vrts"
stars: 27948
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:27.925342"
---

# Résumé
Use whenever adding, updating, regenerating, running, or debugging visual regression tests (VRTs) / screenshot tests in the Actual Budget repo — including phrases like "add a VRT", "add a screenshot test", "update the snapshots", "regenerate the VRT screenshots", "the VRT is failing", "yarn vrt", "vrt:docker", or "/update-vrt", and any time a UI change needs screenshot coverage. VRT snapshots must be generated inside the Linux docker image (never on the host) and snapshot updates must be scoped to the changed test only — getting either wrong produces snapshots CI ignores or rewrites every screenshot in the repo.

# Objectif
Skill d'automatisation/intégration pour running-vrts.

# Déclencheurs d’utilisation
Mots-clés associés: running-vrts, actualbudget

# Procédure
Consulter le dépôt source: https://github.com/actualbudget/actual/tree/master/.claude/skills/running-vrts

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
