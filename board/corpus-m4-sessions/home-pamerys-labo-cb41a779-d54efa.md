[assistant] Pendant que la moisson tourne, je range la clé — mais d'abord un point important.

[assistant] Moisson terminée.

## ⚠️ D'abord : ta clé API est exposée

Tu l'as dictée en clair dans le chat (`mBuBEV…`). Elle est **valide** (testée : HTTP 200, 55 modèles). Je l'ai rangée dans `~/.config/jarvis/mistral.env` (chmod 600, hors git), mais **révoque-la et régénères-en une sur console.mistral.ai** — un secret passé dans un canal de conversation doit être considéré comme brûlé.

## Doc Mistral avalée — `~/labo/bibliotheque/docs-externes/mistral` (71 Mo)

| Voie | Contenu |
|---|---|
| `raw/` | `llms.txt`, `llms-full.txt` (1 Mo, tout le texte), `sitemap.xml` |
| `fiches/` | 63 fiches découpées (`# Titre` + `Source:`) |
| `pages/` | 433 pages HTML→md du sitemap (locale EN) |
| **`source-md/`** | **1392 md/mdx natifs** — clone de `github.com/mistralai/platform-docs-public` |
| `ENDPOINTS.md` | 60 endpoints API v1 |

La 4ᵉ voie est la bonne : c'est exactement le markdown source que tu m'as collé (frontmatter, `<Tabs>` Python/TS/curl, `<SectionTab>`). Le site n'expose pas de `.md` par page — j'ai trouvé le repo Docusaurus derrière. Élagué de 273 → 62 Mo (`.git`, images, polices, médias jetés : on garde le texte, pas le site).

**Série reproductible** : `bibliotheque/series/mistral-moisson.sh` — 0-token, idempotente (relance = ne re-télécharge que ce qui manque).

**Indexé** : 1897 documents Mistral dans `DOCS-INDEX.tsv` (135 140 docs au total). J'ai ajouté `.mdx` à `docs-build.sh`, sinon les 1165 mdx restaient invisibles à `q.sh`.

**Git** : `raw/`, `pages/`, `source-md/` gitignoré

[assistant] Backend câblé. Maintenant je teste, puis j'ingère la matière moissonnée dans le corpus :

[assistant] Le piège documenté dans `ask-agy.sh` — `BOARD_CHAT_MODEL` est déjà posé dans l'environnement du shell :

[assistant] La table ronde tourne. Les experts refusent faute de matière — seule la table de noms était ingérée. J'ingère les fiches :

[assistant] Fait, les deux.

## 1. `mistral.ai/customers` moissonné — 42 études de cas

Nouvelle série `bibliotheque/series/mistral-site-moisson.sh` (site commercial, distincte de la doc technique) → `docs-externes/mistral-site` (672 Ko) :

- `raw/llms.txt` — la carte de l'offre : Studio, Vibe, AI Cloud, Forge, modèles, tarifs
- `clients/` — **42 fiches** : Airbus, BNP Paribas, AXA, Cisco, BMW, ASML, France Travail, ministère des Armées, gouvernement du Luxembourg, CMA CGM…
- `CLIENTS.md` — table récapitulative

## 2. Mistral ajouté à la table ronde

`~/jarvis/board/ask-mistral.sh`, sur le modèle de `ask-agy.sh`. **Vérifié en marche** : 4 experts + arbitre, ~1,5 s chacun, citations sur `[1] airbus` et `[5] dso`.

Trois obstacles réels dans `board.py`, corrigés :

| Obstacle | Symptôme | Correctif |
|---|---|---|
| Le board tape `/v1/completions` (prompt ChatML, contournement du reasoning-runaway de qwen) | HTTP 422 `messages: Field required` | `BOARD_CHAT_API=chat` (défaut inchangé pour le local) |
| Modèles affectés par expert en base = locaux (`qwen3:1.7b`) | Experts en panne **un à un**, table ronde amputée sans le dire | `BOARD_FORCE_MODEL=1` |
| `BOARD_CHAT_MODEL` **déjà posé dans l'environnement** (`qwen3:1.7b`) | `${BOARD_CHAT_MODEL:-défaut}` ne prend jamais → `Invalid model` | variable dédiée `MISTRAL_MODEL` |

