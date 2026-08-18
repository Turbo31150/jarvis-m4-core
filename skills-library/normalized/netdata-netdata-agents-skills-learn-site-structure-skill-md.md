---
id: netdata-netdata-agents-skills-learn-site-structure-skill-md
name: "learn-site-structure"
author: "netdata"
repository: "https://github.com/netdata/netdata/tree/master/.agents/skills/learn-site-structure"
skill_url: "https://skillsmp.com/creators/netdata/netdata/agents-skills-learn-site-structure"
stars: 80011
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:09:10.074519"
---

# Résumé
Authoritative reference for how docs in this repo (and 5 other Netdata-org repos) become published pages on `learn.netdata.cloud`. Covers the `<repo>/docs/.map/map.yaml` source-of-truth (the actual lever -- filesystem path is irrelevant for routing), the live `ingest/ingest.py` orchestrator in the learn repo (NOT the legacy `ingest.js`), frontmatter injection, slug rules, sidebar autogeneration, MDX escape rules, versioning, the 4-mechanism redirect stack, the 6 source repositories, the every-3-hours CI ingest, Netlify deploy, and the `part_of_learn=True` opt-in for files hand-authored in the learn repo. Use when adding/moving/renaming/deleting a docs page; when a page on Learn looks wrong; when wondering whether to edit a doc here or in the learn repo; when reading `ingest.py`, `sidebars.js`, `docusaurus.config.js`, `static.toml`, `LegacyLearnCorrelateLinksWithGHURLs.json`, `netlify.toml`, the `<!--startmeta` blocks in `.mdx` files, or the workflows `ingest.yml` and `daily-learn-link-check.yml`.

# Objectif
Skill d'automatisation/intégration pour learn-site-structure.

# Déclencheurs d’utilisation
Mots-clés associés: learn-site-structure, netdata

# Procédure
Consulter le dépôt source: https://github.com/netdata/netdata/tree/master/.agents/skills/learn-site-structure

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
