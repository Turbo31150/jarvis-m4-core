---
id: posthog-posthog-agents-skills-django-startup-time-skill-md
name: "django-startup-time"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/.agents/skills/django-startup-time"
skill_url: "https://skillsmp.com/creators/posthog/posthog/agents-skills-django-startup-time"
stars: 37496
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:52.216848"
---

# Résumé
Keep heavy imports off the django.setup() path that every process (web, celery, temporal, migrate, shell, CI) pays for. Use when touching AppConfig.ready(), wiring signal receivers, editing the lazy API router (posthog/api/rest_router.py or its __init__.py shim), deferring a heavy import, when the startup-import-budget guard fails, or when merging master into a long-lived branch that made the router lazy.

# Objectif
Skill d'automatisation/intégration pour django-startup-time.

# Déclencheurs d’utilisation
Mots-clés associés: django-startup-time, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/.agents/skills/django-startup-time

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
