[user] Tu audites l'application Flask "Pousseline" dans /home/pamerys/jarvis/webapp/. Objectif : produire une cartographie d'audit FACTUELLE de l'état d'avancement (ce qui est câblé vs orphelin), en vue d'une reprise de travail. NE MODIFIE RIEN, lecture seule.

Fais ces vérifications précises et rends un rapport structuré :

1. **server.py** : liste tous les `import` de modules locaux et tous les `X.register(app)` (ou blueprint enregistré). Dis-moi quels modules .py du dossier sont enregistrés dans server.py et lesquels ne le sont PAS (orphelins backend).

2. Pour chaque module .py suivant, donne en 1 ligne : sa fonction, la présence d'une fonction `register(app)`, et les routes `/api/...` qu'il déclare : adaptatif.py, admin.py, autosave.py, banque_annuelle.py, carnet.py, documents.py, documents_io.py, edt.py, groupes.py, appel.py, ateliers.py, eleves_import.py, integrations.py, commandes.py, automations.py, prof_routes.py, systeme_io.py, adaptatif.py, ressources.py, bibliotheque.py, logiciels.py, sorties.py, equipe.py, outils_classe.py, mailer.py, export_pdf.py.

3. **index.html** : liste les onglets/sections de navigation (cherche les data-tab, onclick, id de sections, libellés d'onglets). Pour chaque onglet, dis si un `fetch('/api/...')` correspondant existe dans index.html (câblé au front) ou si l'onglet est vide/placeholder. Signale les onglets front SANS backend et les backends SANS onglet front.

4. **ai_local.py** : quelle est la cascade IA réelle (ordre des backends : cache

[assistant] I'll start by exploring the directory structure and reading the key files in parallel.

[assistant] Now the front-end tabs, fetch calls, TODOs, and the two modules that showed no `@app.route`.

[assistant] Let me inspect what the `biblio`, `outils`, and `systeme` section bodies actually contain.

[assistant] Audit terminé. Voici la cartographie factuelle.

---

# Audit Pousseline — état de câblage (`/home/pamerys/jarvis/webapp/`)

## 1. server.py — enregistrement des modules

Deux mécanismes : `register(app)` appelés individuellement (logiciels, prof_routes, outils_classe, ressources) + une boucle `for _modname in (...)` (server.py:54-81) qui importe et `register()` les 21 autres. Garde-fou global `@app.before_request` exigeant `X-Prof-Token` sur tout `/api/` sauf localhost (server.py:96-106).

**Modules RÉELLEMENT enregistrés (25) :** logiciels, prof_routes, outils_classe, ressources, sorties, equipe, automations, export_pdf, edt, groupes, appel, ateliers, carnet, eleves_import, bibliotheque, mailer, banque_annuelle, systeme_io, documents, documents_io, autosave, admin, adaptatif, integrations, commandes.

**Modules .py NON enregistrés (pas des modules de routes) :** `ecole_schema.py` (schéma DB), `ecole_demo.py` (données démo), `ai_local.py` (moteur, importé par les autres), `mailer.py`/`export_pdf.py` sont enregistrés. → **Aucun orphelin backend au sens « module route non branché dans server.py »** : les 25 modules demandés ont tous un `register(app)` appelé.

## 2. Fiche par module (fonction · register · routes)

| Module | Fonction | register | Routes `/api` |
|---|---|---|---|
| adaptatif.py | notes/journal pédago adaptatif | ✅75 | /api/adaptatif/note, /journal, /note/<id>, /actualiser |
| admin.py | état admin app | ✅83 | /api/admin/etat |
| autosave.py | backup SQLite | ✅