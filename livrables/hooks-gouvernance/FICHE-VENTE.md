# Fiche de vente — hooks-gouvernance

> Prix PROPOSÉ, à valider par Franck (pack de hooks).

## Accroche
Trois hooks qui rendent votre Claude Code plus sûr : il ne surchauffe plus, il
ne boucle plus, et il répond mieux grâce à votre base locale — sans un token.

## Le problème
Un agent IA local qui tourne en continu peut faire chauffer la machine, se
bloquer en boucle sur un hook mal écrit, ou répondre sans connaître votre contexte.

## La solution
Ce pack livre trois hooks éprouvés et **fail-safe** :
- **thermal-guard** suspend l'exécution quand le CPU dépasse le seuil ;
- **stop-validation** rappelle vos TODO/tests sans jamais bloquer ;
- **cache-board-lookup** injecte des extraits de votre base SQLite avant chaque
  prompt (SQL avant inférence = 0 token).

## Ce que vous recevez
- 3 hooks Bash prêts à copier + README d'installation `settings.json`

## Points forts
- Fail-safe absolu (une erreur = laisse passer)
- Anti-boucle « Operation stopped by hook »
- 0-token, lecture pure

## Prix
**29 € — paiement unique** [PROPOSÉ, à valider].

## Cible
Utilisateurs avancés de Claude Code / agents IA locaux.
