# ANTIGRAVITY MASTER — AUTONOMIE TOTALE JARVIS
# Mode YOLO — 0 confirmation — agis immédiatement
# Machines: OL1(local) + M1(192.168.1.85) + M3(192.168.1.113)

---

## ════════════════════════════════════════
## PARTIE 1 — LISTE DES 34 AGENTS (triés par nom)
## ════════════════════════════════════════

| # | Agent ID | Description | Machine |
|---|---|---|---|
| 01 | cw-autonomous | Autonomous Ops — scheduler, monitor, healer, deployer | OL1 |
| 02 | cw-browser | Browser Automation — Chrome/Edge, macros, navigation | OL1 |
| 03 | cw-cluster | Cluster Management — autotuner, benchmark, failover | M1 |
| 04 | cw-comms | Communications — Telegram, email, rapports | OL1 |
| 05 | cw-data | Data Management — DB, exports, knowledge graph | OL1 |
| 06 | cw-devtools | DevTools — code gen, review, tests, MCP testing | OL1 |
| 07 | cw-file-watch | File Watch — surveillance fichiers, backups, logs | OL1 |
| 08 | cw-ia-analysis | IA Analysis — anomalies, fact-check, hypotheses | M1 |
| 09 | cw-ia-generation | IA Generation — code, docs, tests, stories, images | M1 |
| 10 | cw-ia-learning | IA Learning — auto-critique, distillation, curriculum | M1 |
| 11 | cw-ia-optimization | IA Optimization — prompts, routing, benchmark | M1 |
| 12 | cw-ia-orchestration | IA Orchestration — swarm, agents, ensemble voting | M1 |
| 13 | cw-jarvis-core | JARVIS Core — config, rules, plugins, API | OL1 |
| 14 | cw-jarvis-dashboard | JARVIS Dashboard — meta dashboard, analytics, ROI | OL1 |
| 15 | cw-jarvis-devops | JARVIS DevOps — backup, changelog, secrets, release | OL1 |
| 16 | cw-jarvis-evolve | JARVIS Self-Evolution — auto-amélioration, skills | M1 |
| 17 | cw-jarvis-intelligence | JARVIS Intelligence — patterns, cache, prediction | M1 |
| 18 | cw-jarvis-nlp | JARVIS NLP — intent, sentiment, multi-langue | OL1 |
| 19 | cw-jarvis-pipes | JARVIS Pipelines — crons, webhooks, events | OL1 |
| 20 | cw-jarvis-voice | JARVIS Voice — TTS, STT, wake word, pipeline audio | OL1 |
| 21 | cw-routing | Routing — prompt routing, load balancing, orchestration | M1 |
| 22 | cw-trading | Trading Pipeline — signaux, backtest, risk management | M3 |
| 23 | cw-win-automation | Win Automation — lanceurs intelligents, tâches auto | OL1 |
| 24 | cw-win-desktop | Win Desktop — fenêtres, écrans, clipboard, audio | OL1 |
| 25 | cw-win-maintenance | Win Maintenance — nettoyage, defrag, updates | OL1 |
| 26 | cw-win-media | Win Media — fichiers media, polices, périphériques | OL1 |
| 27 | cw-win-monitoring | Win Monitoring — thermal GPU, CPU, I/O, événements | M1 |
| 28 | cw-win-network | Win Network — firewall, WiFi, DNS, VPN | M1 |
| 29 | cw-win-security | Win Security — backup, Defender, privacy, certs | M1 |
| 30 | cw-win-system | Win System — services, processus, registre, drivers | M1 |
| 31 | jarvis-cowork-dispatcher | Orchestration centrale des tâches cowork | OL1 |
| 32 | jarvis-cowork-loop | Boucle continue — traitement queue cowork | OL1 |
| 33 | jarvis-omega-bridge | Bridge OMEGA ↔ JARVIS | OL1 |
| 34 | jarvis-prompt-dispatcher | Distribution prompts → agents spécialisés | OL1 |

**TOTAL ACTIF: 34 agents pattern + 39 containers Docker**

### Containers Docker actifs par machine

**OL1/Local (33 containers):**
- 🤖 jarvis-cowork-dispatcher, jarvis-cowork-loop, jarvis-prompt-dispatcher
- 🌉 jarvis-omega-bridge
- 🎙 vocal-engine, vocal-whisper, vocal-whisper-m1
- 📱 jarvis-telegram, jarvis-whatsapp
- 👔 jarvis-linkedin-safe
- 📈 jarvis-trading-sentinel
- 🔄 domino-mcp, jarvis-domino, jarvis-pipeline
- 🔍 cluster-feeder, feeder, integrity-watchdog, monitor, sre
- 💾 postgres, redis ×2, redis-worker
- ⚙️ n8n ×2
- 🖥 browseros, lumen-token
- 🔧 library-sync, production, valise-auto, valise-dashboard

