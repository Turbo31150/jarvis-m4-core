[user] Lecture seule, app Pousseline /home/pamerys/jarvis/webapp/. Objectif : préparer le câblage des 2 derniers modules backend orphelins (routes prêtes, pas d'UI).

1. **systeme_io.py** : lis-le. Résume ses routes /api/systeme/* (config, ping, proxy), ce que fait le proxy, et ce qu'il faut au front pour l'utiliser (clé, toggle). Vérifie dans index.html si l'onglet "systeme" appelle déjà ces routes (grep systeme/config, /ping, /proxy) — sinon c'est orphelin.
2. **bibliotheque.py** vs ressources : lis bibliotheque.py (route /api/biblio). Compare à ce que l'onglet "biblio" du front consomme réellement (grep dans index.html : /api/biblio vs /api/prof/ressources). Dis si /api/biblio est une route morte doublonnée, et laquelle garder.
3. Pour chacun, donne une reco tranchée : CÂBLER (avec quel pattern : section .card + hook navigate + loadX via pJson) ou SUPPRIMER du register (dédoublonnage). 

Rends un rapport markdown compact : par module → état (orphelin/doublon), reco (câbler/supprimer), et si câbler : la liste précise des éléments front à ajouter. Factuel, bref.

[assistant] Let me examine the systeme section, the `loadIntegrations` function, and `loadBiblio` in detail.

[assistant] Voici le rapport. Faits confirmés : les deux modules sont bien enregistrés dans `server.py` (lignes 65 et 69 de la liste MODULES), donc backend actif ; à confronter au front `index.html`.

---

# Rapport câblage — 2 modules orphelins

## 1. `systeme_io.py` — intégration systeme.io (SaaS marketing)

**Routes exposées** (`register(app)`, protégées par le garde token global) :
- `GET /api/systeme/config` → `{enabled, key_set, ready}` (jamais la clé en clair)
- `POST /api/systeme/config` → set `{enabled}` et/ou `{api_key}` (+ `{clear_key}`) ; persistés dans `ecole.db` table `kv`, clé `systeme_io_config`
- `POST /api/systeme/ping` → teste la clé via un `GET /api/contacts?limit=10`, ne modifie rien
- `POST /api/systeme/proxy` → proxy générique `{method, path, params, json}` vers `api.systeme.io` (path doit commencer par `/api/`, méthodes GET/POST/PATCH/DELETE). C'est le socle des futurs outils (contacts, tags, tunnels…) : `_call()` gère l'auth `X-API-Key` une seule fois.

**Ce qu'il faut au front** : un champ clé API + un toggle `enabled`, POST sur `/api/systeme/config`, un bouton « Tester » (POST `/api/systeme/ping`), et lecture d'état au chargement (GET `/api/systeme/config`). Désactivé par défaut : rien ne part tant que `enabled && api_key`.

**État : ORPHELIN confirmé.** `grep` sur `systeme/config`, `/ping`, `/proxy`, `/api/systeme` dans `index.html` = **0 occurrence**. 
Piège de nommage : l'onglet `#section-systeme` existe (nav ligne 225, `navigate('systeme')`) mais c'est le *