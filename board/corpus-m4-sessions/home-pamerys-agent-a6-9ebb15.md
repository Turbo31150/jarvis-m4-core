[user] Tu es l'agent REBRAND-CONSOLIDE. Deux objectifs. Aucun secret. Rien publié.

CARTE DE MARQUE (client = AlkymIA ; « JARVIS OS » = technique interne à retirer du client-facing) :
- jarvis-domino-engine → **AlkymIA Flow**
- Formation IA locale souveraine → **AlkymIA Academy**
- Board souverain B2B → **AlkymIA Council**
- Pack n8n → AlkymIA Boost · briques → Les Essences AlkymIA · offre entreprise → AlkymIA Sovereign · gamme → « La Fabrique AlkymIA ».
Règle : remplacer les mentions CLIENT-FACING « JARVIS OS » par « AlkymIA » (ou le nom commercial du produit) dans les LANDINGS et FICHES. Tu peux garder une mention discrète « propulsé par la technologie JARVIS OS » en bas de page si pertinent. Ne casse pas le HTML/CSS.

OBJECTIF 1 — Rebrand des fichiers locaux (Read puis Edit ; si Bash bloqué par la garde thermique, procède fichier par fichier, réessaie) :
- /home/pamerys/jarvis/livrables/jarvis-domino-engine/landing.html → titre/marque = AlkymIA Flow
- /home/pamerys/jarvis/livrables/formation-ia-locale-souveraine/landing.html → AlkymIA Academy
- /home/pamerys/jarvis/livrables/board-souverain-b2b/landing.html → AlkymIA Council
- Les README.md et FICHE-VENTE.md des dossiers sous /home/pamerys/jarvis/livrables/* : remplacer les mentions client-facing « JARVIS OS » par « AlkymIA » + le nom commercial du produit quand il existe.
Vérifie après chaque édition que le fichier reste valide (pas de balise cassée).

OBJECTIF 2 — Consolider l'index Notion (id 3bc7800a81d6813c827bff98ce414d47),

[assistant] The domino landing uses "Domino Engine" as the brand. Let me rebrand it to "AlkymIA Flow" and read the other two landings and the READMEs in parallel.

[assistant] This landing has no explicit brand or JARVIS OS mention. I'll introduce the "AlkymIA Academy" brand in the title, hero eyebrow, and footer.

[assistant] Now the READMEs and FICHE-VENTE with JARVIS OS mentions — jarvis-domino-engine ones. Let me read them.

[assistant] Now let me check all other livrables README/FICHE for client-facing JARVIS OS mentions, plus the board/formation folders.

[assistant] HTML edits were text-only plus balanced added elements. Let me quickly validate the three landings parse cleanly.

[assistant] All three landings parse cleanly with balanced tags. Objective 1 done. Now Objective 2 — the Notion index. Let me load the token and fetch the index children (paginated).

[assistant] Token works. Let me fetch all children across pages and search for an existing "🎨 BRANDING & DESIGN AlkymIA" heading and any existing bookmarks to the target IDs.

[assistant] No branding section exists yet. Five of the six targets are already linked in the index; only the domino landing (3bc7800a81d681c7be4ec5567f12c189) is missing. Let me search for "Recherche marché AlkymIA" before writing.

[assistant] Found the published "🔎 Recherche marché & concurrence — AlkymIA" page. Let me verify which targets are already linked anywhere in the index, then append the branding section with only the missing bookmarks.

[assistant] Both missing. Let me get the domino landing page's canonical URL, then append the branding heading + the two missing bookmarks.

[assistant] Now I'll append the branding heading and the two missing bookmarks to the index.

[assistant] Both objectives complete.

## OBJECTIF 1 — Rebrand des fichiers locaux (fait, HTML valide)

Fichiers rebrandés (tous parsés proprement, balises `<div>` équilibrées) :

| Fichier | Changement marque |
|---|---|
| `/home/pamerys/jarvis/livrables/jarvis-domino-engine/landing.html` | « Domino Engine » → **AlkymIA Flow** (title, hero, panels, cartes, prix, footer) + mention discrète « Propulsé par la technologie JARVIS OS » en footer |
| `/home/pamerys/jarvis/livrables/jarvis-domino-engine/README.md` | H1 → **AlkymIA Flow** (internes `bin/dominos`, `DOMINO_DIR` laissés tels quels) |
| `/home/pamerys/jarvis/livrables/jarvis-domino-engine/FICHE-VENTE.md` | titre + corps « jarvis-domino-engine » → **AlkymIA Flow** |
| `/home/pamerys/jarvis/livrables/board-souverain-b2b/landing.html` | « Board souverain » → **AlkymIA Council** ; footer « Édité dans le cadre de JARVIS OS » → « Propulsé par la technologie JARVIS OS » |
| `/home/pamerys/jarvis/livrables/formation-ia-locale-souveraine/landing.html` | marque **AlkymIA Academy** introduite (title, eyebrow hero, footer) + mention discrète JARVIS OS |

Validation HTML : les 3 landings passent le parseur `html.parser` et ont un compte `<div>`/`</div>` équilibré (56/56, 68/68, 65/65). Les autres livrables (repurpose, cloud-router, checkpoint, pack-n8n, hooks-gouvernance, n8n-mcp, stop-cycles) ne contiennent aucune mention client-facing « JARVIS OS » ni nom de produit de la carte de marque → rien à changer. Seules subsistent 3 mentions « JARVIS 