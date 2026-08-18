---
id: intuitem-ciso-assistant-community-claude-skills-mapping-builder-skill-md
name: "mapping-builder"
author: "intuitem"
repository: "https://github.com/intuitem/ciso-assistant-community/tree/main/.claude/skills/mapping-builder"
skill_url: "https://skillsmp.com/creators/intuitem/ciso-assistant-community/claude-skills-mapping-builder"
stars: 4306
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:15.179916"
---

# Résumé
Build a reviewed crosswalk (RequirementMappingSet YAML library + review xlsx/csv) between two CISO Assistant framework YAML files using Claude itself as the reasoning engine. Zero infrastructure — stdlib + pyyaml only, no embedders, no LM Studio, no Qdrant. Use when the user asks to map / crosswalk / generate a mapping between two frameworks (e.g. ccb-cff-2023-03-01.yaml ↔ cyfun2025.yaml), wants to contribute a community mapping to backend/library/libraries/, or says things like "build a mapping between framework X and Y", "create a crosswalk YAML", "generate requirement_mapping_set". Output matches the schema in backend/library/libraries/mapping-*.yaml exactly so the result is PR-able.

# Objectif
Skill d'automatisation/intégration pour mapping-builder.

# Déclencheurs d’utilisation
Mots-clés associés: mapping-builder, intuitem

# Procédure
Consulter le dépôt source: https://github.com/intuitem/ciso-assistant-community/tree/main/.claude/skills/mapping-builder

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
