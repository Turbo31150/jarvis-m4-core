[user] Tu es l'agent DEDUP-MOISSONS. Objectif : garantir que TOUTES les pages « Moisson » sont référencées dans l'index maître, chacune UNE seule fois (dédup). AUCUN fichier local.

SÉCURITÉ : écriture Notion privé uniquement, token jamais affiché, aucune publication.
REST (MCP Notion déconnecté) : token /home/pamerys/.config/jarvis/notion.env (NOTION_TOKEN, jamais l'afficher), header « Notion-Version: 2022-06-28 ».

PAGE INDEX : id = 3bc7800a81d6813c827bff98ce414d47.

ÉTAPE 1 — Découverte : POST https://api.notion.com/v1/search avec query « Moisson » → récupère TOUTES les pages dont le titre commence par « 🌾/📚/🧩/🏛️/🌐/⛓️/🗄️ Moisson » (titre + id + url). Pages attendues (au moins) :
- 🌾 Moisson — Workflows sessions Claude Code & agy (M4)
- 🌾 Moisson M1 — Workflows sessions (SSD)
- 🌾 Moisson M1 — Workflows réels (n8n·scripts·séries)
- 🧩 Moisson — Assets Claude Code
- 📚 Moisson — Bibliothèque vivante & labo
- 🌐 Moisson — BrowserOS & MCP
- 🏛️ Moisson — Board d'experts
- ⛓️ Moisson — Dominos, artefacts & atomes (si publiée)
- 🗄️ Moisson — Bases SQL/SQLite (si publiée)
- 🚚 Implantation M1→M4 (si publiée)
Note celles trouvées ; celles absentes = « pas encore publiées ».

ÉTAPE 2 — GET https://api.notion.com/v1/blocks/3bc7800a81d6813c827bff98ce414d47/children?page_size=100 (pagine si besoin) → repère les liens/bookmarks vers ces pages Moisson déjà présents. Supprime les DOUBLONS (garde une occurrence par page ; DELETE .../blocks/{block_id} pour les redondants).

ÉTAPE 3 — Sous un heading un

[assistant] I'll start by loading the token and running the Notion search for Moisson pages.

[assistant] 8 Moisson pages found. Now let me fetch the index page children to find existing links/duplicates.

[assistant] Let me view the full file to see the complete structure and confirm no duplicate Moisson bookmarks.

[assistant] Current state is clear: 4 Moisson pages already linked once each (no duplicates) scattered in the "EXTRACTIONS" section; 4 not yet linked. No duplicates to delete. I'll add a dedicated heading plus bookmarks for the 4 missing pages.

[assistant] Terminé. Rapport concis.

## Rapport DEDUP-MOISSONS

**Pages Moisson trouvées (8) — chacune référencée UNE fois dans l'index :**

Déjà liées avant (aucun doublon, conservées telles quelles) :
| Titre | URL |
|---|---|
| 🌾 Moisson M1 — Workflows sessions (SSD) | …3bc7800a81d681e1b9c2d1f52ae4c0ae |
| 🌾 Moisson M1 — Workflows réels (n8n·scripts·séries) | …3bc7800a81d6815ea477c0d4cf2064ad |
| 🏛️ Moisson — Board d'experts | …3bc7800a81d68137bf16f2f0b5040b75 |
| 🧩 Moisson — Assets Claude Code | …3bc7800a81d6814dacc6d6fc5001845a |

Ajoutées sous le nouveau heading **« 🌾 MOISSONS SYSTÈME (M4 + M1) »** :
| Titre | URL |
|---|---|
| 🌾 Moisson — Workflows sessions Claude Code & agy (M4) | …3bc7800a81d68188a1b0f44137e3a572 |
| 📚 Moisson — Bibliothèque vivante & labo | …3bc7800a81d6814d8168ea2893fdf7fa |
| 🌐 Moisson — BrowserOS & MCP | …3bc7800a81d6813a8a79c50b74dc851e |
| ⛓️ Moisson — Dominos, artefacts & atomes logiques | …3bc7800a81d681babfdcdd4b8b9f02e8 |

**Doublons supprimés : 0** (chaque page n'apparaissait qu'une fois avant — aucune suppression nécessaire).

**Pas encore publiées (à relier plus tard) :**
- 🗄️ Moisson — Bases SQL/SQLite
- 🚚 Implantation M1→M4

Note : la page « Améliorer Claude Code — moisson de recherche » existe mais n'est pas une page Moisson système (déjà liée ailleurs), ignorée. Token jamais affiché, écriture Notion privé uniquement.