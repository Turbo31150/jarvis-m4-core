---
id: supabase-supabase-claude-skills-safe-sql-execution-skill-md
name: "safe-sql-execution"
author: "supabase"
repository: "https://github.com/supabase/supabase/tree/master/.claude/skills/safe-sql-execution"
skill_url: "https://skillsmp.com/creators/supabase/supabase/claude-skills-safe-sql-execution"
stars: 107554
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:09:04.183170"
---

# Résumé
Use whenever code will build, return, fetch, or execute SQL that runs against a user's real Postgres database — even when the request reads like an ordinary feature or bug fix and never says "security," "injection," or "SafeSqlFragment." This covers: writing or editing any pg-meta function, query builder, or endpoint that builds/returns SQL for database objects (tables, views, functions, DB triggers, indexes, RLS policies); interpolating a schema/table/column/search/route-param value into SQL text; storing, fetching, or re-running SQL that round-trips from the database (a policy's definition, a function/view definition, a snippet's saved content); and any "Run"/"Apply"/"Execute" action that sends SQL to a project's database (SQL editor run-selection, policy editor apply, snippet runner). Load this BEFORE writing such code, not only when reviewing a finished diff. Skip only for changes that never touch SQL text or execution — styling, unrelated data hooks, non-SQL form validation, or UI layout work.

# Objectif
Skill d'automatisation/intégration pour safe-sql-execution.

# Déclencheurs d’utilisation
Mots-clés associés: safe-sql-execution, supabase

# Procédure
Consulter le dépôt source: https://github.com/supabase/supabase/tree/master/.claude/skills/safe-sql-execution

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
