---
id: posthog-posthog-agents-skills-generating-clickhouse-query-performance-reports-skill-md
name: "generating-clickhouse-query-performance-reports"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/.agents/skills/generating-clickhouse-query-performance-reports"
skill_url: "https://skillsmp.com/creators/posthog/posthog/agents-skills-generating-clickhouse-query-performance-reports"
stars: 37496
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:23.404067"
---

# Résumé
Produce and structure slow-query performance reports for PostHog's production ClickHouse (US and EU). Use when asked for a slow query report, query performance analysis over the last N days, per-team query cost, OOM or timeout investigation, cluster cost/memory regressions, or materialization candidates. Covers the modern `query_log_archive` source (typed `lc_*` columns, multi-day retention), how to categorize and attribute slow queries, root-cause patterns (unmaterialized JSONExtract, high-cardinality breakdowns, heavy joins), and the report structure. Runs queries via the `query-clickhouse-via-metabase` skill.

# Objectif
Skill d'automatisation/intégration pour generating-clickhouse-query-performance-reports.

# Déclencheurs d’utilisation
Mots-clés associés: generating-clickhouse-query-performance-reports, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/.agents/skills/generating-clickhouse-query-performance-reports

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
