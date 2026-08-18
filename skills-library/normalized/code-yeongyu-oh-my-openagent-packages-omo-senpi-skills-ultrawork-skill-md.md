---
{
  "name": "ultrawork",
  "source": "https://skillsmp.com/creators/code-yeongyu/oh-my-openagent/packages-omo-senpi-skills-ultrawork",
  "repository": "https://github.com/code-yeongyu/oh-my-openagent/tree/dev/packages/omo-senpi/skills/ultrawork",
  "author": "code-yeongyu",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:30:47+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "b8dd2bdaa60f656ac214390e4ac9de7d9ea17f2742bee73b07baeaa9434d199c"
}
---

# Résumé
Binding ultrawork mode directive for omo-senpi. When a prompt contains ultrawork or ulw, the omo input hook injects the full directive as a hidden custom message (customType omo-ultrawork:directive, display false) ahead of the user's text, which is left untouched; a prompt queued while the agent is streaming instead carries the directive appended inside that same message. The directive is present in the conversation context; on the idle path it is not shown in the visible prompt, while a queued prompt carries the directive visibly (exactly as before this change). When the directive is already present in the conversation, do not read this file again - this file is that same directive. Read this file only when ultrawork mode is requested and the directive is not already present in the conversation.

# Source originale
- SkillsMP : https://skillsmp.com/creators/code-yeongyu/oh-my-openagent/packages-omo-senpi-skills-ultrawork
- Dépôt    : https://github.com/code-yeongyu/oh-my-openagent/tree/dev/packages/omo-senpi/skills/ultrawork

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
