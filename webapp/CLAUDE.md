# CLAUDE.md — Profil `ecole` (PII-ELEVES) ⚠ RGPD strict

Application enseignante Pousseline. **Cet espace contient des données d'élèves
réelles.** Tout ce qui en sort est une fuite.

## Interdictions absolues
- **Ne jamais** committer `ecole.db` ni aucun `*.db` (données élèves).
- **Ne jamais** copier un nom, prénom, appréciation ou observation d'élève dans
  un autre profil, un log, un rapport, une mémoire ou un message.
- **Ne jamais** envoyer de contenu nominatif à un backend distant. La cascade
  locale s'utilise avec `cache=False` pour tout contenu nominatif — un contenu
  d'élève mis en cache devient consultable par une autre requête.
- Pas de capture d'écran de l'app contenant des noms.

## Ce que contient cet espace
| Chemin | Rôle |
|---|---|
| `ecole.db` | Base élèves — **jamais versionnée** |
| `modules/`, `*.py` | Modules Flask (`register(app)`), API `/api/*` |
| `static/`, `templates/` | Front, onglets, sections |
| `scripts/dispatch_*.py` | Génération de masse 0-token (banque, séances) |
| `backups/` | Sauvegardes locales — hors git |

## Règles de travail
- Pattern modulaire `register(app)` pour tout nouveau module ; brancher l'onglet
  dans `index.html` (section + loader), sinon le module reste orphelin.
- **SQL avant inférence** : lire la base avant de faire générer quoi que ce soit.
- Cascade IA **locale 0-token** (cache → Ollama → Gemini), jamais de compute
  facturé pour du volume.
- Avant tout checkpoint : `checkpoint-securise-app` — pousse **le code seul**,
  jamais les bases ni les secrets.

## Commandes
```bash
python3 app.py                       # webapp :7777
sqlite3 ecole.db ".tables"
python3 scripts/dispatch_banque.py 6 --only CP
```

## Workflow
Écrire le résultat dans `REPORT.md`, tenir `TODO.md` à jour. **Aucun nom d'élève
dans ces deux fichiers** — désigner par identifiant si nécessaire.
