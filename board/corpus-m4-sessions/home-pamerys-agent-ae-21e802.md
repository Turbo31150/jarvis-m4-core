[user] Tu es l'agent DEDUP-GITHUB. Objectif : dans Notion, garder la page GitHub détaillée, la mettre dans l'index, et archiver (corbeille, réversible) la page GitHub doublon légère. AUCUN fichier local.

SÉCURITÉ : écriture Notion privé uniquement, token jamais affiché, aucune publication. « Archiver » = PATCH page {"archived": true} (réversible, PAS une suppression définitive). Ne touche à AUCUNE autre page.

Fallback REST : token /home/pamerys/.config/jarvis/notion.env (NOTION_TOKEN, jamais l'afficher), header « Notion-Version: 2022-06-28 ».

Références :
- Page DÉTAILLÉE à GARDER : « Extraction — Repos GitHub Turbo31150 » (165 repos), id = 3bc7800a81d6812f8d02caab87c7c621, url https://app.notion.com/p/Extraction-Repos-GitHub-Turbo31150-3bc7800a81d6812f8d02caab87c7c621
- Page DOUBLON à ARCHIVER : « GitHub Turbo31150 — 173 repos », id = 3bc7800a81d68118b6ece585bc4fc48c
- Page INDEX : « 📚 POUSSELINE — Index & Mode d'emploi », id = 3bc7800a81d6813c827bff98ce414d47

ÉTAPES :
1. GET https://api.notion.com/v1/blocks/3bc7800a81d6813c827bff98ce414d47/children?page_size=100 — repère le(s) bloc(s) (bookmark/lien) qui pointent vers le DOUBLON (url contient 3bc7800a81d68118b6ece585bc4fc48c).
2. Vérifie si un lien vers la page DÉTAILLÉE (3bc7800a81d6812f8d02caab87c7c621) est déjà présent dans l'index. 
   - Si OUI : supprime simplement le bloc du doublon (DELETE https://api.notion.com/v1/blocks/{block_id}).
   - Si NON : remplace — supprime le bloc du doublon (DELETE) puis append un bookmark 

[assistant] Found the doublon bookmark block. No link to the detailed page exists in the index. Executing: delete doublon block, append bookmark to detailed page, archive doublon page.

[assistant] Terminé. Dédoublonnage GitHub exécuté sur Notion, sans toucher à autre chose.

(a) Index pointe désormais vers la page DÉTAILLÉE : le bloc bookmark du doublon a été supprimé (corbeille) et un nouveau bookmark vers « Extraction — Repos GitHub Turbo31150 » (165 repos) a été ajouté à l'index. Aucun lien vers la page détaillée n'existait auparavant, donc remplacement effectué.

(b) Page DOUBLON « GitHub Turbo31150 — 173 repos » archivée (corbeille, réversible via `archived: false`).

IDs touchés :
- Bloc bookmark doublon supprimé : `3bc7800a-81d6-81a0-87b5-d85c98600041` (dans l'index `3bc7800a81d6813c827bff98ce414d47`)
- Nouveau bloc bookmark vers page détaillée : `3bc7800a-81d6-816e-909a-d7c096936696`
- Page doublon archivée : `3bc7800a81d68118b6ece585bc4fc48c`

Aucune autre page modifiée. Token non affiché.