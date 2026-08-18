---
{
  "name": "a2ui-renderer",
  "source": "https://skillsmp.com/creators/copilotkit/copilotkit/packages-a2ui-renderer-skills-a2ui-renderer",
  "repository": "https://github.com/CopilotKit/CopilotKit/tree/main/packages/a2ui-renderer/skills/a2ui-renderer",
  "author": "CopilotKit",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:31:05+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "a6d33bdab9dc62b96b51e8b368269728f4a0b6d313a2e7b2d04876f9e301b138"
}
---

# Résumé
Render A2UI (Agent-to-UI declarative surfaces) in CopilotKit v2. Enable the runtime via CopilotRuntime({ a2ui: {...} }), then enable the provider via <CopilotKit a2ui={{ theme }}>. Auto-activates via /info — do NOT manually pass renderActivityMessages. createA2UIMessageRenderer ships from @copilotkit/react-core/v2; low-level primitives (A2UIProvider, A2UIRenderer, createCatalog) ship from @copilotkit/a2ui-renderer. Covers theme customization, createSurface dedup, action-bridge try/finally cleanup. Load when an agent emits A2UI operations (createSurface / updateComponents / updateDataModel), when wiring a2ui on CopilotRuntime, or when styling A2UI surfaces.

# Source originale
- SkillsMP : https://skillsmp.com/creators/copilotkit/copilotkit/packages-a2ui-renderer-skills-a2ui-renderer
- Dépôt    : https://github.com/CopilotKit/CopilotKit/tree/main/packages/a2ui-renderer/skills/a2ui-renderer

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
