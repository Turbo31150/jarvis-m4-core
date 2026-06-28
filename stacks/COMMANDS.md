# Bibliothèque de commandes M4 — 285 commandes préchargées

_Source : `jarvis-index.db` (table `commands`). Modèle entreprise : voir ORGANIGRAMME-AGENTS-M4.md._
_Recherche : `sqlite3 ~/jarvis/stacks/jarvis-index.db "SELECT command,description FROM commands WHERE entity='10-ia'"`_


## 00-infra

**audit fuites** — Scanne le repo jarvis a la recherche de secrets en clair.
```bash
gitleaks detect --source ~/jarvis --no-banner
```
**backup portainer** — Sauvegarde la base de configuration de Portainer.
```bash
docker run --rm -v jarvis_portainer_data:/d -v ~/backups:/b alpine tar czf /b/portainer-$(date +%F).tgz -C /d .
```
**backup redis** — Sauvegarde le volume de persistance AOF de Redis.
```bash
docker run --rm -v jarvis_redis_data:/d -v ~/backups:/b alpine tar czf /b/redis-$(date +%F).tgz -C /d .
```
**backup registry** — Sauvegarde le volume du registre d'images prive.
```bash
docker run --rm -v jarvis_registry_data:/d -v ~/backups:/b alpine tar czf /b/registry-$(date +%F).tgz -C /d .
```
**deploy socle** — redis+registry+portainer
```bash
docker stack deploy -c ~/jarvis/stacks/00-infra/docker-compose.yml jarvis
```
**deploy socle** — Deploie/met a jour la stack socle redis+registry+portainer.
```bash
docker stack deploy -c ~/jarvis/stacks/00-infra/docker-compose.yml jarvis
```
**df docker** — Audit de l'espace disque consomme par images, volumes et conteneurs.
```bash
docker system df -v
```
**edit coffre** — Edite un secret chiffre du coffre AES256/age.
```bash
sops ~/jarvis/secrets-vault/infra.enc.env
```
**etat global** — Vue d'ensemble des stacks et services Swarm avec replicas et ports.
```bash
docker stack ls && docker service ls
```
**index commands** — Recupere la bibliotheque de commandes depuis l'index.
```bash
sqlite3 ~/jarvis/stacks/jarvis-index.db 'SELECT entity,label,cmd FROM commands ORDER BY entity'
```
**index tables** — Liste les tables de l'index SQLite (source de verite organigramme).
```bash
sqlite3 ~/jarvis/stacks/jarvis-index.db '.tables'
```
**inspect health** — Verifie l'etat de sante et les erreurs des taches Redis.
```bash
docker service ps jarvis_redis --format '{{.Name}} {{.CurrentState}} {{.Error}}'
```
**join token** — Affiche le token pour rattacher un noeud manager au cluster.
```bash
docker swarm join-token manager
```
**logs portainer** — Affiche les logs de la console Portainer.
```bash
docker service logs --tail 100 jarvis_portainer
```
**logs redis** — Suit les logs du bus Redis en temps reel.
```bash
docker service logs -f --tail 100 jarvis_redis
```
**logs registry** — Suit les logs du registre d'images prive.
```bash
docker service logs -f --tail 100 jarvis_registry
```
**ports exposes** — Inventaire des ports publies par les services du socle.
```bash
docker service ls --format '{{.Name}} {{.Ports}}' | grep -v '^.* $'
```
**prune images** — Nettoie les images locales non utilisees de plus de 7 jours.
```bash
docker image prune -af --filter 'until=168h'
```
**ps jarvis** — Etat des taches de la stack avec erreurs detaillees non tronquees.
```bash
docker stack ps jarvis --no-trunc
```
**redeploy redis** — Force le redemarrage rolling du service Redis (depannage).
```bash
docker service update --force jarvis_redis
```
**redis clients** — Liste les clients connectes au bus (entites consommatrices).
```bash
docker run --rm --network jarvis-bus redis:7-alpine redis-cli -h redis -a "$REDIS_PASSWORD" client list
```
**redis info** — Affiche version, uptime et infos serveur du bus Redis.
```bash
docker run --rm --network jarvis-bus redis:7-alpine redis-cli -h redis -a "$REDIS_PASSWORD" info server
```
**redis memoire** — Surveille la consommation memoire de Redis (used_memory_human).
```bash
docker run --rm --network jarvis-bus redis:7-alpine redis-cli -h redis -a "$REDIS_PASSWORD" info memory
```
**redis monitor** — Trace en direct toutes les commandes traversant le bus (debug).
```bash
docker run --rm --network jarvis-bus redis:7-alpine redis-cli -h redis -a "$REDIS_PASSWORD" monitor
```
**redis ping** — test bus -> PONG
```bash
docker run --rm --network jarvis-bus redis:7-alpine redis-cli -h redis -a "$REDIS_PASSWORD" ping
```
**redis ping** — Teste le bus Redis via le DNS overlay (doit retourner PONG).
```bash
docker run --rm --network jarvis-bus redis:7-alpine redis-cli -h redis -a "$REDIS_PASSWORD" ping
```
**redis secret** — Dechiffre et exporte le mot de passe Redis depuis le coffre sops.
```bash
REDIS_PASSWORD=$(sops -d ~/jarvis/secrets-vault/infra.enc.env | grep REDIS_PASSWORD | cut -d= -f2)
```
**registry catalog** — Liste toutes les images du registre prive.
```bash
curl -s --max-time 5 http://127.0.0.1:5000/v2/_catalog
```
**registry gc** — Lance le garbage collector pour liberer l'espace des layers orphelins.
```bash
CID=$(docker ps -qf name=jarvis_registry) && docker exec $CID registry garbage-collect /etc/docker/registry/config.yml
```
**registry tags** — Liste les tags d'une image du registre (ex: alkymia-site).
```bash
curl -s http://127.0.0.1:5000/v2/50-business/alkymia-site/tags/list
```
**reseau bus** — Liste les conteneurs attaches a l'overlay du bus jarvis-bus.
```bash
docker network inspect jarvis-bus --format '{{range .Containers}}{{.Name}} {{end}}'
```
**rotate redis_pass** — Cree une nouvelle version du secret Redis pour rotation sans downtime.
```bash
sops -d ~/jarvis/secrets-vault/infra.enc.env | grep REDIS_PASSWORD | cut -d= -f2 | tr -d '\n' | docker secret create redis_pass_v2 - && echo 'puis MAJ compose -> redis_pass_v2'
```
**scale registry** — Ajuste/relance le nombre de replicas du registre.
```bash
docker service scale jarvis_registry=1
```
**secret redis** — REDIS_PASSWORD / POSTGRES_PASSWORD
```bash
sops -d ~/jarvis/secrets-vault/infra.enc.env
```
**secrets list** — Liste les docker secrets du cluster (redis_pass, pg_pass).
```bash
docker secret ls
```
**services jarvis** — Detail des services de la stack jarvis (image, replicas, ports).
```bash
docker stack services jarvis
```
**swarm noeuds** — Liste les noeuds du cluster et identifie le manager Leader (pamerys-m4).
```bash
docker node ls
```

## 10-ia

