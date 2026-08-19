[user] Tu es l'agent MOISSON-DOMINO-ATOMES. Objectif : moissonner les chaînes DOMINO, les artefacts, et les « atomes logiques » réutilisables, et les cataloguer dans Notion. AUCUN fichier local. Lecture seule. Aucun secret/PII recopié. Aucune publication.

SOURCES (lecture seule, M4 + M1 disque) :
- Domino : ~/jarvis (domino-action-cascade.yaml, cli/cascade.py, action_validation/, dominos, chaînes) et /media/pamerys/JARVIS-M1/home/turbo/jarvis équivalents.
- Atomes logiques : les skills run-atomes-logiques / run-logique-atomes (~/.claude/skills/) et leurs drivers ; toute brique « atome » réutilisable.
- Artefacts : livrables/artefacts générés réutilisables (gabarits, templates d'action).
Liste/compte d'abord, puis échantillonne.

MOISSON : pour chaque chaîne domino / atome / artefact → nom, intention/déclencheur, ce qu'il enchaîne (étapes génériques sans secret), et « valorisable (vente/automatisation) ? ». Dédoublonne avec les workflows déjà catalogués (note les nouveaux). Vise 15-40 items.

ÉCRIS la page Notion « ⛓️ Moisson — Dominos, artefacts & atomes logiques » sous le hub « 🧠 JARVIS OS — Hub » (id 3bc7800a-81d6-8100-8f97-c66fe6f52f84). Tableaux par type. Callout d'intro. Rattache à l'index maître (id 3bc7800a81d6813c827bff98ce414d47) via bookmark append.
REST : token /home/pamerys/.config/jarvis/notion.env (NOTION_TOKEN, jamais affiché), « Notion-Version: 2022-06-28 ». Lots de 100 blocs.

Rapport final concis : URL page + nb de dominos/atomes/artefacts + rattachée à l'index.

[assistant] I'll start by surveying the DOMINO sources, atomes logiques skills, and artefacts.

[assistant] I'll survey the domino bin dir, atomes skills, and the domino engine docs in parallel.

[assistant] Moisson terminée.

**Page Notion créée** : ⛓️ Moisson — Dominos, artefacts & atomes logiques
URL : https://app.notion.com/p/Moisson-Dominos-artefacts-atomes-logiques-3bc7800a81d681babfdcdd4b8b9f02e8
(sous le hub 🧠 JARVIS OS, rattachée à l'index maître via bookmark ✓)

**Contenu** (callout d'intro + 3 tableaux) :
- **Dominos** — 13 lignes cataloguées : runner unifié `bin/dominos` (sources [C] compilés + [S] séries), recovery auto-heal (13 signaux → chaînes), chaînes N8N (HEALTH_CASCADE / LEARNING_LOOP / BACKUP_CHAIN), agentchain-content/voice, box-docsis, aspiration, cascade-until-success, et les grandes familles `cw-*` (4997) / `mass-*` (250) / métier. Volume réel : **5256 dominos compilés + 260 séries biblio**.
- **Atomes logiques** — 7 lignes : moteur d'atomisation (**597 683 atomes**, matrice de transitions type Markov), skills `run-atomes-logiques` (garde-fou léger) et `run-logique-atomes` (pilote 4 CLI), + les 5 CLI (atomiser/extraire/simuler/inscrire/logique). Piège documenté : `extraire` seul → transitions=0 → échec silencieux.
- **Artefacts** — 9 lignes : `domino-compile.py`, générateurs de masse, autogen engine, indexer git, utilitaires `bin/domino-*`, catalogues (README/RECOVERY/N8N-INDEX/CARTE-MENTALE), le produit forge **jarvis-domino-engine (835 pipelines, 89 €)** et les 260 séries validées.

**Points clés / dédoublonnage** : les dominos agentchain-* et chaînes N8N recoupent des workflows déjà catalogués. **Nouveaux** : le moteur d'atomes logiques, la famille `cw