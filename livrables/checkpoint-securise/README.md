# checkpoint-securise

Skill Claude Code + script de sauvegarde sécurisée d'une application : backup
SQLite local + commit/push GitHub du **code seul**, avec garde-fou qui **refuse**
de pousser toute PII, secret ou binaire lourd.

## Contenu
```
SKILL.md              # définition de la skill (déclencheurs, usage)
scripts/checkpoint.sh # le driver de sauvegarde
README.md / FICHE-VENTE.md / LICENSE.txt
```

## Installation
Prérequis : `git`, `sqlite3`, un dépôt GitHub configuré (`origin`).
```bash
chmod +x scripts/checkpoint.sh
```
Pour l'utiliser comme skill Claude Code, copiez le dossier dans
`~/.claude/skills/checkpoint-securise-app/`.

## Usage
```bash
scripts/checkpoint.sh [APP_DIR] [-m "message"] [--dry-run] [--no-push]
```
Le script :
1. sauvegarde chaque `*.db` en local (`backups/`) via `.backup` (cohérent) ;
2. garantit un `.gitignore` protecteur (bases, `.env`, secrets, certs, binaires) ;
3. stage uniquement le code/docs ;
4. **garde-fou** : refuse et retire tout fichier sensible détecté dans l'index ;
5. commit + push la branche courante.

## Sécurité (garantie RGPD)
Aucune base `*.db` (données), aucun `.env`/token/clé/certs, aucun binaire lourd
n'est jamais poussé. Le garde-fou bloque et signale toute fuite avant le commit.
