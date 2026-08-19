[user] Inventaire READ-ONLY de l'app prof /home/pamerys/jarvis/webapp (Flask, port 7777, base ecole.db). Ne modifie RIEN.

1. Lis `server.py` : liste les modules branchés via le pattern `register(app)` (imports try/except). Lis `ai_local.py` : décris `generate()` (cascade cache→cluster→Ollama, paramètre cache=True, table ai_cache), `backend_status()`, les modèles utilisés. Repère la « bibliothèque 0-token » / `kb_keywords` / `generation_kb` (routeur mot-clé → commande) dans le code ou ecole.db.

2. Liste les onglets front dans `index.html` (boutons data-section + sections + loaders) pour comprendre où ajouter un onglet.

3. Pour CHACUNE de ces briques, dis DÉJÀ PRÉSENT / PARTIEL / À CRÉER + fichier de branchement dans cette app Flask :
   - assistant (barre latérale IA), cascade multi-modèles, personas/agents, mémoire, base de connaissances, analyse-doc, deep-research.

4. Décris comment brancher le registre `/home/pamerys/jarvis/scripts/mochii-commandes-rapides.json` (mapping tâche→modèle, dispatch) dans cette app : quel fichier lirait ce JSON, où.

Rends un rapport structuré : modules register() existants + ai_local (cascade/cache) + emplacement d'ajout d'un onglet + tableau des briques (état + fichier) + comment consommer le registre JSON.

[assistant] Je vais explorer l'app prof pour produire cet inventaire. Commençons par lire les fichiers clés en parallèle.

[assistant] Maintenant, cherchons la bibliothèque 0-token, les onglets front, et les briques.

[assistant] Examinons les tables KB, barre_magique, l'onglet assistant, et le registre JSON.

[assistant] Maintenant regardons l'onglet assistant, les sections/loaders front, et le registre JSON.

[assistant] Vérifions askJarvis, la table profils_types (personas), et la structure de la nav.

[assistant] Vérifions le mécanisme de bascule des sections pour compléter la partie "ajout d'onglet".

[assistant] Voici le rapport d'inventaire complet.

---

# Inventaire READ-ONLY — App prof `/home/pamerys/jarvis/webapp` (Flask :7777, `ecole.db`)

## 1. Modules branchés via `register(app)` dans `server.py`

Tout est monté sur l'objet `app` unique. Deux blocs :

**a) Imports explicites try/except (lignes 21-51)** — chargés en premier, avec message :
- `logiciels` (l.21-26)
- `prof_routes` (l.29-35) → cœur Espace Prof : `/api/eleves`, `/api/exercice/*`, séquences… + exporte `PROF_TOKEN` et `require_token`
- `outils_classe` (l.38-43)
- `ressources` (l.46-51)

**b) Boucle `for _modname in (...)` (l.54-85)** — `__import__(mod).register(app)` :
`sorties`, `equipe`, `automations`, `export_pdf`, `edt`, `groupes`, `appel`, `ateliers`, `carnet`, `eleves_import`, `ressources` (2e fois), `mailer`, `banque_annuelle`, `systeme_io`, `documents`, `documents_io`, `autosave`, `admin`, `adaptatif`, `integrations`, `commandes`, `barre_magique`, `supports`.

**Retiré volontairement** : `bibliotheque` (l.65, commenté) — sa route `/api/biblio` était morte ; l'onglet « biblio » est servi par `ressources.py` (`/api/prof/ressources`).

**Pattern de branchement standard** : chaque module `xxx.py` expose `def register(app):` qui fait des `app.add_url_rule(...)` ou `@app.route`. Ex. type dans `barre_magique.py` l.93-131.

**Garde de sécurité global** (l.100-110) : `@app.before_request` exige le header `X-Prof-Token` sur toute route `/api/` sauf localhost. Tout nouveau module hérite automatiquement de cette protect