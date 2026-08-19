[user] Tu es l'agent EXTRACT-WORKFLOWS. Étudie À FOND le système et extrais TOUS les workflows automatisés (n8n + scripts d'orchestration), pour les transformer en produits vendables. Écris le résultat dans UNE page Notion. AUCUN fichier local.

SÉCURITÉ : lecture seule locale + écriture Notion privé. Ne jamais afficher de secret/credential (les workflows n8n peuvent en contenir → ne recopie AUCUN token/mot de passe, seulement la logique). Aucune publication.

ÉTAPE 1 — Étudie à fond :
- ~/jarvis/n8n/ (fichiers *.json de workflows) : ouvre chacun, comprends le déclencheur (webhook/cron), les étapes, ce qu'il automatise.
- La base n8n si accessible en lecture (~/.n8n/database.sqlite — lecture seule, ne pas verrouiller ; sinon te baser sur les JSON).
- Scripts d'orchestration/automatisation dans ~/jarvis/scripts et ~/jarvis (domino, cascade, dispatch) qui sont des « workflows » réutilisables.

ÉTAPE 2 — Pour CHAQUE workflow : nom, déclencheur, ce qu'il automatise (bénéfice métier concret), pré-requis, et dans quel PACK vendable il rentre (ex : « Pack relances impayés », « Pack tri email », « Pack social autopublish »). Ne recopie aucun credential.

ÉTAPE 3 — Écris la page Notion « 🔧 Extraction — Tous les workflows automatisés » sous le hub « 🧠 JARVIS OS — Hub » (id 3bc7800a-81d6-8100-8f97-c66fe6f52f84). Tableau : workflow · déclencheur · ce qu'il fait · pack vendable · état. Callout d'intro « extraction factuelle, aucun credential inclus ».

Fallback REST : token /home/pamerys/.config

[assistant] Let me read the main workflows and extract names/triggers from the export-wf batch.

[assistant] I have the full n8n inventory. Now let me characterize the key orchestration scripts quickly.

[assistant] Page Notion créée avec succès.

## Rapport

**URL** : https://app.notion.com/p/Extraction-Tous-les-workflows-automatises-3bc7800a81d68128bc19f5c50c5b6955
(sous le hub « 🧠 JARVIS OS — Hub »)

**Workflows extraits** : 71 entrées (regroupant les 85+ workflows n8n de `~/jarvis/n8n/` + les scripts d'orchestration réutilisables de `~/jarvis/scripts`).

**Packs vendables identifiés** : 21, consolidables en ~10 offres commerciales majeures :
- **Pack Prospection & LinkedIn** (WF02/03/04, growth, engagement, Codeur.com) — le plus vendable
- **Pack Tri Email & Assistant Inbox** (WF01 triage IMAP + brouillons LLM)
- **Pack Social Autopublish** (autopublisher, carrousels, Canva, Board publisher)
- **Pack RDV & Agenda** (RDV téléphone→Google Calendar+Email, sync)
- **Pack Veille & Digest / Recherche** (briefings, digests, Manus harvest, Notion report)
- **Pack Supervision Infra (SaaS monitoring)** — la plus grosse famille (~30 workflows : GPU, disque, RAM, services, docker, self-healing, cluster health, Prometheus, audits)
- **Pack Passerelle IA locale 0-token** (LLM Gateway webhook, cascade-cli, multi-llm-orchestrate, dispatcher multi-IA)
- **Pack Trading & Crypto Signals** (majoritairement inactifs)
- **Pack Sauvegarde & Backup**, **Pack Orchestration DOMINO**, **Pack RAG**, **Pack Reporting Dev**

**Structure de la page** : callout d'intro sécurité + phrase de synthèse + tableau à 5 colonnes (Workflow · Déclencheur · Ce qu'il fait · Pack vendable · État).

**Sécurité** : aucun token/cr