**ask big** — Inference modele lourd (qwen3.5-35b M2, fallback Ollama local capable)
```bash
bash ~/jarvis/scripts/lm-ask.sh --big 'Refactor ce code: ...'
```
**ask cloud** — Force le routage cloud ollama.com (gpt-oss:120b, 0 token facture)
```bash
bash ~/jarvis/scripts/lm-ask.sh --cloud 'Tache complexe'
```
**ask fast** — Inference cascade rapide (qwen3.5-9b M1+M2 parallele, premier gagne)
```bash
bash ~/jarvis/scripts/lm-ask.sh --fast 'Resume en 3 points: ...'
```
**ask piped** — Resume/extraction sur contenu pipe sans le faire lire par Opus
```bash
cat /chemin/fichier.txt | bash ~/jarvis/scripts/lm-ask.sh 'Resume ce contenu'
```
**ask reason** — Inference reasoning via deepseek-r1 sur le cluster
```bash
bash ~/jarvis/scripts/lm-ask.sh --reason 'Debug logique: ...'
```
**backup models** — Sauvegarde le cache des modeles Ollama (manifests + blobs)
```bash
tar czf ~/backups/ollama-models-$(date +%F).tgz -C ~/.ollama models
```
**cloud key check** — Verifie la presence de la cle API cloud ollama.com pour le fallback
```bash
test -s ~/.ollama/cloud_api_key && echo 'cloud key OK' || echo 'cloud key MANQUANTE'
```
**cluster M1 ping** — Verifie le noeud cluster M1 LM Studio et ses modeles (distill Opus)
```bash
curl -s --max-time 2 http://192.168.1.85:1234/v1/models | jq -r '.data[].id'
```
**cluster M2 ping** — Verifie le noeud cluster M2 LM Studio et ses modeles
```bash
curl -s --max-time 2 http://192.168.1.26:1234/v1/models | jq -r '.data[].id'
```
**disk models** — Mesure l'espace disque occupe par les modeles Ollama et LM Studio
```bash
du -sh ~/.ollama/models ~/.lmstudio/models 2>/dev/null
```
**gemini ask** — Inference Gemini 2.5 Pro via OAuth Google One (0 token)
```bash
bash ~/jarvis/scripts/gemini-ask.sh 'Question best-quality'
```
**gemini flash** — Inference Gemini 2.5 Flash (rapide, fallback du Pro)
```bash
bash ~/jarvis/scripts/gemini-ask.sh --flash 'Question rapide'
```
**health all** — Sonde sante de tous les backends d'inference (Ollama, LM local, M1, M2)
```bash
for u in 127.0.0.1:11434/api/tags 127.0.0.1:1234/v1/models 192.168.1.85:1234/v1/models 192.168.1.26:1234/v1/models; do printf '%s ' "$u"; curl -s --max-time 2 "http://$u" >/dev/null && echo UP || echo DOWN; done
```
**index commands** — Liste les commandes 10-ia enregistrees dans la bibliotheque SQL
```bash
sqlite3 ~/jarvis/stacks/jarvis-index.db "SELECT label,cmd FROM commands WHERE dept LIKE '%ia%';"
```
**latency stats** — Statistiques de latence moyenne par backend pour arbitrer le routage
```bash
sqlite3 ~/jarvis/cowork_engine.db 'SELECT backend,COUNT(*),ROUND(AVG(latency_ms)) FROM model_usage_log GROUP BY backend;'
```
**lm local models** — Liste les modeles exposes par LM Studio local en OpenAI-compat
```bash
curl -s http://127.0.0.1:1234/v1/models | jq -r '.data[].id'
```
**lms load** — Charge un modele dans le serveur LM Studio local
```bash
~/.lmstudio/bin/lms load qwen/qwen3.5-9b
```
**lms ls** — Liste les modeles LM Studio disponibles sur disque
```bash
~/.lmstudio/bin/lms ls
```
**lms ps** — Liste les modeles LM Studio actuellement charges
```bash
~/.lmstudio/bin/lms ps
```
**lms server** — Demarre le serveur OpenAI-compat LM Studio sur :1234
```bash
~/.lmstudio/bin/lms server start --port 1234
```
**lms status** — Etat du serveur LM Studio local et du runtime
```bash
~/.lmstudio/bin/lms status
```
**lms unload** — Decharge tous les modeles LM Studio pour liberer la VRAM/RAM
```bash
~/.lmstudio/bin/lms unload --all
```
**load latency bench** — Mesure la latence d'un appel Ollama local pour le suivi de perf
```bash
t=$(date +%s%3N); curl -s http://127.0.0.1:11434/api/generate -d '{"model":"gemma3:4b","prompt":"ok","stream":false}' >/dev/null; echo "$(( $(date +%s%3N)-t )) ms"
```
**ollama gen api** — Appel direct API generate Ollama (sans stream) pour valider l'endpoint
```bash
curl -s http://127.0.0.1:11434/api/generate -d '{"model":"gemma3:4b","prompt":"ping","stream":false}' | jq -r .response
```
**ollama list** — Liste les modeles Ollama locaux avec taille et date
```bash
ollama list
```
**ollama logs** — Affiche les derniers logs Ollama pour depannage
```bash
journalctl --user -u ollama -n 50 --no-pager 2>/dev/null || tail -n 50 /tmp/ollama.log
```
**ollama port busy** — Verifie quel process occupe les ports d'inference 11434/1234
```bash
ss -ltnp | grep -E ':11434|:1234'
```
**ollama ps** — Affiche les modeles Ollama actuellement charges en memoire
```bash
ollama ps
```
**ollama pull** — Telecharge/maj un modele Ollama leger adapte au CPU M4
```bash
ollama pull gemma3:4b
```
**ollama restart** — Redemarre le serveur Ollama local en cas de blocage
```bash
systemctl --user restart ollama 2>/dev/null || pkill -f 'ollama serve'; nohup ollama serve >/tmp/ollama.log 2>&1 &
```
**ollama rm** — Supprime un modele Ollama pour liberer du disque
```bash
ollama rm qwen3:1.7b
```
**ollama run test** — Test interactif rapide d'inference sur un modele local
```bash
ollama run qwen2.5:7b 'Reponds OK en un mot'
```
**ollama up** — Verifie qu'Ollama local repond et liste les modeles installes
```bash
curl -s --max-time 3 http://127.0.0.1:11434/api/tags | jq -r '.models[].name'
```
**router task** — Routage par type de tache avec journalisation latence/backend en SQLite
```bash
bash ~/jarvis/scripts/model_router.sh reasoning 'Analyse ce bug' M4
```
**thermal gov** — Lance le gouverneur thermique proportionnel (cible 82 C) en tache de fond
```bash
setsid bash ~/jarvis/scripts/m4-thermal-governor.sh &
```
**thermal watch** — Surveille la temperature CPU pendant l'inference (M4 CPU-only)
```bash
watch -n2 'sensors 2>/dev/null | grep -iE "package|tctl" ; ollama ps'
```
**usage log** — Consulte les 20 derniers appels d'inference (latence, backend)
```bash
sqlite3 ~/jarvis/cowork_engine.db 'SELECT ts,model,backend,task_type,latency_ms FROM model_usage_log ORDER BY ts DESC LIMIT 20;'
```

## 20-automation

