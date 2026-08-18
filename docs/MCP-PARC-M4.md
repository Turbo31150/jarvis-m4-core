# 🔌 PARC MCP — M4 (`pamerys-m4`)

> **État au 2026-08-18 — 52 serveurs connectés · 0 en échec · 1 en attente d'authentification.**
> Point d'entrée unique pour comprendre quels serveurs MCP tournent, d'où ils viennent,
> et pourquoi certains ont été écartés. Toute affirmation ci-dessous a été **vérifiée par test réel**
> (poignée de main `initialize` + `tools/list`), jamais déduite d'un fichier de config.

---

## 1. Comment ils démarrent

Les serveurs sont déclarés dans **`~/.claude.json`** (scope `user`, 47 entrées locales).
**Aucun démon ni script de lancement n'est nécessaire** : Claude Code lit ce fichier au lancement
et démarre chaque serveur stdio lui-même, à chaque session. Ajouter une entrée suffit à la faire
démarrer automatiquement pour toujours.

S'y ajoutent **6 connecteurs claude.ai** distants (Gmail, Agenda, Drive, Notion, Gamma, WordPress),
gérés côté compte et non par ce fichier.

```bash
claude mcp list                      # état réel du parc (relance chaque serveur)
claude mcp add-json <nom> '<json>' -s user   # ajouter (démarrage auto acquis)
claude mcp remove <nom> -s user      # retirer
```

⚠️ **Piège des scopes.** Un même nom peut exister en scope `user` (`~/.claude.json`) **et** `project`
(`~/.mcp.json`). Le scope projet l'emporte et masque silencieusement la version `user`.
En cas de comportement incohérent : `claude mcp list` signale explicitement le conflit.

---

## 2. Les 52 serveurs actifs

### Cœur JARVIS (13)
`jarvis-board` · `table-ronde` · `jarvis-core` · `jarvis-agents` · `jarvis-cluster` · `jarvis-manus`
`jarvis-memory` · `jarvis-cowork` · `jarvis-perplexity` · `jarvis-zerotoken` · `cognitive-supervisor`
`antigravity-bridge` · `ia-web-jarvis`

### Bases de données (7)
`postgres` · `redis` · `jarvis-sql` · `sqlite-jarvis-master` · `sqlite-jarvis-logs`
`sqlite-cowork-engine` · `sqlite-etoile`

### Fichiers (3)
`filesystem` · `jarvis-linux-fs` · `jarvis-filesystem` ⭐

### Navigateur & web (8)
`chrome-devtools` · `puppeteer` · `mcp-web-pilot` · `browser-control` ⭐ · `firecrawl` ⭐
`requestly-jarvis` · `web-api` ⭐ · `netlify`

### Inférence locale (4)
`jarvis-ol1` · `jarvis-linux-ol1` · `jarvis-linux-m1` ⭐ · `openclaw`

### Notebooks & données (4)
`jupyter-mcp` ⭐ · `jupyters` ⭐ · `notebook` ⭐ · `mcp-notebooklm`

### Contenu & social (4)
`mirra` · `local-mirra` ⭐ · `jarvis-linux-telegram` · `notebooklm-bridge`

### Dev (3)
`github` · `GitKraken` ⭐ · `sequential-thinking`

### Divers (1) — `antigravity`

### Connecteurs claude.ai (6)
`Gmail` · `Google Calendar` · `Google Drive` · `Notion` · `Gamma` · `WordPress.com` ⚠️

⭐ = récupéré le 2026-08-18 (voir §3) · ⚠️ = authentification requise

---

## 3. Récupération du 2026-08-18 — 10 serveurs, ~133 outils

Moisson menée sur le SSD USB-C **M1** (`/media/pamerys/JARVIS-M1`, arbo `/home/turbo`, 46 serveurs)
puis sur les configs locales oubliées de M4 — dont **`~/jarvis/.mcp.json` qui en déclarait 91**,
source la plus riche du poste. 56 candidats uniques absents du parc actif ont été testés un par un.

