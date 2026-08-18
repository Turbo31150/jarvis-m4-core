---
{
  "name": "find-regression-risk",
  "source": "https://skillsmp.com/creators/dotnet/maui/github-skills-find-regression-risk",
  "repository": "https://github.com/dotnet/maui/tree/main/.github/skills/find-regression-risk",
  "author": "dotnet",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:37+00:00",
  "verified": false,
  "quality_score": 89,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "14ec96762b9a0e57c4268cfc466945779ab9075d66045c140933864dbdaef47e"
}
---

# Résumé
Detects potential regression risks in a PR by cross-referencing lines the PR REMOVES against lines ADDED by recent labeled bug-fix PRs (`i/regression`, `t/bug`, `p/0`, `p/1`) touching the same files. Purely mechanical — no AI/LLM. Emits a CLEAN / OVERLAP / REVERT verdict plus structured findings. Triggers on: "does this PR revert a previous fix", "check PR for regression risk", "find regression risks in PR", "is this change reverting a bug fix". Do NOT use for: assessing ship-readiness of a release branch (use release-readiness), investigating CI failures (use azdo-build-investigator), or general code review (use code-review).

# Source originale
- SkillsMP : https://skillsmp.com/creators/dotnet/maui/github-skills-find-regression-risk
- Dépôt    : https://github.com/dotnet/maui/tree/main/.github/skills/find-regression-risk

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