**backup n8n** — AVANT migration n8n
```bash
docker run --rm -v docker_jarvis-n8n-data:/d -v ~/backups:/b alpine tar czf /b/n8n-$(date +%F).tgz -C /d .
```
**browseros lire liens** — Extrait le texte et les liens d-une page (scraping leger)
```bash
browseros-cli -p "$page" read --links
```
**browseros lister onglets** — Liste les onglets/pages ouverts dans BrowserOS
```bash
browseros-cli tabs
```
**browseros ouvrir page** — Ouvre une page pilotee et recupere son identifiant pour orchestration
```bash
page=$(browseros-cli open --json https://www.education.gouv.fr | jq -r .page) ; echo $page
```
**browseros snapshot** — Capture l-etat structure de la page pour pilotage automatise
```bash
browseros-cli -p "$page" snapshot
```
**check mail imap** — Detecte les mails non lus comme declencheur de workflow
```bash
python3 -c "import imaplib,os; m=imaplib.IMAP4_SSL('imap.gmail.com'); m.login('miningexpert31@gmail.com',os.environ['IMAP_PASS']); m.select('INBOX'); print(m.search(None,'UNSEEN'))"
```
**controle secrets** — Verifie l-absence de secret en clair dans les exports/configs avant commit
```bash
gitleaks detect --no-git -s /home/pamerys/jarvis/stacks/20-automation/ -v
```
**dechiffre secret** — Dechiffre un secret du coffre (token Telegram, mot de passe IMAP)
```bash
sops -d /home/pamerys/jarvis/secrets-vault/telegram.enc.yaml
```
**delegue resume local** — Delegue le resume/classification d-une execution a un modele local (zero token)
```bash
bash /home/pamerys/jarvis/scripts/lm-ask.sh "Resume en 3 puces ce payload de workflow: $(cat /tmp/exec.json)"
```
**deploy stack auto** — Deploie/Met a jour la pile 20-automation sur le Swarm M4
```bash
docker stack deploy -c /home/pamerys/jarvis/stacks/20-automation/docker-compose.yml automation
```
**index executions** — Inspecte l-index SQLite ou tracer executions et metadonnees automatisation
```bash
sqlite3 /home/pamerys/jarvis/stacks/jarvis-index.db "SELECT name FROM sqlite_master WHERE type='table';"
```
**n8n API health** — Verifie l-API REST n8n (sonde de sante)
```bash
curl -s http://localhost:5678/healthz | jq .
```
**n8n API workflows actifs** — Liste via API les workflows actuellement actifs
```bash
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" http://localhost:5678/api/v1/workflows?active=true | jq '.data[].name'
```
**n8n audit securite** — Genere un rapport d-audit securite de l-instance n8n
```bash
docker exec jarvis-n8n n8n audit
```
**n8n batch** — Execute plusieurs workflows en une passe
```bash
docker exec jarvis-n8n n8n execute-batch --ids=<ID1,ID2>
```
**n8n copie backup hote** — Rapatrie l-export workflows sur le disque M4 et l-horodate
```bash
docker cp jarvis-n8n:/home/node/.n8n/backup-workflows.json /home/pamerys/jarvis/stacks/20-automation/backup-workflows-$(date +%F).json
```
**n8n declenche webhook** — Declenche un webhook de production n8n pour test
```bash
curl -s -X POST http://localhost:5678/webhook/<PATH> -H 'Content-Type: application/json' -d '{"source":"cli-test"}'
```
**n8n etat conteneur** — Verifie que le conteneur n8n tourne et expose bien le port 5678
```bash
docker ps --filter name=jarvis-n8n --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```
**n8n executer workflow** — Lance manuellement un workflow par son ID (test/declenchement)
```bash
docker exec jarvis-n8n n8n execute --id=<WORKFLOW_ID>
```
**n8n export credentials** — Exporte les credentials chiffres pour sauvegarde
```bash
docker exec jarvis-n8n n8n export:credentials --all --decrypted=false --output=/home/node/.n8n/backup-creds.json
```
**n8n export workflows** — Exporte tous les workflows vers un JSON de sauvegarde
```bash
docker exec jarvis-n8n n8n export:workflow --all --output=/home/node/.n8n/backup-workflows.json
```
**n8n import workflows** — Reimporte des workflows depuis un fichier JSON (restauration/migration)
```bash
docker exec jarvis-n8n n8n import:workflow --separate --input=/home/node/.n8n/backup-workflows.json
```
**n8n liste commandes** — Liste les sous-commandes CLI n8n disponibles
```bash
docker exec jarvis-n8n n8n --help
```
**n8n logs live** — Suit en direct les logs n8n (executions, erreurs, webhooks)
```bash
docker logs -f --tail 100 jarvis-n8n
```
**n8n redemarrer** — Redemarre le service d-automatisation n8n proprement
```bash
docker restart jarvis-n8n
```
**n8n stats memoire** — Mesure CPU/RAM du conteneur n8n (surveillance thermique M4)
```bash
docker stats --no-stream jarvis-n8n
```
**n8n version** — Affiche la version n8n installee (controle avant montee de version)
```bash
docker exec jarvis-n8n n8n --version
```
**notif telegram** — Notifie l-utilisateur sur Telegram en cas d-echec critique
```bash
curl -s -X POST "https://api.telegram.org/bot$(sops -d --extract '["bot_token"]' /home/pamerys/jarvis/secrets-vault/telegram.enc.yaml)/sendMessage" -d chat_id=$CHAT_ID -d text='n8n: workflow KO'
```
**portainer ouvrir** — Ouvre Portainer pour supervision graphique de la pile d-automatisation
```bash
xdg-open http://localhost:9000
```
**redis cles bull** — Liste les cles de la file Bull (jobs n8n en mode queue)
```bash
docker exec $(docker ps -qf name=jarvis_redis) redis-cli -a "$(cat /run/secrets/redis_pass)" --scan --pattern 'bull:*' | head -30
```
**redis jobs echoues** — Compte les jobs en echec a rejouer ou purger
```bash
docker exec $(docker ps -qf name=jarvis_redis) redis-cli -a "$(cat /run/secrets/redis_pass)" ZCARD bull:jobs:failed
```
**redis longueur file** — Mesure le backlog de jobs en attente dans la file Bull
```bash
docker exec $(docker ps -qf name=jarvis_redis) redis-cli -a "$(cat /run/secrets/redis_pass)" LLEN bull:jobs:wait
```
**redis ping** — Verifie la disponibilite du bus Redis (file de travail)
```bash
docker exec $(docker ps -qf name=jarvis_redis) redis-cli -a "$(cat /run/secrets/redis_pass 2>/dev/null)" ping
```
**redis purge file** — Vide la file d-attente Bull (apres incident, avec prudence)
```bash
docker exec $(docker ps -qf name=jarvis_redis) redis-cli -a "$(cat /run/secrets/redis_pass)" DEL bull:jobs:wait
```
**swarm services** — Etat des services Swarm (verifie pile jarvis/data/business autour de l-automatisation)
```bash
docker service ls
```
**trace execution sql** — Enregistre une execution de workflow dans la base de tracabilite
```bash
sqlite3 /home/pamerys/jarvis/stacks/jarvis-index.db "INSERT INTO automation_log(ts,workflow,status) VALUES(datetime('now'),'<WF>','ok');"
```

## 30-data

