# Brancher n8n comme serveur MCP dans Claude Code

Backlog #17 — préparer le branchement de n8n (workflows locaux) comme serveur MCP.
Module : `$HOME/jarvis/mcp/tools/n8n.py` (stdlib pure, aucun secret en dur).

## 1. État de l'existant (constaté le 2026-08-14)

| Élément | Valeur |
|---|---|
| URL locale n8n | `http://127.0.0.1:5678` (surchargeable par `N8N_BASE_URL`) |
| Base n8n | `~/.n8n/database.sqlite` (~101 Mo, présente) |
| Workflows JSON | 8 fichiers dans `~/jarvis/n8n/` (dont `workflows/`) |
| Auth API REST | en-tête `X-N8N-API-KEY` (jeton via `N8N_API_KEY`) |
| Déclenchement | par **webhook** (`/webhook/<path>`), pas par l'API REST |

> Remarque : la vérification live (up/down) n'a pas pu être exécutée pendant la
> préparation (garde thermique CPU active). Sonder avec `curl -s http://127.0.0.1:5678/healthz`.

## 2. Récupérer un jeton d'API n8n (jamais en clair dans git)

1. Ouvrir l'UI n8n : `http://127.0.0.1:5678` → **Settings → n8n API → Create API Key**.
2. Exporter le jeton en variable d'environnement (session courante) :

   ```bash
   export N8N_API_KEY="<colle-le-jeton-ici>"
   ```

3. Pour le rendre persistant **sans le mettre en clair**, préférer le coffre
   `sops+age` (`~/jarvis/secrets-vault`) puis l'injecter au lancement :

   ```bash
   export N8N_API_KEY="$(sops -d ~/jarvis/secrets-vault/n8n.enc.env | grep '^N8N_API_KEY=' | cut -d= -f2-)"
   ```

   Ne jamais écrire le jeton dans `.mcp.json`, un `.py` ou un fichier suivi par git.

## 3. Tester le module en CLI (avant de le brancher)

```bash
# Lister les workflows
python3 $HOME/jarvis/mcp/tools/n8n.py list

# Détail d'un workflow (id vu dans `list`)
python3 $HOME/jarvis/mcp/tools/n8n.py get <workflow_id>

# Déclencher un workflow par son chemin de webhook (payload optionnel)
python3 $HOME/jarvis/mcp/tools/n8n.py trigger mon-webhook --payload '{"cle":"valeur"}'
```

Si n8n est éteint, la sortie est un JSON propre `{"ok": false, "error": ..., "hint": ...}`
(message actionnable, **aucun crash**).

## 4. Déclarer le serveur MCP dans `~/.claude/.mcp.json`

Le module expose des fonctions Python ; pour l'exposer en MCP, l'enrober dans un
petit serveur (ex. `mcp/n8n_mcp.py` bâti sur `manus_mcp.py` déjà présent) ou le
brancher via un lanceur `stdio`. Bloc d'exemple à ajouter sous la clé `mcpServers` :

```jsonc
{
  "mcpServers": {
    "n8n-jarvis": {
      "command": "python3",
      "args": ["$HOME/jarvis/mcp/n8n_mcp.py"],
      "env": {
        "N8N_BASE_URL": "http://127.0.0.1:5678",
        "N8N_API_KEY": "${N8N_API_KEY}"
      }
    }
  }
}
```

Points clés :
- `N8N_API_KEY` est passé par **référence d'environnement** (`${N8N_API_KEY}`),
  jamais collé en clair dans le fichier.
- `N8N_BASE_URL` permet de pointer une autre instance (M6, conteneur…) sans
  toucher au code.
- Les outils exposés côté MCP : `list_workflows`, `get_workflow`, `trigger_workflow`.

Après édition, relancer Claude Code (ou `/help` / rechargement MCP) et vérifier
que le serveur `n8n-jarvis` apparaît connecté. Un connecteur `DISCONNECTED` doit
être signalé, pas contourné en silence.

## 5. Garde-fous (RGPD / sécurité)

- **Ne jamais pousser sur git** : `~/.n8n/database.sqlite` (contient credentials
  chiffrés + historique d'exécutions), ni aucun `*.sqlite`/`*.sqlite-wal`/`*.bak`,
  ni un `.env` contenant `N8N_API_KEY`. Backup dédié : repo privé `jarvis-sql-backups`.
- Vérifier le `.gitignore` du dépôt : y ajouter `.n8n/`, `*.sqlite*`, `*.enc.env`,
  `**/n8n/*.bak*` si absents.
- Le module `n8n.py` **ne journalise jamais** la valeur du jeton (lu à la volée
  depuis l'environnement).
- Déclenchement d'un workflow = action potentiellement irréversible (envoi mail,
  post…) : confirmer cible + payload avant d'appeler `trigger_workflow`.
- Modifier la base n8n partagée ou redémarrer le service → confirmation explicite.
