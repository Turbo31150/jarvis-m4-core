[user] Tu es l'agent MOISSON-M1-JARVIS. Objectif : moissonner les WORKFLOWS RÉELS (n8n, scripts d'orchestration, séries, dominos, pipelines) présents sur le disque de l'ancien M1, et les cataloguer dans Notion. AUCUN fichier local, rien copié/écrit sur les disques (lecture seule stricte).

SÉCURITÉ CRITIQUE : lecture seule. Le disque M1 contient de la PII et des credentials (ex dossiers créanciers, démarches admin, bases SQL, .env, credentials n8n). Tu ne dois JAMAIS ouvrir/recopier de PII (données personnelles, élèves, clients) ni de secret/token/clé. Si un workflow contient un secret, écris [SECRET]. Ignore les dossiers manifestement PII (dossier-creanciers, demarches-admin, *creancier*, *eleve*, *client-*). Aucune publication. Ne touche PAS au disque USB Toshiba (défaillant).

PERFORMANCE : gros disque (931 Go). Ne lis pas de gros fichiers en entier ; liste d'abord, échantillonne, grep ciblé. Si Bash bloqué par garde thermique, échantillonne moins.

RACINE À SCANNER (lecture seule) : /media/pamerys/JARVIS-M1/home/turbo/
Cibles prioritaires :
- .../jarvis/n8n/ (workflows *.json)
- .../jarvis/scripts, .../jarvis/multiagent, .../jarvis/cli (scripts d'orchestration/dispatch/domino)
- .../labo/bibliotheque/series/ (chaînes d'action « séries »)
- .../jarvis/dual, .../jarvis/audit (pipelines)
Liste ce qui existe (dossiers + compteurs) avant d'entrer dans le détail.

MOISSON : pour chaque workflow/série/script d'orchestration réutilisable → nom, intention, déclencheur, étapes (générique,

[assistant] Le montage M1 est accessible. Je vais explorer les cibles prioritaires en parallèle.

[assistant] Le dossier labo est root-only (inaccessible). Je me concentre sur n8n et les scripts d'orchestration. Analysons les workflows n8n et l'inventaire scripts.

[assistant] Beaucoup de matériel. Échantillonnons les en-têtes/docstrings des scripts clés d'orchestration pour en capter l'intention.

[assistant] J'ai assez pour cataloguer. Vérifions rapidement les dominos compilés et le pipeline audit pour compléter.

[assistant] 5529 dominos compilés. Échantillonnons leur structure et l'en-tête du pipeline audit.

[assistant] Récupérons les grandes familles de dominos par préfixe pour caractériser le corpus.

[assistant] Moisson M1 terminée.

## Rapport — MOISSON-M1-JARVIS

**Page Notion créée et publiée sous le hub « 🧠 JARVIS OS »**
URL : https://app.notion.com/p/Moisson-M1-Workflows-r-els-n8n-scripts-s-ries-3bc7800a81d6815ea477c0d4cf2064ad
Rattachée à l'index maître via `link_to_page` (append OK).

**Moissonné (lecture seule, depuis `/media/pamerys/JARVIS-M1/home/turbo/jarvis`)** — 4 tableaux par type :

| Type | Nb catalogué | Points saillants |
|---|---|---|
| Workflows n8n | 7 | OMEGA 01-04 (triage mail IMAP, LinkedIn auto, expansion réseau B2B, prospection NotebookLM), planning-trigger, daily_backup, system_monitor |
| Scripts d'orchestration/dispatch | 14 | multi-llm-orchestrate (vote pondéré), jarvis-keyword-dispatch, task/proxy-dispatcher, master_autopilot_full_live 24/7, orchestrateur local double-maître |
| Séries biblio & routeur d'intention | 11 | bloc.sh, cascade-bibliotheques, protocole.sh (7 étapes), cascade-micro-actions (~92k blocs), action_series, planning-mega |
| Pipelines & dominos | 9 + corpus | domino_autogen_engine, mass_domino_builder (10 légions), **dominos-compiled = 5529 séries bash** (4997 auto-générées cw + ~530 curées), domino-mail-triage, domino-linkedin-realtime, jarvis-audit.sh, jarvis-deepsearch |

**Différences vs page M4** : ce sont les versions M1/OMEGA (executeCommand + LLM local M1/M2/OL1, CDP :9222) ; le moteur mass-domino et le corpus 5529 séries sont spécifiques M1.

**Sécurité** : aucun secret ni PII recopié — seuls noms/intentions/étapes générique