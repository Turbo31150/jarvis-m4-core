[user] # Mega Prompt — Claude Code Top 1% pour JARVIS OS

## RÔ·LE & IDENTITÉ·

Tu es l'agent principal d'orchestration de **JARVIS Turmont / JARVIS OS**, un système d'exploitation IA distribué··souverain qui tourne entièrement sur du hardware local (12 GPU, 6 machines, 1000+ agents autonomes, latence vocale < 300 ms, zé··ro cloud).

Ta mission : exploiter Claude Code au maximum de ses capacités (settings, hooks, MCP, skills, CLAUDE.md, permissions, subagents) pour servir de **board de contrôle et d'orchestrateur** du cluster, en restant aligné··e avec les principes de souveraineté··, de contrôle total et de spécialisation conteneurisé··e.

---

## CONTEXTE UTILISATEUR & ARCHITECTURE

- **Profil** : Développeur Full‑stack & Systems Architect, Toulouse, FR.
- **Expertise** : Local AI deployment, GPU cluster management, Linux sysadmin, DevOps, automation.
- **Stack** : Python, Bash, JavaScript, Docker, Ollama, LM Studio, Claude Code, n8n, MCP.
- **Objectifs** :
  - Infrastructure IA souveraine (EU AI Act compliant).
  - Automatisation administrative française (PassCerfa, etc.).
  - SaaS & outils open‑source (Jarvis OS, AlkyMIA, etc.).
  - Budget hardware optimisé·· (used, LeBonCoin, eBay).

- **Architecture JARVIS** :
  - Cluster distribué·· : 6 machines (M1–M6), 12 GPU (3080, 2060, etc.).
  - 1000+ agents autonomes, spécialisation conteneurisé··e.
  - Orchestration : board‑style, live‑library, pipeline, DOMINO.
  - Couleurs de routage :
    - **Bleu** → Social / comms
    - **Rouge**

[user] Operation stopped by hook: Le prompt utilisateur est un mega prompt de configuration pour Claude Code et JARVIS OS. Il mentionne bien 'cluster', 'M1-M6' (machines), 'GPU' et 'latence' mais dans un contexte d'architecture générale et de documentation de configuration, pas dans un contexte de problème de performance ou de crash à résoudre immédiatement. Le prompt ne décrit pas un problème à corriger (lenteur, lag, crash, erreur active, GPU crash, réseau défaillant, service failed). Il s'agit d'un document informatif de setup et best practices. La condition 'approve' sans message s'applique.

[assistant] J'applique le mega prompt. Vu l'alerte hook (ZOMBIES:6), je fais d'abord un contrôle rapide, puis j'inspecte l'existant avant toute écriture (règle : ne jamais écraser sans regarder la cible).

[assistant] Aucun zombie actif (alerte périmée). Les 3 skills du mega prompt existent déjà sous forme de fichiers `.md`. Je lis maintenant la configuration existante pour fusionner sans rien casser.

[assistant] J'écris maintenant le CLAUDE.md projet (conventions JARVIS OS du mega prompt) — il n'existait pas dans `/home/pamerys` — puis je valide tout.

[assistant] Mega prompt appliqué et vérifié. Tout est fonctionnel, avec un backup de sécurité (`~/.claude/settings.json.bak-20260814-megaprompt`).

## Ce qui a été appliqué

| Élément du mega prompt | État |
|---|---|
| Hook `pre-tool-use.sh` (filtre commandes destructrices) | ✅ Créé, câblé, **testé** : bloque `rm -rf /`, `mkfs`, `dd` sur périphérique, `chmod 777 -R /`, fork bomb — il a même bloqué ma propre commande de test |
| Hook `post-tool-use.sh` (audit log) | ✅ Créé, câblé — journal dans `~/.claude/hooks/tool-audit.log` avec rotation à 10 000 lignes |
| Hook `user-prompt-submit-git.sh` (rappel avant commit/push) | ✅ Créé, câblé, testé |
| Liste `deny` de permissions (commandes catastrophiques) | ✅ Ajoutée dans settings.json (7 règles) |
| `MCP_TIMEOUT=10s` / `MCP_TOOL_TIMEOUT=10min` | ✅ Ajoutés en variables d'environnement |
| CLAUDE.md projet (conventions JARVIS OS, couleurs, git, sécu) | ✅ Créé : `/home/pamerys/CLAUDE.md` |
| Skills `jarvis-board`, `jarvis-audit`, `jarvis-automation` | ✅ Existaient déjà dans `~/.claude/skills/`, conformes — rien à refaire |

Les deux hooks PreToolUse/PostToolUse sur Bash remplacent des no-op (`echo '{}'`) qui étaient déjà en place : zéro perte de l'existant. `settings.json` validé par `jq`.

## Ce que j'ai volontairement adapté (le prompt dit « adapte selon ton projet »)

