---
{
  "name": "mirror-netdata-repos",
  "source": "https://skillsmp.com/creators/netdata/netdata/agents-skills-mirror-netdata-repos",
  "repository": "https://github.com/netdata/netdata/tree/master/.agents/skills/mirror-netdata-repos",
  "author": "netdata",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:01+00:00",
  "verified": false,
  "quality_score": 89,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "d75fb00abe27c827397023150d1d75f31e99d9667186b2fd4bec38580197badc"
}
---

# Résumé
Maintains a local mirror of Netdata-org source repositories at `${NETDATA_REPOS_DIR}` so AI assistants and developers can do cross-repo grep / code review locally without GitHub API round-trips and rate limits. Ships a vendored sync script (`scripts/sync-netdata-repos.sh`) that updates ~150 repos in two phases (resync existing on default branch, discover and clone new). Safety -- skips repos that have staged or modified changes; otherwise switches to the default branch and recursively updates submodules. Reset-to-default is intentional -- it prevents stale-feature-branch "black hole" repos that confuse cross-repo reasoning. Supports `--repo NAME` (repeatable) to scope to specific repos. Independent from any other repo mirrors this workstation may have. Use when the local mirror is out of date, before a cross-repo grep / review session, when adding a new netdata-org repo (auto-discovered), when an assistant needs cross-repo cognition without `gh` API turnaround.

# Source originale
- SkillsMP : https://skillsmp.com/creators/netdata/netdata/agents-skills-mirror-netdata-repos
- Dépôt    : https://github.com/netdata/netdata/tree/master/.agents/skills/mirror-netdata-repos

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
