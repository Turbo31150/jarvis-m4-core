# DIAG — Ventes hors Gumroad (systeme.io + checkout Netlify)

> Diagnostic **lecture seule** du 2026-08-14. Aucune modification en ligne, aucun déploiement, aucun secret touché.
> Objectif : comprendre pourquoi l'encaissement ne passe **que** par Gumroad, et lister les gestes exacts pour rouvrir les autres canaux.

## 1. Tableau des URLs testées

| URL testée | Code HTTP | État |
|---|---|---|
| https://franckdelmas00.systeme.io | **404** | Sous-domaine entier mort (aucun funnel publié) |
| https://franckdelmas00.systeme.io/accueil | **404** | idem |
| https://franckdelmas00.systeme.io/vente · /offre | **404** | idem |
| https://jarvis-delmas.netlify.app | **200** | En ligne — page « Franck Delmas — Architecte IA » (ancien build) |
| https://jarvis-delmas.netlify.app/.netlify/functions/paypal-ipn | **404** | **Fonction IPN absente du build déployé** |
| https://jarvis-delmas.netlify.app/merci | **404** | Page de retour après paiement absente |
| https://jarvis-delmas.netlify.app/cgv | **404** | Page CGV absente |
| https://jarvis-products.netlify.app | **200** | En ligne (template services JARVIS OS) |
| https://franckdelmas.gumroad.com/l/jarvis-architecture | **200** | Produit Gumroad vivant (canal qui marche) |

## 2. Mécanique de checkout par site (sources locales `sites-2026/*.html`)

