---
id: rikkahub-rikkahub-agents-skills-claude-api-skill-md
name: "claude-api"
author: "rikkahub"
repository: "https://github.com/rikkahub/rikkahub/tree/master/.agents/skills/claude-api"
skill_url: "https://skillsmp.com/creators/rikkahub/rikkahub/agents-skills-claude-api"
stars: 6621
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:13.169463"
---

# Résumé
Reference for the Claude API / Anthropic SDK — model ids, pricing, params, streaming, tool use, MCP, agents, caching, token counting, model migration.
TRIGGER — read BEFORE opening the target file; don't skip because it "looks like a one-liner" — whenever: the prompt names Claude/Anthropic in any form (Claude, Anthropic, Fable, Opus, Sonnet, Haiku, `anthropic`, `@anthropic-ai`, `claude-*`, `us.anthropic.*`, `[1m]`); the user asks about an LLM (pricing/model choice/limits/caching) — never answer from memory; OR the task is LLM-shaped with provider unstated (agent/MCP/tool-definition/multi-agent/RAG/LLM-judge/computer-use; generate/summarize/extract/classify/rewrite/converse over NL; debugging refusals/cutoffs/streaming/tool-calls/tokens).
SKIP only when another provider is being worked on (overrides all triggers): OpenAI/GPT/Gemini/Llama/Mistral/Cohere/Ollama named in the query; OR `grep -rE 'openai|langchain_openai|google.generativeai|genai|mistralai|cohere|ollama'` over the project hits (run this grep FIRST 

# Objectif
Skill d'automatisation/intégration pour claude-api.

# Déclencheurs d’utilisation
Mots-clés associés: claude-api, rikkahub

# Procédure
Consulter le dépôt source: https://github.com/rikkahub/rikkahub/tree/master/.agents/skills/claude-api

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
