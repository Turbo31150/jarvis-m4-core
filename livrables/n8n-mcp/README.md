# n8n-mcp

Outils MCP (et CLI) pour piloter une instance **n8n locale** : lister les
workflows, lire leur détail, déclencher un workflow par webhook. Stdlib Python
uniquement, aucun secret en dur.

## Contenu
```
n8n.py                 # les 3 outils : list_workflows / get_workflow / trigger_workflow
BRANCHER-N8N-MCP.md    # guide de branchement MCP
README.md / FICHE-VENTE.md / LICENSE.txt
```

## Installation
Aucune dépendance tierce (urllib/json).
```bash
export N8N_BASE_URL="http://127.0.0.1:5678"   # défaut
export N8N_API_KEY="<jeton>"                   # Settings > n8n API (jamais loggé)
```

## Usage CLI
```bash
python3 n8n.py list
python3 n8n.py get <workflow_id>
python3 n8n.py trigger <chemin-webhook> --payload '{"cle":"valeur"}'
```

## Branchement MCP
Voir `BRANCHER-N8N-MCP.md` — les 3 fonctions sont directement exposables comme
outils MCP.

## Sécurité
- Le jeton `N8N_API_KEY` est lu dans l'environnement, jamais écrit ni journalisé.
- Aucune exception ne remonte : n8n injoignable/refusé → dict d'erreur
  actionnable (`{"ok": false, "error": ..., "hint": ...}`).
