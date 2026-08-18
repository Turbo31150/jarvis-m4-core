---
{
  "name": "pr-quiz",
  "source": "https://skillsmp.com/creators/stirling-tools/stirling-pdf/claude-skills-pr-quiz",
  "repository": "https://github.com/Stirling-Tools/Stirling-PDF/tree/main/.claude/skills/pr-quiz",
  "author": "Stirling-Tools",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:27:56+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "7ca570b22a0ee1a33651dd0a4dfefef6724409888f196bd4b583776a49822af0"
}
---

# Résumé
Quiz the PR author on their own branch before they request review, to prove they actually understand the change - especially code an AI wrote for them. Scopes the branch diff vs its base, reads the changed code, then asks graded questions about what changed, why, how it works, what it could break, and which edge cases it must handle. Presents all questions first, waits for the author's answers, then grades each honestly against the real code (Correct / Partial / Incorrect with the true answer and file:line), scores it, and gives a readiness verdict that names the areas to re-study before asking humans to review. Use when asked to quiz me on my PR/branch, "test my understanding before review", a self-check gate before opening a PR, or before requesting reviewers. Administered as an interactive multiple-choice quiz (clickable options) by default; pass --free-text for written answers, --questions N to set count, --save to write a scorecard.

# Source originale
- SkillsMP : https://skillsmp.com/creators/stirling-tools/stirling-pdf/claude-skills-pr-quiz
- Dépôt    : https://github.com/Stirling-Tools/Stirling-PDF/tree/main/.claude/skills/pr-quiz

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
