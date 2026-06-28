# Cahier des charges — Organigramme conteneurs JARVIS sur M4 (pamerys-m4)

> Cible : faire converger les services existants/à créer vers une organisation en **6 entités** sous Docker Swarm, autour d'un **bus Redis** et d'un réseau overlay `jarvis-bus`, sans casser l'existant (`jarvis_portainer`, `jarvis_registry`, `jarvis-n8n`) et **sans copier** les conteneurs distants M1/M2/M5.
> Contexte M4 : seul nœud Ready/Leader, CPU-only, RAM ~15 Gi, contrainte thermique. **M1/M2/M5 OFFLINE** ce soir → fédération différée.
> *Produit par workflow multi-agent (8 agents, audit disque réel) le 2026-06-28.*

---

## 1) Vue d'ensemble de l'organigramme

| Entité | Rôle | Services clés | Fédération M1/M2/M5 |
|---|---|---|---|
| **00-infra** | Socle technique partagé : bus, registry, UI Swarm | redis, registry, portainer | Source d'images + bus consommés par les nœuds à leur retour |
| **10-ia** | Inférence IA derrière routeur multi-LLM | ia-router, ollama-bridge, lmstudio-bridge, open-webui | Consomme LM Studio/Ollama distants par IP LAN puis nom overlay |
| **20-automation** | Orchestration & automatisation métier | n8n, n8n-worker, omega-api/worker/db, browseros | Workers n8n distants dépilent la même file Redis |
| **30-data** | Données + index (PG, SQLite RO, Pinecone, chiffrement) | postgres, sqlite-bridge, pinecone-indexer, sqlcipher-harden | Nœuds consomment postgres/sqlite-bridge par nom |
| **40-voice** | Chaîne STT/TTS | whisper-stt, vocal-router, bdqt, piper-tts, lumen | `whisper-gpu` sur nœuds GPU au retour via VIP overlay |
| **50-business** | Apps métier/commercial (CA + marque) | facturesaas-{db,backend,frontend}, tradeoracle-{ui,mcp}, healthcare-api, delmas-site, alkymia-site | Inférence déléguée aux LLM distants par nom, fallback cloud |
| **90-secrets-git** | Sécurité/git : durcissement, hook anti-secret, scan, push sur GO | gitleaks-scan, git-secrets-pusher | Aucune copie ; durcissement rejoué par nœud |

**Colonne vertébrale** : réseau `jarvis-bus` (overlay `--attachable --scope swarm`, à créer). Bus/cache/discovery = **Redis** (hébergé par 00-infra, consommé par toutes les entités via `redis:6379`).

---

## 2) Entités (détail)

### 2.1 — 00-infra (socle)
- **redis** `redis:7-alpine` — bus pub/sub + cache + discovery, à créer, `127.0.0.1:6379` host-only + DNS overlay, `node.role==manager`.
- **registry** `registry:2` — EXISTANT (`jarvis_registry` Up), `5000:5000`.
- **portainer** `portainer/portainer-ce` — EXISTANT (`jarvis_portainer` Up), `9000:9000`, monte `/var/run/docker.sock`.
- Réseaux : `jarvis-bus` (à créer, attachable) ; `jarvis_default` (existant, `attachable=false` → à remplacer) ; `jarvis-net` (legacy n8n, à migrer).
- Volumes : `redis_data`, `registry_data`, `portainer_data`.
- Fédération : registry pull `192.168.1.149:5000` par les nœuds (insecure-registry à déclarer dans leur `daemon.json`).

