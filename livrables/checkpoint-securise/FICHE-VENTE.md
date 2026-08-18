# Fiche de vente — checkpoint-securise

> Prix PROPOSÉ, à valider par Franck (skill, palier bas).

## Accroche
Sauvegardez votre app sur GitHub sans jamais y pousser une donnée sensible — le
garde-fou s'en assure à votre place.

## Le problème
Un `git push` maladroit et vos bases de données, vos `.env` ou vos clés
finissent en public. Pour qui manipule des données d'élèves, de patients ou de
clients, c'est une faute RGPD.

## La solution
checkpoint-securise fait un backup local de vos bases SQLite, puis ne pousse que
le code — jamais les données ni les secrets. Un garde-fou inspecte l'index avant
chaque commit et **refuse** tout fichier `*.db`, `.env`, token, clé ou binaire.

## Ce que vous recevez
- La skill Claude Code (`SKILL.md`)
- Le driver `checkpoint.sh` (backup + commit + push protégés)

## Points forts
- Garde-fou anti-fuite « 0 secret / 0 PII »
- `.gitignore` protecteur généré automatiquement
- Mode `--dry-run` et `--no-push`

## Prix
**19 € — paiement unique** [PROPOSÉ, à valider].

## Cible
Développeurs et professions manipulant des données sensibles qui versionnent
leur app.
