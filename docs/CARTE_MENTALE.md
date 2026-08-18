# 🧠 CARTE MENTALE — Système JARVIS (M1) — scan 2026-07-16

```
JARVIS (M1)
│
├─ 🗄️ DONNÉES (36 bases SQLite)
│   ├─ jarvis_master.db ....... 172M · 37 tables (task_queue, tool_map, cascade)
│   ├─ jarvis-cowork/etoile.db  388M · hub intelligence
│   ├─ .n8n/database.sqlite .... 99M · 95 tables (workflows)
│   ├─ jarvis_rag.db/chroma .... 40M · embeddings RAG
│   └─ cowork_engine · secrets · web_archive · trading_v9 · passcerfa…
│
├─ 🧰 ARSENAL DÉTECTABLE (≈ 19 670, routage mots-clés 0-token)
│   ├─ Blocs bibliothèque ...... 18 497   → bloc.sh <kw>
│   ├─ Skills Claude ........... 407      → hook + Skill
│   ├─ Agents ................. 246      → agent-tools
│   ├─ Slash commands ......... 113      → /…
│   ├─ Séries d'action ........ 86       → lib.sh run
│   └─ Scripts ~/jarvis ....... 321      → catalog-all
│
├─ 📝 PROMPTS (694 prompts · 50 catégories · 740 fichiers)
│   └─ claude-code 183 · multi-ia 32 · gemini-cli 31 · models-locaux 31 · codex 29…
│
├─ ⏰ AUTOMATISATION (agents planifiés, backend gratuit)
│   ├─ Cron ................... 56 jobs (health, biblio, backup, mail, pinecone…)
│   ├─ Timers systemd ........ 21 (task-auto, autoheal, lms-keepwarm, backup-hourly…)
│   ├─ task_queue ............ jarvis task add → auto-exec 3/cycle (10min)
│   └─ Domino ................ séries self-healing (watchdog, prospection) + incident-responder
│
├─ 🤖 LLM / INFÉRENCE (hub 0-token)
│   ├─ chat_proxy.js :18800 ... cascade failover (OpenAI/Ollama compat)
│   ├─ LM Studio M1 :1234 ..... qwen3.5-9b · gpt-oss-20b · nomic-embed
│   ├─ Ollama local :11434 .... gemma3:4b · gpt-oss:20b-cloud (gratuit)
│   └─ Cluster : M1=OK · OL1=OK · M2=DOWN · M5=DOWN
│
├─ 🎙️ VOIX
│   ├─ jarvis-lumen :?? ....... STT/TTS/LLM routing (actif)
│   ├─ whisper-api :9743 ...... STT OpenAI-compat (actif)
│   └─ jarvis-whisper :8789 ... ⛔ COUPÉ (boucle STT garbled neutralisée)
│
├─ 🐳 INFRA (25 containers · 5 GPU)
│   ├─ jv-<dept>-<unité> ...... entreprise 7 dépts
│   ├─ n8n · postgres biblio (jv-infra-pg-biblio) · redis
│   └─ browseros :9108/9201 (MCP)
│
└─ 🌐 SORTIES / BUSINESS
    ├─ Mirra (IG/Threads/TikTok/YouTube) · LinkedIn CDP
    ├─ Netlify (6 sites commerciaux) · Gumroad (9 produits)
    └─ PassCerfa+ATSD · CRM prospection (952 entreprises)
```

## État live (scan)
| Métrique | Valeur |
|---|---|
| Services jarvis (system/user) | 16 / 13 running |
| Timers / Cron | 21 / 56 |
| Containers Docker | 25 |
| GPU | 5 (GPU2 ventilo HS → exclu LLM) |
| Tâches en file | 50 pending |
| Cluster | M1✅ OL1✅ M2❌ M5❌ |

## Points d'attention
- ⚠️ 6 zombies détectés au boot · jarvis-openclaw FAIL loop (02:40→02:58)
- ⚠️ Timeshift : dernier snapshot 22j (>7j → snapshot conseillé)
- ⚠️ 50 tâches pending (le timer les vide 3/cycle = ~3h pour tout écouler)