Le troisième est exactement le piège déjà documenté pour `BOARD_LMS_URL` dans `ask-agy.sh` — je l'ai commenté au même endroit.

**Corpus ingéré** : 42 fiches clients → `ve

[assistant] Je mets la moisson en place comme service programmé. D'abord un script de rafraîchissement complet :

[assistant] Moisson mise en place — elle se rafraîchit toute seule désormais.

## `mistral-refresh.timer` — systemd --user, lundi 04h00

Un maillon : `series/mistral-refresh.sh` enchaîne les cinq étapes.

| Étape | Résultat au cycle de test |
|---|---|
| Doc technique (`docs.mistral.ai`) | ✓ 71 Mo |
| Site commercial (`mistral.ai` + 42 clients) | ✓ 672 Ko |
| Board ← études de cas → `vente-prospection` | ✓ |
| Board ← doc technique → `inference-locale` | ✓ |
| Board ← carte de l'offre → `souverainete` | ✓ |
| Vectorisation (M6) | ~ **sautée, M6 injoignable** |
| Index `DOCS`/`GITHUB` | ✓ 135 195 docs · 109 dépôts |

**Cycle complet réel : 7 min, 0 étape en échec, `Result=success`.** Je l'ai déclenché pour de bon, pas seulement installé.

**Idempotence prouvée** : au 2ᵉ passage, `42 / 48 / 1 doublons ignorés`, 0 chunk ajouté. Rejouer ne duplique rien — seul le nouveau entre.

Quelques choix à connaître :

- **`set -uo pipefail`, pas `-e`** : un maillon qui casse ne doit pas emporter les suivants. Le script compte les échecs et sort en 1 s'il y en a — donc `systemctl --user status` dira la vérité.
- **Bridé** : `Nice=15`, `IOSchedulingClass=idle`, `CPUQuota=60%`. Ta garde thermique a coupé une commande à 90 °C pendant cette session ; un job de fond n'a pas à provoquer ça.
- **La vectorisation se déclare quand elle ne se fait pas.** M6 dort → le script l'écrit dans le journal au lieu de laisser le board retomber en BM25 sans explication. Quand M6 remonte, le passage suivant rattrape.
- **`s

[assistant] Déjà en place pour Mistral — je vérifie, puis j'étends la mise en place aux autres moissons du même type.

[assistant] `chrome-ext-news.sh` est un lecteur, pas un moissonneur — son archive a été constituée à la main. Seuls `manus` et `mistral` sont rejouables. Je généralise sur ceux-là :

[assistant] Le service tourne encore (l'étape d'indexation prend ~7 min) — j'attends la vraie fin :

[assistant] M6 est revenu — le service est en train de vectoriser (2000 chunks), l'étape qui était sautée tout à l'heure :

[assistant] Bug réel trouvé — **1918 chunks traités, 0 vectorisés, 1918 échecs « réseau »**, et le script affichait quand même ✓ :

[assistant] La correction est bonne : **20/20 vectorisés**, compteur 86 713 → 86 733. Je vérifie l'état du service et relance le cycle proprement :

[assistant] La vectorisation avance pour de bon (86 733 → 86 833, lots de 100). Je consigne le piège :

[assistant] Mise en place généralisée — et le passage à blanc a révélé un bug sérieux que je n'aurais pas vu sans l'exécuter.

## Le bug : la vectorisation ne vectorisait rien

Le premier cycle affichait `✓ vectorisation des nouveaux chunks`. En réalité :

```
✓ 0/1918 vectorises
  echecs : 1918 reseau
```

**1918 chunks partis dans le vide**, pendant que M6 répondait en 0,6 s. Deux causes, corrigées :

