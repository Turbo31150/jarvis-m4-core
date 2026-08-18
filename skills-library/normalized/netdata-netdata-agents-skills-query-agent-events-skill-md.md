---
{
  "name": "query-agent-events",
  "source": "https://skillsmp.com/creators/netdata/netdata/agents-skills-query-agent-events",
  "repository": "https://github.com/netdata/netdata/tree/master/.agents/skills/query-agent-events",
  "author": "netdata",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:30:42+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "bf6eaf2840e5c3b770ea36b51374232cb6e277487a997a0cd8ca214c918bc2e9"
}
---

# Résumé
Bug-investigation tool for the Netdata agent-events ingestion namespace -- triage crashes, panics, fatals across the fleet by downloading events of interest and clustering locally. Covers the three transports (Cloud API and direct agent API are primary; ssh is operator-only), the verified AE_* field map and enum meanings, the dedup model (23h client-side per agent and event signature), the after-the-fact event timing (POST only on agent restart), and the Netdata systemd-journal plugin multi-value filter syntax (FIELD in A, B, C) AND ... Use when investigating crashes / panics / fatals; when grepping for events touching a specific function or file or version; when looking for regressions across versions; when an agent is reported crashing in a way you want to triage. Ships scripts get-events.sh and analyze-events.sh that fetch events with index-friendly filters and compute group-by stats. Defaults to last 24 hours and to the latest stable plus latest 2-3 nightlies.

# Source originale
- SkillsMP : https://skillsmp.com/creators/netdata/netdata/agents-skills-query-agent-events
- Dépôt    : https://github.com/netdata/netdata/tree/master/.agents/skills/query-agent-events

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
