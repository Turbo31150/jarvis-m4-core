# ORGANIGRAMME-AGENTS-M4

> **Entreprise virtuelle Jarvis-M4** — Modelisation de l'infrastructure du poste M4 (hostname `pamerys-m4`, Docker Swarm manager Leader) sous forme d'organigramme d'entreprise. Chaque "departement" est un agent-employe specialise, pilote par la Direction Pamerys.
> Cluster LLM de support : **M1** `192.168.1.85:1234` / **M2** `192.168.1.26:1234` / **OL1** `127.0.0.1:11434`.

---

## 1. Organigramme visuel

```
                          ┌─────────────────────────────────────────┐
                          │           DIRECTION PAMERYS              │
                          │  (Franck/Pamerys — Prof. des ecoles)     │
                          │  Decisions archi · debug critique · GO   │
                          └────────────────────┬────────────────────┘
                                               │
          ┌──────────────┬──────────────┬──────┼──────────────┬──────────────┬──────────────┐
          │              │              │      │              │              │              │
   ┌──────┴──────┐┌──────┴──────┐┌──────┴──────┐┌─────┴──────┐┌──────┴──────┐┌──────┴──────┐┌──────┴───────┐
   │  00-INFRA   ││   10-IA     ││20-AUTOMATION││  30-DATA   ││  40-VOICE   ││ 50-BUSINESS ││90-SECRETS-GIT│
   │  DSI/Socle  ││ LLMOps      ││ Operations  ││ Archiviste ││ Standardiste││ Webmaster   ││ RSSI/Coffre  │
   │  Technique  ││ Inference   ││ Automation  ││ Donnees    ││ Vocal STT/TTS││ DevOps Sites││ Securite SI  │
   └──────┬──────┘└─────────────┘└─────────────┘└────────────┘└─────────────┘└─────────────┘└──────────────┘
          │
          │  SOCLE TRANSVERSE (dont dependent tous les departements)
          │  • Docker Swarm (manager pamerys-m4)   • Bus Redis jarvis-bus :6379
          │  • Registry prive :5000               • Portainer :9000
          │  • Secrets sops+age / docker secrets
          │
          └───────────────────────────────────────────────────────────────────────────┐
                                                                                        │
                                                              ┌─────────────────────────┴─────────────────────────┐
                                                              │            ESPACE PERSONNEL PAMERYS                 │
                                                              │   (pamerys-ecole — Prof. des ecoles + Famille)     │
                                                              │   PWA gestion-journee :7777/:8443 · Dictee vocale  │
                                                              │   Planning · RDV · To-do · Notes · Rituel matin    │
                                                              └────────────────────────────────────────────────────┘

  Hierarchie fonctionnelle :  50-business & 20-automation  ──reportent──▶  00-infra (reseau/registry)
                              30-data & 00-infra & 40-voice ──secrets───▶  90-secrets-git (coffre/GO push)
                              tous les departements         ──inference─▶  10-ia (endpoints LLM zero-token)
```

---

## 2. Fiches employes-departements

### 00-INFRA — DSI / Responsable Services Generaux & Socle Technique
**Profil :** Platform/Infra Engineer. Garant du coeur du systeme M4 : disponibilite, sauvegarde, securite et observabilite du socle dont dependent toutes les autres entites.

| | |
|---|---|
| **Outils** | docker swarm/stack/service/secret · redis-cli · registry API v2 (curl) · portainer-ce · sops · age · sqlite3 (jarvis-index.db) · gitleaks · tar |
| **Ports / Endpoints** | Redis `127.0.0.1:6379` (host-only) · Registry `:5000` · Portainer `:9000` · overlay `jarvis-bus` |