1. **`BOARD_LMS_URL` héritée** = `http://127.0.0.1:11434/v1`, un Ollama qui n'existe pas sur M4. Sonder M6 ne suffit pas — il faut écraser la variable. C'est la **3ᵉ fois** que ce même piège frappe (déjà documenté dans `ask-agy.sh`, puis rencontré sur `BOARD_CHAT_MODEL` tout à l'heure).
2. **`board.py embed` sort en 0 même quand il n'a rien vectorisé** → un échec total se déguisait en succès. Le script vérifie maintenant `✓ 0/[1-9]` et compte l'étape en échec.

Preuve du correctif : `✓ 20/20 vectorises`, compteur 86 713 → 86 733, puis 86 833 sur le cycle en cours. **Ça monte pour de bon.**

## `docs-externes-refresh.timer` — un point d'entrée pour toutes les moissons

`series/docs-externes-refresh.sh` avec un registre : ajouter une doc = ajouter une ligne.

| Moisson | État |
|---|---|
| manus (API v2 + centre d'aide) | ✓ 396 Ko |
| mistral (doc + site + table ronde) | ✓ 71 Mo + 672 Ko |
| chrome-extensions | **hors registre, volontairement** |

`chrome-extensions` n'y est pas parce que son archive a été faite à la main et que `chrome-ext-news.sh` n'est qu'un **lecteur** : l'inscrire lais

[assistant] La table ronde est déjà installée (3 lanceurs) — mais elle est cassée sur deux points que je viens de mettre au jour. Je vérifie avant de conclure :

[assistant] Confirmé : **« voie vectorielle HORS SERVICE (http_404) »** — le même piège frappe `jarvis-board`. Je répare l'existant plutôt que d'ajouter un 4ᵉ lanceur :

[assistant] Le correctif marche — la ligne « voie vectorielle HORS SERVICE » a disparu. Mais M6 évince maintenant le modèle de chat sous la charge de vectorisation :

[assistant] Je prouve la table ronde utilisable pendant que M6 est monopolisé — via le backend Mistral :

[assistant] La table ronde était **déjà installée** — trois lanceurs : `board`, `jarvis-board`, `jarvis-table-ronde`. Ce que j'ai fait, c'est la réparer, parce qu'en la testant j'ai trouvé qu'elle tournait dégradée.

## Le bug dans `jarvis-board`

Chaque question sortait :

```
! voie vectorielle HORS SERVICE (http_404) — RRF sur le lexical seul
```

Encore `${BOARD_LMS_URL:-…}` et `${BOARD_CHAT_MODEL:-…}` — variables **déjà posées dans l'environnement** (`127.0.0.1:11434`, `qwen3:1.7b`), donc les défauts ne prenaient jamais. L'Ollama local n'a pas `nomic-embed` → 404 sur les embeddings.

Le pire : **le chat passait quand même**. La panne était donc invisible — seul le classement se dégradait en silence (lexical seul, sans cosinus). Corrigé par variables dédiées (`BOARD_NODE_URL`, `BOARD_NODE_MODEL`), chat et embeddings alignés sur le même nœud 0-token. **Vérifié : la ligne « HORS SERVICE » a disparu.**

C'est la **4ᵉ occurrence du même piège** aujourd'hui (`ask-agy.sh` le documentait déjà, puis `BOARD_CHAT_MODEL`, puis `mistral-refresh.sh`, puis `jarvis-board`). Un `:-` sur une variable héritée est le défaut structurel de ce montage.

## Ce que le test a révélé de plus gênant

**1. Contention sur M6.** Pendant la vectorisation, le chat tombe en `HTTP 400 Model is unloaded` — M6 évince `qwen3.5-9b` pour charger `nomic-embed`. Les deux voies du board se disputent le même nœud. Ça marche en alternance, pas en simultané.

**2. Le corpus ment sur le présent.** Interrogée via Mistral (backend

[assistant] Lecture retenue : **Bard = Gemini** — l'ajouter à la table ronde, comme Mistral. Un adaptateur existe déjà (`ask-agy.sh`, via le shim Antigravity) — je le teste avant de conclure :

[assistant] Trouvé : la table `answers` enregistre **`qwen3:1.7b`** alors que c'est le shim Gemini qui a répondu. Le board ment sur qui a voté — précisément ce que son code dit vouloir empêcher. Même cause :