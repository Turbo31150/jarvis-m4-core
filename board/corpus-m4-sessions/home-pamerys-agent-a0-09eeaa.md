[user] Tu es analyste. Objectif : produire une COMPARAISON PRO des plateformes de vente + hébergement pour AlkymIA (marque souveraine/EU/RGPD, vend produits digitaux 19-597€ + offres B2B 18-20k€, profil solo/TPE, veut « plus pro que Netlify »). Écris dans Notion. Aucun secret. Rien publié.

MÉTHODE : WebSearch (le connecteur Perplexity est en 401) pour vérifier prix/features 2026. Chaque chiffre sourcé ; « non trouvé » si absent. N'invente rien.

RECHERCHE (comparer) :
1. **Vente digitale tout-en-un** : systeme.io (FR), LemonSqueezy, Paddle, Podia, Payhip, Stan.store — prix/commission, gestion TVA UE (Merchant of Record ou pas), tunnels, email, abonnements.
2. **Hébergement statique pro** : Cloudflare Pages, Vercel, Netlify (référence actuelle), OVHcloud Pages/hosting, Scaleway — prix, perf, localisation données (EU/souverain), domaine custom.
3. **RDV/B2B** : Cal.com (self-hosted vs cloud), Calendly — souveraineté.

LIVRABLE — page Notion « 🏗️ Choix plateforme PRO — vente & hébergement AlkymIA » sous le hub « 🧠 JARVIS OS — Hub » (id 3bc7800a-81d6-8100-8f97-c66fe6f52f84) :
- Callout « comparaison sourcée pour un lancement souverain/EU ».
- 3 tableaux (Vente / Hébergement / RDV) : Solution · Prix/commission · TVA UE gérée ? · Souveraineté (données EU ?) · Pour AlkymIA (recommandé/à éviter + pourquoi).
- Section « TRANCHÉ — le setup recommandé » : la combinaison optimale pour AlkymIA (vente + hébergement + B2B), avec le coût mensuel estimé et pourquoi c'est plus pro que Netlify+Gumroa

[assistant] I'll research the platforms via WebSearch, then build the Notion page. Let me load the tools and start searching in parallel.

[assistant] The build_notion.py already exists from a prior session. Let me write to a fresh name.

[assistant] Page créée et rattachée à l'index maître. Rapport final.

## Livrable

Page Notion créée sous le hub « JARVIS OS » et rattachée à l'index maître (lien ajouté).
**URL** : https://app.notion.com/p/Choix-plateforme-PRO-vente-h-bergement-AlkymIA-3bc7800a81d68111bc72e9d4a3a29ac8

Contenu : callout souveraineté + 3 tableaux sourcés (Vente / Hébergement / RDV) avec colonnes Prix, TVA UE gérée, Souveraineté, Reco AlkymIA + sections « TRANCHÉ » et « Migration ». Aucun secret, rien publié en ligne (page privée uniquement).

## Setup recommandé (tranché)
- **Vente digitale 19-597 €** : Payhip (TVA UE collectée ET reversée dès le plan gratuit, MoR sur la TVA, 5 %) — ou Lemon Squeezy si license keys/checkout premium souhaités.
- **B2B 18-20k €** : facturation directe société + Paddle (MoR, sans surcharge internationale) pour les abonnements SaaS récurrents.
- **Hébergement** : OVHcloud ou Scaleway (français, exempts CLOUD Act, données 100 % EU) ; Cloudflare Pages seulement si la perf prime sur la souveraineté stricte.
- **RDV B2B** : Cal.com self-hosted sur le VPS EU (0 coût/siège, souveraineté totale).

**Coût estimé lancement** : ~10-20 €/mois fixes (hébergement OVH/Scaleway + VPS Cal.com mutualisé) + 5 % sur les ventes via Payhip (0 €/mois de base). Passage Payhip Pro 99 $/mois = 0 % commission au volume.

**Plus pro que Netlify+Gumroad+PayPal** : MoR/TVA UE auto (fini les IPN PayPal à sécuriser et la déclaration TVA pays par pays) + données EU (cohérent RGPD/EU AI Act, vs infra US) + 