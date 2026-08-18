# AlkymIA Flow

Moteur d'automatisation 100 % local. Un « domino » est une brique d'action prête
à l'emploi ; une chaîne de dominos forme un « pipeline » qui exécute une tâche
complète de bout en bout. Aucune donnée ne quitte votre machine.

## Contenu du dossier
```
bin/dominos          # runner unifié (liste, recherche, dry-run, exécution)
exemples/*.sh        # exemples de séries prêtes à l'emploi (a11y, admin…)
README.md
FICHE-VENTE.md
LICENSE.txt
```

> Note : le moteur complet s'appuie sur deux bibliothèques (dominos compilés +
> séries). Ce dossier livre le runner et des exemples représentatifs. La
> bibliothèque complète (835 pipelines / 5256 dominos) est fournie séparément
> lors du packaging final.

## Installation
1. Prérequis : `bash` (Linux/macOS), Python 3.11+ pour la recompilation optionnelle.
2. Copiez le dossier où vous voulez, rendez le runner exécutable :
   ```bash
   chmod +x bin/dominos
   ```
3. (Optionnel) Pointez vos bibliothèques via variables d'environnement :
   ```bash
   export DOMINO_DIR="$HOME/dominos-compiled/dominos"   # dominos compilés
   export DOMINO_SERIES="$HOME/series"                   # séries prêtes
   ```

## Usage
```bash
bin/dominos                 # liste tout (compilés + séries)
bin/dominos search <mot>    # recherche par nom
bin/dominos <nom>           # DRY-RUN / aperçu (n'exécute rien)
bin/dominos <nom> --run     # exécute réellement
```
Les dominos compilés tournent en DRY-RUN par défaut ; les actions destructrices
demandent confirmation. Les séries sont affichées en aperçu avant toute
exécution : rien ne part sans `--run`.

## Sécurité
Exécution locale uniquement. Aucun secret n'est stocké dans le runner ; les
chemins sont paramétrables par variables d'environnement.
