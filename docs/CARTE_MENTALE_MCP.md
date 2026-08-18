# 🧠 Carte mentale MCP — écosystème JARVIS (2026-07-16)

Serveurs MCP réellement connectés à la session (la liste `.claude.json` locale n'en déclare que 4 ; les autres viennent des plugins/config projet).

```mermaid
mindmap
  root((MCP JARVIS))
    Cluster LLM / Agents<br/>0-token
      jarvis-agents<br/>lm_ask · gemini_ask · claude_code · invoke_agent · list_agents
      jarvis-cluster<br/>query_model · list_models · health_check_all
      jarvis-linux-m1<br/>lm_chat · lm_models
      jarvis-ol1 / jarvis-linux-ol1<br/>Ollama run/chat/pull
      antigravity + antigravity-bridge<br/>IDE agent Google
      ia-web-jarvis<br/>ChatGPT/Gemini/Perplexity via navigateur
    Mémoire / Données
      jarvis-memory<br/>save · search · list
      jarvis-sql-bridge
      jarvis-linux-sqlite<br/>read/write_query · describe_table
      filesystem / jarvis-linux-fs<br/>read · write · edit · search
      pinecone<br/>index · search-records · rerank
    Web / Navigateur / API
      browseros<br/>66 outils navigateur :9201
      chrome-devtools<br/>CDP click/fill/trace/lighthouse
      claude-in-chrome<br/>navigate · computer · gif_creator
      requestly-jarvis<br/>collections · requests · waypoints · import_postman
      notebooklm-bridge<br/>query · automate
    Social / Contenu
      mirra + local-mirra<br/>IG/Threads/TikTok/YouTube · carousel · shorts · blog
      canva<br/>generate-design · export · brand-kit
    Déploiement
      netlify<br/>deploy · project/team readers
      vercel<br/>deploy_to_vercel · logs · runtime
    Connecteurs claude.ai
      Gmail · Calendar · Drive
      Microsoft 365 · Notion
      Hugging Face · Intercom · Jam · Plaid
    Docs
      microsoft-docs<br/>learn search · code-sample · fetch
```

## Lecture rapide par usage (LOI #2 — déléguer 0-token)
| Besoin | Serveur MCP prioritaire |
|---|---|
| Inférence LLM locale gratuite | `jarvis-agents.lm_ask` / `jarvis-cluster.query_model` / `jarvis-linux-m1.lm_chat` |
| Mémoire persistante | `jarvis-memory` |
| Requête SQL | `jarvis-linux-sqlite` / `jarvis-sql-bridge` |
| Test/rejouer une API HTTP | **`requestly-jarvis`** (collections, waypoints, import Postman) |
| Navigateur/scrape/formulaire | `browseros` (:9201) → `chrome-devtools` → `claude-in-chrome` |
| Publication sociale | `mirra` (+ LinkedIn via CDP hors OAuth) |
| Déploiement site | `netlify` / `vercel` |
| Recherche vectorielle | `pinecone` |

> **requestly-jarvis** = banc d'essai HTTP : `add_collection` → `add_request` → `execute_request` / `execute_waypoint`, import Postman. Idéal pour valider/rejouer les endpoints du hub :18800, du cluster LLM, ou des webhooks n8n de façon reproductible.
