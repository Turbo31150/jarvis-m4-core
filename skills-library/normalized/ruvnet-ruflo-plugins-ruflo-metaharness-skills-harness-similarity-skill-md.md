---
{
  "name": "harness-similarity",
  "source": "https://skillsmp.com/creators/ruvnet/ruflo/plugins-ruflo-metaharness-skills-harness-similarity",
  "repository": "https://github.com/ruvnet/ruflo/tree/main/plugins/ruflo-metaharness/skills/harness-similarity",
  "author": "ruvnet",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:30:54+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "6d4f5da9ab0c2e58dfddf13899675290bff173eb1bc776af50e984944a618418"
}
---

# Résumé
ADR-152 — weighted similarity between two harness fingerprints (genome + score JSON). Returns overall score in [0,1] plus per-component breakdown (cosine over 9 numerics, categorical agreement over 4 enums, jaccard over agent_topology). Unblocks ADR-151 §3.2 Recommender, §3.3 Drift Detection, §3.5 Plugin Compat. Pure-TS, no `@metaharness/*` dep — preserves ADR-150's four architectural constraints.

# Source originale
- SkillsMP : https://skillsmp.com/creators/ruvnet/ruflo/plugins-ruflo-metaharness-skills-harness-similarity
- Dépôt    : https://github.com/ruvnet/ruflo/tree/main/plugins/ruflo-metaharness/skills/harness-similarity

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