**Responsabilites cles :**
- Maintenir le cluster Swarm (etat noeuds, drain, rotation tokens de join).
- Deployer/MAJ la stack socle `jarvis` (redis + registry + portainer).
- Exploiter le bus Redis (sante, ping authentifie, memoire, persistance AOF).
- Administrer le registry prive (catalogue, tags, garbage collection).
- Gerer les secrets (coffre sops+age, docker secrets `redis_pass`/`pg_pass`, audit gitleaks).
- Sauvegarder les volumes critiques (registry_data, redis_data, portainer_data) + tester restauration.
- Maintenir l'index SQLite `jarvis-index.db` (source de verite organigramme + commandes).
- Controler reseau (overlay jarvis-bus, exposition host-only Redis) et inventaire des ports.

---

### 10-IA — Ingenieur Atelier IA / Inference (LLMOps)
**Profil :** Responsable du routeur multi-LLM et de l'inference locale-cloud **zero-token** sur M4. Objectif : qualite maximale a cout 0 token facture, escalade vers Opus uniquement pour archi/debug critique.

| | |
|---|---|
| **Outils** | ollama · LM Studio + lms CLI · lm-ask.sh (cascade M1+M2 parallele) · gemini-ask.sh (OAuth Google One) · model_router.sh · curl/jq · m4-thermal-governor.sh · sqlite3 (cowork_engine.db) |
| **Ports / Endpoints** | Ollama `:11434` · LM Studio local `:1234` · cluster M1 `192.168.1.85:1234` · M2 `192.168.1.26:1234` · cloud `ollama.com` (gpt-oss:120b, 0 token) |

**Responsabilites cles :**
- Operer le routeur multi-LLM (choix backend selon tache, latence, thermique).
- Maintenir l'inference M4 solo (Ollama CPU) avec fallback cloud quand le cluster est down.
- Verifier sante/latence des endpoints OpenAI-compat et basculer automatiquement.
- Charger/decharger modeles (lms CLI, ollama pull/run/rm).
- Surveiller VRAM/RAM/thermique (M4 CPU-only, plafond **82-95 C**), privilegier modeles legers.
- Journaliser l'usage (`model_usage_log` dans cowork_engine.db), auditer latences/backends.
- Servir automation/voice/data/business en endpoints d'inference + extractions JSON.
- Gerer/sauvegarder le cache modeles Ollama, depanner backends KO/timeouts/ports occupes.

---

### 20-AUTOMATION — Bureau des Operations & Automatisation
**Profil :** Operations Officer. Transforme les demandes (mail, message, evenement planning PWA, RDV) en taches automatisees fiables, tracees et sauvegardees. **SLA :** workflows actifs sains, executions sans backlog, sauvegarde quotidienne.

| | |
|---|---|
| **Outils** | n8n CLI + REST API · docker/docker service · redis-cli (file Bull) · browseros-cli · docker secrets · sops+age · postgres · sqlite3 · IMAP · Telegram Bot API · curl/jq · ollama/LM Studio · gitleaks · portainer |
| **Ports / Endpoints** | n8n `:5678` (healthz, webhooks, API v1) · Redis bus `:6379` (file `bull:*`) · Portainer `:9000` · PWA `:7777` |

**Responsabilites cles :**
- Maintenir `jarvis-n8n` en sante (etat, restart, logs, RAM).
- Concevoir/importer/exporter/versionner les workflows (planning, RDV, mail, business).
- Activer/desactiver workflows + audit securite (`n8n audit`).
- Exploiter webhooks de prod, tester via execute / execute-batch.
- Surveiller/purger la file Redis/Bull (jobs en attente, jobs echoues).
- Orchestrer taches navigateur via browseros-cli (scraping, formulaires).
- Brancher declencheurs externes (IMAP mail, Telegram) sur les workflows.
- Deleguer tout calcul/resume/classification aux modeles locaux (zero token).
- Sauvegarder workflows + credentials + base n8n, controler fuites (gitleaks/sops).
- Notifier l'utilisateur (Telegram) en cas d'echec critique.

---

