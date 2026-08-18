---
id: posthog-posthog-agents-skills-optimizing-clickhouse-and-hogql-queries-skill-md
name: "optimizing-clickhouse-and-hogql-queries"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/.agents/skills/optimizing-clickhouse-and-hogql-queries"
skill_url: "https://skillsmp.com/creators/posthog/posthog/agents-skills-optimizing-clickhouse-and-hogql-queries"
stars: 37496
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:09:04.185297"
---

# Résumé
Workflow for optimizing ClickHouse and HogQL queries. Use when a HogQL query, query runner, insight, or report is too slow; when a hand-written ClickHouse query (via `sync_execute` or in a migration) is too slow; when ClickHouse times out or hits memory limits; when investigating a slow `system.query_log` row; or when reviewing a proposed HogQL printer change for performance. Covers extracting the ClickHouse SQL, common smells (`FROM ... FINAL`, `JSONExtract` over properties, missing skip indexes, self-joins, CTE blow-up), measuring against a real cluster, and applying the fix at the right layer (printer, query runner, or migration). Does NOT cover Postgres / Django ORM / app-database queries; those need pganalyze and the Postgres section of `query-performance-optimization.md`.

# Objectif
Skill d'automatisation/intégration pour optimizing-clickhouse-and-hogql-queries.

# Déclencheurs d’utilisation
Mots-clés associés: optimizing-clickhouse-and-hogql-queries, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/.agents/skills/optimizing-clickhouse-and-hogql-queries

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
