---
id: posthog-posthog-products-data-modeling-skills-modeling-warehouse-foundations-skill-md
name: "modeling-warehouse-foundations"
author: "PostHog"
repository: "https://github.com/PostHog/posthog/tree/master/products/data_modeling/skills/modeling-warehouse-foundations"
skill_url: "https://skillsmp.com/creators/posthog/posthog/products-data-modeling-skills-modeling-warehouse-foundations"
stars: 37496
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:35.864698"
---

# Résumé
Shared foundations for building reusable data models in PostHog, on either of two stacks: PostHog-native data-warehouse views / materialized views (HogQL, via the view-* MCP tools), or an external dbt project (sources.yml + staging/marts + schema tests) run against your own or PostHog's managed warehouse. Read before authoring any specific business model — covers the PostHog-vs-dbt decision, the view-create → view-materialize → sync_frequency workflow and the HogQL column-aliasing rule, the dbt project skeleton and the honest "no native dbt integration" picture, warehouse joins and star-schema dimensions, currency conversion with convertCurrency(), and checking/registering models in the data catalog for reuse. Companion to the domain skills modeling-revenue-metrics, modeling-conversion-metrics, modeling-activation-metrics, modeling-product-usage-metrics, and modeling-dimension-tables. Use when the user asks how to build a view, materialized view, or dbt model in PostHog, or which of the two stacks to use.

# Objectif
Skill d'automatisation/intégration pour modeling-warehouse-foundations.

# Déclencheurs d’utilisation
Mots-clés associés: modeling-warehouse-foundations, PostHog

# Procédure
Consulter le dépôt source: https://github.com/PostHog/posthog/tree/master/products/data_modeling/skills/modeling-warehouse-foundations

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
