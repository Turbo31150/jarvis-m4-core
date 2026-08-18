---
id: posthog-posthog-agents-skills-writing-code-comments-skill-md
name: "writing-code-comments"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/.agents/skills/writing-code-comments"
skill_url: "https://skillsmp.com/creators/posthog/posthog/agents-skills-writing-code-comments"
stars: 37496
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:09:04.185384"
---

# Résumé
Gates whether a code comment should exist and forces the ones that stay to explain why, not what. Use ALWAYS before writing or editing a comment in any language (Python, TypeScript, Go, Rust, SQL), and when reviewing a diff that adds comments. Removes the comment types that clutter the codebase: narration that restates the code, change-history and chat-context notes ("previously did X", "per PR #123", "AI:"), commented-out code, and redundant docstrings. Keeps the ones that earn their place: a non-obvious why, a warning about a non-local consequence, a pointer to context a future reader can't reconstruct. Not for user-facing copy (see `/writing-user-facing-copy`) or commit messages.

# Objectif
Skill d'automatisation/intégration pour writing-code-comments.

# Déclencheurs d’utilisation
Mots-clés associés: writing-code-comments, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/.agents/skills/writing-code-comments

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
