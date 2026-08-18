---
id: nrwl-nx-claude-skills-setup-review-sandbox-skill-md
name: "setup-review-sandbox"
author: "nrwl"
repository: "https://github.com/nrwl/nx/tree/master/.claude/skills/setup-review-sandbox"
skill_url: "https://skillsmp.com/creators/nrwl/nx/claude-skills-setup-review-sandbox"
stars: 29188
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:27.925248"
---

# Résumé
One-time setup of the sandbox prerequisites used by the reproduce-issue skill and the reproduce-verifier agent — Docker, the isolation runtime (gVisor on Linux / Colima on macOS), healthy container networking, and the nx-review-sandbox toolchain image (built from the repo's mise.toml). Idempotent; re-run any time to verify or repair. Use when the user says "set up the review sandbox", "install the sandbox prereqs", "build the sandbox image", or a reproduce-issue preflight reports something MISSING.

# Objectif
Skill d'automatisation/intégration pour setup-review-sandbox.

# Déclencheurs d’utilisation
Mots-clés associés: setup-review-sandbox, nrwl

# Procédure
Consulter le dépôt source: https://github.com/nrwl/nx/tree/master/.claude/skills/setup-review-sandbox

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
