---
{
  "name": "n8n-code-tool",
  "source": "https://skillsmp.com/creators/czlonkowski/n8n-mcp/data-skills-n8n-code-tool",
  "repository": "https://github.com/czlonkowski/n8n-mcp/tree/main/data/skills/n8n-code-tool",
  "author": "czlonkowski",
  "category": null,
  "tags": [],
  "license": null,
  "collected_at": "2026-08-08T00:28:37+00:00",
  "verified": false,
  "quality_score": 95,
  "security_status": "REVIEW_REQUIRED",
  "security_reasons": [],
  "sha256": "20dd8013dee9a83af7187f297a612f30c07fcdf84c26baf8965e223d26ca7063"
}
---

# Résumé
Write JavaScript or Python for the n8n Custom Code Tool (@n8n/n8n-nodes-langchain.toolCode) — the AI-agent-callable tool, NOT the workflow Code node. Use when building a Code Tool attached to an AI Agent, writing code that an LLM will invoke, parsing the `query` input, returning a string result, defining an input schema for structured arguments (specifyInputSchema, jsonSchemaExample, DynamicStructuredTool), or troubleshooting errors like "Wrong output type returned", "No execution data available", "The response property should be a string, but it is an object", "Cannot assign to read only property 'name'", or an AI agent that refuses to call the tool. Covers the critical differences between Code node and Code Tool: return format (string vs `[{json:{...}}]`), unavailability of `$fromAI`/`$input`/`$helpers` in the Code Tool sandbox, naming rules for AI invocation, and when to use `toolWorkflow`/HTTP Request Tool instead.

# Source originale
- SkillsMP : https://skillsmp.com/creators/czlonkowski/n8n-mcp/data-skills-n8n-code-tool
- Dépôt    : https://github.com/czlonkowski/n8n-mcp/tree/main/data/skills/n8n-code-tool

# Statut
Métadonnées API uniquement — contenu SKILL.md non récupéré, donc NON vérifié.
Aucune exécution. L'installation exige une revue séparée.