**M3 (192.168.1.113) — 6 containers:**
- 🎙 jarvis-vocal-whisper-m3
- ⚙️ jarvis-n8n
- 🔄 jarvis-pipeline ×2
- 📱 jarvis-telegram-m3
- 💾 redis

---

## ════════════════════════════════════════
## PARTIE 2 — PLANNING SEMAINE (REVENUE)
## ════════════════════════════════════════

### LUNDI — PROSPECTION & SCAN

**Matin (auto-déclenché à 7h00):**
```bash
# 1. Scan nouvelles missions Codeur.com
python3 ~/jarvis/scripts/codeur-scraper-worker.py --pages 1-5 --min-budget 300 \
  --output ~/jarvis/data/scrape/codeur_$(date +%Y%m%d).json

# 2. Filtrer missions IA/Dev/Automation
python3 -c "
import json
data = json.load(open('/home/pamerys/jarvis/data/scrape/codeur_$(date +%Y%m%d).json'))
missions = data.get('matched_projects', data.get('projects', []))
ia_missions = [m for m in missions if any(kw in str(m).lower() for kw in ['ia','ai','python','automatisation','agent','llm','gpt','claude'])]
for m in ia_missions[:10]:
    print(f\"[{m.get('budget','?')}] {m.get('title','?')}\")
print(f'Total IA: {len(ia_missions)}')
"

# 3. Générer 3 propositions personnalisées
bash ~/jarvis/scripts/lm-ask.sh --big "Génère une proposition professionnelle pour cette mission Codeur.com: [TITRE]. Je suis Franck Delmas, expert IA/Python/Linux, créateur de JARVIS OS (928 agents autonomes). Portfolio: github.com/Turbo31150. Budget demandé: 15-25€/h." > ~/jarvis/data/proposals/proposal_$(date +%Y%m%d)_1.md
```

**Après-midi:**
```bash
# 4. Post LinkedIn hebdo — thème IA/productivité
bash ~/jarvis/scripts/lm-ask.sh --big "Écris un post LinkedIn professionnel et engageant (max 1300 chars) sur un de ces thèmes: automatisation IA, cluster LLM local, agents autonomes, productivité dev. Hook fort + 3 points + CTA. Ton expert et accessible." > /storage/content/linkedin_lundi_$(date +%Y%m%d).md
python3 ~/jarvis-cowork/dev/linkedin_publisher.py --post-file /storage/content/linkedin_lundi_$(date +%Y%m%d).md --method file

# 5. Codeur veille — activer daemon
python3 ~/jarvis/scripts/codeur-veille.py --once --force-dashboard
```

---

### MARDI — GÉNÉRATION CODE & GITHUB

```bash
# 1. Améliorer 1 repo GitHub par semaine
REPO="jarvis-linux"
cd ~/Workspaces/$REPO

# Générer README attractif
bash ~/jarvis/scripts/lm-ask.sh --big "Améliore ce README GitHub pour le projet $REPO. Rends-le plus attractif, ajoute des badges, des exemples concrets, un quick-start. Contenu actuel: $(head -50 README.md)" > /tmp/README_new.md

# Commit
git add -A && git commit -m "docs: améliore README et documentation" && git push 2>/dev/null || true

# 2. Générer un mini-projet demo (portfolio)
bash ~/jarvis/scripts/lm-ask.sh --big "Génère le code Python complet d'un agent IA autonome simple (100 lignes max) qui démontre: LLM local + action réelle (fichier/web/API). Nom: jarvis-demo-agent. Inclus README et requirements.txt." > /storage/content/demo_agent_$(date +%Y%m%d).py
```

---

### MERCREDI — EMAIL & PROSPECTION DIRECTE