### 2.2 — 10-ia (inférence)
- **ia-router** `python:3.12-slim` (wrap `lm-ask.sh` + `model_router.sh`, cible litellm) — routeur OpenAI-compat `8900`, lit `health:<backend>`, cache `cache:<sha256>`, file `jobs:inference`.
- **ollama-bridge** — reste **systemd HOST** (`OLLAMA_HOST=0.0.0.0:11434`), via `host.docker.internal`.
- **lmstudio-bridge** — app **HOST** M4 (`:1234`), via `host.docker.internal`.
- **open-webui** `ghcr.io/open-webui/open-webui:main` (**CPU, PAS :cuda**, retirer devices nvidia) — `3000:8080`, `OPENAI_API_BASE_URLS=http://ia-router:8900/v1`.
- Redis : cache réponses, registre `health:*` lu avant routage, file `jobs:inference`. Dégradé gracieux si Redis KO.
- Fédération : LAN M1 `192.168.1.85:1234`, M2 `.26:1234`, M5 `.94` → bascule nom overlay (`lmstudio-m1`) au retour ; `cluster_nodes.py` exclut les down.

### 2.3 — 20-automation
- **n8n** `n8nio/n8n:latest` — conteneur RÉEL `jarvis-n8n` (volume `docker_jarvis-n8n-data`→`/home/node/.n8n`), `5678`, à migrer en queue Redis + jarvis-bus.
- **n8n-worker** (`command: worker`) — dépile la file Bull.
- **omega-api / omega-worker** build local `~/Bureau/workflow-gestion/docker` → push registry ; **omega-db** `postgres:16-alpine`.
- **browseros** — natif host (`:9200` HTTP, `:9100` CDP), piloté par n8n, hors-Swarm.
- Redis : file Bull n8n (`N8N_EXECUTIONS_MODE=queue`, `QUEUE_BULL_REDIS_HOST=jarvis-redis`), broker OMEGA (remplace `omega-redis`).

### 2.4 — 30-data
- **postgres** `postgres:15-alpine` (DB `jarvis_agents`) — source `~/jarvis-db-migration`, **retirer expo 0.0.0.0:5432**, `node.hostname==pamerys-m4`.
- **sqlite-bridge** `python:3.12-slim` — API RO `:18801` sur ~773 SQLite (`jarvis_sql_bridge.py`).
- **pinecone-indexer** — job SQLite→Pinecone (index `jarvis-memory`), **lock Redis SETNX** anti double-run.
- **sqlcipher-harden** — script (Vague 3) chiffrement bases sensibles.
- ⚠️ **Clé Pinecone `pcsk_…` EN DUR** dans `jarvis_sql_bridge.py` + `index_sql_to_pinecone.py` → **RÉVOQUER + secret**.

### 2.5 — 40-voice
- **whisper-stt** (faster-whisper, `whisper-server.py`, BDQT intégré) — `8789`, CPU.
- **vocal-router** — failover STT M1→M2→M5→M4 par nom de service.
- **bdqt** — qualité transcription `:8790`.
- **piper-tts** — TTS `fr_FR-siwis-medium` (micro-API HTTP, onnx ro).
- **lumen** (Dockerfile node:22 existant) — hub token/routing `:8788`.
- Redis : file `voice:stt:queue`, cache transcriptions, pub/sub `voice:events`, présence `voice:node:*`.
- Fédération : `whisper-gpu` sur nœuds GPU au retour (VIP overlay), fallback whisper-stt local.

### 2.6 — 50-business
- **facturesaas-{db,backend,frontend}** (Postgres + Django + Next.js) — source `~/Documents/Soorce_facture`.
- **tradeoracle-{ui,mcp}** (Streamlit + FastMCP, **Dockerfile à créer**) — `8501` / `8000` SSE.
- **healthcare-api** (FastAPI, **Dockerfile à créer**, corriger requirements).
- **delmas-site / alkymia-site** `nginx:alpine` (HTML statique, COPY au build) — `8085` / `8086`.
- ⚠️ **Stripe LIVE `pk_live_`/`sk_live_` + SECRET_KEY Django** en clair dans `docker_servercompose.yml` → **rotater + docker secret**.
- Redis cloisonné par DB : db0 tradeoracle, db1 healthcare, db2 facturesaas, db3 signals pub/sub.

### 2.7 — 90-secrets-git
- **gitleaks-scan** `zricethezav/gitleaks` — scan RO périodique des 3 repos, verdict sur Redis (`sec:gitleaks:last`), pub/sub `sec:alerts`.
- **git-secrets-pusher** `alpine/git` — push **only on green** (profile manuel).
- Coffre sops+age déjà en place (`~/jarvis/secrets-vault`, clé `~/.config/sops/age/keys.txt`).
- Hook pre-commit (`gitleaks protect --staged` / fallback regex) + `.gitleaks.toml` (allowlist `*.enc.env`).

