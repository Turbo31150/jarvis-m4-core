[user] Explore le dossier /home/pamerys/jarvis/webapp/ (app Flask enseignante "Pousseline", front prof.html, backend modules *.py montés via register(app) dans server.py).

Objectif : cartographier tout ce qui existe déjà pour l'EXPORT PDF et le MODE CORRECTION IMPRIMABLE, car je vais planifier : (a) export PDF de la préparation 3 mois par semaine/domaine, (b) un mode correction imprimable des exercices.

Cherche et rapporte précisément (avec chemins fichier:ligne) :
1. Le module export_pdf.py : quelles routes /api expose-t-il, quelle lib PDF utilise-t-il (reportlab? weasyprint? wkhtmltopdf?), quelles données il sait exporter.
2. La route /api/banque/pdf dans banque_annuelle.py : comment elle génère un PDF (fonction pdf()), quelle lib.
3. La route /api/prof/export dans prof_routes.py : ce qu'elle exporte (vers ~/Documents/Classe en .md ?).
4. Tout ce qui touche "correction" : table corrections (schéma), route /api/exercice/corriger, et si un affichage/impression du corrigé existe côté front prof.html.
5. La table banque (colonnes) et comment un corrigé est stocké (contenu_md contient-il le corrigé ?).
6. Côté front prof.html : onglet "export" (data-p="export") — que fait-il, quelle fonction loadOutils/loadExport, quels boutons d'export existent.

Ne modifie rien (lecture seule). Rends un rapport structuré : ce qui existe, ce qui manque, et les fonctions/libs réutilisables pour générer des PDF proprement.

[assistant] Je vais explorer le dossier webapp. Commençons par cartographier les fichiers pertinents.

[assistant] Lisons les sections front pertinentes (panneaux export, corrections, banque PDF).

[assistant] Vérifions les usages de downloadPdf, le loader de l'onglet corrections, et le déclencheur loadAnnee.

[assistant] Exploration terminée. Voici le rapport de cartographie complet.

---

# Cartographie EXPORT PDF & MODE CORRECTION — webapp Pousseline

## 1. Module `export_pdf.py` — le moteur PDF central

Fichier : `/home/pamerys/jarvis/webapp/export_pdf.py` (chargé via `server.py:58`).

- Lib PDF : **AUCUNE lib Python** (pas reportlab/weasyprint/wkhtmltopdf). Le pipeline est **markdown → HTML → Chrome/Chromium headless** (`--headless=new --print-to-pdf`). Détection du binaire à `export_pdf.py:19-23` (`google-chrome` / `chromium` / `chromium-browser`).
- Conversion markdown : lib Python `markdown` (`export_pdf.py:14-17`, `_md.markdown(...)` avec extensions `tables, fenced_code, sane_lists, nl2br`). Fallback `<pre>` si absente.
- Feuille de style CSS intégrée (`export_pdf.py:25-38`) : `@page A4 margin 16mm 14mm`, thème vert Pousseline (h1/h2/h3 colorés, tables stylées, blockquotes). C'est le gabarit visuel réutilisable pour tout PDF.
- Fonction pivot réutilisable : **`md_to_pdf_path(markdown_str, titre)`** (`export_pdf.py:58-83`) — écrit un `.html` temporaire, lance Chrome, renvoie le chemin du `.pdf`. Lève `RuntimeError` si Chrome absent ou échec.
- Route exposée : **`POST /api/prof/export-pdf`** (`export_pdf.py:87-107`) — reçoit JSON `{markdown|contenu, titre}`, renvoie le PDF en `send_file` attachment. C'est une route générique « donne-moi du markdown, je te rends un PDF ».

Ce qu'il sait exporter : **n'importe quel markdown** (cahier-journal, séance, bulletin, banque…). Il n'est pas spéci