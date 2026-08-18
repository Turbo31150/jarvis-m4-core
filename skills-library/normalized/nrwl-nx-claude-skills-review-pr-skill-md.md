---
id: nrwl-nx-claude-skills-review-pr-skill-md
name: "review-pr"
author: "nrwl"
repository: "https://github.com/nrwl/nx/tree/master/.claude/skills/review-pr"
skill_url: "https://skillsmp.com/creators/nrwl/nx/claude-skills-review-pr"
stars: 29188
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:08:27.925140"
---

# Résumé
Deep code review of a single open PR in nrwl/nx. Checks out the PR inside an isolated sandbox container — gVisor on Linux, the Docker VM on macOS — never into the host working tree, runs the pr-review-toolkit review agents, the reproduce-verifier agent (grounds the review in the linked issues and executes the repro inside the sandbox), the alternative-approach agent (independently designs competing solutions and contrasts them with the PR's choice), the performance-analyzer agent (checks the changes don't waste CPU or memory and execute quickly at workspace scale), and the security-analyzer agent (hunts injection-class vulnerabilities — command injection, zip-slip, SSRF, credential leakage — across real trust boundaries), then — only when a finding turns on why the author did something, and only once the review is finished — verifies that finding against the PR's Polygraph session (read-only, never resumed; it can downgrade a finding or raise a question but never add one, and its internal content never reache

# Objectif
Skill d'automatisation/intégration pour review-pr.

# Déclencheurs d’utilisation
Mots-clés associés: review-pr, nrwl

# Procédure
Consulter le dépôt source: https://github.com/nrwl/nx/tree/master/.claude/skills/review-pr

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
