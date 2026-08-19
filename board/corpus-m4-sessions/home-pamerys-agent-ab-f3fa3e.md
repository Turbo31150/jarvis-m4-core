[user] Tu es l'agent PDF-LIVRABLES. Objectif : générer un PDF « Guide d'installation & mise en place » par produit (depuis les .md existants), les ranger dans les dossiers, et les lister dans Notion suivant l'index. Aucun secret. Rien publié.

⚠️ CONTRAINTE MACHINE CRITIQUE : le M4 est à ~91 % de RAM (un navigateur lourd tourne). AVANT toute génération, vérifie `free -h`. Utilise l'outil PDF le PLUS LÉGER disponible, dans cet ordre de préférence : `pandoc` (sans moteur LaTeX lourd → `--pdf-engine=weasyprint` ou `wkhtmltopdf` si présents), sinon `md-to-pdf`/`markdown-pdf`, sinon convertis md→HTML simple et laisse le HTML (pas de PDF) en notant « PDF non généré, outil absent ». N'utilise PAS chrome headless (trop lourd, risque de freeze avec le navigateur déjà ouvert). Procède par PETITS LOTS (2-3 produits), et si `free` montre <300 Mo dispo ou si la garde thermique bloque le bash → ARRÊTE, note ce qui reste, ne force pas.

SOURCE : /home/pamerys/jarvis/livrables/<slug>/ — chaque dossier a DOSSIER-COMPLET.md + README.md + FICHE-VENTE.md. Génère un PDF « INSTALLATION-<slug>.pdf » (ou GUIDE-<slug>.pdf) combinant : présentation + installation/mise en place + usage (à partir de README + DOSSIER-COMPLET). Mets-le dans le dossier du produit.

PRODUITS : jarvis-domino-engine, formation-ia-locale-souveraine, board-souverain-b2b, pack-n8n-workflows, pack-gouvernance-claude-code, cloud-router-8, repurpose-1-4, checkpoint-securise, n8n-mcp, stop-cycles-m4, hooks-gouvernance, alkymia-sovereign, a

[assistant] No PDF engines installed. Let me verify more thoroughly and inspect a product folder.

[assistant] Chrome/LibreOffice are too heavy for current RAM (795 MB free, navigator open) and none of the preferred light engines (pandoc/weasyprint/wkhtmltopdf/md-to-pdf) exist. Per instructions I'll generate combined styled HTML per product (Python `markdown`, near-zero RAM) and mark PDF as not generated. Writing the generator.

[assistant] Les 13 guides HTML sont générés, RAM stable (~700 Mo libres, aucun pic). Maintenant la page Notion.

[assistant] Terminé.

## Rapport PDF-LIVRABLES

**Outil utilisé :** Python `markdown` → HTML autonome stylé (pur Python, ~0 RAM). Aucun moteur PDF léger n'existe sur le M4 (`pandoc`, `weasyprint`, `wkhtmltopdf`, `md-to-pdf`, `markdown-pdf` tous absents). `google-chrome` et `libreoffice` sont présents mais écartés : trop lourds pour la RAM (navigateur ouvert, ~700 Mo libres) — risque de freeze, conformément à la consigne.

**Résultat :**
- **PDF générés : 0**
- **HTML seul : 13/13** — un `GUIDE-<slug>.html` par produit, rangé dans son dossier `/home/pamerys/jarvis/livrables/<slug>/`, combinant Présentation (FICHE-VENTE) + Prise en main (README) + Dossier complet installation/usage (DOSSIER-COMPLET).
- **Non générés : 0**

Produits traités (ordre de l'index) : jarvis-domino-engine, formation-ia-locale-souveraine, board-souverain-b2b, pack-n8n-workflows, pack-gouvernance-claude-code, cloud-router-8, repurpose-1-4, checkpoint-securise, n8n-mcp, stop-cycles-m4, hooks-gouvernance, alkymia-sovereign, alkymia-suite.

**RAM au fil :** 1281 Mo dispo au départ → 1123 Mo après génération → jamais sous le seuil de 300 Mo. Aucun pic (pas de Chrome/LibreOffice lancé). Aucune garde thermique déclenchée.

**Notion :**
- Page créée « 📄 Guides d'installation PDF — par produit » sous le hub JARVIS OS, avec tableau (Produit · chemin du fichier · statut = « HTML seul ») + callout honnête : moteur PDF absent, Chrome/LibreOffice trop lourds, l'API Notion n'héberge pas les fichiers → guides dans les dossiers liv