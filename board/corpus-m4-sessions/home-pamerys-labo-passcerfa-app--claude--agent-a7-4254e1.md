[user] Contexte : l'utilisatrice a une app « exemple » de facturation électronique dans /home/pamerys/app.atsd.info (Flask/FastAPI backend + frontend HTML, page client avec choix de PDP + un CTA d'affiliation Pennylane qu'on vient d'ajouter). Elle dit que sa VRAIE application est bien plus complète — probablement liée à « PassCerfa » (démarches administratives). Elle veut transposer le modèle « services certifiés + affiliation + CTA » sur sa vraie app, avec un design différent et de la scalabilité.

Tâche (LECTURE LOCALE, read-only — n'écris aucun code) :
1. Explore le repo modèle : /home/pamerys/app.atsd.info — comprends l'architecture de la page client (frontend/e-invoicing-settings.html), le pattern config (backend/config.py, .env.example), le connecteur PDP (backend/pdp_connector.py), et le CTA affiliation qu'on a ajouté (chercher PENNYLANE_AFFILIATE_ID).
2. Trouve la vraie app de l'utilisatrice : cherche « passcerfa » et « demarches.db » sous /home/pamerys (repos, skills .claude/skills/passcerfa-demarches, dossiers). Décris sa structure (backend, base SQLite, front, modules/onglets, combien de « dossiers »/démarches).
3. Produis un PLAN DE TRANSPOSITION concret : comment porter (a) le sélecteur de services certifiés, (b) le pattern config affiliation (env var + referral URL), (c) le CTA de parrainage, dans l'architecture de la vraie app — en listant les fichiers à créer/modifier, sans les écrire.

Écris le plan dans /home/pamerys/.claude/jobs/161b6ed8/tmp/veille-04-transpositio

[assistant] I'll explore both repos in parallel to understand the model and find the real app.

[assistant] Let me read the model's CTA/config details and the real app's server, front, and data.

[assistant] Plan écrit dans `/home/pamerys/.claude/jobs/161b6ed8/tmp/veille-04-transposition-passcerfa.md`.

Résumé (10 lignes) :

1. **Vraie app = PassCerfa** — `/home/pamerys/labo/passcerfa-app` (pré-remplissage CERFA via FranceConnect+, propriétaire Franck Delmas).
2. **Stack** : backend Node/Express (`server.js`, routes `/api/{auth,cerfa,llm,facturx}`, ~13 services, pipeline 8 étapes, orchestrateur multi-agents + ~22 profils-agents) ; front **Vite/TypeScript SPA** (`frontend/src/`, a11y-first) ; dockerisé (compose + swarm).
3. **Données** : `cerfa-registry.json` (5 seed → catalogue officiel ~15 578) ; SQLite `passcerfa.db` (scenarios/simulations/agent_weights + user_profils/injection_templates, actuellement vide). Tracker perso séparé `demarches.db` = 44 démarches / 51 organismes / 39 courriers.
4. **Modèle à porter** (`app.atsd.info`, FastAPI+HTML) : `<select id="pdp-select">` de PDP certifiés ; env-vars `PENNYLANE_AFFILIATE_ID` + `PENNYLANE_REFERRAL_URL` (gabarit `{affiliate_id}`) ; carte CTA `#pennylane-affiliate` conditionnelle.
5. **5 étapes de transposition** :
   - (a) `data/partners-registry.json` (catalogue partenaires certifiés, data-driven scalable) + `backend/routes/partners.js` + montage dans `server.js`.
   - (b) `backend/config/affiliation.js` (config centrale absente) lisant `AFFILIATE_<X>`/`REFERRAL_URL_<X>` depuis `.env.example` → `buildReferralUrl()`.
   - (c) `frontend/src/partners/selector.ts` (équivalent `pdp-select`, filtré par profil détecté).
   - (d) `fronte