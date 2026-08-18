# JARVIS OMEGA — Passerelle MCP Unique (Cloudflare Workers + Tunnel)

## Architecture

```
                    ┌─────────────────────────┐
                    │  CLAUDE / CODEX / AGENTS │
                    └───────────┬─────────────┘
                                │
                                │ UNE SEULE URL
                                ▼
            https://jarvis-omega.<compte>.workers.dev/mcp
                                │
                    ┌───────────┴─────────────┐
                    │   Cloudflare Worker     │
                    │  (Auth Bearer Token)    │
                    └───────────┬─────────────┘
                                │
                                │ Cloudflare Tunnel (cloudflared)
                                ▼
                    ┌─────────────────────────┐
                    │  Local OMEGA Gateway    │
                    │  (127.0.0.1:18810/mcp)  │
                    └───────────┬─────────────┘
                                │
     ┌───────────┬──────────────┼──────────────┬────────────┐
     ▼           ▼              ▼              ▼            ▼
  Linux       Docker        Cluster         Gemini       SQLite
 Système    Conteneurs    LLM (M1/M2/OL1)  Interactions  Master DB
  (core)      (core)         (core)         (core)       (core)
     ▼           ▼              ▼              ▼
   Manus     Perplexity     Filesystem       Board
```

---

## 1. État des Composants Locaux

- **Service Passerelle** : `systemctl --user status jarvis-omega-gateway.service`
- **Endpoint Local** : `http://127.0.0.1:18810/mcp`
- **Santé** : `curl -s http://127.0.0.1:18810/sante | jq .`
- **Catalogue d'outils actuel** : **40 outils fédérés** (`core__*`, `manus__*`, `perplexity__*`, `filesystem__*`, `board__*`).

---

## 2. Déploiement du Cloudflare Worker

Dossier : `~/jarvis/cloudflare/jarvis-omega-mcp`

### Étape 1 : Définir les secrets
```bash
cd ~/jarvis/cloudflare/jarvis-omega-mcp
npx wrangler secret put OMEGA_PUBLIC_TOKEN   # Token présenté par Claude
npx wrangler secret put ORIGIN_URL           # URL du tunnel (ex: https://xxx.trycloudflare.com/mcp)
npx wrangler secret put ORIGIN_TOKEN         # Token local de ~/.config/jarvis/omega.env
```

### Étape 2 : Déployer
```bash
npx wrangler deploy
```

L'URL permanente sera :
`https://jarvis-omega.<ton-sous-domaine>.workers.dev/mcp`

---

## 3. Configuration dans Claude Desktop & Agents

Dans `claude_desktop_config.json` ou dans l'interface de l'agent :

```json
{
  "mcpServers": {
    "jarvis-omega": {
      "url": "https://jarvis-omega.<ton-sous-domaine>.workers.dev/mcp",
      "headers": {
        "Authorization": "Bearer <TON_OMEGA_PUBLIC_TOKEN>"
      }
    }
  }
}
```

---

## 4. Ajout d'une nouvelle application sans changer d'URL

Pour ajouter n'importe quelle nouvelle application (ex: PostgreSQL, GitHub, N8N, Browser) :
1. Ajouter le serveur dans `~/.mcp.json`.
2. Le gateway le prend en charge automatiquement.
3. Claude Desktop et tous les agents distants découvrent immédiatement les nouveaux outils sans modification de l'URL ni des configurations clientes !
