[user] Tu es l'agent NOTION-PROD. Consolide les brouillons de PRODUCTION Pousseline dans UNE page Notion propre sous le hub JARVIS OS.

SÉCURITÉ : documentation seulement. Aucune publication réseau, aucun envoi. Écriture uniquement dans le Notion privé. Ne jamais afficher de token.

ÉTAPE 1 — Lis les 5 fichiers (lecture seule) dans /home/pamerys/jarvis/wbs/drafts/pousseline-prod/ :
- linkedin-30j.md (15 posts + index)
- x-30j.md (20 tweets + 3 threads)
- page-vente.md + faq-objections.md
- catalogue-packs.md
- emails-avances.md

ÉTAPE 2 — Crée une page Notion « 🚀 Pousseline — Arsenal de production 2026-08-14 » sous le hub « 🧠 JARVIS OS — Hub » (id 3bc7800a-81d6-8100-8f97-c66fe6f52f84). Structure :
- Callout en tête : « BROUILLONS de production — relire, remplir les placeholders [PRIX]/[TÉMOIGNAGE], choisir UN pilote de publication. Rien n'est publié. »
- Section « 📅 LinkedIn 30 jours » (les 15 posts intégraux)
- Section « 🐦 X/Twitter » (20 tweets + 3 threads)
- Section « 💰 Page de vente » + « ❓ FAQ & objections »
- Section « 📦 Catalogue des packs » (les 3 packs + comparatif)
- Section « ✉️ Emails avancés » (les 3 séquences)
Reproduis le TEXTE réel des brouillons en blocs Notion natifs. Découpe en lots de 100 blocs, et si un bloc dépasse 2000 caractères découpe-le.

ÉTAPE 3 — MCP Notion DÉCONNECTÉ → fallback REST direct : token dans /home/pamerys/.config/jarvis/notion.env (NOTION_TOKEN, jamais l'afficher), API https://api.notion.com/v1/pages, header « Notion-Version: 2022-06-28 ».

R

[assistant] Bien. J'ai tout le contenu. J'écris un script Python qui parse le markdown en blocs Notion natifs, crée la page et append par lots de 100.

[assistant] Terminé. La page Notion a été créée avec succès sous le hub JARVIS OS via fallback REST direct (MCP Notion déconnecté).

Résultat
- URL : https://app.notion.com/p/Pousseline-Arsenal-de-production-2026-08-14-3bc7800a81d68123ba30f28a0c3b6403
- Titre : « 🚀 Pousseline — Arsenal de production 2026-08-14 »
- Parent : hub « 🧠 JARVIS OS — Hub »
- Sections : 6 (LinkedIn 30j, X/Twitter, Page de vente, FAQ & objections, Catalogue des packs, Emails avancés)
- Blocs : 802 blocs Notion natifs (callout d'avertissement en tête + headings/paragraphes/listes/quotes/dividers), poussés en 9 lots de ≤100 (create initial + 8 append), avec découpe automatique des textes >2000 caractères.

Contenu intégral reproduit : les 15 posts LinkedIn + index, les 20 tweets + 3 threads, la page de vente complète, les 10 objections FAQ, les 3 packs + tableau comparatif + 3 bundles, et les 3 séquences (10 emails) avec variantes d'objet. Les placeholders [PRIX]/[TÉMOIGNAGE]/[À COMPLÉTER] sont conservés tels quels.

Sécurité respectée : documentation uniquement, aucune publication réseau ni envoi, écriture dans le Notion privé seulement. Le token n'a jamais été affiché (lu depuis notion.env, injecté en en-tête Bearer).