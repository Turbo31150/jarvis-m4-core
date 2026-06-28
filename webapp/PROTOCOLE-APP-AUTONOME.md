# PROTOCOLE — Application enseignante autonome (Pousseline / Espace Prof)

> Document maître **unique** de l'orchestration. Complète `CDC-TEETSH-ESPACE-PROF.md` (roadmap des 56 fonctionnalités) : ici = **comment l'app tourne seule**, sans chauffer le M4, avec OpenClaw comme agent maître intégré.
> App : PWA Flask `~/jarvis/webapp`, service `jarvis-webapp` (:7777 / :8443). Repo : `jarvis-m4-core` (dossier `webapp/`).

---

## 1. Principe directeur

**Une seule application, autonome et automatisée.** Tout est dedans : bibliothèque de commandes, agents, IA, branchements, routages, documents générés. L'IA intervient **sur le planning à des moments choisis**, en tâche de fond, **on-demand uniquement** (jamais en boucle → anti-surchauffe).

**Règle d'or économie/chaleur** : *plus il y a de commandes, pipelines et dominos pré-calculés, moins il y a d'inférence donc moins de chauffe.* Le compute coûteux est **dispatché intelligemment** vers les IA/agents **extérieurs ou déportés** (cloud, autres ordinateurs du LAN), jamais sur le CPU du M4 quand il est chaud.

---

## 2. Les 5 couches

| Couche | Rôle | Implémentation |
|---|---|---|
| **1. Données** | Vérité unique, locale, RGPD | `ecole.db` (SQLite) — **jamais dans le cloud** |
| **2. Modules** | Fonctionnalités métier | `module.py` → `register(app)` + onglet `index.html` |
| **3. Cascade IA** | Génération texte 0-token, déportée d'abord | `ai_local.py` (voir §4) |
| **4. Orchestration** | Agent maître + dispatch + dominos | OpenClaw (voir §5) |
| **5. Checkpoint** | Sauvegarde SQL + doc + GitHub | Protocole §7 |

---

## 3. Bibliothèque de commandes, pipelines, dominos

**But** : transformer une intention récurrente en chaîne **pré-calculée et instantanée**, pour ne PAS relancer l'IA à chaque fois.

- **Commande** = action unitaire nommée (ex. `generer_appreciation`, `rotation_ateliers`).
- **Pipeline** = enchaînement de commandes (ex. `EDT → cahier-journal → PDF`).
- **Domino** = pipeline déclenché par un événement/un horaire, dont les résultats sont **mis en cache SQL** (`ai_cache`) → la 2ᵉ exécution est gratuite et instantanée.

Effet thermique : un domino qui sert du cache = **0 inférence = 0 chaleur**. Chaque nouveau domino réutilisable réduit la charge globale.

---

## 4. Cascade IA — DÉPORTÉ D'ABORD (implémenté)

Ordre dans `ai_local.generate()` :
```
1. Cache SQL (ecole.db: ai_cache)        → instantané, 0 watt, 0 chaleur
2. LM Studio M1/M2 (LAN)                  → DÉPORTÉ (autres ordinateurs)
3. Ollama CLOUD (gpt-oss:120b, clé API)  → DÉPORTÉ hors-machine, 0 chaleur ✅ actif
4. Gemini / Antigravity                   → DÉPORTÉ (Google One)
5. Ollama local CPU                        → DERNIER RECOURS, BLOQUÉ si M4 ≥ 82°C
```
- Clé cloud dans `~/.config/jarvis-webapp.env` (chmod 600) chargée par drop-in systemd. **Jamais en clair dans le code/git.**
- Garde-fou thermique : `_gpu_temp()` lit le point le plus chaud (nvidia-smi **+** `/sys/class/thermal`). Au-delà de 82°C, l'inférence locale est refusée → l'app reste utilisable (manuel/cache) **sans cuire le M4**.
- **RGPD** : si le prompt contient des données élève (prénom, besoins) → `cache=False` + rester sur backend non traçant ; anonymiser (`[ELEVE]`) avant tout fallback cloud.

---

## 5. OpenClaw — agent maître intégré (à activer)

OpenClaw est l'**agent maître** : il gère, route, dispatche, en **parallèle / tâche de fond / multitâche**, et est **intégré dans l'application**.

Rôle :
- Reçoit les intentions (UI, planning, événements) et **route** vers la bonne commande/agent/IA.
- **Dispatch déporté** : décide où exécuter (cloud, LAN M1/M2, agent spécialisé) selon charge et température → économie de chaleur.
- Déclenche les **dominos** aux bons moments (ex. nuit : bulletins de classe en série ; matin : suggestions du jour).

État actuel : **aucun container OpenClaw actif** (ports 8085/8086 écoutent mais vides). Prérequis avant intégration :
1. Démarrer le runtime OpenClaw (containers) — **hors boucle d'inférence locale** (cf. mémoire surchauffe).
2. Le brancher sur la cascade §4 (modèle cloud `gpt-oss:120b` par défaut ; `glm-5.2:cloud` = payant, non retenu).
3. Exposer un point d'entrée `/api/orchestrate` côté app pour que l'agent maître soit pilotable depuis l'UI.

⚠️ Anti-surchauffe : OpenClaw **dispatche** le compute, il ne doit pas **générer en boucle locale** sur le M4.

---

## 6. Planning automatisé (IA on-demand)

L'IA agit sur le planning **à des moments précis**, pas en continu :
- Génération/équilibrage de l'emploi du temps (`/api/automations/planning-auto`) — sur demande.
- Suggestions du jour (absences à suivre, bilans dus, sorties imminentes) — pré-calculées par domino, servies en cache.
- Lots lourds (bulletins classe, prépa semaine) — **agents série de nuit** en cron on-demand, dispatchés déporté, jamais en boucle.

---

## 7. Protocole CHECKPOINT / SAUVEGARDE

À chaque checkpoint, **3 cibles** :

| Cible | Quoi | Où | RGPD |
|---|---|---|---|
| **SQL** | `sqlite3 .backup` de `ecole.db` + `notes.db` | `webapp/backups/<db>-<horodatage>.db` (local) | reste **local** (données élèves) |
| **Document** | ce protocole + CDC = la doc unique | `webapp/*.md` | OK |
| **GitHub** | **tout le code** de l'app, un seul dossier | repo `jarvis-m4-core`, dossier `webapp/` | **sans `ecole.db` ni secrets ni binaires** |

**Exclus du push** (`.gitignore`) : `logiciels/` (binaires Wine, 664M), `certs/` (clés TLS), `*.db` (PII élèves), `*.env`, `.prof_token`, `__pycache__/`, `backups/`.

Commande type : backup SQL → `git add` (code+docs) → `commit` → `push origin`.

---

## 8. Invariants (cahier des charges, à respecter partout)

- [ ] Toute fonction IA passe par la cascade **cache → déporté → local bridé** (`ai_local`).
- [ ] **SQL/cache lu AVANT toute inférence** (protocole `protocole-sql-avant-compute`).
- [ ] **Aucune donnée élève** hors `ecole.db` ; anonymisation avant tout fallback cloud.
- [ ] **On-demand only** : zéro boucle d'inférence de fond sur le M4 (plafond 95°C).
- [ ] Chaque module = `register(app)` + table `ecole.db` + onglet `index.html` + PWA offline préservé.
- [ ] Chaque checkpoint = SQL local + doc + push GitHub (sans PII/secrets/binaires).
- [ ] Plus de dominos/cache = moins d'inférence = moins de chaleur.
