# INDEX — Organigramme conteneurs M4 (pamerys-m4)

_Généré depuis `jarvis-index.db` le 2026-06-28 10:51. Source de vérité : la base SQLite._

## Services live (Swarm)

| Entité | Stack | Service | Replicas | Ports | Réseau |
|---|---|---|---|---|---|
 |  00-infra | jarvis | jarvis_portainer | 1/1 | *:9000->9000/tcp | jarvis-bus |
 |  00-infra | jarvis | jarvis_redis | 1/1 | *:6379->6379/tcp | jarvis-bus |
 |  00-infra | jarvis | jarvis_registry | 1/1 | *:5000->5000/tcp | jarvis-bus |
 |  20-automation | (standalone) | jarvis-n8n | 1/1 | 5678 | jarvis-net |
 |  30-data | data | data_postgres | 1/1 | (interne) | jarvis-bus |
 |  50-business | business | business_alkymia-site | 1/1 | *:8086->80/tcp | jarvis-bus |
 |  50-business | business | business_delmas-site | 1/1 | *:8085->80/tcp | jarvis-bus |

## Entités de l'organigramme
- **00-infra** : redis (bus) · registry (:5000) · portainer (:9000)
- **10-ia** : routeur LLM (à venir) — Ollama/LM Studio host
- **20-automation** : n8n (:5678) · OMEGA (à venir)
- **30-data** : postgres (bus) · sqlite-bridge (à venir) · index Pinecone
- **40-voice** : whisper/piper/lumen (à venir)
- **50-business** : alkymia-site (:8086) · delmas-site (:8085) · trading/healthcare/factures (à venir)
- **90-secrets-git** : coffre sops+age · gitleaks (à venir)

## Secrets (chiffrés, gitmore)
- Coffre : `~/jarvis/secrets-vault/*.enc.env` (AES256, clé age `~/.config/sops/age/keys.txt`)
- Docker secrets : `redis_pass`, `pg_pass`

## Bibliothèque de commandes
Voir **COMMANDS.md** ou : `sqlite3 ~/jarvis/stacks/jarvis-index.db 'SELECT * FROM commands'`
