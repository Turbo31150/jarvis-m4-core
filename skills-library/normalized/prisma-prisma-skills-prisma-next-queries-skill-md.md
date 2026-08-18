---
id: prisma-prisma-skills-prisma-next-queries-skill-md
name: "prisma-next-queries"
author: "prisma"
repository: "https://github.com/prisma/prisma/tree/main/skills/prisma-next-queries"
skill_url: "https://skillsmp.com/creators/prisma/prisma/skills-prisma-next-queries"
stars: 47525
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:09:04.184192"
---

# Résumé
Write Prisma Next queries for Postgres, SQLite, or Mongo — pick a lane (Postgres/SQLite `db.orm.<Model>` + `db.sql.<table>`; Mongo `db.orm.<root>` + `db.query.from(...)` pipeline builder), filter / project / sort / paginate, eager-load with `.include(...)`, Postgres/SQLite `db.transaction(...)`, Postgres/SQLite ORM `.aggregate(...)`, Mongo aggregations via query builder, namespace-aware accessors (`db.orm.<ns>.<Model>`, `db.sql.<ns>.<table>`). Triggers: query, where, match, select, project, orderBy, take, skip, include, lookup, first, all, count, aggregate, group, create, update, delete, upsert, returning, transaction, db.close, script teardown, variant, polymorphism, drizzle-style, kysely-style. Notes: `.all()` is a Thenable (just `await` it), iterators are single-use (`RUNTIME.ITERATOR_CONSUMED`), Postgres `count` is `number` while sum/avg/min/max are `number | null`, ranges use chained `.where()` or `and(...)` (no `.between(...)`).

# Objectif
Skill d'automatisation/intégration pour prisma-next-queries.

# Déclencheurs d’utilisation
Mots-clés associés: prisma-next-queries, prisma

# Procédure
Consulter le dépôt source: https://github.com/prisma/prisma/tree/main/skills/prisma-next-queries

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