---

## 3) Stratégie Swarm + Redis
- **`jarvis-bus`** : `docker network create -d overlay --attachable --scope swarm jarvis-bus` ; `external:true` dans chaque compose.
- **Redis** : 1 instance (00-infra), `node.role==manager`, AOF, `requirepass` via docker secret. Rôles : BUS (`jarvis.events.*`, `voice:events`, `trading:signals`, `sec:alerts`), CACHE, DISCOVERY/HEALTH. DB index distincts par app. **Dégradé gracieux si Redis KO.**
- **Fédération sans copie** : jamais recréer M1/M2/M5. Offline → IP LAN ; retour → noms overlay + VIP + `placement.constraints` ; workers en replicas qui dépilent la même file Redis.
- **Nœuds offline** : **nettoyer ~80 nœuds fantômes Down** (NE PAS rm le Leader M4 `i2kp46…`) ; forcer `node.hostname==pamerys-m4` sur les stateful ; SPOF assumé (redis+registry+portainer sur le seul manager).

---

## 4) Sécurité / secrets
**Secrets à sortir du code/compose → `docker secret`** :
- `POSTGRES_PASSWORD` en clair (30-data) + port 5432 ouvert 0.0.0.0.
- **Clé Pinecone `pcsk_…` EN DUR** (sql_bridge) → RÉVOQUER.
- **Stripe LIVE + SECRET_KEY Django** en clair (Soorce_facture) → ROTATER.
- `IMAP_PASSWORD` / `TELEGRAM_BOT_TOKEN` OMEGA, `requirepass` Redis, `~/.ollama/cloud_api_key`.

