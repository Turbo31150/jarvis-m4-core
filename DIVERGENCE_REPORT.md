# JARVIS DIVERGENCE REPORT
*Généré le 2026-04-30 — Agent OMEGA-ANALYSIS*

---

## 1. TIMELINE DES DÉPLOIEMENTS MAJEURS

| Date | Problème | Solution déployée |
|---|---|---|
| 2026-03-12 | Migration Windows→Linux | Full Recovery Base (jarvis-linux init) |
| 2026-03-13 | Telegram bot cassé (Docker/TTS/OpenClaw) | Fix Linux migration bot, pipeline voix |
| 2026-03-16 | Pas d'interface browser headless | BrowserOS CDP client + session save/restore |
| 2026-03-20 | qwen3:1.7b absent sur cluster | Remplacement par qwen2.5:1.5b partout |
| 2026-03-23 | Pas d'identité système stable | JARVIS déclaré "Cognitive OS", docs formalisés |
| 2026-03-29 | Chaos/stress test OMEGA v16/v17 | Swarm 50k tâches, OnFailure handlers, domino dedup |
| 2026-04-04 | Fragmentation scripts cowork | Sync 170+ scripts depuis jarvis-linux → jarvis-cowork |
| 2026-04-27 | Automatisation LinkedIn manquante | Page Agent LinkedIn config ajoutée |
| 2026-04-29 | État dev non sauvegardé | auto-save snapshot cowork (stash git) |

---

## 2. ÉTAT ACTUEL DES COMPOSANTS

### Services systemd (77 déployés / 94 dans le repo)

