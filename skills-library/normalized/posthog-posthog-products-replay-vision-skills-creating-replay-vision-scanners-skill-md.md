---
{
  "name": "creating-replay-vision-scanners",
  "source": "https://skillsmp.com/creators/posthog/posthog/products-replay-vision-skills-creating-replay-vision-scanners",
  "repository": "https://github.com/PostHog/posthog/tree/master/products/replay_vision/skills/creating-replay-vision-scanners",
  "author": "PostHog",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:31:05+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "9ff66f1fafbef877303f8a9ff3bd236205c4756474559c2fdef35de1a541f815"
}
---

# Résumé
Guides agents through creating and safely sizing a Replay Vision scanner: choosing the scanner type (monitor/classifier/scorer/summarizer), shaping the RecordingsQuery that selects sessions, and — crucially — estimating observation volume and checking the org's monthly quota before creating, so a broad scanner doesn't exhaust the budget on its first scheduled sweep.
TRIGGER when: user asks to create, set up, or configure a Replay Vision scanner, OR when you are about to call vision-scanners-create, OR when widening an existing scanner's query or sampling_rate via vision-scanners-update.
DO NOT TRIGGER when: only reading scanners or observations, deleting a scanner, or running an existing scanner against a single session on demand (vision-scanners-scan-session). For a one-off question about sessions you already have, use vision-scanners-inline-scan-create rather than creating a scanner — the skill's first section covers when that applies.

# Source originale
- SkillsMP : https://skillsmp.com/creators/posthog/posthog/products-replay-vision-skills-creating-replay-vision-scanners
- Dépôt    : https://github.com/PostHog/posthog/tree/master/products/replay_vision/skills/creating-replay-vision-scanners

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