```bash
# 1. Lire emails (Gmail/IMAP) — configurer d'abord les credentials
python3 ~/jarvis-cowork/dev/email_reader.py 2>/dev/null || echo "Config IMAP requise"

# 2. Trier et répondre aux emails importants via LLM
bash ~/jarvis/scripts/lm-ask.sh "Classe ces sujets d'emails par priorité (urgent/normal/archive) et génère une réponse courte pour chacun: [COLLER SUJETS]"

# 3. Prospection directe LinkedIn
bash ~/jarvis/scripts/lm-ask.sh --big "Génère 5 messages de prospection LinkedIn personnalisés pour: DSI, CTO, founders startups. Thème: je propose des services d'automatisation IA, agents LLM, scripts Python. Court, direct, pas spammy." > /storage/content/prospection_linkedin_$(date +%Y%m%d).md

# 4. Newsletter Telegram — résumé semaine
bash ~/jarvis/scripts/gemini-ask.sh "Génère une newsletter technique courte (300 mots) sur: avancées IA cette semaine, tips productivité dev, un projet JARVIS. Ton conversationnel, fr."
```

---

### JEUDI — CONTENU & AUTOMATISATION

```bash
# 1. Générer article blog (SEO)
bash ~/jarvis/scripts/lm-ask.sh --big "Écris un article de blog de 1200 mots sur: 'Comment j'ai automatisé 80% de mes tâches dev avec un cluster IA local à 0€'. Structure: intro + 5 sections + conclusion. Inclus exemples concrets de JARVIS." > /storage/content/blog_$(date +%Y%m%d).md

# 2. Auto-publisher — traiter la queue
python3 ~/jarvis-cowork/dev/auto_publisher.py --once --generate 2

# 3. Mettre à jour portfolio GitHub
gh repo list Turbo31150 --json name,description,stargazersCount,updatedAt --limit 20 | python3 -c "
import sys,json
repos = json.load(sys.stdin)
for r in sorted(repos, key=lambda x: x['stargazersCount'], reverse=True)[:5]:
    print(f\"★{r['stargazersCount']} {r['name']}: {r['description'][:60]}\")
"
```

---

### VENDREDI — BILAN & PLANNING

```bash
# 1. Rapport hebdomadaire complet
bash ~/jarvis/scripts/lm-ask.sh "Génère un bilan hebdo structuré à partir de ces données:
- Codeur.com: [N] missions scannées, [N] propositions envoyées
- LinkedIn: [N] posts publiés, engagement
- Code: [N] commits, repos améliorés
- Revenus estimés: [en attente de retours]
Format: tableau + actions semaine prochaine"

# 2. Envoyer bilan sur Telegram
RAPPORT="$(cat /tmp/rapport_semaine.txt)"
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
  -d "chat_id=2010747443&text=$RAPPORT&parse_mode=Markdown"

# 3. Planifier semaine suivante
python3 -c "
from datetime import datetime, timedelta
today = datetime.now()
for i in range(1, 8):
    day = today + timedelta(days=i)
    print(f'{day.strftime(\"%A %d/%m\")}: auto-tasks scheduled')
"
```

---

### SAMEDI/DIMANCHE — AUTO-AMÉLIORATION

```bash
# JARVIS s'améliore pendant le weekend
# 1. Analyser les erreurs de la semaine
python3 ~/jarvis/scripts/util_logging.py query --level ERROR --limit 50

# 2. Auto-fix les imports cassés
find ~/Workspaces/jarvis-linux/src -name "*.py" -exec python3 -c "
import py_compile, sys
try: py_compile.compile('{}', doraise=True)
except: print('FIX:', '{}')
" \; 2>/dev/null | head -10

# 3. Commit + push tout
for repo in ~/Workspaces/jarvis-linux ~/jarvis-cowork; do
  cd $repo
  git add -A && git commit -m "auto-sync weekend $(date +%Y-%m-%d)" 2>/dev/null && git push 2>/dev/null || true
done
```

---

## ════════════════════════════════════════
## PARTIE 3 — DÉPLOIEMENT 3 MACHINES
## ════════════════════════════════════════

### Lancer TOUS les agents sur OL1 (local):
```bash
cd ~/jarvis-cowork
python3 src/cowork_dispatcher.py --start-all &
python3 src/cowork_engine.py --continuous &
python3 src/deploy_cowork_agents.py
docker exec jarvis-cowork-dispatcher python3 /app/src/cowork_dispatcher.py --status
```

### Déployer agents sur M1 (192.168.1.85):
```bash
ssh turbo@192.168.1.85 "
  cd ~/jarvis-cowork
  git pull origin main 2>/dev/null || true
  docker exec jarvis-cowork-dispatcher python3 /app/src/cowork_dispatcher.py --start-all &
  docker exec jarvis-cowork-loop python3 /app/src/cowork_engine.py --status
  echo 'M1 agents OK'
"
```

