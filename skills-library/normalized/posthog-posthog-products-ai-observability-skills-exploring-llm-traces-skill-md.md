---
id: posthog-posthog-products-ai-observability-skills-exploring-llm-traces-skill-md
name: "exploring-llm-traces"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/products/ai_observability/skills/exploring-llm-traces"
skill_url: "https://skillsmp.com/creators/posthog/posthog/products-ai-observability-skills-exploring-llm-traces"
stars: 37496
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:09:04.185474"
---

# Résumé
ABSOLUTE MUST to debug and inspect LLM/AI agent traces using PostHog's MCP tools. Use when the user pastes a trace or session URL (e.g. /ai-observability/traces/<id> or /ai-observability/sessions/<id>), asks to debug a trace, figure out what went wrong, check if an agent used a tool correctly, verify context/files were surfaced, inspect subagent behavior, investigate LLM decisions, or analyze token usage and costs. Also use when raw SQL/HogQL against `events.properties.$ai_input` / `$ai_output_choices` returns empty — message content lives only on the dedicated `posthog.ai_events` table.

# Objectif
Skill d'automatisation/intégration pour exploring-llm-traces.

# Déclencheurs d’utilisation
Mots-clés associés: exploring-llm-traces, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/products/ai_observability/skills/exploring-llm-traces

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
