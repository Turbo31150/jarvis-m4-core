[user] Tu es l'agent DEDUP-ORFEVRES. Objectif : garantir que les pages « Livrable orfévré » sont référencées dans l'index maître, chacune UNE seule fois, sous une section dédiée. AUCUN fichier local. Écriture Notion privé uniquement, token jamais affiché, aucune publication.

REST : token /home/pamerys/.config/jarvis/notion.env (NOTION_TOKEN, jamais affiché), header « Notion-Version: 2022-06-28 ».
PAGE INDEX : id = 3bc7800a81d6813c827bff98ce414d47.

ÉTAPE 1 — Découverte : POST https://api.notion.com/v1/search query « orfévr » ET query « orfévré » → récupère toutes les pages « 🏅 Livrable(s) orfévré(s) … » (titre + id + url). Pages déjà connues à inclure :
- 🏛️ Board souverain (conseil IA local) : https://app.notion.com/p/Livrable-orf-vr-Board-souverain-conseil-IA-local-3bc7800a81d681cd81a9c7a418330297
- 🏅 Livrables orfévrés — synthèse & priorisation : https://app.notion.com/p/Livrables-orf-vr-s-synth-se-priorisation-3bc7800a81d681adb5e6d845879c2ba7
- (chercher aussi : « Formation phare IA locale souveraine » et « Pack Automatisation métier n8n » — peut-être pas encore publiées ; si absentes, noter « pas encore publiée »).

ÉTAPE 2 — GET https://api.notion.com/v1/blocks/3bc7800a81d6813c827bff98ce414d47/children?page_size=100 (pagine) → repère les liens/bookmarks déjà présents vers ces pages orfévré. Supprime les DOUBLONS éventuels (garde une occurrence ; DELETE .../blocks/{id} pour les redondants issus des auto-rattachements).

ÉTAPE 3 — Crée (si absent) un heading « 🏅 LIVRABLES ORFÉV

[assistant] I'll work with the Notion API via curl, sourcing the token without displaying it.

[assistant] Both orfévré pages are already linked, once each (no duplicates), but as `link_to_page` blocks, not under a dedicated heading. Let me see their context on page 2.

[assistant] The two orfévré pages sit as bare `link_to_page` auto-rattachements at the very end, no dedicated heading, each once (no duplicates). I'll convert to a clean dedicated section: delete the two bare auto-rattachements, then append a heading + one bookmark each.

[assistant] Fait. Rapport DEDUP-ORFÈVRES.

Livrables orfévrés référencés dans l'index maître (chacun UNE fois, sous la nouvelle section « 🏅 LIVRABLES ORFÉVRÉS (produits finis) ») :

| Titre | URL |
|---|---|
| 🏅 Livrables orfévrés — synthèse & priorisation | https://app.notion.com/p/Livrables-orf-vr-s-synth-se-priorisation-3bc7800a81d681adb5e6d845879c2ba7 |
| 🏛️/🏅 Livrable orfévré — Board souverain (conseil IA local) | https://app.notion.com/p/Livrable-orf-vr-Board-souverain-conseil-IA-local-3bc7800a81d681cd81a9c7a418330297 |

Découverte : la recherche « orfévr »/« orfévré » n'a retourné que ces 2 pages orfévré publiées.

Doublons supprimés : 0 doublon vrai (chaque page n'apparaissait qu'une fois). En revanche, les 2 pages n'existaient que comme `link_to_page` nus (auto-rattachements en fin de page, sans section dédiée). Je les ai supprimés (2 blocs auto-rattachés retirés) et remplacés par une section propre : heading « 🏅 LIVRABLES ORFÉVRÉS (produits finis) » + 1 paragraphe + 1 bookmark cliquable par page. Bilan net = 1 occurrence propre par livrable.

Pas encore publiées (à relier au prochain passage) :
- « Formation phare IA locale souveraine » — introuvable dans Notion (non publiée).
- « Pack Automatisation métier n8n » — introuvable en tant que livrable orfévré dédié (non publié ; seules des pages connexes existent : Kit contenu offre automatisation IA, Workflows n8n catalogue).

Aucun fichier local créé, token jamais affiché, aucune publication déclenchée.