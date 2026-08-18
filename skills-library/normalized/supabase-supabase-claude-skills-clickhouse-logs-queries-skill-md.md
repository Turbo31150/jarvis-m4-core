---
id: supabase-supabase-claude-skills-clickhouse-logs-queries-skill-md
name: "clickhouse-logs-queries"
author: "supabase"
repository: "https://github.com/supabase/supabase/tree/master/.claude/skills/clickhouse-logs-queries"
skill_url: "https://skillsmp.com/creators/supabase/supabase/claude-skills-clickhouse-logs-queries"
stars: 107554
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:09:04.183298"
---

# Résumé
Write, review, and migrate Supabase logs queries against the ClickHouse-backed `logs` table (the `logs.all.otel` analytics endpoint). Use this whenever a task involves Logs Explorer SQL, the `log_attributes` map, querying a log `source` (edge_logs, postgres_logs, auth_logs, etc.), translating an old BigQuery `cross join unnest(metadata)` logs query to ClickHouse, or wiring analytics log SQL in `apps/studio/data/logs` and `apps/studio/components/interfaces/Settings/Logs`. Reach for it even when the user just says "logs query", "Logs Explorer", or pastes a BigQuery logs query to convert, not only when they name ClickHouse.

# Objectif
Skill d'automatisation/intégration pour clickhouse-logs-queries.

# Déclencheurs d’utilisation
Mots-clés associés: clickhouse-logs-queries, supabase

# Procédure
Consulter le dépôt source: https://github.com/supabase/supabase/tree/master/.claude/skills/clickhouse-logs-queries

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