| Serveur | Outils | Ce qu'il apporte |
|---|---|---|
| `GitKraken` | 31 | Git/GitLens complet : blame, historique, PR, worktrees |
| `chrome-devtools-mcp` → *écarté* | 29 | doublon de `chrome-devtools` (même paquet npm) |
| `firecrawl` | 25 | Scraping & crawl web structuré — ⚠️ requiert `FIRECRAWL_API_KEY` |
| `jupyter-mcp` | 17 | Noyaux Jupyter : exécuter cellules, gérer notebooks |
| `jupyters` | 17 | Édition notebook (lecture/écriture cellules) — freemium, 10 exéc./jour |
| `jarvis-filesystem` | 14 | Accès à `/home/pamerys/jarvis-linux`, **non couvert** par `filesystem` |
| `notebook` | 9 | Data-agent-kit, mode notebook |
| `browser-control` | 7 | navigate, screenshot, click, type, evaluate, get_text, open_chrome |
| `local-mirra` | 6 | Pipeline Mirra **local** : backends, generate, carousel, publish |
| `web-api` | 5 | http_request, webhook_send, telegram_send, **n8n_trigger**, api_health_check |
| `jarvis-linux-m1` | 2 | `lm_chat` / `lm_models` sur LM Studio — **réadressé sur M6** |

### Deux correctifs de fond appliqués au passage

**a) `lmstudio-mcp-server.py` — deux défauts réels.**
Le script visait `192.168.1.85:1234`, une IP qui n'est plus dans la topologie, et appelait
`/v1/models` en **POST** là où LM Studio exige un **GET** (`Unexpected endpoint or method`).
Corrigé : ajout d'un helper `_get()`, passage de `/models` en GET, défaut réadressé sur
**M6 `10.42.0.230:1234`** (nœud vivant, 1,4 ms). Vérifié : renvoie 5 modèles
(`qwen3.5-9b`, `deepseek-r1-0528-qwen3-8b`, `nomic-embed-text-v1.5`, `qwen3-4b`, `qwen2.5-coder-14b`).
Sauvegarde : `lmstudio-mcp-server.py.bak-*`.

**b) `openclaw` — n'a jamais pu fonctionner.**
Deux défauts empilés : (1) `OPENCLAW_GATEWAY_TOKEN` exporté par `~/.bashrc` et `~/.zshrc` était
hérité par le **client** mais pas par le **gateway** systemd → `token_mismatch` systématique ;
(2) l'entrée pointait sur `openclaw acp`, or **ACP n'est pas MCP** (il renvoie `protocolVersion`
en nombre, sans `serverInfo`). Corrigé : token unifié dans les trois fichiers de config
(`openclaw.json`, `openclaw-gateway.json`, `config.json`) et entrée recâblée sur **`openclaw mcp serve`**.

---

## 4. Écartés — et pourquoi

46 des 56 candidats n'ont pas été retenus. Aucun n'a été écarté sur intuition : chacun a échoué à un test.

| Motif | Serveurs |
|---|---|
| **Doublon prouvé** | `jarvis-sql-bridge` (MD5 **identique** à `jarvis-sql`) · `chrome-devtools-mcp` · `jarvis-master`/`jarvis-logs`/`jarvis-mind`/`jarvis-cowork-db` (bases déjà servies) |
| **Paquet npm supprimé du registre (404)** | `server-sqlite` · `server-openai-compatible` · `openai-compatible-mcp-server` (`jarvis-m1`, `jarvis-m2`) · `server-notion` · `server-linear` · `server-pinecone` · `server-supabase` · `server-playwright` · `@sourcegraph/mcp-server` |
| **Identifiants cloud absents** | 10 connecteurs Google Toolbox (`bigquery`, `spanner`, `bigtable`, `alloydb-*`, `cloud-sql-*`, `dataproc`, `serverless-spark`, `knowledge_catalog`) · `slack` (`SLACK_BOT_TOKEN`) · `github-mcp-server` (docker) |
| **Fichier introuvable** | `comet` · `mcp-desktop-linux` · `desktop-control` · `navigation-api` · `notebooklm-rag` · `cdp` · `trading-ai-ultimate` |
| **Service éteint** | `browseros` (:9201) · `cc-workflow-studio` (:6282) · `jarvis-linux-voice` (:8765) · `jarvis-pipeline` (:19742) · `lm-11235` (192.168.0.10, hors topologie) |
| **Dépendances cassées** | `jarvis-mcp` (`No module named 'modules.cowork...'`) · `browser-control-firefox` (port 8089 occupé) |
| **Sans objet** | `n8n-mcp` (définition sans commande) · `visualization` (0 outil) |

