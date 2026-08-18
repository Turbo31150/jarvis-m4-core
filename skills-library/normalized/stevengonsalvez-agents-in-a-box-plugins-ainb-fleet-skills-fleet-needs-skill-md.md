---
id: stevengonsalvez-agents-in-a-box-plugins-ainb-fleet-skills-fleet-needs-skill-md
name: "ainb-fleet-fleet-needs"
author: "stevengonsalvez"
repository: "https://github.com/stevengonsalvez/agents-in-a-box/tree/main/plugins/ainb-fleet/skills/fleet-needs"
skill_url: "https://skillsmp.com/creators/stevengonsalvez/agents-in-a-box/plugins-ainb-fleet-skills-fleet-needs"
stars: 19
verified: false
quality_score: 79
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:48.383187"
---

# Résumé
Workflow-backed Jarvis control panel. Runs the deterministic `hangar`
workflow with verb=needs (discover → enrich → prioritize), renders the
Jarvis HUD from its render-ready cards, fires AskUserQuestion per blocked
session, and routes each answer back via tmux send-keys (broker fallback
only). Requires the workflow gate (CLAUDE_CODE_WORKFLOWS=1). If the gate is
off, fall back to the prompt-driven `/ainb-fleet:needs` skill.

# Objectif
Skill d'automatisation/intégration pour ainb-fleet-fleet-needs.

# Déclencheurs d’utilisation
Mots-clés associés: ainb-fleet-fleet-needs, stevengonsalvez

# Procédure
Consulter le dépôt source: https://github.com/stevengonsalvez/agents-in-a-box/tree/main/plugins/ainb-fleet/skills/fleet-needs

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
