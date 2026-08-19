[user] Audit READ-ONLY (0 token, grep uniquement, ne modifie RIEN) du câblage front↔back de l'app enseignante Pousseline : /home/pamerys/jarvis/webapp.

Procédure exacte :
1. Modules enregistrés : lis `server.py` — la boucle `for _modname in (...)` + les imports try/except `register(app)`. Liste tous les modules montés.
2. Routes par module : `grep -rnE "@app.route|add_url_rule" *.py` → toutes les routes `/api/...` avec leur module.
3. Onglets front : dans `index.html`, `grep -n 'data-section='` (nav) + le tableau `const SECTIONS = [...]`.
4. Loaders/fetch front : `grep -n "function load|fetch('/api|pJson('/api"` dans `index.html`.
5. Croiser et produire le rapport :
   - (A) Câblés OK : route backend appelée par un fetch/pJson du front.
   - (B) ORPHELINS backend : module `register()` avec des routes `/api/...` mais AUCUN fetch/pJson du front ne les appelle (prêt mais non branché).
   - (C) ONGLETS MORTS : `data-section="X"` dans la nav SANS `<div id="section-X">` OU sans `loadX()`/fetch correspondant.
   - (D) DOUBLONS / routes mortes : 2 modules exposant la même donnée dont un seul consommé (ex connu : `/api/biblio` vs `/api/prof/ressources`).
   - (E) PRIORITÉS de câblage/amélioration : classe les orphelins/onglets morts par valeur (quoi brancher d'abord).

Rends un rapport structuré (5 sections A-E) avec, pour chaque orphelin, le module + la/les route(s) + le fichier. Sois exhaustif mais concis (tableaux). N'exécute aucune commande mutante ; `curl -s localhost:7777/api/...` en 

[assistant] Let me check the supports page's use of /api/modeles and confirm the server responds to key orphan routes.

[assistant] Audit terminé. Tous les fichiers analysés sont sous `/home/pamerys/jarvis/webapp/`. Rapport ci-dessous.

---

# Audit câblage front↔back — Pousseline (`/home/pamerys/jarvis/webapp`)

## Contexte relevé

**Modules montés** (via `server.py`) : 4 imports explicites (`logiciels`, `prof_routes`, `outils_classe`, `ressources`) + boucle `for _modname in (...)` : `sorties, equipe, automations, export_pdf, edt, groupes, appel, ateliers, carnet, eleves_import, ressources, mailer, banque_annuelle, systeme_io, documents, documents_io, autosave, admin, adaptatif, integrations, commandes, barre_magique, supports, assistant, registre`. **`bibliotheque` est explicitement retiré** (commenté, `server.py` l.66-67).

**Front** : 26 onglets `data-section` (l.203-229), tableau `const SECTIONS` (l.1205) — les deux listes concordent. ~90 appels `pJson/fetch` vers `/api/...`.

---

## (A) Câblés OK (route back consommée par le front)

Ne sont listés que les modules pleinement branchés (routes appelées par un `pJson/fetch` d'`index.html`) :

| Module | Routes clés consommées |
|---|---|
| server.py | `/api/status,budget,planning,notes,cluster,jarvis-ask,docs,open,service-status,run-cmd,rdv,voice-record,todo,agents,keywords,system` |
| prof_routes.py | `/api/eleves*, /api/exercice/*, /api/sequence/generer, /api/cahier-journal*, /api/corrections, /api/presence, /api/prof/{bulletin,dashboard,edt,eval,eval/bilan,export,ia-status,programmation,dictee}` |
| outils_classe.py | `/api/prof/{probleme-maths,ritu