[user] Tu es l'agent NETLIFY-PREP. Objectif : tâche #14 — préparer TOUT ce qui est faisable pour réparer l'encaissement Netlify/PayPal, jusqu'au point où il ne reste que le clic dashboard de Franck. Lecture seule + écriture de fichiers de préparation. NE MODIFIE RIEN en ligne, ne déploie rien, aucun secret.

CONTEXTE (diag déjà fait) : jarvis-products.html a 56 boutons PayPal dont les URL de retour /.netlify/functions/paypal-ipn, /merci, /cgv sont en 404 → client paie, reçoit rien. Fix = reconnecter le repo jarvis-commercial-2026 (branche fix-paypal-price-validation) sur le site Netlify jarvis-delmas + redeploy.

PRODUIS :
1. Un script de SMOKE-TEST (lecture seule, curl) /home/pamerys/jarvis/scripts/smoke-vente.sh qui teste les URL clés (paypal-ipn, /merci, /cgv, les 7 slugs Gumroad 404, systeme.io) et affiche un tableau PASS/FAIL — pour vérifier AVANT/APRÈS le redeploy. Idempotent, 0 secret, exit 0.
2. Vérifie (lecture seule) où sont les fichiers du site (~/jarvis/sites-2026, ~/jarvis/jarvis-products.html si présent) et si les fonctions Netlify (paypal-ipn, pages /merci /cgv) existent en local dans le repo jarvis-commercial-2026 — confirme qu'elles seront restaurées par le redeploy.
3. La procédure EXACTE côté dashboard Netlify (étapes numérotées) que Franck doit faire : Link repository → jarvis-commercial-2026 → branche fix-paypal-price-validation → Trigger deploy → relancer smoke-vente.sh.

ÉCRIS le tout dans une page Notion « 🔧 Prêt-à-réparer — Encaissement Netlify/PayPal » sous

[assistant] I'll start by exploring the site files, Netlify functions, and the diagnostic context in parallel.

[assistant] The broad finds are timing out on this large filesystem. Let me check interim output and target precisely.

[assistant] Site files found. Now let me read the deployment README and find the repo/functions more precisely.

[assistant] Repo found. Let me inspect the repo structure, branch, and Netlify functions/pages.

[assistant] The functions and pages exist in `jarvis-website/`. Let me confirm netlify.toml location, publish dir, and the exact production URL for the site.

[assistant] All PayPal return URLs confirmed. Let me get the Gumroad/systeme.io URLs from diag-vente while I build the script.

[assistant] The smoke test works and confirms the diagnosis (paypal-ipn, /merci, /cgv → 404). Let me check for diag-vente's reply and verify the Notion token format.

[assistant] Now I'll create the Notion page via REST API. Let me write a script that builds it.

[assistant] The Notion page was created successfully. Everything is done. Let me clean up the scratchpad token-handling script (it read the token but doesn't store it).

[assistant] Tâche #14 terminée. Tout le préparable est fait ; il ne reste que le clic dashboard de Franck.

## Résultats

**1. Script smoke-test** : `/home/pamerys/jarvis/scripts/smoke-vente.sh` (lecture seule, 0 secret, exit 0, idempotent, exécutable).
Premier run (14/08/2026) : **PASS=10 FAIL=4 SKIP=1**
- FAIL (les 404 attendus, confirment le diag) : `/.netlify/functions/paypal-ipn`, `/merci`, `/cgv`, `/confidentialite`
- PASS : accueil `jarvis-delmas.netlify.app` (200), `/mentions-legales`, profil Gumroad + 7 fiches produit (toutes 200)
- SKIP : systeme.io (fournir `SYSTEMEIO_URL=...`)

**2. Vérification locale (le redeploy restaurera tout)** :
- Repo trouvé : `~/jarvis-commercial-2026`, branche courante = `fix-paypal-price-validation` (remote `Turbo31150/jarvis-commercial-2026`)
- Base du site = sous-dossier `jarvis-website/` (son `netlify.toml` : `publish="."`, `functions="netlify/functions"`)
- Présents et prêts à être redéployés : `netlify/functions/paypal-ipn.js` (+ map + tests TDD), `merci.html`, `cgv.html`, `confidentialite.html`, `mentions-legales.html`
- Dernier commit branche : `dd465d4 fix(security): bloque la falsification de montant PayPal (IPN)` → reconnecter restaure encaissement + garde-fou anti-falsification
- Confirmé côté boutique : `jarvis-products.html` = 56 formulaires PayPal, tous `notify_url→/.netlify/functions/paypal-ipn`, `return→/merci`, `business=franckdelmas00@gmail.com`

**3. Procédure dashboard Netlify pour Franck** : app.netlify.com → site `jarvis-delma

[assistant] The background command already returned its useful output earlier. Task #14 is complete — no further action needed. Final report already delivered above (smoke script created and run, local repo/functions verified, dashboard procedure written, Notion page published).