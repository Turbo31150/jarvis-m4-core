[user] Tu es l'agent WORKFLOWS-SOUVERAINS. Objectif : définir le PRODUIT « workflows 100 % locaux » d'AlkymIA — trier les workflows réels de Franck selon leur SOUVERAINETÉ (full-local vs hybride vs externe) et cadrer l'offre. Écris dans Notion. AUCUN fichier local. Lecture seule. Aucun secret. Rien publié.

DÉFINITION PRODUIT (donnée par Franck) : le produit vendable = chaque workflow qu'il a réellement utilisé, monté UNIQUEMENT avec ses propres outils (JARVIS OS : Ollama local, n8n self-hosted, board/RAG local, cascade 0-token, scripts locaux, coffre) — RIEN pris de l'extérieur, aucune API/SaaS tiers, aucune donnée qui sort. Un workflow FULL LOCAL / souverain.

SOURCES (Notion, lecture seule) : les pages Moisson workflows (« 🔧 Tous les workflows automatisés » 3bc7800a81d68128bc19f5c50c5b6955 ; « 🌾 Moisson M1 — Workflows réels » 3bc7800a81d6815ea477c0d4cf2064ad ; « ⚙️ Workflows n8n catalogue » ; « ⛓️ Dominos/atomes »). Récupère la liste réelle des workflows/dominos/séries.

TÂCHE — classe CHAQUE workflow en 3 catégories, HONNÊTEMENT :
- 🟢 **FULL LOCAL (souverain, vendable tel quel)** : n'utilise QUE des briques locales (Ollama/LM Studio local, n8n self-hosted en local, board, fichiers/SQLite locaux, cascade 0-token). Aucun appel réseau externe, aucune donnée qui sort. Ex probables : tri/résumé local, génération de contenu 0-token, RAG board, audit local, backup local, dominos d'orchestration locale.
- 🟠 **HYBRIDE (à rendre local avant de le vendre « souverain »)** : cœur local mais 

[assistant] The content is in nested blocks (tables/toggles). Let me fetch them recursively.

[assistant] I have the full inventory from both source pages. Now I'll create the Notion page under the hub and populate it.

[assistant] Terminé. Page créée, remplie et rattachée à l'index maître.

## Rapport

**Classement des workflows réels de Franck (sources : Moisson M4 « Tous les workflows » + Moisson M1 « Workflows réels ») :**
- 🟢 **FULL LOCAL : ~14 briques** (le cœur vendable)
- 🟠 **HYBRIDE : ~10 workflows** (rendables 100 % locaux)
- 🔴 **EXTERNE : ~7 blocs** (à écarter de l'argument souverain)

**Les 5 meilleurs FULL LOCAL à vendre :**
1. **Passerelle LLM 0-token** (JARVIS LLM Gateway + dispatchers) — le hub local qui remplace toute API cloud
2. **Cascade bibliothèque vivante** (bloc.sh, cascade-bibliotheques, protocole, single_request_pipeline) — routage d'intention + contexte maximal, 0-token
3. **Consensus multi-LLM local** (multi-llm-orchestrate.py) — fan-out + vote pondéré sur modèles locaux
4. **RAG Board souverain** (Board FTS5 + vecteurs + reindex) — base de connaissances qui ne sort jamais
5. **Supervision Infra self-hosted** (GPU/VRAM/ZRAM/Disk/Systemd/Docker/Cluster health + Self-Healing) — monitoring 100 % local, produit SaaS-like on-premise

**Hybrides typiques et leur correctif :** Mail Triage (couper IMAP/Telegram → mail local + notif locale) · cascade-cli (couper fallback Gemini) · board-publisher (couper Perplexity) · jarvis-audit (désactiver scan-web) · digests Telegram (→ notif locale).

**Externes écartés :** toute la suite LinkedIn/CDP, NotebookLM, Codeur.com, Google Calendar/Gmail, trading/MEXC, GitHub API.

**Page :** https://app.notion.com/p/Workflows-100-LOCAUX-l-offre-souvera