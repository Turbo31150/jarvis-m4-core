---
name: checkpoint-securise-app
description: Sauvegarde sécurisée d'une application (backup SQLite local + commit/push GitHub du CODE seul, jamais les données élèves ni les secrets). À déclencher quand l'utilisatrice dit « fais un checkpoint », « sauvegarde l'app / la webapp », « backup + push », « sauvegarde sur GitHub », « commit la webapp », « point de sauvegarde », ou veut versionner son app après des modifs. Garantit le RGPD : aucune base *.db (données élèves), aucun secret (.env, token, clé, certs) ni binaire lourd n'est poussé. Utiliser cette skill dès qu'il s'agit de sauvegarder/versionner l'app, même sans le mot « checkpoint ».
---

# Checkpoint sécurisé d'une application

Sauvegarder une app de façon sûre, en séparant **ce qui reste local** (données, secrets) de **ce qui va sur GitHub** (le code). Conçu pour l'app enseignante (`~/jarvis/webapp`) où `ecole.db` contient des **données élèves** : les pousser sur un dépôt distant serait une fuite RGPD. Le checkpoint sauvegarde donc les bases **en local** et ne versionne que le code, avec un garde-fou qui **bloque** tout secret/PII tenté à l'envoi.

## Quand l'utiliser

Dès qu'il faut sauvegarder/versionner l'app : après une session de modifs, avant une expérimentation risquée, ou sur demande explicite (« checkpoint », « sauvegarde », « push »). En cas de doute, l'utiliser — un checkpoint de trop ne coûte rien, une fuite de données élèves coûte cher.

## Procédure (3 cibles de sauvegarde)

| Cible | Quoi | Où | RGPD |
|---|---|---|---|
| **SQL** | `.backup` de chaque `*.db` | `backups/<db>-<horodatage>.db` (local) | reste **local** |
| **Document** | docs `.md` du projet | dans le dépôt | OK |
| **GitHub** | **code** uniquement | dépôt distant, dossier de l'app | **sans `.db`/secrets/binaires** |

## Voie rapide : le script

La séquence est déterministe → utiliser le script bundlé plutôt que de réécrire les commandes :

```bash
bash scripts/checkpoint.sh [DOSSIER_APP] -m "message" [--dry-run] [--no-push]
```
- Défaut `DOSSIER_APP` = `~/jarvis/webapp`.
- `--dry-run` : montre ce qui serait staged + le verdict du garde-fou, sans committer (idéal pour vérifier avant).
- Le script fait : backup SQLite local → garantit le `.gitignore` protecteur → stage **uniquement** code+docs → **garde-fou** (abandon si un secret/PII/binaire est dans l'index) → commit (avec trailer co-auteur) → push la branche courante.

Lancer d'abord en `--dry-run` quand le dépôt n'a pas de `.gitignore` éprouvé, pour confirmer que rien de sensible ne part.

## Le garde-fou anti-fuite (cœur de la skill)

Avant tout commit, vérifier que l'index ne contient **aucun** fichier sensible. C'est le filet de sécurité qui rend la skill fiable même si le `.gitignore` est incomplet :

```bash
git diff --cached --name-only | grep -iE '\.db$|\.env$|\.token|secret|\.pem$|\.key$|certs/|/logiciels/|\.(exe|appimage|jar|bin)$'
```
Si cette commande renvoie quoi que ce soit → **ne pas committer**, retirer ces chemins de l'index (`git reset -- <chemin>`), corriger le `.gitignore`, recommencer. Le script applique exactement cette logique et s'arrête avec un code d'erreur si une fuite est détectée.

Pourquoi c'est important : un `.gitignore` peut oublier un fichier, ou un nouveau secret peut apparaître. Le garde-fou attrape ce que l'ignore-list laisse passer — c'est la dernière ligne de défense avant que des données élèves ne quittent la machine.

## Faire à la main (si besoin de contrôle fin)

1. **Backup SQL local** : `for db in *.db; do sqlite3 "$db" ".backup 'backups/${db%.db}-$(date +%Y%m%d-%H%M).db'"; done`
2. **`.gitignore`** : s'assurer qu'il exclut `*.db`, `backups/`, `*.env`, `*token*`, `*.key`, `*.pem`, `certs/`, les binaires lourds (`logiciels/`), `__pycache__/`.
3. **Stage ciblé** : `git add *.py *.html *.md *.json *.js .gitignore` (pas `git add -A` qui ratisserait les binaires/data).
4. **Garde-fou** (ci-dessus) — bloquer si fuite.
5. **Commit + push** : message clair + trailer `Co-Authored-By:` ; `git push origin "$(git branch --show-current)"`.

## Vérifier après coup

- Le push a réussi : `git log --oneline -1` et l'état distant.
- Aucun secret côté distant : `git ls-files | grep -iE '\.db$|\.env$|token|\.key$'` doit être **vide**.
- Les backups existent : `ls -t backups/ | head`.

## Adapter

- **Autre app** : passer le dossier en 1er argument du script. Le dépôt git est auto-détecté (l'app peut être un sous-dossier d'un mono-repo).
- **Branche** : le script pousse la branche **courante** (ne force pas `main`). Si un merge vers `main` est voulu, le faire explicitement ensuite.
- **Données chiffrées** : pour archiver aussi les `*.db` hors-ligne de façon sûre, les chiffrer (ex. `age`/`sops`) vers un stockage privé — jamais en clair sur GitHub.
