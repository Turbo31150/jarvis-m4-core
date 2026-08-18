---
id: perminder-klair-subwave-claude-skills-subwave-deploy-skill-md
name: "subwave-deploy"
author: "perminder-klair"
repository: "https://github.com/perminder-klair/subwave/tree/develop/.claude/skills/subwave-deploy"
skill_url: "https://skillsmp.com/creators/perminder-klair/subwave/claude-skills-subwave-deploy"
stars: 1172
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:13.181286"
---

# Résumé
Set up, deploy, or update SUB/WAVE (a personal internet radio station). On a fresh checkout, runs scripts/setup.sh, prompts for Navidrome + Ollama credentials, brings the stack up, and generates jingles. On an already-running stack, pulls the latest, rebuilds only the Docker services whose code actually changed, recreates them, and verifies the stream is on-air. Use this skill any time the user wants to install, set up, bootstrap, deploy, update, sync, redeploy, refresh, restart, or "pull and restart" SUB/WAVE — including phrases like "set up subwave", "install subwave", "first boot", "bootstrap the radio", "pull subwave", "update the radio", "deploy subwave", "rebuild controller", "restart sub-wave", "redeploy after pull", "git pull and restart as needed", "check if the stream is healthy", or simply "deploy" / "install" / "set up" while in the subwave repo. Trigger proactively whenever the user is working in the subwave repo and mentions setting up, installing, deploying, updating, rebuilding, restarting, or

# Objectif
Skill d'automatisation/intégration pour subwave-deploy.

# Déclencheurs d’utilisation
Mots-clés associés: subwave-deploy, perminder-klair

# Procédure
Consulter le dépôt source: https://github.com/perminder-klair/subwave/tree/develop/.claude/skills/subwave-deploy

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