**audit fuite dumps** — Scanne le dossier de backups pour des secrets exposés
```bash
gitleaks detect --no-git --source ~/backups -v
```
**backup sqlite live** — Sauvegarde à chaud cohérente d'une base SQLite (rdv.db)
```bash
sqlite3 ~/jarvis/rdv.db ".backup '/home/pamerys/backups/rdv-$(date +%F).db'"
```
**backup volume pg** — Snapshot tar du volume de données PostgreSQL
```bash
docker run --rm -v data_jarvis_postgres_data:/d -v ~/backups:/b alpine tar czf /b/pg-vol-$(date +%F).tgz -C /d .
```
**chiffrer sqlite** — Chiffre une base SQLite sensible (cours) avec SQLCipher
```bash
docker run --rm -v ~/jarvis:/w -w /w nouchka/sqlcipher sh -c "sqlcipher cours.db \"PRAGMA key='clef'; ATTACH DATABASE 'cours.enc.db' AS enc KEY 'clef'; SELECT sqlcipher_export('enc'); DETACH DATABASE enc;\""
```
**connexions actives** — Liste les connexions et requêtes en cours (diagnostic blocage)
```bash
docker run --rm --network jarvis-bus -e PGPASSWORD=$PG postgres:15-alpine psql -h postgres -U jarvis -d jarvis_agents -c 'SELECT pid,usename,state,query FROM pg_stat_activity;'
```
**deploy data** — postgres
```bash
docker stack deploy -c ~/jarvis/stacks/30-data/docker-compose.yml data
```
**deploy data** — Déploie/met à jour le stack data (service postgres) sur le swarm M4
```bash
docker stack deploy -c ~/jarvis/stacks/30-data/docker-compose.yml data
```
**diag global data** — Vue d'ensemble santé du stack data (services + tâches)
```bash
docker stack services data && docker service ps data_postgres
```
**dump pg** — Sauvegarde compressée (format custom) de la base dans ~/backups
```bash
docker run --rm --network jarvis-bus -e PGPASSWORD=$PG -v ~/backups:/b postgres:15-alpine sh -c 'pg_dump -h postgres -U jarvis -Fc jarvis_agents > /b/jarvis_agents-$(date +%F).dump'
```
**déchiffrer secret** — Déchiffre le fichier de secrets infra (mots de passe Redis/Postgres)
```bash
sops -d ~/jarvis/secrets-vault/infra.enc.env
```
**export csv sqlite** — Exporte le contenu d'une base SQLite en CSV pour archivage
```bash
sqlite3 -header -csv ~/jarvis/planning.db 'SELECT * FROM sqlite_master;' > ~/backups/planning-export.csv
```
**index commandes data** — Lit les commandes cataloguées pour le département 30-data
```bash
sqlite3 ~/jarvis/stacks/jarvis-index.db "SELECT label,command FROM commands WHERE entity='30-data';"
```
**index tables** — Liste les tables du catalogue d'index (services, commands)
```bash
sqlite3 ~/jarvis/stacks/jarvis-index.db '.tables'
```
**inspect volume pg** — Affiche le point de montage et les métadonnées du volume Postgres
```bash
docker volume inspect data_jarvis_postgres_data
```
**intégrité sqlite** — Vérifie l'intégrité d'une base SQLite métier (ex. planning.db)
```bash
sqlite3 ~/jarvis/planning.db 'PRAGMA integrity_check;'
```
**inventaire sqlite** — Recense les bases SQLite de l'hôte par taille décroissante
```bash
find /home/pamerys -name '*.db' -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -30
```
**liste tables pg** — Liste les tables de la base jarvis_agents
```bash
docker run --rm --network jarvis-bus -e PGPASSWORD=$PG postgres:15-alpine psql -h postgres -U jarvis -d jarvis_agents -c '\dt'
```
**logs postgres** — Suit les logs en direct du service PostgreSQL
```bash
docker service logs -f --tail 100 data_postgres
```
**pg ready** — test postgres
```bash
docker run --rm --network jarvis-bus postgres:15-alpine pg_isready -h postgres -U jarvis -d jarvis_agents
```
**pg ready** — Teste la disponibilité de Postgres via le bus overlay (non publié)
```bash
docker run --rm --network jarvis-bus postgres:15-alpine pg_isready -h postgres -U jarvis -d jarvis_agents
```
**pinecone index stats** — Consulte les stats de l'index vectoriel Pinecone (vecteurs, namespaces)
```bash
echo 'via MCP: mcp__plugin_pinecone_pinecone__describe-index-stats (index RAG)'
```
**pinecone liste index** — Liste les index Pinecone disponibles pour le RAG
```bash
echo 'via MCP: mcp__plugin_pinecone_pinecone__list-indexes'
```
**psql** — console SQL
```bash
docker run --rm -it --network jarvis-bus -e PGPASSWORD=$PG postgres:15-alpine psql -h postgres -U jarvis jarvis_agents
```
**psql console** — Ouvre une console SQL interactive sur jarvis_agents (mot de passe déchiffré à la volée)
```bash
docker run --rm -it --network jarvis-bus -e PGPASSWORD="$(sops -d ~/jarvis/secrets-vault/infra.enc.env | grep -E '^(PG|POSTGRES_PASSWORD)=' | cut -d= -f2-)" postgres:15-alpine psql -h postgres -U jarvis jarvis_agents
```
**redeploy postgres** — Force le redéploiement de la tâche postgres (dépannage)
```bash
docker service update --force data_postgres
```
**redis ping (bus)** — Vérifie le bus Redis dont dépend la couche données
```bash
docker run --rm --network jarvis-bus redis:7-alpine redis-cli -h redis -a "$REDIS_PASSWORD" ping
```
**restore pg** — Restaure la base jarvis_agents depuis un dump (à dater)
```bash
docker run --rm --network jarvis-bus -e PGPASSWORD=$PG -v ~/backups:/b postgres:15-alpine sh -c 'pg_restore -h postgres -U jarvis -d jarvis_agents --clean /b/jarvis_agents-2026-06-28.dump'
```
**rotation secret pg** — Crée une nouvelle version du secret pg_pass pour rotation
```bash
printf '%s' "$NEW_PG_PASS" | docker secret create pg_pass_v2 - && echo 'puis mettre à jour le compose et redeploy'
```
**schéma planning** — Affiche le schéma de la base planning de la professeure
```bash
sqlite3 ~/jarvis/planning.db '.schema'
```
**service détail** — Liste les tâches du service avec nœud, état courant et erreurs éventuelles
```bash
docker service ps data_postgres --no-trunc
```
**service état** — Affiche l'état et les replicas (1/1) du service postgres
```bash
docker service ls --filter name=data_postgres
```
**shell conteneur pg** — Ouvre un shell dans le conteneur PostgreSQL pour inspection locale
```bash
docker exec -it $(docker ps -qf name=data_postgres) sh
```
**taille base pg** — Affiche la taille disque de la base jarvis_agents
```bash
docker run --rm --network jarvis-bus -e PGPASSWORD=$PG postgres:15-alpine psql -h postgres -U jarvis -d jarvis_agents -c "SELECT pg_size_pretty(pg_database_size('jarvis_agents'));"
```
**vacuum sqlite** — Compacte/défragmente une base SQLite RAG volumineuse
```bash
sqlite3 ~/jarvis/jarvis/rag_index.db 'VACUUM;'
```

## 40-voice