**3 repos nettoyés à pousser SUR GO** : `jarvis-machines-private` (main, +1), `jarvis-m5-config` (master, +1), `jarvis-core` (master) — ⚠️ **jarvis-core devant 2 / DERRIÈRE 234** + `config/browser-automation.env` modifié → **auditer + `git pull --rebase` AVANT push** (un push naïf casserait l'historique distant).

**Hook anti-secret** : pre-commit gitleaks + scan périodique (contournable par `--no-verify` → garder le filet scan/CI). Purger `~/.git-credentials`.

---

## 5) TODOLISTE DYNAMIQUE (vagues V1→V8)
> Ordre = ne rien casser. portainer(9000)/registry(5000)/n8n(5678) UP à chaque vague.

### V1 — Hygiène Swarm + secrets urgents
- [ ] Lister + supprimer les nœuds Down (sauf Leader M4) : `docker node ls | awk '$4=="Down"{print $1}' | xargs -r docker node rm --force`
- [ ] **RÉVOQUER + régénérer la clé Pinecone `pcsk_…`** (en clair dans sql_bridge)
- [ ] **ROTATER Stripe LIVE + SECRET_KEY Django** (docker_servercompose.yml)
- [ ] Auditer `jarvis-core/config/browser-automation.env` puis `git pull --rebase`
- [ ] Sauvegarder le volume `docker_jarvis-n8n-data` avant migration

### V2 — Arborescence + réseau bus + pulls hors-ligne
- [ ] `mkdir -p ~/jarvis/stacks/{00-infra,10-ia,20-automation,30-data,40-voice,50-business,90-secrets-git/reports}`
- [ ] `docker network create -d overlay --attachable --scope swarm jarvis-bus` (+ `jarvis-voice-internal`)
- [ ] Puller : `redis:7-alpine`, `zricethezav/gitleaks:latest`, binaire gitleaks dans `~/.local/bin`

### V3 — 00-infra (socle)
- [ ] Secret `requirepass` Redis (depuis le coffre) → `docker secret create`
- [ ] Écrire `00-infra/docker-compose.yml` (redis AOF + requirepass + healthcheck ; registry ; portainer ; jarvis-bus external)
- [ ] `docker stack deploy -c …/00-infra/docker-compose.yml jarvis` ; vérifier 3/3 UP + `redis-cli ping`→PONG

### V4 — 10-ia
- [ ] Packager ia-router (lm-ask.sh + model_router.sh + cluster_nodes.py) `:8900` + health/cache/queue Redis
- [ ] Écrire `10-ia/docker-compose.yml` (ia-router + open-webui CPU, `host.docker.internal`)
- [ ] Garder Ollama/LM Studio HOST ; brancher `lm-ask.sh` sur `ia-router:8900`

### V5 — 20-automation
- [ ] Builder+pousser image OMEGA (registry) ; écrire `20-automation/docker-compose.yml` (n8n + worker + omega-* , SANS Redis local)
- [ ] Migrer `jarvis-n8n` en service Swarm en conservant le volume ; activer mode queue ; tester webhook+cron
- [ ] OMEGA → `redis://jarvis-redis:6379/0`, secrets IMAP/TELEGRAM ; décider browseros (host vs `network_mode host`)

### V6 — 30-data
- [ ] Secrets `POSTGRES_PASSWORD` + `PINECONE_API_KEY` (régénérée)
- [ ] Porter postgres (réseau bus, retirer expo 0.0.0.0, init.sql) ; builder sqlite-bridge ; indexer en job + lock SETNX
- [ ] Écrire `30-data/docker-compose.yml` ; (différé) Vague 3 SQLCipher sur bases sensibles

### V7 — 40-voice + 50-business
- [ ] Builder whisper-stt/piper/bdqt/lumen/vocal-router ; écrire `40-voice/docker-compose.yml` ; **stopper les systemd-user redondants APRÈS validation** (sinon « address already in use »)
- [ ] Cibler clients (PWA :7777, n8n, widgets) sur les nouveaux endpoints
- [ ] Dockerfiles TradeOracle + healthcare (corriger requirements) ; builder facturesaas ; écrire `50-business/docker-compose.yml` ; deploy `business`
- [ ] (Option) reverse-proxy Traefik pour les domaines/ports

### V8 — 90-secrets-git + fédération différée
- [ ] `.gitleaks.toml` + hook pre-commit dans les 3 repos + `core.hooksPath`
- [ ] Écrire `90-secrets-git/docker-compose.yml` (gitleaks-scan RO, clé age NON montée ; pusher profile manuel)
- [ ] Scan → vérifier `sec:gitleaks:last`=0 leak
- [ ] **SUR GO (vert) :** pousser jarvis-machines-private, jarvis-m5-config, jarvis-core (après rebase)
- [ ] Documenter la fédération (insecure-registry, join-token, labels gpu/role) ; activer entrées overlay au retour M1/M2/M5
- [ ] Archiver `~/jarvis/swarm-stack.yml` (redondant)

---

## 6) Vérification end-to-end
```bash
docker stack ls ; docker service ls            # existant préservé (portainer/registry/n8n UP)
docker run --rm --network jarvis-bus redis:7-alpine redis-cli -h redis -a <pass> ping   # PONG
curl -s http://localhost:8900/v1/models        # ia-router
curl -s http://localhost:8789/health           # whisper (après stop systemd-user)
docker compose --profile scan run --rm gitleaks-scan ; redis-cli -a <pass> get sec:gitleaks:last
bash ~/jarvis/scripts/sec-audit.sh             # étape [7] verte
for r in jarvis-machines-private jarvis-m5-config jarvis-core; do
  git -C ~/$r grep -nE 'pcsk_|sk_live_|ghp_|age1[0-9a-z]+' $(git -C ~/$r rev-parse origin/HEAD) || echo "$r clean"; done
```
**Succès** : (1) portainer/registry/n8n jamais tombés ; (2) `redis-cli ping`=PONG avec auth ; (3) healthcheck par entité ; (4) Redis KO ne casse rien ; (5) `sec-audit.sh` [7] vert ; (6) `git grep` origin = 0 secret ; (7) fédération différée documentée, 0 nœud fantôme hors Leader.
