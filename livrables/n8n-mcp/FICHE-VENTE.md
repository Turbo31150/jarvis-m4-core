# Fiche de vente — n8n-mcp

> Prix PROPOSÉ, à valider par Franck (dev-tool + doc).

## Accroche
Pilotez vos workflows n8n depuis votre assistant IA — lister, inspecter,
déclencher — sans jamais exposer votre jeton.

## Le problème
Connecter un agent IA à n8n oblige d'habitude à écrire du glue-code fragile et à
manipuler des jetons à la main.

## La solution
n8n-mcp fournit 3 outils MCP prêts à brancher (`list_workflows`,
`get_workflow`, `trigger_workflow`). Stdlib Python seule, jeton lu dans
l'environnement, gestion d'erreurs actionnable : n8n éteint ou jeton invalide
renvoient un message clair au lieu de planter.

## Ce que vous recevez
- Le module `n8n.py` (MCP + CLI)
- Le guide `BRANCHER-N8N-MCP.md`

## Points forts
- 0 dépendance tierce
- Aucun secret en dur, jamais journalisé
- Déclenchement webhook prod + fallback mode test

## Prix
**49 € — paiement unique** [PROPOSÉ, à valider].

## Cible
Automaticiens, intégrateurs, makers qui veulent connecter n8n à un agent IA
local.