**Activer au boot** — Active le demarrage automatique de la pile vocale (lingering requis).
```bash
systemctl --user enable jarvis-whisper jarvis-lumen bdqt-http jarvis-vocal-health
```
**Ajouter correction phonetique** — Ajoute une regle de post-correction au pipeline BDQT.
```bash
curl -s -X POST http://127.0.0.1:8790/correction -H 'Content-Type: application/json' -d '{"wrong":"des cole","right":"ecole"}'
```
**Benchmark qualite** — Mesure le WER/qualite de transcription sur le jeu de test.
```bash
python3 /home/pamerys/jarvis/scripts/transcription/bdqt_bench.py
```
**Bus redis vocal** — Teste le bus jarvis et ecoute les evenements vocaux publies.
```bash
redis-cli -h 127.0.0.1 PING && redis-cli -h 127.0.0.1 SUBSCRIBE voice.events
```
**Compter dataset vocal** — Compte les echantillons wav disponibles pour l'entrainement.
```bash
ls /home/pamerys/jarvis/voice_dataset/wav/*.wav | wc -l
```
**Convertir audio 16kHz mono** — Normalise un audio en 16kHz mono PCM, format attendu par Whisper.
```bash
ffmpeg -y -i /tmp/in.m4a -ar 16000 -ac 1 -c:a pcm_s16le /tmp/in16k.wav
```
**Demarrer pile vocale** — Lance Whisper STT, hub Lumen, BDQT et le moniteur de sante.
```bash
systemctl --user start jarvis-whisper jarvis-lumen bdqt-http jarvis-vocal-health
```
**Espace disque dataset** — Surveille l'occupation disque du dataset, modeles et logs vocaux.
```bash
du -sh /home/pamerys/jarvis/voice_dataset /home/pamerys/jarvis/models/piper /home/pamerys/jarvis/voice_logs
```
**Extraire audio dataset** — Decoupe/extrait les segments audio pour le dataset vocal.
```bash
python3 /home/pamerys/jarvis/scripts/transcription/bdqt_extract_audio.py
```
**Fine-tune BDQT** — Lance l'affinage du modele/lexique sur le dataset voix.
```bash
python3 /home/pamerys/jarvis/scripts/transcription/bdqt_finetune.py
```
**Generer prompt initial Whisper** — Produit l'initial_prompt enrichi (hotwords) pour Whisper.
```bash
python3 /home/pamerys/jarvis/scripts/transcription/bdqt_gen_prompt.py
```
**Health BDQT** — Verifie la base qualite (lexique/corrections/log) du microservice BDQT :8790.
```bash
curl -s http://127.0.0.1:8790/health | python3 -m json.tool
```
**Health Lumen** — Confirme que le token-server Lumen repond (ok=true).
```bash
curl -s http://127.0.0.1:8788/health
```
**Health monitor failover** — Controle le moniteur de failover STT M1/M2/M3.
```bash
journalctl --user -u jarvis-vocal-health.service -n 50 --no-pager
```
**Importer corrections** — Importe en masse des corrections dans la base qualite.
```bash
python3 /home/pamerys/jarvis/scripts/transcription/bdqt_import_corrections.py
```
**Lexique metier BDQT** — Affiche les hotwords/termes scolaires injectes dans Whisper.
```bash
sqlite3 /home/pamerys/IA/Core/jarvis/db/transcription_quality.db 'SELECT term,weight FROM lexicon ORDER BY weight DESC LIMIT 30;'
```
**Lire le wav TTS** — Decode et joue le rendu vocal Piper sur la sortie audio.
```bash
ffmpeg -i /tmp/tts_test.wav -f wav - 2>/dev/null | aplay -q
```
**Logs Lumen hub** — Affiche les logs du hub de routage STT/TTS/LLM Lumen.
```bash
journalctl --user -u jarvis-lumen.service -n 100 --no-pager
```
**Logs Whisper live** — Suit en direct les logs du STT pour diagnostiquer une transcription.
```bash
journalctl --user -u jarvis-whisper.service -f -n 80
```
**Logs widget vocal** — Inspecte les logs du widget de dictee (Alt+X).
```bash
tail -n 60 /home/pamerys/jarvis/logs/voice_widget.log
```
**Modeles LM Studio** — Liste les modeles LM Studio disponibles en fallback de routage.
```bash
curl -s http://127.0.0.1:1234/v1/models | python3 -m json.tool | head -30
```
**Modeles Ollama dispo** — Liste les LLM locaux mobilisables par le hub Lumen pour le post-traitement vocal.
```bash
curl -s http://127.0.0.1:11434/api/tags | python3 -c 'import sys,json;[print(m["name"]) for m in json.load(sys.stdin)["models"]]'
```
**Ports vocaux ouverts** — Verifie que Whisper, Lumen, BDQT et la PWA ecoutent bien.
```bash
ss -tlnp | grep -E ':(8789|8788|8790|7777)'
```
**Reconstruire le lexique** — Regenere le lexique BDQT a partir des corpus scolaires/famille.
```bash
python3 /home/pamerys/jarvis/scripts/transcription/bdqt_build_lexicon.py
```
**Redemarrer Whisper** — Relance le serveur faster-whisper persistant sur :8789.
```bash
systemctl --user restart jarvis-whisper.service
```
**Reload daemon user** — Recharge les unites systemd apres edition d'un service vocal.
```bash
systemctl --user daemon-reload
```
**Sauvegarde base qualite** — Backup coherent SQLite de la base qualite de transcription.
```bash
sqlite3 /home/pamerys/IA/Core/jarvis/db/transcription_quality.db ".backup '/home/pamerys/jarvis/backups/bdqt_$(date +%F).db'"
```
**Sauvegarde modeles Piper** — Archive les modeles TTS Piper et leur config json.
```bash
tar czf /home/pamerys/jarvis/backups/piper_$(date +%F).tar.gz -C /home/pamerys/jarvis/models piper
```
**Secrets Lumen** — Verifie la presence des tokens du hub Lumen sans exposer les valeurs.
```bash
sops -d /home/pamerys/jarvis/secrets-vault/secrets.env 2>/dev/null | grep -i -E 'token|key' | sed 's/=.*/=***/'
```
**Stats BDQT (SQLite)** — Liste les tables de la base qualite de transcription.
```bash
sqlite3 /home/pamerys/IA/Core/jarvis/db/transcription_quality.db 'SELECT name FROM sqlite_master WHERE type="table";'
```
**Statut services voix** — Etat des 4 services du departement vocal en un coup d'oeil.
```bash
systemctl --user status jarvis-whisper jarvis-lumen bdqt-http jarvis-vocal-health --no-pager
```
**Synthese TTS Piper** — Genere un wav vocal francais avec le modele Piper siwis.
```bash
echo 'Bonjour, la classe va bien commencer.' | /home/pamerys/.local/bin/piper -m /home/pamerys/jarvis/models/piper/fr_FR-siwis-medium.onnx -f /tmp/tts_test.wav
```
**Test STT Whisper** — Envoie un wav d'exemple au STT et recupere la transcription.
```bash
curl -s -X POST http://127.0.0.1:8789/transcribe -F 'file=@/home/pamerys/jarvis/voice_dataset/wav/voice_00220.wav' -F 'language=fr'
```

## 50-business