| Service | État | Problème |
|---|---|---|
| jarvis-ai-proxy | ACTIF | OK — tourne depuis /home/pamerys/IA/Core/jarvis/scripts/ |
| jarvis-chrome-cdp | ACTIF | OK — port 9222 |
| jarvis-ia-web-mcp | ACTIF | OK |
| jarvis-master | ACTIF (en boucle) | SIGKILL toutes les 30-45s — fichier ExecStart INTROUVABLE |
| jarvis-orchestrator | ACTIF | OK mais CDP hardcodé sur port 9108 (ancien) |
| jarvis-pulse | ACTIF | OK |
| jarvis-score-updater | ACTIF | OK — depuis IA/Core/jarvis/core/jarvis_score.py |
| jarvis-watchdog | ACTIF | OK |
| health-patrol | ACTIF (silencieux) | health_patrol.py ABSENT dans scripts/ |
| jarvis-telegram | ECHEC (boucle #94) | telegram-bot.js ABSENT dans infra/interfaces/canvas/ |
| jarvis-ws | ECHEC (boucle #137) | module python_ws.server INTROUVABLE |
| jarvis-domino-engine | MASQUÉ | Volontairement désactivé |
| jarvis-feeder | MASQUÉ | Volontairement désactivé |

### Dépôts Git

| Dépôt | Commits | État |
|---|---|---|
| Workspaces/jarvis-linux | 2738 | Source principale, actif |
| jarvis-linux | symlink → Workspaces/jarvis-linux | Alias |
| JARVIS-CLUSTER | ~50 | Secondaire, doc + orchestration |
| jarvis-cowork | ~30 | Sous-ensemble scripts synchro depuis jarvis-linux |
| jarvis/lumen | ~15 | UI React/Vite, sous-repo dans /jarvis/ (non-git parent) |
| JARVIS-OMEGA | 2 | Vide/draft |

### Composants hors-git

| Chemin | Rôle | Lien avec git |
|---|---|---|
| /home/pamerys/jarvis/ | Scripts runtime (lm-ask.sh, gemini-ask.sh, monitoring) | Non versionné |
| /home/pamerys/IA/Core/jarvis/ | App séparée (orchestrator, score, ai-proxy, browser) | Non versionné |
| /home/pamerys/.jarvis/ | Runtime node (etoile.db, session-start.sh) | Non versionné |
| /home/pamerys/.openclaw/ | Workspace OpenClaw | Propre git |

---

## 3. DIVERGENCES IDENTIFIÉES

### D1 — CRITIQUE : jarvis-master.service pointe vers un fichier inexistant
- **Attendu** : `src/jarvis/core/scripts/devops/jarvis_unified_boot.py`
- **Existant** : `src/jarvis/core/scripts/devops/jarvis_master_launch.py`
- **Effet** : Restart loop infini, SIGKILL toutes les 30s depuis le boot

### D2 — CRITIQUE : jarvis-telegram cherche canvas/ dans mauvais répertoire
- **Attendu** : `/home/pamerys/jarvis-linux/infra/interfaces/canvas/telegram-bot.js`
- **Existant** : `/home/pamerys/jarvis-linux/canvas/` contient `data/` uniquement (pas de .js)
- **Effet** : Restart loop #94 — Telegram bot complètement mort

### D3 — CRITIQUE : jarvis-ws module python_ws inexistant
- **Attendu** : module `python_ws.server` dans le venv
- **Existant** : Aucun dossier python_ws dans le repo
- **Effet** : Restart loop #137 — WebSocket server mort

### D4 — MOYEN : health-patrol.py absent du chemin configuré
- **Attendu** : `Workspaces/jarvis-linux/scripts/health_patrol.py`
- **Existant** : `scripts/` contient seulement `lm-ask.sh`, `resource-alert-monitor.py`, `token-guardian/`, `eco/`
- **Effet** : Monitoring silencieux — tourne mais ne fait rien (bash swallow l'erreur)

### D5 — MOYEN : jarvis-orchestrator utilise CDP port 9108 (obsolète)
- **Configuré dans orchestrator** : `http://127.0.0.1:9108/json`
- **Chrome CDP tourne sur** : port 9222
- **Effet** : CODEUR et LINKEDIN agents échouent silencieusement (404)

### D6 — FAIBLE : 17 services définis dans le repo mais non déployés
- 94 fichiers .service dans `infra/systemd/`, 77 en production
- Exemples non déployés : jarvis-api, jarvis-mcp, jarvis-voice, jarvis-vector, jarvis-rag-indexer

### D7 — FAIBLE : Deux espaces de travail parallèles non connectés
- `/home/pamerys/IA/Core/jarvis/` est un projet autonome (son propre orchestrator.db, CLAUDE.md, agents)
- `Workspaces/jarvis-linux/` est le repo principal
- Les services pointent vers les deux sans cohérence (ai-proxy → IA/Core, master → Workspaces)

---

## 4. PLAN DE CONVERGENCE — 5 ACTIONS PRIORITAIRES

### P1 — Corriger jarvis-master.service (30 min)
```bash
# Option A : renommer le fichier dans le repo pour matcher le service
mv src/jarvis/core/scripts/devops/jarvis_master_launch.py \
   src/jarvis/core/scripts/devops/jarvis_unified_boot.py
# OU Option B : corriger le .service pour pointer sur jarvis_master_launch.py
sudo sed -i 's/jarvis_unified_boot.py/jarvis_master_launch.py/' \
  /etc/systemd/system/jarvis-master.service
sudo systemctl daemon-reload && sudo systemctl restart jarvis-master
```

### P2 — Corriger jarvis-telegram + jarvis-ws (1h)
- Localiser telegram-bot.js (chercher dans git log, peut être supprimé lors d'un refactor canvas/)
- Si supprimé : restaurer depuis `git log --all -- "*telegram-bot.js"` + `git show <hash>:path`
- Pour python_ws : identifier si remplacé par autre chose ou créer stub minimal
- Mettre à jour les .service si les chemins ont changé

### P3 — Corriger CDP port dans orchestrator (15 min)
```bash
grep -r "9108" /home/pamerys/IA/Core/jarvis/orchestrator/ 
# Remplacer 9108 → 9222 dans les fichiers concernés
sudo systemctl restart jarvis-orchestrator
```

### P4 — Ajouter health_patrol.py ou corriger le service (20 min)
- Vérifier si un équivalent existe sous autre nom dans le repo
- Si oui : corriger le chemin dans health-patrol.service
- Si non : le service peut être remplacé par `resource-alert-monitor.py` qui existe

### P5 — Unifier IA/Core/jarvis et Workspaces/jarvis-linux (demi-journée)
- Décider d'une source unique pour les scripts (actuellement split entre les deux)
- Déplacer ai-proxy-server.js vers le repo principal ou créer symlink
- Versionner /home/pamerys/IA/Core/jarvis/ dans un sous-module ou repo dédié

---

## 5. LIAISONS MANQUANTES

| Source | Destination attendue | Liaison manquante |
|---|---|---|
| jarvis-master.service | jarvis_unified_boot.py | Fichier inexistant |
| jarvis-telegram.service | infra/interfaces/canvas/telegram-bot.js | Fichier disparu (refactor ?) |
| jarvis-ws.service | python_ws.server | Module jamais créé ou supprimé |
| health-patrol.service | scripts/health_patrol.py | Fichier jamais migré |
| jarvis-orchestrator | Chrome CDP :9222 | Hardcodé sur ancien port 9108 |
| /home/pamerys/jarvis/ (runtime) | git | Aucune — scripts critiques non versionnés |
| /home/pamerys/IA/Core/ | git | Aucune — composant autonome non versionné |
