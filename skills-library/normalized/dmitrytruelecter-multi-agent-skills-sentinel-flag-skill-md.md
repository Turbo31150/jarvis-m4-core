---
id: dmitrytruelecter-multi-agent-skills-sentinel-flag-skill-md
name: "sentinel-flag"
author: "DmitryTrueLecter"
repository: "https://github.com/DmitryTrueLecter/multi-agent/tree/main/skills/sentinel-flag"
skill_url: "https://skillsmp.com/creators/dmitrytruelecter/multi-agent/skills-sentinel-flag"
stars: 0
verified: false
quality_score: 60
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:25.881573"
---

# Résumé
Record a prompt/process problem for sentinel to review. Creates a Task issue in the tracker's Sentinel queue (status sentinel_inbox; labels sentinel-flag + flag-type:<type> + agent:sentinel). Runs alongside the caller's task; invoke once per defect — creation and the Sentinel-queue transition are one unit the skill completes internally. Invocation: /dma:sentinel-flag <type> "<problem>" where:<file:section> [originating:<KEY>] [details:<text>].

# Objectif
Skill d'automatisation/intégration pour sentinel-flag.

# Déclencheurs d’utilisation
Mots-clés associés: sentinel-flag, DmitryTrueLecter

# Procédure
Consulter le dépôt source: https://github.com/DmitryTrueLecter/multi-agent/tree/main/skills/sentinel-flag

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
