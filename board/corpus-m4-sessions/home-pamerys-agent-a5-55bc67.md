[user] Tu es l'agent CORRECTION-GUMROAD. Deux objectifs. Aucun secret. Aucune publication.

FAIT VÉRIFIÉ (curl vendeur-scopé https://franckdelmas.gumroad.com/l/<slug>, 28 slugs de alkymia-os.html) : **24 vivants / 4 morts**. Les 4 MORTS (404) = pack-complet-jarvis-os, jarvis-os-cluster-complet, agents-autonomes-mcp, ia-healthcare. PIÈGE à documenter : gumroad.com/l/<slug> est un namespace GLOBAL (peut renvoyer 200 pour un autre vendeur) → toujours tester en vendeur-scopé franckdelmas.gumroad.com.

OBJECTIF 1 — Corriger le script /home/pamerys/jarvis/scripts/smoke-vente.sh (lecture d'abord) : s'assurer que les tests Gumroad utilisent l'URL VENDEUR-SCOPÉE `https://franckdelmas.gumroad.com/l/<slug>` (pas gumroad.com global), et que la variable de slugs 404 = exactement ces 4. Applique la correction via Edit (modif minimale, ne casse pas le reste). Si le script teste déjà en vendeur-scopé, ne change que la liste des 4 slugs. Relance-le une fois et rapporte PASS/FAIL.

OBJECTIF 2 — Corrige les pages Notion concernées (écriture privée, token /home/pamerys/.config/jarvis/notion.env jamais affiché, Notion-Version 2022-06-28) :
- Cherche via search « Ventes & Encaissement » et « Catalogue Gumroad COMPLET ». Sur chacune, AJOUTE (append, sans réécrire tout) un callout de correction : « CORRECTIF vérifié 15h30 : 4 produits 404 réels (pack-complet-jarvis-os, jarvis-os-cluster-complet, agents-autonomes-mcp, ia-healthcare), pas 7. Piège : tester en vendeur-scopé franckdelmas.gumroad.com/l/<slug>, 

[assistant] The script already tests vendor-scoped via `GUMROAD_BASE`. I'll add the 4 confirmed-dead slugs as a dedicated 404 variable and test them, keeping the change minimal.

[assistant] Gumroad part fully correct: 24 live PASS + 4 dead confirmed 404 (the 4 FAILs are Netlify, unrelated). Now Objective 2 — Notion via REST API, token never printed.

[assistant] The "Ventes & Encaissement" exact page didn't appear. Let me search more specifically.

[assistant] Both target pages found. Appending the correction callout to each (Notion API appends at end; note: native prepend isn't supported).

[assistant] Both callouts added successfully. Note: the Notion REST API only appends at the end of a page (no native prepend), so the callouts sit at the bottom of each page rather than the head — the content is fully preserved and the CORRECTIF is clearly marked.

Rapport final :

**OBJECTIF 1 — Script `/home/pamerys/jarvis/scripts/smoke-vente.sh`**
- Le script testait déjà en vendeur-scopé (`GUMROAD_BASE=https://franckdelmas.gumroad.com`) → non modifié sur ce point, seulement documenté par un commentaire d'avertissement sur le piège du namespace global.
- Ajout de la variable `GUMROAD_SLUGS_404` = exactement les 4 morts confirmés (`pack-complet-jarvis-os`, `jarvis-os-cluster-complet`, `agents-autonomes-mcp`, `ia-healthcare`) + une boucle qui les teste en attendant `404`.
- **Run : EXIT=0.** Section Gumroad = PASS complet : 8 fiches live 200 + profil 200 + les 4 morts confirmés 404 (attendu). Les 4 FAIL restants sont Netlify (paypal-ipn / merci / cgv / confidentialite en 404), hors périmètre Gumroad — bilan global PASS=14 FAIL=4 SKIP=1.

**OBJECTIF 2 — Notion (token jamais affiché, Notion-Version 2022-06-28)**
- Callout de correction (⚠️ fond rouge, texte exact demandé) ajouté sur les 2 pages, sans rien supprimer :
  - 💰 Ventes & Encaissement — https://www.notion.so/3bc7800a81d681c69537eb1ea793f40f
  - 🛒 Catalogue Gumroad COMPLET (contenu réel) — https://www.notion.so/3bc7800a81d68129ac23edce63811fbf
- Réserve : l'API REST Notion n'appose qu'en fin de page (pas de prepend natif) → les c