### 30-DATA — Archiviste / Responsable des donnees et de l'index
**Profil :** Data & Index Steward. Garant unique des donnees structurees M4. **Regle d'or :** ne publie **jamais** Postgres sur le reseau host ; tout acces passe par un conteneur attache a `jarvis-bus`.

| | |
|---|---|
| **Outils** | docker (swarm/stack/service/secret/volume) · psql/pg_dump/pg_restore (conteneur postgres:15-alpine) · pg_isready · sqlite3 · sqlcipher · sops+age · gitleaks · pinecone (MCP) · MCP jarvis-linux-sqlite · tar/gzip · cron |
| **Ports / Endpoints** | PostgreSQL `postgres:5432` **non publie** (overlay jarvis-bus, db `jarvis_agents`, user `jarvis`) · ~1327 bases SQLite hote |

**Responsabilites cles :**
- Deployer/maintenir `data_postgres` (contrainte `node.hostname==pamerys-m4`, healthcheck pg_isready).
- Garantir disponibilite (replicas 1/1, logs, healthcheck).
- Executer SQL d'exploitation/maintenance via conteneur psql sur le bus.
- Sauvegarder quotidien : pg_dump `jarvis_agents` + snapshot tar volume `data_jarvis_postgres_data`.
- Restaurer Postgres (pg_restore) et verifier integrite.
- Inventorier/indexer les ~1327 bases SQLite dans `jarvis-index.db`.
- Exploiter/sauvegarder bases metier prof : `planning.db`, `rdv.db`, `cours`, RAG `rag_index.db`/`etoile.db`.
- Gerer chiffrement (sops/age, rotation `pg_pass`, sqlcipher pour SQLite sensibles).
- Preparer/operer l'indexation vectorielle Pinecone (RAG).
- Depanner : connexions refusees, volume plein, corruption SQLite (`PRAGMA integrity_check`).

---

### 40-VOICE — Standardiste vocal & Responsable transcription
**Profil :** Voice/STT-TTS Operator. Tient le "standard vocal" M4 : transcription parole→texte, voix sur textes, qualite via BDQT, routage via hub Lumen. Disponibilite 24/7 (failover M1/M2/M3).

| | |
|---|---|
| **Outils** | whisper-server (faster-whisper) · piper (TTS fr_FR-siwis-medium) · lumen token-server (Node) · bdqt_server.py + bdqt_core/build_lexicon/finetune · ffmpeg · curl · systemctl --user · journalctl · redis-cli · sqlite3 · ollama/LM Studio · sops+age · aplay/arecord |
| **Ports / Endpoints** | Whisper STT `:8789` · hub Lumen `:8788` · BDQT qualite `:8790` · PWA dictee `:7777` · services systemd-user : jarvis-whisper / jarvis-lumen / bdqt-http / jarvis-vocal-health |

**Responsabilites cles :**
- Faire tourner le STT Whisper persistant et transcrire en francais.
- Synthetiser la voix (Piper modele siwis) pour les retours vocaux.
- Maintenir la base BDQT (lexique metier 228 termes, 616 corrections phonetiques, prompt snippets) branchee sur Whisper.
- Enrichir dictionnaire vocal + dataset (`voice_dataset/wav`) pour fine-tuning.
- Assurer le failover STT M1/M2/M3 via `jarvis-vocal-health`.
- Router STT/TTS/LLM via le hub Lumen.
- Surveiller la sante des 4 services systemd-user, redemarrer en incident.
- Servir la dictee vocale vers la PWA gestion-journee.
- Sauvegarder la base qualite transcription et les modeles Piper.
- Publier les evenements vocaux sur le bus redis (`voice.events`), journaliser dans `voice_logs`.

---

### 50-BUSINESS — Responsable Commercial & Web Metier
**Profil :** Webmaster / DevOps Vitrines. Gere le portefeuille de sites clients/metiers M4. **Reporte a la DSI (00-infra)** pour bus reseau/secrets. Futur perimetre : trading, healthcare, facturation.

