# 🎯 Cascade parfaite — système assistant « professeure des écoles »

Index maître de l'écosystème de Claire (Pamerys). Relie l'app unique, les skills, les agents
et l'ordre d'exécution IA. Objectif : décharger les tâches répétitives, se recentrer sur les
élèves, **0 token facturé** par défaut.

## 1. L'app unique (cœur)
`~/jarvis/webapp` — PWA Flask, service `jarvis-webapp`, HTTP :7777 / HTTPS :8443 (tél).
Onglets : Dashboard · Planning · Budget · Notes · **Espace Prof** · Logiciels (Wine) · Assistant ·
Documents · Système · Calendrier · Agents · TODO.

Modules backend (`register(app)` dans server.py) :
- `prof_routes.py` — élèves, exercices (3 niveaux + différenciés/élève), corrections, séances,
  cahier-journal, mails parents, présences. Données : `ecole.db`. Protégé par `@require_token`.
- `ai_local.py` — moteur IA 0-token (voir §3).
- `logiciels.py` — cockpit Wine (Gén.5, Biblio Manuels, Read&Write, PhotoFiltre).

## 2. Les 6 skills (savoir-faire réutilisable, ~/.claude/skills/)
| Skill | Se déclenche sur | Rôle |
|---|---|---|
| **espace-prof-app** | « ajoute un outil/onglet à mon app » | Étendre l'app (route, module, front) |
| **differenciation-pedagogique** | « différencie cet exercice / par élève » | 1 notion → variante par profil |
| **cahier-journal-preparations** | « rédige mon cahier-journal / prépare une séance » | Séances + journal depuis l'EDT |
| **evaluation-lsu-bulletins** | « appréciations bulletin / LSU / synthèse » | Notes, compétences, livret |
| **communication-parents** | « écris un mail aux parents / mot liaison » | Communication familles |
| **creer-outil-cascade-locale** | « crée un outil/agent / mets au point la cascade » | Méta : créer outils/agents/skills |

## 3. La cascade IA — ORDRE D'EXÉCUTION (règle d'or : 0-token d'abord)
```
1. SQL / cache          → lire ecole.db (ai_cache) ou bases AVANT toute inférence   (0 token)
2. Ollama local         → ai_local.generate / lm-ask.sh — gemma3:4b puis qwen2.5:7b (0 token, CPU, lent)
3. Gemini (Google One)  → gemini-ask.sh / mcp jarvis-agents.gemini_ask              (0 token, qualité+)
4. Antigravity / cluster→ si dispo (M1/M2 actuellement MORTS)                        (0 token)
5. Opus (moi)           → orchestration, archi, debug critique UNIQUEMENT            (💸 facturé)
```
**Anti-surchauffe** : on-demand seulement. NE PAS relancer de boucles d'inférence permanentes
(domino/cowork) sur ce PC seul → emballement thermique 90-100°C. Cf. mémoire M4.

## 4. Agents (à créer au besoin via creer-outil-cascade-locale)
Pistes utiles, non encore créés : `prof-eval-batch` (génère tous les bulletins d'une classe en
série, nuit), `prep-semaine` (remplit le cahier-journal de la semaine depuis l'EDT), `veille-progs`
(suivi B.O.). Les créer en `.claude/agents/*.md`, tools restreints, branchés sur la cascade §3.

## 5. État & reste à faire
- ✅ App unique + Espace Prof (front+back) + cockpit Wine + 6 skills + config (fastMode, auto-restart).
- ⏳ Génération 5 (Explorer) : licence à fournir (compte generation5.fr / CD).
- ⏳ Biblio Manuels : finaliser install Adobe AIR sous Wine.
- ⏳ Téléphone : installer la PWA (token) → pilotage vocal.
- ⏳ Optionnel : optimiser vitesse IA (précharger gemma3:4b au boot, baisser max_tokens), agents §4.

## 6. Vérifier vite
`curl -s localhost:7777/api/prof/ia-status` (backends) · ouvrir :7777 onglet Espace Prof ·
restart auto à chaque édition de webapp (hook). Token tél : `~/jarvis/webapp/.prof_token`.

## 7. ROADMAP — mise au point de la cascade (ordonnée, par priorité)
Objectif : cascade fiable + rapide, 0 token, sans surchauffe. Faire dans l'ordre.

| # | Étape | Pourquoi | Coût |
|---|---|---|---|
| P1 | **Précharger gemma3:4b** (warm au boot via `ollama run gemma3:4b ''` au démarrage du service, `keep_alive`) | 1er appel = 50 s de chargement à froid → préchargé = réponses rapides | RAM +3 Go |
| P2 | **Baisser `max_tokens`** des exercices 1800→~1000 sur CPU | Génération CPU lente ∝ tokens → 2× plus rapide | 0 |
| P3 | **Ajouter Gemini en fallback qualité** dans `ai_local` (étage 3, via `gemini-ask.sh`) | Si Ollama trop lent/faible → bascule 0-token Google One | 0 |
| P4 | **Bouton « Tester la cascade »** dans l'app (appelle `/api/prof/ia-status` + 1 mini-génération chronométrée) | Voir d'un coup quel backend répond et en combien de temps | léger |
| P5 | **Surveiller RAM/thermique** : ne PAS précharger si RAM <2 Go libres ; respecter le gouverneur 82°C | Éviter l'emballement (cf. mémoire surchauffe M4) | 0 |
| P6 | **Agents série de nuit** (bulletins classe, prépa semaine) en cron on-demand | Décharger les gros lots quand le PC est libre, jamais en boucle | moyen |
| P7 | **Tester en réel** : 2 élèves + 1 exo différencié + 1 correction | Valider toute la chaîne avant d'aller plus loin | 0 |

Règle : à chaque étape, vérifier que le runtime reste **0 token** et **on-demand** (pas de boucle).
