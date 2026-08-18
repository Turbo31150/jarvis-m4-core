---
id: activepieces-activepieces-agents-skills-debug-failed-run-skill-md
name: "debug-failed-run"
author: "activepieces"
repository: "https://github.com/activepieces/activepieces/tree/main/.agents/skills/debug-failed-run"
skill_url: "https://skillsmp.com/creators/activepieces/activepieces/agents-skills-debug-failed-run"
stars: 23574
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:29.689561"
---

# Résumé
Debug a failed Activepieces flow run end-to-end: given a flow run id (or BullMQ job id), find why it failed, cross-referencing the live BullMQ job + Postgres rows (SSH script on the DevOps box), the centralized ClickHouse logs (ClickStack MCP), and the code in this repo, then categorize the failed-job backlog on request.

# Objectif
Skill d'automatisation/intégration pour debug-failed-run.

# Déclencheurs d’utilisation
Mots-clés associés: debug-failed-run, activepieces

# Procédure
Consulter le dépôt source: https://github.com/activepieces/activepieces/tree/main/.agents/skills/debug-failed-run

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
