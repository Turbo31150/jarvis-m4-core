---
id: bytedance-deer-flow-agent-skills-blocking-io-guard-skill-md
name: "blocking-io-guard"
author: "bytedance"
repository: "https://github.com/bytedance/deer-flow/tree/main/.agent/skills/blocking-io-guard"
skill_url: "https://skillsmp.com/creators/bytedance/deer-flow/agent-skills-blocking-io-guard"
stars: 79272
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:40.961196"
---

# Résumé
Ensure async-path backend code that could block the asyncio event loop is protected by a teeth-verified runtime anchor in tests/blocking_io/. Use when changing backend Python under app/, packages/harness/deerflow/, or scripts/, when running a blocking-IO triage round over the whole repo, or when a reviewer/CI asks for blocking-IO coverage. Runs a deterministic scan (changed-lines or full-repo), routes each candidate, drafts/extends an anchor, and proves it fails when the blocking IO regresses.

# Objectif
Skill d'automatisation/intégration pour blocking-io-guard.

# Déclencheurs d’utilisation
Mots-clés associés: blocking-io-guard, bytedance

# Procédure
Consulter le dépôt source: https://github.com/bytedance/deer-flow/tree/main/.agent/skills/blocking-io-guard

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
