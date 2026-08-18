---
{
  "name": "scanning-experiments-with-replay-vision",
  "source": "https://skillsmp.com/creators/posthog/posthog/products-experiments-skills-scanning-experiments-with-replay-vision",
  "repository": "https://github.com/PostHog/posthog/tree/master/products/experiments/skills/scanning-experiments-with-replay-vision",
  "author": "PostHog",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:11+00:00",
  "verified": false,
  "quality_score": 89,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "599f2ef99414cdeedda7af5a3b7796f3dc744d5362dd7f5e7c0d04b3f2b3e17b"
}
---

# Résumé
Provisions a Replay Vision scanner scoped to one experiment's exposed sessions: derives the recordings filter from the experiment's exposure criteria (with session-linkability checks and honest fallbacks), templates a prompt that stays comparable across variants, sizes credit spend against the experiment's own population, and creates the scanner disabled so its prompt can be previewed on real sessions before it sweeps.
TRIGGER when: user wants Replay Vision to watch an experiment, asks to scan or analyze an experiment's recordings with AI, asks "what are users actually doing in the test variant", or wants a scanner scoped to an experiment's exposed sessions.
DO NOT TRIGGER when: creating a general-purpose scanner not tied to an experiment (use creating-replay-vision-scanners), reading observations a scanner already produced (use exploring-replay-vision-observations), or manually browsing an experiment's recordings without AI analysis (use analyzing-experiment-session-replays).

# Source originale
- SkillsMP : https://skillsmp.com/creators/posthog/posthog/products-experiments-skills-scanning-experiments-with-replay-vision
- Dépôt    : https://github.com/PostHog/posthog/tree/master/products/experiments/skills/scanning-experiments-with-replay-vision

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