| | |
|---|---|
| **Outils** | docker (build/push/service/stack) · registry prive `:5000` · nginx:alpine · curl (health) · git · sqlite3 · sops+age · tar · Portainer `:9000` · n8n `:5678` |
| **Ports / Endpoints** | Vitrine **alkymia-communication** `:8086` · site **franckdelmas.dev** `:8085` · stack Swarm `business` · images `localhost:5000/50-business/*` · placement `node.role==manager` |

**Responsabilites cles :**
- Maintenir/versionner les sources : `/home/pamerys/alkymia-communication/site-v2` et `/home/pamerys/jarvis-delmas-site`.
- Construire les images statiques (nginx:alpine), pousser sur le registry prive.
- Deployer/MAJ le stack `business` (alkymia-site :8086, delmas-site :8085).
- Verifier disponibilite HTTP (code 200) + etat des replicas.
- Consulter logs, redemarrer/forcer redeploy, rollback en cas d'echec.
- Sauvegarder sources + images registry avant chaque mise en production.
- Garantir rattachement au reseau `jarvis-bus` et la contrainte de placement.
- Tenir a jour l'inventaire commandes/services dans `jarvis-index.db`.
- Coordonner avec 00-infra (secrets sops/age + registry).

---

### 90-SECRETS-GIT — RSSI / Gardien du coffre
**Profil :** Responsable Securite des SI. Confidentialite et integrite de tout le SI Jarvis. **Regle d'or :** seuls les `*.enc.env` chiffres sont commites ; la cle privee age ne quitte jamais la machine (sauvegarde hors-ligne) ; push **uniquement sur GO explicite**.

| | |
|---|---|
| **Outils** | sops · age · age-keygen · gitleaks · git · gh · docker · sqlite3 · sec-audit.sh · ssh-keygen · stat · chmod |
| **Cibles / Repere** | Coffre `~/jarvis/secrets-vault/*.enc.env` · cle privee `~/.config/sops/age/keys.txt` (chmod 600) · docker secrets `redis_pass`/`pg_pass` · repo distant `github.com/Turbo31150/jarvis-m4-core` (branche `sites-2026-refonte`) |

**Responsabilites cles :**
- Detenir/proteger la cle privee age (perms 600, backup hors-ligne, jamais commitee).
- Chiffrer/dechiffrer/editer les secrets du coffre sans exposer les valeurs.
- Provisionner et faire tourner les docker secrets `redis_pass`/`pg_pass`.
- Lancer l'audit red-team `sec-audit.sh` (cible : zero croix rouge), historiser dans `90-secrets-git/reports/`.
- Installer/exploiter gitleaks (scan repo + staging, hook pre-commit).
- Controler chaque push (scan gitleaks + revue diff, GO explicite obligatoire).
- Garantir que seuls les `*.enc.env` sont versionnes (.gitignore du coffre).
- Durcir les permissions des fichiers sensibles (.env, .git-credentials, .netrc, cles SSH).
- Maintenir `.sops.yaml` (creation_rules / cle age destinataire) + coherence index.
- Reagir en incident : revoquer/re-chiffrer apres fuite, reemettre les secrets docker, documenter.

---

## 3. Espace personnel Pamerys (pamerys-ecole)

> **Professeur des ecoles (primaire) + Famille.** Poste numerique personnel de Franck/Pamerys. Contexte impose : reponses en **francais clair et actionnable**, adaptees au metier d'enseignant du primaire et a la vie de famille.

**Role :** Responsable de l'Espace Personnel — tient le planning de cours, les RDV (parents, reunions, ecole, perso/famille), les to-do, notes pedagogiques et fiches de cours. Exploite la PWA gestion-journee comme tableau de bord du quotidien, assure la dictee vocale et l'automatisation du rituel matinal.