**Backup images registry** — Exporte les images vitrines en archive pour restauration hors-ligne
```bash
docker save localhost:5000/50-business/alkymia-site:latest localhost:5000/50-business/delmas-site:latest | gzip > ~/backups/business-images-$(date +%F).tgz
```
**Backup sources sites** — Archive les sources des deux sites avant mise en production
```bash
tar czf ~/backups/business-sites-$(date +%F).tgz -C /home/pamerys alkymia-communication/site-v2 jarvis-delmas-site
```
**Build+push alkymia** — Construit et publie l'image vitrine alkymia sur le registry prive
```bash
docker build -t localhost:5000/50-business/alkymia-site:latest /home/pamerys/alkymia-communication/site-v2 && docker push localhost:5000/50-business/alkymia-site:latest
```
**Build+push delmas** — Construit et publie l'image site franckdelmas.dev sur le registry prive
```bash
docker build -t localhost:5000/50-business/delmas-site:latest /home/pamerys/jarvis-delmas-site && docker push localhost:5000/50-business/delmas-site:latest
```
**Catalog registry** — Liste les depots d'images presents dans le registry prive
```bash
curl -s --max-time 5 http://127.0.0.1:5000/v2/_catalog
```
**Deploy sites** — Deploie/met a jour les vitrines alkymia + delmas depuis la compose
```bash
docker stack deploy -c ~/jarvis/stacks/50-business/docker-compose.yml business --with-registry-auth
```
**Diff sources delmas** — Verifie les modifications non commitees et l'historique du site delmas
```bash
git -C /home/pamerys/jarvis-delmas-site status -s && git -C /home/pamerys/jarvis-delmas-site log --oneline -5
```
**Etat stack business** — Liste les services du stack business avec replicas et ports
```bash
docker stack services business
```
**Health alkymia** — Verifie que la vitrine alkymia repond bien en HTTP 200
```bash
curl -s -o /dev/null -w '%{http_code}\n' --max-time 4 http://127.0.0.1:8086/
```
**Health delmas** — Verifie que le site delmas repond bien en HTTP 200
```bash
curl -s -o /dev/null -w '%{http_code}\n' --max-time 4 http://127.0.0.1:8085/
```
**Index SQL business** — Consulte la bibliotheque de commandes du departement business
```bash
sqlite3 ~/jarvis/stacks/jarvis-index.db "SELECT * FROM commands WHERE entity LIKE '%business%'"
```
**Inspect ports alkymia** — Affiche le mapping de ports publie du service alkymia
```bash
docker service inspect business_alkymia-site --format '{{json .Endpoint.Ports}}'
```
**Lecture compose** — Affiche la definition Swarm des services business (source de verite)
```bash
cat ~/jarvis/stacks/50-business/docker-compose.yml
```
**Logs alkymia (suivi)** — Suit en direct les logs nginx de la vitrine alkymia
```bash
docker service logs -f --tail 100 business_alkymia-site
```
**Logs delmas (suivi)** — Suit en direct les logs nginx du site delmas
```bash
docker service logs -f --tail 100 business_delmas-site
```
**Nettoyage images obsoletes** — Libere l'espace des images intermediaires apres les builds de sites
```bash
docker image prune -f && docker builder prune -f
```
**Portainer UI** — Ouvre Portainer pour piloter graphiquement les services business
```bash
xdg-open http://127.0.0.1:9000 2>/dev/null || echo 'http://127.0.0.1:9000'
```
**Redemarrage force alkymia** — Recree les taches du service alkymia sans changer l'image (depannage)
```bash
docker service update --force business_alkymia-site
```
**Redemarrage force delmas** — Recree les taches du service delmas sans changer l'image (depannage)
```bash
docker service update --force business_delmas-site
```
**Restore image** — Recharge les images vitrines sauvegardees dans le daemon Docker
```bash
docker load < ~/backups/business-images-$(date +%F).tgz
```
**Rollback service** — Revient a la version precedente du service alkymia en cas d'echec deploy
```bash
docker service rollback business_alkymia-site
```
**Scale alkymia** — Ajuste le nombre de replicas de la vitrine alkymia (montee en charge)
```bash
docker service scale business_alkymia-site=2
```
**Secret registry/infra** — Dechiffre les secrets (auth registry, bus) necessaires aux deploiements
```bash
sops -d ~/jarvis/secrets-vault/infra.enc.env
```
**Suppression stack** — Retire entierement le stack business (maintenance/reset avant redeploy)
```bash
docker stack rm business
```
**Taches alkymia** — Detaille l'etat/erreurs des taches du service alkymia
```bash
docker service ps --no-trunc business_alkymia-site
```
**Taches delmas** — Detaille l'etat/erreurs des taches du service delmas
```bash
docker service ps --no-trunc business_delmas-site
```
**Tags image alkymia** — Liste les tags publies de l'image alkymia dans le registry
```bash
curl -s --max-time 5 http://127.0.0.1:5000/v2/50-business/alkymia-site/tags/list
```
**Tags image delmas** — Liste les tags publies de l'image delmas dans le registry
```bash
curl -s --max-time 5 http://127.0.0.1:5000/v2/50-business/delmas-site/tags/list
```
**Test image en local** — Lance l'image alkymia en local sur :8099 pour validation avant deploy
```bash
docker run --rm -p 8099:80 localhost:5000/50-business/alkymia-site:latest
```
**Update alkymia (rolling)** — Force la mise a jour rolling du service alkymia avec la derniere image
```bash
docker service update --image localhost:5000/50-business/alkymia-site:latest --with-registry-auth business_alkymia-site
```
**Update delmas (rolling)** — Force la mise a jour rolling du service delmas avec la derniere image
```bash
docker service update --image localhost:5000/50-business/delmas-site:latest --with-registry-auth business_delmas-site
```
**Verif reseau bus** — Confirme que les conteneurs business sont bien attaches au reseau jarvis-bus
```bash
docker network inspect jarvis-bus --format '{{range .Containers}}{{.Name}} {{end}}'
```
**Vue globale Swarm** — Affiche tous les stacks et services live du Swarm M4
```bash
docker stack ls && docker service ls
```
**build+push site** — app->image->registry
```bash
docker build -t localhost:5000/50-business/<nom>:latest <dir> && docker push localhost:5000/50-business/<nom>:latest
```
**deploy sites** — alkymia+delmas
```bash
docker stack deploy -c ~/jarvis/stacks/50-business/docker-compose.yml business --with-registry-auth
```

## 90-secrets-git

