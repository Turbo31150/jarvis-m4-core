---
{
  "name": "copilot-pr-autopilot",
  "source": "https://skillsmp.com/creators/github/awesome-copilot/skills-copilot-pr-autopilot",
  "repository": "https://github.com/github/awesome-copilot/tree/main/skills/copilot-pr-autopilot",
  "author": "github",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:31:03+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "579ef5e4e22bfb2771d923277dfdbe1f8647d6f7866d678146dfbb8d58675ab1"
}
---

# Résumé
Copilot left 14 review comments on your PR — half are nits. Hours of fix → reply → resolve → re-request, and each round lands MORE comments. This skill runs loop engineering: auto-triggers Copilot Code Review via GraphQL (no @copilot mention), triages every open thread (Copilot, humans, advanced-security) with a fix / decline / escalate rubric, dispatches parallel fix sub-agents that obey the repo build/test/lint conventions, commits per iteration, replies+resolves citing the pushed SHA, then re-triggers until HEAD is reviewed with zero threads awaiting the agent's reply (remaining open threads are explicit hand-offs to the human — escalated declines, design tradeoffs). You merge a clean PR; the bot runs it. Trigger phrases: "address copilot comments", "run a copilot review loop", "fix this PR", "iterate on copilot feedback". Repo-agnostic, gh CLI + PowerShell. Full autopilot needs repo Triage/Write; external PR authors get single-iteration mode plus manual re-trigger (UI 🔄 or substantive-commit push).

# Source originale
- SkillsMP : https://skillsmp.com/creators/github/awesome-copilot/skills-copilot-pr-autopilot
- Dépôt    : https://github.com/github/awesome-copilot/tree/main/skills/copilot-pr-autopilot

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
