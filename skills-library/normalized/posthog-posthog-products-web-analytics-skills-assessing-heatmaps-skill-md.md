---
id: posthog-posthog-products-web-analytics-skills-assessing-heatmaps-skill-md
name: "assessing-heatmaps"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/products/web_analytics/skills/assessing-heatmaps"
skill_url: "https://skillsmp.com/creators/posthog/posthog/products-web-analytics-skills-assessing-heatmaps"
stars: 37496
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:19.525591"
---

# Résumé
Assesses what a page's heatmap is telling you and recommends concrete changes. Pulls click / rageclick / scroll-depth data for a URL, names the hot elements by cross-referencing autocapture events on the same page, and can create a saved heatmap the user opens in PostHog, then summarizes the behavior and proposes improvements.
TRIGGER when: user asks what a heatmap shows, why people aren't clicking something, where users rage-click, how far they scroll, what to change on a page based on heatmap/click data, or to 'analyze/assess/review the heatmap' for a URL.
DO NOT TRIGGER when: the user only wants to create a saved heatmap screenshot with no analysis (use heatmaps-saved-create directly), or is asking about session replay in general (use investigating-replay).

# Objectif
Skill d'automatisation/intégration pour assessing-heatmaps.

# Déclencheurs d’utilisation
Mots-clés associés: assessing-heatmaps, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/products/web_analytics/skills/assessing-heatmaps

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
