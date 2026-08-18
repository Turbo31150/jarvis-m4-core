---
id: ruvnet-ruflo-plugins-ruflo-business-pods-skills-pod-sales-skill-md
name: "pod-sales"
author: "ruvnet"
repository: "https://github.com/ruvnet/ruflo/tree/main/plugins/ruflo-business-pods/skills/pod-sales"
skill_url: "https://skillsmp.com/creators/ruvnet/ruflo/plugins-ruflo-business-pods-skills-pod-sales"
stars: 66991
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:09:04.184074"
---

# Résumé
Run one tick of the sales business-pod (ADR-164 §4.1, Phase 2). Loads templates/sales.json, validates it against the pod-schema, resolves agents against ruflo's agent registry, reserves budget via the Phase-2 file-based stub ledger (atomic SQLite tracker is Phase 3 per ADR-164.1), constructs per-agent dry-run prompts, posts a summary envelope to room "sales" via the federation_bbs_publish JSONL backing store, and emits a structured {podName, tickId, agentsRan, totalUsd, envelopeId, status} line for /loop ingestion. Dry-run by default; --live is reserved for Phase 3.

# Objectif
Skill d'automatisation/intégration pour pod-sales.

# Déclencheurs d’utilisation
Mots-clés associés: pod-sales, ruvnet

# Procédure
Consulter le dépôt source: https://github.com/ruvnet/ruflo/tree/main/plugins/ruflo-business-pods/skills/pod-sales

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