| Page source | Canal de vente | Verdict |
|---|---|---|
| `jarvis-products.html` | **PayPal `_xclick`** (56 formulaires) → `notify_url` et `return` vers `jarvis-delmas.netlify.app` | Cassé côté Netlify (voir §3) |
| `alkymia-os.html`, `bespoke-pony-491fd1.html` (JARVIS Academy) | **Gumroad** (71 liens `/l/...`) | OK — c'est le seul canal fonctionnel |
| `admin-ia`, `agent-sans-coder`, `alkymia-oss`, `euphonious-youtiao`, `reparation-ia`, `transcription-ia-jarvis` | **`mailto:` uniquement** (2-3 liens, aucun bouton d'achat) | Pas de checkout du tout (capture lead par email) |

Extrait type d'un formulaire PayPal (`jarvis-products.html`) :
- `business = franckdelmas00@gmail.com`
- `return = https://jarvis-delmas.netlify.app/merci`
- `notify_url = https://jarvis-delmas.netlify.app/.netlify/functions/paypal-ipn`

## 3. Causes racines

**A. systeme.io — sous-domaine non publié + clés révoquées.**
`franckdelmas00.systeme.io` renvoie 404 sur toutes les pages : il n'y a **aucun funnel/page publié** sur ce sous-domaine (ce n'est pas une page précise en panne, c'est tout le tunnel qui est absent). Côté local, `AUDIT-SESSION-HANDOFF.md` confirme : les clés API **et** le MCP systeme.io ont été **révoqués** par l'utilisatrice, le module `systeme_io.py` est désactivé (OFF par défaut). systeme.io n'est donc, à ce jour, relié à aucune vente.

**B. Checkout PayPal cassé côté Netlify — le build déployé est obsolète.**
Le POST vers `paypal.com` fonctionne (le formulaire est valide), **mais** les 3 URL que PayPal rappelle sur `jarvis-delmas.netlify.app` sont toutes en 404 :
- `/.netlify/functions/paypal-ipn` → l'IPN qui doit livrer le PDF **n'existe pas dans le build** → aucune livraison automatique.
- `/merci` → l'acheteur tombe sur un 404 **après avoir payé** (aucune confirmation).
- `/cgv` → lien mort dans les encarts de confiance.

**C. Repos Netlify non reliés (source du build obsolète).**
`sites-2026/README-DEPLOIEMENT.md` indique que les 9 sites se déploient **par glisser-déposer manuel du `.html`** (branche `sites-2026-refonte`), donc **repo non connecté** à Netlify. Les corrections (`sites-2026-refonte`) n'ont jamais été poussées en ligne → Netlify sert encore l'ancien build. Le correctif PayPal vit dans un **autre repo** (`jarvis-commercial-2026`, branche `fix-paypal-price-validation`) qui héberge la fonction IPN sur le site `jarvis-delmas` — non déployé lui non plus, d'où le 404 de la fonction.

## 4. Ce que Franck doit faire lui-même (dashboard — irremplaçable par script)

**systeme.io (si l'on veut ré-ouvrir ce canal)**
1. Se reconnecter au dashboard systeme.io.
2. **Recréer/republier** un tunnel ou une page de vente sous `franckdelmas00.systeme.io` (aujourd'hhui vide) — vérifier le statut « Publié », pas « Brouillon ».
3. Régénérer une **nouvelle clé API** (l'ancienne est révoquée) → la coller dans le coffre age, **jamais en clair/git**, puis réactiver le module via l'onglet 🚀 de l'app.

**Netlify — `jarvis-delmas` (site qui encaisse le PayPal)**
1. Netlify → projet `jarvis-delmas` → **Site settings → Build & deploy → Link repository** : reconnecter le repo `jarvis-commercial-2026`, branche `fix-paypal-price-validation` (celle qui contient la fonction `paypal-ipn` + le garde-fou prix).
2. Vérifier que la config expose bien les Functions (`netlify/functions/`) et publie `/merci`, `/cgv`.
3. **Redeploy** (Trigger deploy → Deploy site).
4. Test réel : achat au **prix normal** → le PDF doit arriver ; un montant falsifié doit donner `amount mismatch` dans les logs Functions.
5. Confirmer que le compte marchand PayPal est bien `franckdelmas00@gmail.com`.

**Netlify — les 9 sites vitrine (build obsolète)**
- Soit **connecter** chaque site à la branche `sites-2026-refonte` (recommandé, fin des drag-drop),
- soit **glisser-déposer** les `.html` corrigés (mapping fichier→site dans `README-DEPLOIEMENT.md`).

## 5. Ce qui peut être scripté plus tard (pas besoin de Franck en direct)

- Vérification post-déploiement automatisée (smoke test HTTP des URLs du §1, alerte si un 404 réapparaît).
- Contrôle de cohérence des `notify_url`/`return` dans tous les `sites-2026/*.html` avant chaque deploy.
- Une fois les repos reliés : redeploy déclenché par push git (plus de drag-drop manuel).
- Remplacement des `mailto:` par des vrais boutons Gumroad sur les 6 sites sans checkout (montée en gamme capture → vente).

---

## Synthèse — 2-3 causes racines + geste le plus rapide

1. **systeme.io = tunnel non publié + clés révoquées** → canal simplement inexistant aujourd'hui.
2. **Checkout PayPal cassé** : la fonction IPN, `/merci` et `/cgv` sont en **404** sur `jarvis-delmas.netlify.app` (build obsolète) → l'acheteur paie mais ne reçoit ni confirmation ni PDF.
3. **Repos Netlify non reliés** (déploiement par drag-drop manuel) → les corrections `sites-2026-refonte` et le fix PayPal `jarvis-commercial-2026` ne sont jamais montés en ligne.

**Geste le plus rapide pour ré-encaisser hors Gumroad :** dans Netlify, **relier le site `jarvis-delmas` au repo `jarvis-commercial-2026` (branche `fix-paypal-price-validation`) puis Trigger deploy** — cela restaure d'un coup la fonction `paypal-ipn`, la page `/merci` et `/cgv`, réparant tous les boutons PayPal de `jarvis-products`. systeme.io peut attendre (recréation de tunnel + nouvelle clé), Gumroad continue d'encaisser entre-temps.
