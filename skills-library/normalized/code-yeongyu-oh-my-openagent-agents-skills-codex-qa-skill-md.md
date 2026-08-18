---
id: code-yeongyu-oh-my-openagent-agents-skills-codex-qa-skill-md
name: "codex-qa"
author: "code-yeongyu"
repository: "https://github.com/code-yeongyu/oh-my-openagent/tree/dev/.agents/skills/codex-qa"
skill_url: "https://skillsmp.com/creators/code-yeongyu/oh-my-openagent/agents-skills-codex-qa"
stars: 67193
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:09:04.183693"
---

# Résumé
QA the omo Codex Light edition (lazycodex / packages/omo-codex) itself, in strict isolation so ONLY our plugin is exercised, never the user's real ~/.codex. The first-party method drives the real `codex app-server` against an isolated CODEX_HOME plus a LOCAL mock model (no real API call), and proves a plugin hook fired by asserting hook/started + hook/completed notifications. Also: isolated install verification, per-component hook probes, a tmux TUI smoke, and runtime log observation (RUST_LOG / logs SQLite / /debug-config). Ships tested helper scripts each with a --self-test. Use whenever someone changes anything under packages/omo-codex or wants to QA, smoke-test, verify, or debug the Codex plugin, its hooks/components, the installer/config.toml, the app-server flow, or the Codex TUI. Triggers: codex qa, qa codex, codex-qa, test codex plugin, verify codex hook, codex app-server, lazycodex qa, isolated CODEX_HOME, prove codex hook fired, codex tui test.

# Objectif
Skill d'automatisation/intégration pour codex-qa.

# Déclencheurs d’utilisation
Mots-clés associés: codex-qa, code-yeongyu

# Procédure
Consulter le dépôt source: https://github.com/code-yeongyu/oh-my-openagent/tree/dev/.agents/skills/codex-qa

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