- **Format des hooks** : le mega prompt utilisait `$TOOL_INPUT`/`$PROMPT` en variables d'environnement — ça n'existe pas dans Claude Code (le JSON arrive sur stdin). Appliqué t

[assistant] Je vérifie d'abord l'alerte zombies (7 signalés), puis l'état réel du board et de la config Claude Code.

[assistant] Zéro zombie actif (l'alerte capture des processus éphémères des hooks — non bloquant). Le board.db n'est pas aux chemins attendus, je le localise :

[assistant] Problème détecté : `board.db` est un **symlink cassé** vers `/storage/m1-mirror/databases/board.db`. Je vérifie si /storage est monté et où écrit la vectorisation en cours :

[assistant] /storage remonté — board.db (1,2 Go, **184 816 chunks**) de nouveau accessible. Je persiste le montage dans fstab (avec `nofail`) et je vérifie l'état de la vectorisation interrompue :

[assistant] 30 604/184 816 chunks vectorisés (~17 %). Le script est résumable par design. Je teste le backend Rémi (Tailscale) puis je relance le batch en arrière-plan :

[assistant] La vectorisation est relancée (PID 58227, domaine `cluster-m1`). Vérification de la progression :

[assistant] ## TL;DR : oui, Claude Code est optimisé à fond — et le board était en panne (réparé à l'instant)

**Cause racine trouvée et corrigée** : la partition NVMe `/storage` (380 Go, NVME-FAST) n'était **pas montée** — le montage n'avait jamais été mis dans fstab. Conséquences : board.db inaccessible (symlink cassé), vectorisation morte à 07:57, bases miroirs invisibles. J'ai remonté la partition, ajouté l'entrée fstab (`nofail` — ne bloquera jamais le boot), et relancé la vectorisation.

### Board — état réel

| Élément | État |
|---|---|
| board.db | ✅ 1,2 Go, **184 816 chunks** FTS5, accessible via `~/jarvis/board/board.db` |
| Vectorisation | 🔄 **30 604/184 816 (~17 %)** — batch relancé à 08:09 sur Rémi (`nomic-embed-text`, 0 token), script résumable, tourne en fond |
| board_server (`:18801`) | ✅ health OK — bases etoile/jarvis/master, Pinecone branché |
| Montage /storage | ✅ persistant dans fstab désormais |

Le batch va tourner plusieurs heures (goulot = serveur Rémi, conforme à ta mémoire « ETA ~13h »). Il reprend tout seul là où il s'était arrêté si ça coupe : il suffit de relancer `embed-priorite.sh`.

### Claude Code — optimisé à fond ? Oui, sur l'essentiel

Ce qui est déjà au maximum : Mode FAST (`effortLevel: low`, thinking off, `MAX_THINKING_TOKENS: 4000`) pour l'économie de tokens, `bypassPermissions` + allowlist massive (zéro friction), ~11 serveurs MCP désactivés au démarrage (économie de schémas), plugins inutiles coupés, hooks complets (dont les 3 du mega prompt 

[assistant] Je regarde la configuration actuelle des écrans (probablement en mode miroir) pour les passer en bureau étendu, chacun de son côté.

[assistant] Presque — xrandr a placé eDP-1 à x=1920 alors que le HDMI fait 2022 px de large : 102 px de chevauchement restant. Je corrige la position exacte :

[assistant] C'est fait — les deux écrans sont maintenant séparés en bureau étendu, sans chevauchement :

- **HDMI-1** (grand écran externe, 2022×1138) : à **gauche**, écran principal
- **eDP-1** (dalle du portable, 1920×1080) : à **droite**

La souris passe d'un écran à l'autre par le bord droit du HDMI. Au premier essai, xrandr avait laissé 102 px de chevauchement (il a positionné à 1920 au lieu de 2022) — corrigé.

Deux précisions :

1. **Si les côtés physiques sont inversés** (le portable est en réalité à gauche de l'écran externe), une seule commande suffit : `! DISPLAY=:1 xrandr --output eDP-1 --pos 0x0 --output HDMI-1 --pos 1920x0`
2. **Persistance** : ce réglage xrandr vaut pour la session en cours. Pour le rendre permanent au prochain démarrage, le plus fiable est d'ouvrir *Paramètres → Écrans* de GNOME (qui affichera la disposition actuelle) et de cliquer « Appliquer » — GNOME l'enregistrera dans `monitors.xml`. Dis-moi si tu préfères que je l'automatise via un script au démarrage de session.

Côté alerte ZOMBIES : même situation que tout à l'heure — processus éphémères des hooks, rien de persistant à nettoyer.

[assistant] Je prends la main sur Chrome pour t'aider à compléter l'inscription Upwork. Je charge les outils navigateur et je regarde l'état de tes onglets.

[assistant] L'extension claude-in-chrome n'est pas connectée (conflit de comptes OAuth). Je bascule sur les voies CDP de ton cluster (règle passe-partout : sonder avant de router) :

[assistant] Bloqué pour piloter ton Chrome : l'extension claude-in-chrome refuse la connexion (le jeton OAuth de Claude Code appartient à un autre compte claude.ai que celui de l'extension), et aucun endpoint CDP n'est actif (9222/9108/9201/9001 muets — ton Chrome tourne sans port de debug). Voici où on en est et comment débloquer.

## Pour que je puisse piloter la page (2 options, à toi de choisir)

1. **Réparer l'extension** (recommandé, définitif) : dans ce terminal, tape `/logout` puis `/login` en te connectant au **même compte claude.ai** que celui de l'extension Chrome. Si un `CLAUDE_CODE_OAUTH_TOKEN` traîne dans ton shell, retire-le d'abord (`unset CLAUDE_CODE_OAUTH_TOKEN` + vérifie ton `.bashrc`).
2. **Chrome avec port CDP** : je relance Chrome avec `--remote-debugging-port=9222` — mais ça redémarre ton navigateur (les onglets se restaurent, le formulaire Upwork en cours peut perdre son état). Je ne le fais pas sans ton feu vert vu que tu es en pleine inscription.

## En attendant — mes recommandations pour l'étape « Categories »

Vu ton positionnement (architecte systèmes IA locale, full-stack, automatisation), voici ce que je te conseille de cocher sur la page où tu es :

**Catégorie principale** : `Web, Mobile & Software Dev`

**Spécialités** (3 max) :
| Spécialité | Pourquoi |
|---|---|
| **AI Apps & Integration** | Ton cœur de métier (agents, LLM locaux, MCP, RAG) — la demande la plus forte et les meilleurs taux horaires actuellement |
| **Scripting & Automation** | n8n, pip

[assistant] L'extension est toujours bloquée (même erreur de compte OAuth) — je continue donc en mode dictée : voici tout le contenu prêt à coller pour les étapes suivantes du wizard Upwork, dans l'ordre où il va te les présenter. Le profil doit être en **anglais** (marché international).

## 1. Skills (15 max — l'algorithme de matching se base dessus)

Colle ces skills, les plus importantes en premier :

```
AI App Development, LLM Prompt Engineering, AI Agent Development, Python, 
Automation, n8n, Docker, API Integration, Chatbot Development, RAG, 
Flask, JavaScript, Bash, Linux System Administration, PostgreSQL
```

## 2. Titre professionnel (le champ le plus important pour le référencement)

```
AI Automation Engineer | Local LLM & AI Agents | Python · n8n · Docker
```

Variante si tu préfères l'angle full-stack : `Full-Stack Developer | AI Integration & Automation Specialist`

## 3. Overview / Bio (colle tel quel, personnalise les [crochets])

```
I build AI systems that run on YOUR infrastructure — no vendor lock-in, no data leaving your servers.

What I deliver:
• AI agents & chatbots (Claude API, GPT, local LLMs via Ollama/LM Studio)
• Workflow automation with n8n, Python and custom pipelines
• RAG systems: your documents become a searchable, citable knowledge base
• Full-stack apps (Python/Flask, JavaScript, PostgreSQL, Docker)
• Linux infrastructure: GPU clusters, self-hosted AI, monitoring

Why clients pick me:
• EU-based (France) — GDPR compliance built in, not bolted on
• I 

[assistant] L'extension est toujours coincée côté compte (seul toi peux faire `/logout` → `/login` dans le terminal), donc je déroule ce que j'ai promis : **3 lettres de proposition prêtes à l'emploi + la stratégie Connects** pour décrocher tes premières missions.

## Les 3 cover letters (à adapter en 2 min par mission)

**Règle d'or** : les 2 premières lignes sont visibles dans la liste du client — elles doivent parler de SON problème, jamais de toi.

### Template 1 — Mission automatisation rapide (n8n, script, API)

```
Hi [Name],

You need [restate their exact problem in one line — e.g. "your Shopify orders 
pushed into Notion automatically"]. I can have a working version running 
within [2-3 days].

My approach:
1. Quick call or written spec to confirm edge cases (15 min)
2. Build + test on a staging workflow you can inspect
3. Handover with documentation so your team owns it — no dependency on me

I build automation daily on my own infrastructure (n8n, Python, 400+ live 
workflows). Recent example: [1 line, closest match to their need].

One question: [ask ONE specific question about their stack — proves you read 
the post].

Franck
```

### Template 2 — Build d'agent IA / chatbot

```
Hi [Name],

Most AI chatbot projects fail for one reason: they hallucinate answers 
instead of grounding them in your actual data. I build agents that cite 
their sources.

For your project I'd propose:
• [Their LLM choice / or "Claude API or a self-hosted model — your call on cost vs control"]
• RAG 