| | |
|---|---|
| **Outils** | sqlite3 (`planning.db`=cours, `rdv.db`=rdv, `todo.db`=todo, `notes.db`=notes) · PWA Flask `jarvis-webapp.service` · curl (API REST) · Whisper STT `:8789` · voice_widget.py / whisper_bridge.py · n8n · ollama + lm-ask.sh / gemini-ask.sh · systemctl --user · rsync/cp backups |
| **Ports / Endpoints** | PWA HTTP `:7777` + HTTPS `:8443` (installable Android offline) · API `/api/planning` `/api/rdv` `/api/todo` `/api/notes` `/api/voice-record` `/api/status` · Whisper `:8789` · n8n `:5678` (webhook `assistant-matin`) |

**Responsabilites cles :**
- Tenir a jour l'emploi du temps (planning.db) via PWA + API `/api/planning`.
- Gerer les RDV parents/reunions/ecole/famille (rdv.db).
- Suivre taches et preparations de classe (todo.db : categorie, priorite, statut, deadline).
- Capturer notes pedagogiques a la voix (Whisper, `/api/voice-record`, voice_widget Alt+X).
- Maintenir la PWA operationnelle (service, certifs HTTPS pour usage Android offline).
- Lancer/surveiller le rituel matinal automatise (n8n `assistant-matin` : planning + RDV + meteo).
- Sauvegarder quotidiennement les bases SQLite dans `~/jarvis/backups`.
- Produire resumes/preparations de cours en deleguant aux modeles locaux (zero token).
- Depanner webapp/whisper, consulter logs.
- Organiser/indexer les fiches de cours (`Documents/Cours`).

---

## 4. Bibliotheque de commandes (renvoi SQLite)

Toutes les commandes operationnelles de chaque departement sont cataloguees dans l'**index SQLite source de verite** :

```
~/jarvis/stacks/jarvis-index.db
```

| Action | Commande |
|---|---|
| Lister les tables de l'index | `sqlite3 ~/jarvis/stacks/jarvis-index.db '.tables'` |
| Toutes les commandes par departement | `sqlite3 ~/jarvis/stacks/jarvis-index.db 'SELECT entity,label,cmd FROM commands ORDER BY entity'` |
| Commandes d'un departement (ex. data) | `sqlite3 ~/jarvis/stacks/jarvis-index.db "SELECT label,command FROM commands WHERE entity='30-data';"` |
| Commandes business | `sqlite3 ~/jarvis/stacks/jarvis-index.db "SELECT * FROM commands WHERE entity LIKE '%business%'"` |
| Commandes secrets | `sqlite3 ~/jarvis/stacks/jarvis-index.db "SELECT label,cmd FROM commands WHERE stack LIKE '%secret%';"` |

> **Protocole SQL avant compute :** consulter cette bibliotheque AVANT toute inference/compute. Regeneration documentaire : `INDEX.md` / `COMMANDS.md` derives de `jarvis-index.db` (maintenus par 00-infra).

| Departement | Nb commandes cataloguees | Endpoints principaux |
|---|---|---|
| 00-infra | 30 | Redis :6379 · Registry :5000 · Portainer :9000 |
| 10-ia | 35 | Ollama :11434 · LM Studio :1234 · M1/M2 :1234 · cloud ollama.com |
| 20-automation | 32 | n8n :5678 · Redis bull :6379 |
| 30-data | 30 | Postgres :5432 (non publie) · SQLite hote |
| 40-voice | 33 | Whisper :8789 · Lumen :8788 · BDQT :8790 |
| 50-business | 33 | alkymia :8086 · delmas :8085 · registry :5000 |
| 90-secrets-git | 33 | coffre sops+age · github jarvis-m4-core |
| pamerys-ecole | 32 | PWA :7777/:8443 · Whisper :8789 · n8n :5678 |

---

*Document genere comme source de verite organisationnelle de l'entreprise virtuelle Jarvis-M4. Direction Pamerys — socle 00-infra transverse — inference zero-token via 10-ia — securite garantie par 90-secrets-git.*