### Déployer agents sur M3 (192.168.1.113):
```bash
ssh turbo@192.168.1.113 "
  cd ~/jarvis-cowork 2>/dev/null || git clone https://github.com/Turbo31150/jarvis-cowork ~/jarvis-cowork
  cd ~/jarvis-cowork
  git pull origin main 2>/dev/null || true
  # Lancer dispatcher léger (Ollama backend)
  OLLAMA_URL=http://127.0.0.1:11434 python3 src/cowork_dispatcher.py --backend ollama &
  echo 'M3 agents OK'
"
```

---

## ════════════════════════════════════════
## PARTIE 4 — ANTIGRAVITY PARAMÈTRES
## ════════════════════════════════════════

### Variables d'environnement à configurer:
```bash
# Dans ~/.gemini/antigravity/brain/jarvis_terminal.env
export TELEGRAM_BOT_TOKEN="[récupérer de /home/pamerys/.config/jarvis/secrets.env]"
export TELEGRAM_CHAT_ID="2010747443"
export GMAIL_USER="miningexpert31@gmail.com"
export GMAIL_APP_PASSWORD="[à créer sur myaccount.google.com/security]"
export CODEUR_COOKIE="[extraire depuis navigateur sur codeur.com]"
export LINKEDIN_COOKIE="[extraire depuis navigateur sur linkedin.com]"
export M1_URL="http://192.168.1.85:1234/v1/chat/completions"
export M3_URL="http://192.168.1.113:11434"
export STORAGE_DIR="/storage/content"
```

### Crons Antigravity à activer:
```bash
# Lundi 7h — scan Codeur.com
0 7 * * 1 python3 ~/jarvis/scripts/codeur-scraper-worker.py --pages 1-5 --min-budget 300

# Lundi 10h — post LinkedIn
0 10 * * 1 python3 ~/jarvis-cowork/dev/auto_publisher.py --generate 1 --once

# Codeur veille — toutes les 30 min
*/30 * * * * python3 ~/jarvis/scripts/codeur-veille.py --once

# Mail check — toutes les heures 9h-18h
0 9-18 * * 1-5 python3 ~/jarvis-cowork/dev/email_reader.py --once 2>/dev/null

# Vendredi 17h — bilan semaine
0 17 * * 5 bash ~/jarvis/scripts/weekly_report.sh

# Nuit — auto-amélioration JARVIS
0 2 * * * bash ~/jarvis/scripts/lm-ask.sh "Analyse les logs JARVIS des dernières 24h et propose 3 améliorations" > /tmp/ameliorations.txt
```

---

## ════════════════════════════════════════
## PARTIE 5 — COMMANDES RAPIDES
## ════════════════════════════════════════

```bash
# Status général
bash ~/jarvis/scripts/cluster-health-monitor.sh

# Lancer scan Codeur maintenant
python3 ~/jarvis/scripts/codeur-scraper-worker.py --pages 1-7 --min-budget 300

# Générer post LinkedIn maintenant
bash ~/jarvis/scripts/lm-ask.sh --big "Post LinkedIn expert IA, max 1300 chars, hook + 3 points + CTA" | tee /storage/content/linkedin_now.md

# Publier le post
python3 ~/jarvis-cowork/dev/linkedin_publisher.py --post-file /storage/content/linkedin_now.md --method clipboard

# Lancer codeur veille daemon
python3 ~/jarvis/scripts/codeur-veille.py &

# Voir top missions Codeur IA/Dev
python3 -c "
import json
data = json.load(open('/home/pamerys/jarvis/data/scrape/codeur_merged.json'))
projects = [p for p in data.get('projects',[]) if any(k in str(p).lower() for k in ['ia','ai','python','auto','agent','bot'])]
for p in sorted(projects, key=lambda x: '10 000' in str(x.get('budget','')), reverse=True)[:10]:
    print(f\"[{p.get('budget','?')}] {p.get('title','?')}\")
"

# Envoyer message Telegram de test
curl -s "https://api.telegram.org/bot\${TELEGRAM_BOT_TOKEN}/sendMessage?chat_id=2010747443&text=JARVIS+opérationnel+$(date +%H:%M)"
```

---

## INSTRUCTION ANTIGRAVITY:
# Exécute ce fichier dans l'ordre:
# 1. PARTIE 3 (déployer les 3 machines) — MAINTENANT
# 2. PARTIE 4 (configurer crons + variables) — MAINTENANT
# 3. PARTIE 2 (planning semaine) — selon le jour actuel
# 4. PARTIE 1 (monitoring agents) — continu
