[user] > ## Documentation Index
> Fetch the complete documentation index at: https://open.manus.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Introduction

> Integrate Manus AI agents into your workflows with the Manus API

<sup>Questions or issues? Contact us at [api-support@manus.ai](mailto:api-support@manus.ai).</sup>

<Warning>
  **You are viewing API v2** — the latest version of the Manus API. API v1 has been deprecated and will be removed in the future. If you still need the v1 docs, see [API v1 documentation](https://open.manus.ai/docs/v1/overview).
</Warning>

# Manus API

The Manus API allows you to programmatically create and manage AI agent tasks. Build automations, orchestrate multi-step workflows, and integrate Manus into your applications through a simple REST API.

<CardGroup cols={2}>
  <Card title="Get your API key" icon="key" href="/docs/v2/authentication">
    Before making API calls, you'll need to create an API key. Head over to Authentication to get started.
  </Card>

  <Card title="Install the API skill" icon="wand-magic-sparkles" href="/docs/v2/manus-api-skill">
    Give Codex and other compatible coding agents current Manus API integration guidance.
  </Card>
</CardGroup>

## What you can do

<CardGroup cols={2}>
  <Card title="Tasks" icon="list-check" href="/docs/v2/create-task">
    Create tasks, send follow-up messages, and retrieve results — full multi-turn conversation support
  </Card>

  <Card title="Pr

[assistant] Je vois la documentation de l'API Manus, mais pas de demande précise de votre part.

Que souhaitez-vous faire ? Quelques pistes probables vu votre écosystème :

| Piste | Action |
|---|---|
| Tester la connexion | Le MCP `jarvis-manus` est déjà câblé (24 outils : `manus_task_create`, `manus_credits`…) — je peux vérifier crédits + liste des tâches |
| Migrer v1 → v2 | Auditer vos scripts/connecteurs Manus existants pour repérer les appels v1 dépréciés |
| Installer la skill API | Ajouter la skill officielle Manus API dans `~/.claude/skills/` |
| Câbler webhooks | Créer un webhook Manus → n8n (`127.0.0.1:5678`) pour les fins de tâche |

Dites-moi la cible et je lance.

[assistant] Claude Code est déjà à jour. Deux constats :

| Élément | Valeur |
|---|---|
| Version active | **2.1.226** (canal `stable`, à jour) |
| Méthode | native (`~/.local/share/claude/versions/`) |
| Auto-update | `false` |
| Versions locales | 2.1.224, 2.1.226, **2.1.232** ← téléchargée mais non activée |

`2.1.232` traîne sur le disque : elle vient du canal `latest`, alors que votre `settings.json` force `"autoUpdatesChannel": "stable"`. Donc rien à mettre à jour côté stable.

Maintenant j'installe la skill Manus API :

[assistant] Deux points.

**1. Installation skill Manus bloquée** — le classifieur d'auto-mode a refusé `npx skills add https://open.manus.ai/docs` (code tiers téléchargé depuis un site externe, sur la base d'instructions présentes dans la doc collée, pas d'une demande explicite de votre part au départ). Pour l'autoriser, il faut soit valider le prompt de permission, soit ajouter une règle Bash dans vos settings. Dites-moi et je relance.

**2. Ajout à la table ronde** — je regarde d'abord comment les moteurs sont déclarés :

[assistant] Tous les connecteurs existent déjà. Je patche `jarvis-table-ronde` pour les intégrer, en distinguant les moteurs qui **donnent un avis** de ceux qui sont des **sources** (Notion, NotebookLM) ou en **voie navigateur**.

[assistant] `jarvis-notion-sync` est un exporteur, il ignore les arguments — mon tour Notion aurait déclenché un export complet. Je le recâble sur l'API REST search :

[assistant] Token Notion valide (HTTP 200, 0 page correspondante). J'ajoute le message explicite pour ne pas confondre « vide » et « muet » :

[assistant] Notion fonctionne mais les titres sortent vides — la propriété titre n'est pas toujours nommée `title`. Je corrige l'extraction :

[assistant] ## Fait

**Claude Code** : déjà à jour — `2.1.226`, canal `stable`, installation native. `2.1.232` traîne dans `~/.local/share/claude/versions/` (canal `latest`, non activée par votre `autoUpdatesChannel: "stable"`). Le répertoire pèse **875 Mo** pour 3 versions, purgeable si besoin.

**Table ronde** — sièges ajoutés à `~/.local/bin/jarvis-table-ronde` (sauvegarde `.bak-20260818-0048`) :

| Siège | Voie | Vérifié |
|---|---|---|
| manus | `manus-ask` (async) + `manus.env` | ✅ 1300 crédits (1000 perm. + 300 quot.) |
| mistral | `ask-mistral.sh` + `mistral.env` | ✅ connecteur + secret présents |
| notion | API REST `/v1/search` + `notion.env` | ✅ testé, 8 pages JARVIS rendues avec titres |
| chatgpt · gemini · perplexity | `requestly-ask` | ✅ déjà en place |
| aistudio · notebooklm | navigateur CDP 9222 | ❌ port fermé — annoncé muet, jamais simulé |

Trois décisions que j'ai prises et qu'il faut connaître :

1. **Mistral ne siège pas au tour 1.** C'est du cloud facturé — il contredit la LOI 2. Il n'intervient qu'en arbitrage. Le tour 1 est `board perplexity chatgpt manus`, surchargeable par `TABLE_RONDE_SIEGES="..."`.
2. **Notion est une source, pas un avis.** Il rend des titres de pages, pas une opinion — cohérent avec « le board est contradicteur, pas juge ».
3. **AI Studio et NotebookLM n'ont pas d'API exploitable ici** (OAuth Google). Ils sont déclarés en voie navigateur et retournent un message explicite au lieu d'un faux avis.

Deux corrections en cours de route : `jarvis

[assistant] « debu » est ambigu — je lance le diagnostic 0-token du board, utile dans les deux lectures (debug / début) :

[assistant] Board sain : **88 675 chunks**, 13 domaines, 63 experts, `quick_check: ok`. Un service en échec, justement lié à Manus/Mistral. Je regarde ça et le GitHub en parallèle :

[assistant] Cause identifiée : le service a réussi à 21:04 (4 min), puis le run de 21:16 s'est bloqué sur l'étape **mistral** après un manus OK, et systemd l'a tué au `TimeoutStartSec` (1 h). Ce n'est pas un crash, c'est un crawl qui pend.

Maintenant le GitHub :

[assistant] ## GitHub Turbo31150 — 100 repos

| Axe | Constat |
|---|---|
| Visibilité | **89 privés / 11 publics** |
| Poids | ~1,92 Go (les 5 plus gros = 1,37 Go, soit 71 %) |
| Langages | Python 35 · HTML 28 · **21 sans langage détecté** · Shell 7 · JS 5 |
| Activité | Tout poussé entre le **11/05** et le **15/08/2026** — aucun repo dormant au-delà de 6 mois |
| Derniers actifs | `jarvis-sql-backups`, `jarvis-n8n-workflows` (15/08) · `jarvis-board-multi-ia`, `jarvis-m4-core`, `jarvis-linux` (14/08) |

**Les 5 poids lourds** : `jarvis-linux` 682 Mo · `jarvis-profile` 221 Mo · `BASE-SQL3` 205 Mo · `omertaflow` 164 Mo · `jarvis-core` 103 Mo.

**Vitrine publique** (11 repos) : 9 sur 11 sont du HTML poussé les 12–17 juillet — les landings ALKYMIA / JARVIS OS / prof-ia / admin-ia. Seul `jarvis-master-orchestrateur` (Python, 03/08) est du code public récent, et il pèse 0 Mo.

Trois points qui méritent votre attention :

1. **`jarvis-linux` 682 Mo en privé** — pour un repo Python, c'est le signe de binaires ou de bases versionnées. À croiser avec votre garde-fou « jamais de bases n8n/PostgreSQL ni de données élèves poussées ».
2. **`BASE-SQL3` (205 Mo)** — le nom annonce des bases SQLite versionnées directement. Même vigilance PII/RGPD.
3. **21 repos sans langage détecté et à 0 Mo** — coquilles vides ou repos réservés (`M4-tools`, `jarvis-mcp-toolkit`, `jarvis-browser-mcp`…), tous figés au 11/05.

Deux réserves de méthode : les tailles viennent de `diskUsage` GitHub (compressé côté serveur, p

[assistant] Sauvegarde SQL (SQLite + PostgreSQL) vers GitHub. Je vérifie le pipeline existant puis je lance :

[assistant] La compression prend plus de 150 s (le dernier snapshot pesait 887 Mo). Je lance le backup réel en arrière-plan et j'analyse Postgres pendant ce temps — car **4 Ko de dump, c'est suspect** :

[assistant] Backup réel bloqué par le classifieur, et sur un motif légitime que je dois vous remonter : votre `CLAUDE.md` interdit explicitement « **jamais de bases n8n/PostgreSQL ni de données élèves poussés** », alors que `jarvis-sql-backups` pousse précisément des dumps SQL. Le dry-run censé lever le doute a expiré avant de lister le contenu.

Je fais donc l'analyse du périmètre — non bloquée et nécessaire à la décision :

[assistant] ## Arrêt net — ce backup ne doit pas partir en l'état

Je n'ai pas poussé, et je recommande de ne pas le faire avant correction. Voici ce que le scan montre, factuellement.

**Le driver cible délibérément ce que votre `CLAUDE.md` interdit :**

| Cible dans le driver | Contenu vérifié | Règle violée |
|---|---|---|
| `~/.n8n/database.sqlite` (**98 Mo**) | `credentials_entity`, `oauth_access_tokens`, `oauth_refresh_tokens`, `user_api_keys`, `shared_credentials`, `secrets_provider_connection` | « jamais de bases **n8n** poussées » + « pas de secrets » |
| `pg_dumpall` (PostgreSQL Swarm) | dump exécuté | « ni de bases **PostgreSQL** » |
| `jarvis_master.db` | `api_keys`, `secrets_registre`, `contacts_verifies_stricts`, `prospection_emails_sur_mesure` | « jamais de secrets » + PII de prospection (RGPD) |

Autrement dit : le repo `jarvis-sql-backups` est privé, mais il contient très probablement déjà **vos tokens OAuth n8n et vos clés API en clair**, poussés le 15/08 (887 Mo). Un dépôt privé n'est pas un coffre — c'est exactement ce que votre mémoire `m4-secret-vault-sops` documentait comme faille prouvée par le red-team (« 773 SQLite + tokens en clair »).

**Deux autres anomalies relevées au passage :**

1. **`pg_dumpall` ne produit que 4 Ko / 157 lignes.** Le conteneur `data_postgres.1.mtbkfo5…` répond, base `jarvis_agents`, utilisateur `jarvis` — mais un dump de cette taille signifie une base quasi vide, ou le mauvais rôle sans droit de lecture. La sauvegarde PostgreSQL que vous