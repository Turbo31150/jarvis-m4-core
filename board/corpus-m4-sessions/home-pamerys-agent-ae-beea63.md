[user] Tu es l'agent EXTRACT-FORMATIONS. Étudie À FOND le système et extrais TOUTES les formations / contenus pédagogiques vendables. Écris le résultat dans UNE page Notion. AUCUN fichier local.

SÉCURITÉ : lecture seule locale + écriture Notion privé. Aucun secret affiché. Aucune publication.

ÉTAPE 1 — Étudie à fond, cherche les formations réellement produites :
- Le fichier ~/.claude/memories/notion_deliverables_2026.md et tout NOTION_LIVRABLES_COMPLETS_2026.md (~/jarvis, ~) — il contiendrait ~72 formations compilées.
- Les sorties de la « forge » de formations (cherche forge_formations, formations, cours dans ~/jarvis/wbs, ~/jarvis/docs, ~/labo).
- Tout dossier de cours/tutoriel/guide vendable.
- Ne fabrique pas de formations : recense ce qui EXISTE. Si le nombre réel diffère de 72, dis-le.

ÉTAPE 2 — Pour CHAQUE formation : titre, thème, public cible, format (vidéo/PDF/texte), niveau, et regroupe-les en PARCOURS vendables (ex : « Parcours IA locale débutant », « Parcours automatisation métier »). Marque l'état (rédigée / brouillon / idée).

ÉTAPE 3 — Écris la page Notion « 🎓 Extraction — Toutes les formations » sous le hub « 🧠 JARVIS OS — Hub » (id 3bc7800a-81d6-8100-8f97-c66fe6f52f84). Tableaux par thème + section « parcours/bundles vendables ». Callout d'intro « recensement factuel, prix à fixer ».

Fallback REST : token /home/pamerys/.config/jarvis/notion.env (NOTION_TOKEN, jamais affiché), API https://api.notion.com/v1/pages, « Notion-Version: 2022-06-28 ». Lots de 100 bloc

[assistant] I have the catalogue of 72. Let me verify against the actual filesystem and the SQL DB.

[assistant] The DB confirms exactly 72. Let me pull the authoritative DB records and check the forge directory for anything beyond 72.

[assistant] 72 confirmed authoritative (DB = 72, catalogue = 72, categories sum to 72). The 196 PDFs on disk are duplicate/versioned renders of the same 72. Now I'll build the Notion page via REST.

[assistant] I'll write one Python script that reads the DB directly and builds the Notion page.

[assistant] Page créée avec succès.

## Rapport final

**Page Notion** : 🎓 Extraction — Toutes les formations
URL : https://app.notion.com/p/Extraction-Toutes-les-formations-3bc7800a81d68187acd3d7c02908b72a
Créée sous le hub « 🧠 JARVIS OS — Hub ».

**Nombre réel de formations : 72** (et non « ~72 » approximatif — c'est exactement 72, confirmé et concordant sur trois sources) :
- `commercial.db` table `formations` = **72 lignes** (source d'autorité)
- Catalogue `NOTION_LIVRABLES_COMPLETS_2026.md` = **72 lignes**, mêmes titres/prix
- 196 PDF sur disque = rendus/versions multiples des mêmes 72 modules (pas 196 formations distinctes)
- 66 brouillons markdown dans `~/jarvis/data/forge` = sources régénérables des modules

**Répartition par thème** (10 catégories) : dev 14, infra 14, metier 13, avance 10, premium 6, agents 6, trading 3, securite 2, nocode 2, debutant 2. État catalogue : toutes « Prêtes » (PDF/HTML compilés). Prix catalogue de 39 € à 149 € l'unité.

**Contenu de la page** :
- Callout d'intro « recensement factuel, prix à fixer »
- Tableaux par thème listant les 72 modules avec prix
- Section **11 parcours vendables proposés** (IA locale, Développeur/Claude Code, Agents & MCP, Automatisation métier, Trading, Infra/MLOps, RAG & VectorDB, Voix & Multimodal, IA métier verticale, JARVIS OS premium, Sécurité) avec public cible
- Les **4 Master Packs Gumroad** déjà définis (39 / 79 / 99 / 297 €)

**Parcours proposés : 11** (plus les 4 bundles Master Packs déjà existants).

Sécurité res