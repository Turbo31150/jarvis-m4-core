---
id: netdata-netdata-agents-skills-codacy-audit-skill-md
name: "codacy-audit"
author: "netdata"
repository: "https://github.com/netdata/netdata/tree/master/.agents/skills/codacy-audit"
skill_url: "https://skillsmp.com/creators/netdata/netdata/agents-skills-codacy-audit"
stars: 80011
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:31.692705"
---

# Résumé
Codacy Cloud workflow for this repository -- run Codacy's analyzers locally before `git push` (mirrors what Codacy CI runs), and fetch/cluster Codacy issues for any PR via the v3 API. Use when the user mentions Codacy, "codacy analysis", `codacy-analysis-cli`, "codacy issues on PR", "fix codacy CI", "codacy markdownlint findings", or any Codacy gate failing on a netdata-org PR. Ships scripts analyze-local.sh (docker/binary runner for codacy-analysis-cli) and pr-issues.sh (paginated v3 issue fetch + group-by tool/pattern/severity/file). Token-safe -- CODACY_TOKEN never reaches assistant-visible stdout. Read-only by design; write actions (mark FP, mark fixed) require a GitHub issue or branch-local SOW.

# Objectif
Skill d'automatisation/intégration pour codacy-audit.

# Déclencheurs d’utilisation
Mots-clés associés: codacy-audit, netdata

# Procédure
Consulter le dépôt source: https://github.com/netdata/netdata/tree/master/.agents/skills/codacy-audit

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
