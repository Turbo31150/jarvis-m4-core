# JARVIS Common MCP

Serveur MCP local et **lecture seule** pour les dix répertoires partagés par
l'utilisateur. Il permet d'inventorier, rechercher et inspecter les contenus
non sensibles, puis de préparer des plans de conversion sans écrire de fichier.

`_admin-prive` et `connexion` sont volontairement exposés comme `restricted` :
leur contenu ne quitte jamais l'hôte via ce serveur.

## Démarrage local

```bash
python3 tools/jarvis-common-mcp/server.py
```

## Utilisation avec tunnel-client

```bash
tunnel-client init --sample sample_mcp_stdio_local --profile jarvis-common \
  --tunnel-id "$CONTROL_PLANE_TUNNEL_ID" \
  --mcp-command "python3 /home/turbo/jarvis/tools/jarvis-common-mcp/server.py"
tunnel-client doctor --profile jarvis-common --explain
tunnel-client run --profile jarvis-common
```

L'écriture, les conversions effectives, les appels HTTP et toute action externe
doivent être proposés dans un second serveur, avec une approbation explicite et
une liste blanche dédiée.