**audit -> rapport** — Execute l'audit et archive le rapport date dans le dossier reports du departement.
```bash
bash ~/jarvis/scripts/sec-audit.sh | tee ~/jarvis/stacks/90-secrets-git/reports/audit-$(date +%F-%H%M).log
```
**audit gh auth** — Verifie l'etat d'authentification GitHub et les scopes du token avant operations distantes.
```bash
gh auth status 2>&1 | grep -E 'Logged in|Token scopes'
```
**audit red-team** — Lance l'audit reproductible (lecture seule, valeurs masquees) : LUKS, .env clairs, cles SSH, secrets commites.
```bash
bash ~/jarvis/scripts/sec-audit.sh
```
**backup cle hors-ligne** — Sauvegarde la cle age sur support externe (irrecuperable si perdue) puis verrouille les perms.
```bash
cp ~/.config/sops/age/keys.txt /media/$USER/USB/age-keys-$(date +%F).txt && chmod 600 /media/$USER/USB/age-keys-$(date +%F).txt
```
**chercher tokens clairs** — Recherche manuelle de tokens/cles en clair hors fichiers chiffres.
```bash
grep -rIlE 'ghp_[A-Za-z0-9]{20,}|api[_-]?key=|password=' ~/jarvis --exclude-dir=.git --exclude='*.enc.env'
```
**chiffrer nouveau fichier** — Chiffre in-place un fichier en suivant les creation_rules du .sops.yaml.
```bash
SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt sops -e -i ~/jarvis/secrets-vault/nouveau.enc.env
```
**cles SSH sans passphrase** — Liste les cles SSH privees sans passphrase (a corriger).
```bash
for k in ~/.ssh/id_*; do [[ $k == *.pub ]] && continue; ssh-keygen -y -P '' -f "$k" >/dev/null 2>&1 && echo "NUE: $k"; done
```
**dechiffrer backup fuite** — Consulte le backup chiffre des repos ayant fuite pour traitement d'incident.
```bash
SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt sops -d ~/jarvis/secrets-vault/leaked-repos-backup.enc
```
**derniers commits secrets** — Trace l'historique recent des modifications du coffre pour audit.
```bash
git -C ~/jarvis log --oneline -10 -- secrets-vault/
```
**diff vs audit avant** — Compare l'etat de securite actuel a l'instantane de reference sec-audit-AVANT.txt.
```bash
diff <(bash ~/jarvis/scripts/sec-audit.sh) ~/jarvis/scripts/sec-audit-AVANT.txt
```
**durcir .env trouves** — Restreint a 600 tout fichier .env en clair detecte par l'audit.
```bash
find ~ -maxdepth 4 -name '*.env' ! -name '*.enc.env' -exec chmod 600 {} \; -print
```
**durcir cle age** — Restreint la cle privee age au seul proprietaire (correctif si perms trop ouvertes).
```bash
chmod 600 ~/.config/sops/age/keys.txt
```
**editer secret** — Ouvre l'editeur sur un secret : edition en clair en RAM, re-chiffrement automatique a la sauvegarde.
```bash
SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt sops ~/jarvis/secrets-vault/infra.enc.env
```
**empreinte cle publique** — Affiche la cle publique age associee (a comparer au destinataire du .sops.yaml).
```bash
age-keygen -y ~/.config/sops/age/keys.txt
```
**fichiers traques sensibles** — Detecte un fichier sensible deja versionne par erreur (doit ne rien renvoyer).
```bash
git -C ~/jarvis ls-files | grep -E '\.env$|keys\.txt|\.key$|credentials'
```
**gitleaks via docker** — Alternative conteneurisee si le binaire n'est pas installe.
```bash
docker run --rm -v ~/jarvis:/repo zricethezav/gitleaks:latest detect -s /repo --no-banner --redact
```
**hook pre-commit** — Installe un hook pre-commit qui bloque tout commit contenant un secret.
```bash
printf '#!/usr/bin/env bash\ngitleaks protect --staged --redact --no-banner || { echo "FUITE detectee, commit bloque"; exit 1; }\n' > ~/jarvis/.git/hooks/pre-commit && chmod +x ~/jarvis/.git/hooks/pre-commit
```
**injecter REDIS_PASSWORD** — Charge le mot de passe Redis depuis le coffre dans l'environnement pour une commande ponctuelle.
```bash
export REDIS_PASSWORD=$(SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt sops -d ~/jarvis/secrets-vault/infra.enc.env | grep -E '^REDIS_PASSWORD=' | cut -d= -f2-)
```
**inspect secret (meta)** — Affiche les metadonnees d'un docker secret sans en reveler la valeur.
```bash
docker secret inspect pg_pass --format '{{.Spec.Name}} cree {{.CreatedAt}}'
```
**installer gitleaks** — Installe le binaire gitleaks (actuellement MANQUANT sur M4) dans ~/.local/bin.
```bash
curl -sSL https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_linux_x64.tar.gz | tar -xz -C ~/.local/bin gitleaks && gitleaks version
```
**inventaire commandes SQL** — Consulte la bibliotheque SQL des commandes du departement secrets (protocole SQL avant compute).
```bash
sqlite3 ~/jarvis/stacks/jarvis-index.db "SELECT label,cmd FROM commands WHERE stack LIKE '%secret%';"
```
**lire secret coffre** — Dechiffre et affiche un fichier du coffre (a piper, ne pas logger).
```bash
SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt sops -d ~/jarvis/secrets-vault/secrets.enc.env
```
**lister docker secrets** — Liste les secrets Swarm provisionnes (redis_pass, pg_pass) avec dates de creation.
```bash
docker secret ls
```
**push sur GO** — Pousse vers github.com/Turbo31150/jarvis-m4-core APRES validation explicite (jamais automatique).
```bash
git -C ~/jarvis push origin sites-2026-refonte
```
**qui consomme pg_pass** — Identifie les services Swarm montant le secret pg_pass avant toute rotation.
```bash
docker service ls -q | xargs -I{} docker service inspect {} --format '{{.Spec.Name}} {{range .Spec.TaskTemplate.ContainerSpec.Secrets}}{{.SecretName}} {{end}}' | grep pg_pass
```
**revue avant GO push** — Affiche etat et diff stage pour la revue manuelle avant d'autoriser le push (branche sites-2026-refonte).
```bash
git -C ~/jarvis status -s && git -C ~/jarvis diff --staged --stat
```
**rotation cle redis-pass** — Cree un nouveau docker secret redis_pass_v2 depuis la valeur du coffre (rotation sans exposer la valeur).
```bash
SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt sops -d ~/jarvis/secrets-vault/infra.enc.env | grep -E '^REDIS_PASSWORD=' | cut -d= -f2- | docker secret create redis_pass_v2 -
```
**scan repo gitleaks** — Scanne tout l'historique du repo jarvis a la recherche de secrets (valeurs masquees).
```bash
gitleaks detect --source ~/jarvis --no-banner --redact -v
```
**scan staging (pre-push)** — Verifie les changements en staging AVANT commit/push : bloque si secret detecte.
```bash
gitleaks protect --staged --source ~/jarvis --no-banner --redact
```
**verif aucun clair stage** — Garde-fou : refuse de pousser si un .env, une cle ou keys.txt est stage.
```bash
git -C ~/jarvis diff --staged --name-only | grep -E '\.env$|keys\.txt|\.key$' && echo 'STOP secret en clair' || echo 'OK rien en clair'
```
**verif cle age perms** — Verifie que la cle privee age est bien en 600 et appartient a pamerys.
```bash
stat -c '%a %U %n' ~/.config/sops/age/keys.txt
```
**verif gitignore coffre** — Confirme que *.env/*.key/keys.txt sont ignores et que seuls *.enc.env passent.
```bash
cd ~/jarvis/secrets-vault && git check-ignore -v secrets.enc.env keys.txt test.env 2>&1; cat .gitignore
```
**verif integrite coffre** — Teste que chaque fichier du coffre est dechiffrable avec la cle courante (detecte corruption/rotation cle).
```bash
for f in ~/jarvis/secrets-vault/*.enc.env; do SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt sops -d "$f" >/dev/null 2>&1 && echo "OK $f" || echo "KO $f"; done
```
**verif sops.yaml** — Controle les creation_rules et la cle age destinataire utilisee pour chiffrer.
```bash
cat ~/jarvis/secrets-vault/.sops.yaml
```

## global

**etat** — vue globale
```bash
docker stack ls; docker service ls
```
**index sql** — cette bibliotheque
```bash
sqlite3 ~/jarvis/stacks/jarvis-index.db ".tables"
```

## pamerys-ecole

**Activer webapp au boot** — Assure le demarrage automatique de la PWA au login.
```bash
systemctl --user enable jarvis-webapp.service && systemctl --user daemon-reload
```
**Ajouter un RDV** — Cree un rendez-vous via l'API rdv.
```bash
curl -s -X POST http://127.0.0.1:7777/api/rdv -H 'Content-Type: application/json' -d '{"titre":"RDV parents Lucas","date":"2026-07-02","heure_debut":"17:00","heure_fin":"17:20","type":"parents"}'
```
**Ajouter un cours** — Cree une entree d'emploi du temps via l'API planning.
```bash
curl -s -X POST http://127.0.0.1:7777/api/planning -H 'Content-Type: application/json' -d '{"jour":"lundi","heure":"08:30","duree":"45min","titre":"Lecture CP","salle":"Classe 2"}'
```
**Ajouter une tache** — Cree une tache via l'API todo.
```bash
curl -s -X POST http://127.0.0.1:7777/api/todo -H 'Content-Type: application/json' -d '{"titre":"Preparer eval maths","categorie":"ecole","priorite":"haute","deadline":"2026-07-01"}'
```
**Cocher tache faite** — Marque la tache 1 comme terminee.
```bash
curl -s -X PATCH http://127.0.0.1:7777/api/todo/1 -H 'Content-Type: application/json' -d '{"statut":"done"}'
```
**Cours du jour (SQL)** — Affiche les cours programmes par creneau horaire.
```bash
sqlite3 -box /home/pamerys/jarvis/planning.db "SELECT heure,duree,titre,salle FROM cours WHERE lower(jour)=lower(strftime('%w','now')) ORDER BY heure;"
```
**Dictee vocale RDV/note** — Envoie un enregistrement audio a transcrire (Whisper) pour saisie a la voix.
```bash
curl -s -X POST http://127.0.0.1:7777/api/voice-record -F audio=@/tmp/note.wav | python3 -m json.tool
```
**Etat n8n** — Verifie que le conteneur n8n (automatisations) tourne.
```bash
docker ps --filter name=n8n --format '{{.Names}} {{.Status}} {{.Ports}}'
```
**Etat service webapp** — Verifie que la PWA gestion-journee tourne (actif/inactif, PID, erreurs).
```bash
systemctl --user status jarvis-webapp.service
```
**Export RDV CSV** — Exporte tous les rendez-vous au format CSV pour archive/partage.
```bash
sqlite3 -header -csv /home/pamerys/jarvis/rdv.db 'SELECT * FROM rdv ORDER BY date;' > ~/jarvis/backups/rdv_$(date +%F).csv && echo exporte
```
**Health PWA** — Teste l'endpoint de statut de la webapp et formate le JSON.
```bash
curl -s http://127.0.0.1:7777/api/status | python3 -m json.tool
```
**Integrite SQLite** — Controle l'integrite des 4 bases du poste enseignant.
```bash
for d in planning rdv todo notes; do echo "== $d =="; sqlite3 /home/pamerys/jarvis/$d.db 'PRAGMA integrity_check;'; done
```
**Inventaire bases** — Verifie les tables presentes dans les bases scolaires/familiales.
```bash
sqlite3 /home/pamerys/jarvis/planning.db '.tables'; sqlite3 /home/pamerys/jarvis/rdv.db '.tables'; sqlite3 /home/pamerys/jarvis/todo.db '.tables'
```
**Lancer widget vocal** — Demarre le widget de dictee vocale (Alt+X) pour saisie mains-libres.
```bash
DISPLAY=:0 python3 /home/pamerys/jarvis/scripts/voice_widget.py &
```
**Liste RDV API** — Liste les rendez-vous (parents/reunions/famille) via l'API.
```bash
curl -s http://127.0.0.1:7777/api/rdv | python3 -m json.tool
```
**Liste to-do** — Affiche les taches/preparations de classe en cours.
```bash
curl -s http://127.0.0.1:7777/api/todo | python3 -m json.tool
```
**Lister fiches de cours** — Inventorie les fiches de cours du dossier Documents/Cours.
```bash
find /home/pamerys/Documents/Cours -type f \( -name '*.pdf' -o -name '*.docx' -o -name '*.odt' \) | sort
```
**Logs n8n** — Consulte les derniers logs n8n pour depanner un workflow.
```bash
docker logs --tail 50 jarvis-n8n
```
**Logs webapp live** — Suit en direct les logs du backend Flask :7777/:8443.
```bash
journalctl --user -u jarvis-webapp.service -f -n 50
```
**Notes recentes (SQL)** — Affiche les 10 dernieres notes pedagogiques saisies.
```bash
sqlite3 -box /home/pamerys/jarvis/notes.db 'SELECT * FROM notes ORDER BY rowid DESC LIMIT 10;'
```
**Ouvrir PWA navigateur** — Ouvre le tableau de bord gestion-journee dans le navigateur.
```bash
DISPLAY=:0 xdg-open http://127.0.0.1:7777/ &
```
**Planning du jour** — Recupere l'emploi du temps des cours via l'API REST.
```bash
curl -s http://127.0.0.1:7777/api/planning | python3 -m json.tool
```
**Ports services ecole** — Verifie d'un coup que webapp, HTTPS, Whisper et n8n ecoutent.
```bash
ss -tlnp 2>/dev/null | grep -E ':7777|:8443|:8789|:5678'
```
**RDV du jour (SQL)** — Liste directe des rendez-vous d'aujourd'hui depuis la base.
```bash
sqlite3 -box /home/pamerys/jarvis/rdv.db "SELECT heure_debut,titre,type FROM rdv WHERE date=date('now') ORDER BY heure_debut;"
```
**Redaction Gemini** — Redige un courrier parents via Gemini OAuth (zero cout).
```bash
bash ~/jarvis/scripts/gemini-ask.sh "Redige un mot aux parents pour annoncer une sortie scolaire jeudi"
```
**Redemarrer webapp** — Relance la PWA gestion-journee apres modif de server.py ou incident.
```bash
systemctl --user restart jarvis-webapp.service
```
**Restaurer une base** — Restaure rdv.db depuis la sauvegarde du jour et relance la webapp.
```bash
cp ~/jarvis/backups/ecole_$(date +%F)/rdv.db /home/pamerys/jarvis/rdv.db && systemctl --user restart jarvis-webapp.service
```
**Resume cours (local)** — Genere un resume pedagogique via modele local (zero token).
```bash
bash ~/jarvis/scripts/lm-ask.sh "Resume en 5 points pour des CE1 ce texte: $(cat ~/Documents/Cours/Fiches-cours/*.txt 2>/dev/null | head -c 4000)"
```
**Rituel matin n8n** — Declenche le workflow n8n du rituel matinal (planning + RDV du jour).
```bash
curl -s -X POST http://127.0.0.1:5678/webhook/assistant-matin | python3 -m json.tool
```
**Sauvegarde quotidienne** — Sauvegarde a chaud les bases scolaires/familiales du jour.
```bash
mkdir -p ~/jarvis/backups/ecole_$(date +%F) && for d in planning rdv todo notes; do sqlite3 /home/pamerys/jarvis/$d.db ".backup '$HOME/jarvis/backups/ecole_$(date +%F)/$d.db'"; done && echo OK
```
**Supprimer un RDV** — Supprime le rendez-vous d'identifiant 1.
```bash
curl -s -X DELETE http://127.0.0.1:7777/api/rdv/1
```
**Taches urgentes (SQL)** — Liste les preparations non terminees triees par echeance.
```bash
sqlite3 -box /home/pamerys/jarvis/todo.db "SELECT priorite,titre,deadline FROM todo WHERE statut!='done' ORDER BY deadline;"
```
**Test HTTPS Android** — Verifie le port HTTPS :8443 (PWA installable offline sur telephone).
```bash
curl -sk https://127.0.0.1:8443/manifest.json
```
**Test Whisper STT** — Verifie que le serveur de dictee Whisper :8789 repond.
```bash
curl -s http://127.0.0.1:8789/health || curl -sk https://127.0.0.1:8789/health
```

## registry

**catalog** — images du registry prive
```bash
curl -s --max-time 5 http://127.0.0.1:5000/v2/_catalog
```

## secrets

**audit** — red-team reproductible
```bash
bash ~/jarvis/scripts/sec-audit.sh
```
**coffre** — editer un secret chiffre
```bash
sops ~/jarvis/secrets-vault/<fichier>.enc.env
```
