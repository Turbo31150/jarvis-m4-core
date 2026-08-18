---
id: posthog-posthog-agents-skills-debugging-local-task-agent-runs-skill-md
name: "debugging-local-task-agent-runs"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/.agents/skills/debugging-local-task-agent-runs"
skill_url: "https://skillsmp.com/creators/posthog/posthog/agents-skills-debugging-local-task-agent-runs"
stars: 37496
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:08:31.693086"
---

# Résumé
Debug the output of local PostHog task runs — the wizard cloud-run path that executes inside a Docker sandbox under the local Temporal `process-task` workflow (the wizard that integrates PostHog, then the coding agent that commits and opens the PR). Use when a local run looks stuck, failed, or silent, or when you need to read the wizard or agent logs. Covers the `.env.local` keys + `ai_features` intent required for cloud runs locally, finding the task UUID (docker ps, temporal CLI, Temporal UI at localhost:8081), tailing live logs inside the sandbox container (`/tmp/posthog-wizard.log`, `/tmp/agent-server.log`), and reading the durable per-run console log from object storage after the sandbox is torn down. Trigger terms: task-sandbox, run_wizard, agent-server, process-task, SANDBOX_PROVIDER, LLM_GATEWAY, cloud_run, posthog-wizard.log.

# Objectif
Skill d'automatisation/intégration pour debugging-local-task-agent-runs.

# Déclencheurs d’utilisation
Mots-clés associés: debugging-local-task-agent-runs, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/.agents/skills/debugging-local-task-agent-runs

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
