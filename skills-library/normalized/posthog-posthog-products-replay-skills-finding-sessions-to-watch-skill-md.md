---
id: posthog-posthog-products-replay-skills-finding-sessions-to-watch-skill-md
name: "finding-sessions-to-watch"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/products/replay/skills/finding-sessions-to-watch"
skill_url: "https://skillsmp.com/creators/posthog/posthog/products-replay-skills-finding-sessions-to-watch"
stars: 37496
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:19.525862"
---

# Résumé
Guides a user from "I want to watch recordings but don't know which ones" to a short, high-signal list of sessions worth watching. Use when the user asks which sessions or replays to watch, wants help finding interesting / useful recordings, says they don't know where to start in session replay, or wants to watch sessions about a goal (signup, pricing, onboarding, checkout, a feature, rageclicks, errors, mobile, a specific person) without naming exact filters. Turns a vague intent into a focused RecordingsQuery via `query-session-recordings-list`, then deep-links the best few and hands off to `investigating-replay`. Do NOT use when the user already has a recording/session ID (use investigating-replay) or wants the replay for a known error issue (use finding-replay-for-issue).

# Objectif
Skill d'automatisation/intégration pour finding-sessions-to-watch.

# Déclencheurs d’utilisation
Mots-clés associés: finding-sessions-to-watch, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/products/replay/skills/finding-sessions-to-watch

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