---

## 5. Services optionnels — à démarrer à la demande

Ces unités systemd **existent et sont `enabled`**, mais ont été **arrêtées volontairement**
le 2026-08-18 (M4 n'a que 16 Go de RAM et une RTX 3050). Elles ne sont **pas** rallumées
automatiquement : ce serait revenir sur une décision d'exploitation délibérée.

```bash
systemctl --user start browseros.service          # BrowserOS — navigateur agentique, MCP sur :9200
systemctl --user start jarvis-voice-pilot.service # wake word + STT + LLM + TTS
```

Une fois `browseros` démarré, son MCP peut être ajouté :
`claude mcp add-json browseros '{"type":"http","url":"http://127.0.0.1:9200/mcp"}' -s user`

**`omega-gateway`** (`~/jarvis/mcp/omega_gateway.py`) mérite un mot : ce n'est pas un serveur stdio
mais une **passerelle HTTP sur `:18810/mcp` qui agrège 36 serveurs**. Non câblée ici — elle ferait
doublon avec le parc actuel, mais reste la bonne réponse si tu veux un point d'entrée unique.

---

## 6. Dépendances réseau (sondées le 2026-08-18)

| Cible | État | Sert à |
|---|---|---|
| `127.0.0.1:5432` Postgres · `:6379` Redis | ✅ UP | `postgres`, `redis` |
| `127.0.0.1:11434` Ollama | ✅ UP | `jarvis-ol1`, `jarvis-linux-ol1` |
| `10.42.0.230:1234` **M6** LM Studio | ✅ UP | `jarvis-linux-m1`, `jarvis-cluster` |
| `127.0.0.1:9222` Chrome CDP | ✅ UP | `chrome-devtools` |
| `127.0.0.1:18789` OpenClaw ACP | ✅ UP | `openclaw` |
| `192.168.1.26:1234` M2 | ❌ DOWN | — |
| `192.168.50.2:5432` mémoire longue | ❌ DOWN | injection mémoire hors service |
| `127.0.0.1:8899` cockpit planning | ❌ DOWN | — |

---

## 7. Reste à faire

- **WordPress.com** — seul élément non connecté. OAuth navigateur, à lancer manuellement :
  `claude mcp login "claude.ai WordPress.com"`
- **`firecrawl`** — connecté mais ses outils échoueront sans clé :
  `claude mcp add-json firecrawl '{"type":"stdio","command":"/usr/bin/npx","args":["-y","firecrawl-mcp"],"env":{"FIRECRAWL_API_KEY":"fc-…"}}' -s user`
- **`n8n-mcp`** — repéré dans des configs de projet mais jamais défini. À câbler si les 56 workflows n8n doivent être pilotés depuis Claude Code.

---

## 8. Sauvegardes

| Fichier | Sauvegarde |
|---|---|
| `~/.claude.json` | `~/.claude.json.bak-mcpfix-*`, `.bak-avant-recup-*` |
| `~/.mcp.json` | `~/.mcp.json.bak-mcpfix-*` |
| `~/.openclaw/{openclaw,openclaw-gateway,config}.json` | `*.bak-tokenfix-*` |
| `lmstudio-mcp-server.py` | `lmstudio-mcp-server.py.bak-*` |

Journal : `sqlite3 ~/jarvis/logs/jarvis_logs.db "SELECT * FROM system_actions WHERE action LIKE 'mcp_%';"`
