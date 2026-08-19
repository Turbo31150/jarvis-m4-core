[user] Tu es l'agent LEAD-CONSOLIDE. Deux objectifs. Écriture Notion privé uniquement, token jamais affiché, aucune publication. REST : token /home/pamerys/.config/jarvis/notion.env (NOTION_TOKEN, jamais affiché), header « Notion-Version: 2022-06-28 ». « Archiver » = PATCH page {"archived": true} (corbeille, réversible).

OBJECTIF 1 — Ajouter à la page index (id 3bc7800a81d6813c827bff98ce414d47) une section « 🚀 EXÉCUTION — VENTE & TODOLIST » avec des bookmarks (sans doublon : GET .../blocks/{index}/children?page_size=100 paginé d'abord, ne pas re-lier ce qui existe déjà) vers :
- 🛍️ Fiche de vente — jarvis-domino-engine (89 €) : https://app.notion.com/p/Fiche-de-vente-jarvis-domino-engine-89-3bc7800a81d6817198b9f8436ce91b9b
- ⚙️ Patch env settings.json : https://app.notion.com/p/Patch-env-settings-json-appliquer-3bc7800a81d68173a8b6f16eb1dd0dfe
- 🔧 « Prêt-à-réparer — Encaissement Netlify/PayPal » : cherche-la via POST https://api.notion.com/v1/search query « Netlify » ; si trouvée, lie-la ; sinon note « pas encore publiée ».
- 🛒 « Catalogue Gumroad COMPLET » : cherche via search query « Gumroad COMPLET » ; si trouvée, lie-la ; sinon « pas encore publiée ».

OBJECTIF 2 — Dédoublonner « Arsenal de production » : via search query « Arsenal de production », identifie les 2 pages homonymes. GARDE celle avec le plus de contenu (compare via GET .../blocks/{id}/children?page_size=1 → has_more, ou la date la plus récente) ; ARCHIVE l'autre (PATCH page archived:true). Dans l'index, si un lien

[assistant] Le token est chargé. Je vais écrire un script Python qui fait tout le travail via l'API REST Notion.

[assistant] La dédup Arsenal a trouvé 0 homonyme. Vérifions ce que renvoie réellement la recherche Arsenal avant de conclure.

[assistant] Les deux homonymes existent (mon filtre de titre était trop strict). Je corrige et relance uniquement la dédup.

[assistant] Terminé. Voici le rapport.

## Rapport LEAD-CONSOLIDE

**OBJECTIF 1 — Section « 🚀 EXÉCUTION — VENTE & TODOLIST » ajoutée à l'index (id 3bc7…4d47)**

Pagination des 118 blocs existants d'abord, aucun doublon recréé. Liens ajoutés (titre → url) :
- 🛍️ Fiche de vente — jarvis-domino-engine (89 €) → https://app.notion.com/p/Fiche-de-vente-jarvis-domino-engine-89-3bc7800a81d6817198b9f8436ce91b9b
- ⚙️ Patch env settings.json → https://app.notion.com/p/Patch-env-settings-json-appliquer-3bc7800a81d68173a8b6f16eb1dd0dfe
- 🔧 Prêt-à-réparer — Encaissement Netlify/PayPal → https://app.notion.com/p/Pr-t-r-parer-Encaissement-Netlify-PayPal-3bc7800a81d681b89e59e87b618527a6

**Statuts recherche :**
- Netlify : **liée** (page « 🔧 Prêt-à-réparer — Encaissement Netlify/PayPal » trouvée via search).
- Gumroad : **trouvée** (« 🛒 Catalogue Gumroad COMPLET (contenu réel) ») mais **déjà présente dans l'index** → non re-liée (dédup respectée).

**OBJECTIF 2 — Dédoublonnage « Arsenal de production »**

Deux homonymes identiques « 🚀 Pousseline — Arsenal de production 2026-08-14 » :
- A `3bc7800a-…-810b-…` : 802 blocs, modifié 11:05
- B `3bc7800a-…-8123-…` : 802 blocs, modifié 10:31

Contenu égal (802 = 802) → départage par date la plus récente (critère prévu). **Gardée : A (11:05)** · **Archivée : B (10:31)** (PATCH archived:true, réversible). Aucun lien de l'index ne pointait vers la page archivée → rien à remplacer.

Token jamais affiché, écriture privée uniquement, aucune publication.