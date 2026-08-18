---
id: nrwl-nx-claude-skills-reproduce-issue-skill-md
name: "reproduce-issue"
author: "nrwl"
repository: "https://github.com/nrwl/nx/tree/master/.claude/skills/reproduce-issue"
skill_url: "https://skillsmp.com/creators/nrwl/nx/claude-skills-reproduce-issue"
stars: 29188
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:08:27.925019"
---

# Résumé
The single skill for reproducing an nx issue. Given a GitHub issue number (human entry) OR explicit repro parameters (agent entry), it runs the reproduction ENTIRELY inside an isolated Docker sandbox — gVisor on Linux, the Docker VM on macOS — so the untrusted repro's install scripts and commands never execute on the host, then reports whether it reproduces. Called by humans via "/reproduce-issue

# Objectif
Skill d'automatisation/intégration pour reproduce-issue.

# Déclencheurs d’utilisation
Mots-clés associés: reproduce-issue, nrwl

# Procédure
Consulter le dépôt source: https://github.com/nrwl/nx/tree/master/.claude/skills/reproduce-issue

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
