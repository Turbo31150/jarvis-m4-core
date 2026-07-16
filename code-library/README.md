# Bibliothèque de code — SQL avant compute

Base SQLite des patterns/recettes validés du système Pousseline (cascade 0-token, dispatch par vagues).
**Principe : chercher un pattern éprouvé ICI avant de re-générer du code.**

## Usage
```bash
./libcode "remplir banque parallèle"     # recherche full-text (FTS5)
./libcode --list                          # tous les patterns
./libcode --show dispatch-masse-0token    # code réutilisable complet
```
Alias conseillé (à ajouter soi-même dans ~/.bashrc) : `alias libcode='/home/pamerys/jarvis/code-library/libcode'`

## Étendre
Ajouter un pattern dans `build.py` (liste `PATTERNS`) puis `python3 build.py` (idempotent, UPSERT sur `nom`).

## Schéma
`patterns(nom, categorie, langage, triggers, description, quand_utiliser, code, source)` + `patterns_fts` (FTS5).
