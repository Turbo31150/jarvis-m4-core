---
id: stirling-tools-stirling-pdf-claude-skills-feature-walkthrough-skill-md
name: "feature-walkthrough"
author: "Stirling-Tools"
repository: "https://github.com/Stirling-Tools/Stirling-PDF/tree/main/.claude/skills/feature-walkthrough"
skill_url: "https://skillsmp.com/creators/stirling-tools/stirling-pdf/claude-skills-feature-walkthrough"
stars: 88793
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:21.938411"
---

# Résumé
Explain the full logic and process of the current branch end-to-end so someone with no prior knowledge of the task can understand, review, and reproduce it. Scopes the change from the branch diff, traces the flow across every layer it touches (frontend tool/hook/component, Java controller/service/endpoint, Python engine, config, i18n, tests), and produces a self-contained walkthrough document with Mermaid diagrams (sequence/flow/architecture), annotated file map with clickable references, before/after behavior, screenshots where a UI is involved, a "try it locally" section, and edge cases/risks. Use when asked for a feature or branch walkthrough, "explain what this branch does", a design/logic writeup, PR reviewer onboarding, or a hand-off doc. Pass --html to also emit a rendered HTML version; --no-screens to skip screenshots.

# Objectif
Skill d'automatisation/intégration pour feature-walkthrough.

# Déclencheurs d’utilisation
Mots-clés associés: feature-walkthrough, Stirling-Tools

# Procédure
Consulter le dépôt source: https://github.com/Stirling-Tools/Stirling-PDF/tree/main/.claude/skills/feature-walkthrough

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
