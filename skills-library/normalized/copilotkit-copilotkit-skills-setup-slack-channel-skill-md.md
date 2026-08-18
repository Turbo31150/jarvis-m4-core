---
{
  "name": "setup-slack-channel",
  "source": "https://skillsmp.com/creators/copilotkit/copilotkit/skills-setup-slack-channel",
  "repository": "https://github.com/CopilotKit/CopilotKit/tree/main/skills/setup-slack-channel",
  "author": "CopilotKit",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:31:05+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "da02ccb3d5ca126420ce908e30c450dc1ed38c9287f3ff3d7095ef009c7295eb"
}
---

# Résumé
Use for the PROVIDER half of getting a locally running CopilotKit Channels agent to answer in Slack, when no Slack app exists yet — setting up a Channels bot in Slack for the first time, creating the Slack app and its tokens, attaching it to a managed Intelligence Channel, or when a Channel reports setup_required, sits at "Waiting for runtime", the Channel is Online but a Slack mention gets no reply, or a Slack app was built with Socket Mode instead of an Intelligence Request URL. Scoped to an OpenTag checkout, or the OpenTag example inside a channels-sdk clone — the phases assume those conventions (app/channel.tsx, app/env.ts, INTELLIGENCE_CHANNEL_NAME, a local agent on port 8123) and do not describe a project scaffolded by copilotkit init, which already ships its own channel host. If the Slack app and Channel already exist and the question is about declaring or customising the Channel in code, use the copilotkit-channels skill instead.

# Source originale
- SkillsMP : https://skillsmp.com/creators/copilotkit/copilotkit/skills-setup-slack-channel
- Dépôt    : https://github.com/CopilotKit/CopilotKit/tree/main/skills/setup-slack-channel

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
