---
{
  "name": "teammode",
  "source": "https://skillsmp.com/creators/code-yeongyu/oh-my-openagent/packages-omo-codex-plugin-components-teammode-skills-teammode",
  "repository": "https://github.com/code-yeongyu/oh-my-openagent/tree/dev/packages/omo-codex/plugin/components/teammode/skills/teammode",
  "author": "code-yeongyu",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:30:47+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "5a404b0b60816f18885b9e01a864198ce5fe0f72350f7112100c8253d4adaf1a"
}
---

# Résumé
Codex-only team orchestration: run a named team of cooperating Codex workers with durable, script-managed state. MUST USE when the user asks Codex to create, run, coordinate, inspect, archive, or delete a team of agents/threads/sessions, or to work on something as a team in parallel. FIRST inspects the active tool surface (checking tool_search for deferred tools) and tells the user the route: native MultiAgentV2 agents (flat spawn_agent with task_name) when available, Codex App threads as the fallback, or a plain-subagent split when neither set exists. The main session is always the leader; members are defined by a concrete part, ownership area, or perspective - never a vague job role; a bundled cross-platform script writes the .omo/teams state plus an auto-generated member field manual. Use a team when the work is not perfectly isolated but parallelizing helps; use plain subagents when scope is perfectly isolated or the goal is ambiguous. Triggers: team mode, teammode, make a team, run as a team, team of age

# Source originale
- SkillsMP : https://skillsmp.com/creators/code-yeongyu/oh-my-openagent/packages-omo-codex-plugin-components-teammode-skills-teammode
- Dépôt    : https://github.com/code-yeongyu/oh-my-openagent/tree/dev/packages/omo-codex/plugin/components/teammode/skills/teammode

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
