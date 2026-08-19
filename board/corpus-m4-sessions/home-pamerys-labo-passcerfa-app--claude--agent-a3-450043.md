[user] Inventaire READ-ONLY de l'app labo /home/pamerys/labo/passcerfa-app (Node/Express + frontend Vite/TS). Ne modifie RIEN.

1. Liste `routes/` (auth, cerfa, llm, facturx, affiliation, assistant) + ce que chaque route expose. Liste `services/` (surtout llm-router = cascade + circuit-breaker, llm-local, llm-cloud, cerfa-mapper, ocr-engine, franceconnect, field-extractor). Structure `frontend/src/`. `database/`, `data/`.

2. Pour CHACUNE de ces 10 « briques » (logique captée de Mochii), dis : DÉJÀ PRÉSENT / PARTIEL / À CRÉER, et le fichier exact où ça se branche :
   - B1 barre latérale assistant, B2 cascade multi-modèles, B3 pré-remplissage CERFA, B4 personas, B5 mémoire longue durée, B6 base de connaissances, B7 analyse de documents, B8 deep-research, B9 chatbot marque blanche, B10 extension navigateur.

3. Note les branches git ouvertes et leur contenu : `worktree-passcerfa-affiliation`, `clean-pennylane-affiliation`, `feat/assistant-command`, et l'état de `master` (routes/affiliation.js déjà présent ?). Liste les PR ouvertes via `gh pr list` si dispo.

Rends un rapport structuré : tableau des 10 briques (état + fichier de branchement) + liste des branches/PR + liste des routes/services existants réutilisables.

[assistant] Je vais explorer l'app en lecture seule. Commençons par la structure globale et les branches git.

[assistant] Je suis dans un worktree. Explorons-le spécifiquement et lisons les fichiers clés en parallèle.

[assistant] Lisons les fichiers clés en parallèle: le routeur LLM (cascade + circuit breaker), les nouvelles routes assistant/affiliation, et les services.

[assistant] Lisons les services CERFA/OCR/FranceConnect, le prefill front, et vérifions la présence d'une UI assistant côté front.

[assistant] Vérifions le front (barre assistant B1, prefill B3), la route cerfa/llm, le schema validate, et cherchons les briques B6/B8/B9/B10.

[assistant] Vérifions le schema assistant, les agents/pipelines, la route llm, le seed affiliations, et la route partners de l'autre branche.

[assistant] Deux derniers points: l'agent embedding/history (B5/B6) et la page front demarches (UI affiliation).

[assistant] J'ai tout ce qu'il faut. Voici le rapport structuré.

---

# Inventaire READ-ONLY — passcerfa-app (labo)

Aucune modification effectuée. Analyse menée sur le worktree `passcerfa-affiliation` (branche `feat/assistant-command`, la plus complète) + comparaison inter-branches.

## Note importante sur l'arborescence des branches

Attention à un piège de nommage : le worktree **`passcerfa-affiliation`** est en réalité pointé sur la branche **`feat/assistant-command`** (verrouillé). Il y a **deux implémentations concurrentes de l'affiliation** :
- `feat/assistant-command` → `routes/affiliation.js` (SQLite `affiliations`/`affiliation_clicks`) + `assistant.js`
- `worktree-passcerfa-affiliation` → `routes/partners.js` + `services/affiliation.js` (registre JSON + liens de parrainage par env, Qonto en vitrine)

---

## 1. Structure existante

### `routes/` (branche feat/assistant-command — montées dans `server.js`)
| Route | Monté sur | Expose |
|---|---|---|
| `auth.js` | `/api/auth` | Login FranceConnect+ PKCE (`fc-authorize`, `callback`, `logout`), stub gated `FC_STUB=1` |
| `cerfa.js` | `/api/cerfa` | `POST /upload` (OCR→détection→extraction, option `?llm=1`), `GET /list` (10 CERFA), `POST /prefill`, `POST /auto-inject`, `POST /analyze`, `POST /simulate`, `GET /scenarios`, `POST /feedback`, `GET /metrics` |
| `llm.js` | `/api/llm` | `POST /reformat`, `POST /cerfa-assist`, `GET /health`, `POST /embed` |
| `facturx.js` | `/api/facturx` | Facture électronique Factur-X (réforme 2026) |
|