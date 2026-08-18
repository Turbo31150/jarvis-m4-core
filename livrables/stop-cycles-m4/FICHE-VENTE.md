# Fiche de vente — stop-cycles-m4

> Prix PROPOSÉ, à valider par Franck (skill, palier bas).

## Accroche
Votre machine chauffe et rame parce qu'un agent recharge des modèles en boucle ?
Une commande, et la boucle est coupée — pour de bon.

## Le problème
Les agents IA autonomes lancent parfois des boucles d'inférence qui saturent la
RAM et font monter le CPU à 95-100 °C — et qui se relancent au démarrage.

## La solution
stop-cycles-m4 détecte et neutralise ces boucles à tous les niveaux : process,
services systemd --user, autostart, crontab, et décharge les modèles Ollama
résidents — tout en **protégeant** vos applications légitimes. Idempotent et
fail-safe, avec un mode `--dry` pour inspecter d'abord.

## Ce que vous recevez
- La skill (`SKILL.md`) + le driver `driver.sh`

## Points forts
- Coupe ET désactive (ne revient pas au reboot)
- Liste de protection des apps légitimes
- 0-token, mode dry-run

## Prix
**19 € — paiement unique** [PROPOSÉ, à valider].

## Cible
Utilisateurs d'agents IA locaux sur machine contrainte (laptop, mini-PC).
