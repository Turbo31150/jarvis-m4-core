[assistant] Je lance l'inventaire complet — Docker, MCP, ports, services. Tout en 0-token (Bash déterministe).

[assistant] Docker local bloqué par le garde-fou (pile périmée) — je repasse par `jarvis-docker`. Trois trous détectés : LM Studio M6 (:1234), Chrome CDP (:9222), LM Studio local.

[assistant] Docker tourne (29.7.0). 3 conteneurs standalone à terre : `jarvis-mcp`, `jarvis-telegram`, `jarvis-litellm`. Je relance et je répare l'accès M6.

[assistant] Les conteneurs `jarvis-mcp`/`jarvis-telegram` sont en fait des **doublons** des services Swarm déjà Up sur 3100/3400 — je les laisse à terre, c'est l'état sain. Je m'attaque à M6 et aux 2 trous restants.

[assistant] M6 répond bien sur :1234 au second sondage (premier test = faux négatif). Je valide par l'API réelle plutôt que par le socket.

[assistant] M6 répond en 40 s avec contenu vide : c'est le mode *thinking* de qwen3.5 qui brûle les 20 tokens en raisonnement. Je valide avec `/no_think`.

[assistant] La cascade 0-token marche (`jarvis-fast` → gemma3:4b, 9,9 s). M6 est intermittent — je caractérise avant de conclure.

[assistant] HTTP 000 en 1,5 ms = refus immédiat, pas un timeout : LM Studio a lâché le port sur M6. J'ai un accès admin par le repli Tailscale — je l'utilise pour diagnostiquer.

[assistant] Compris — j'enchaîne sur la moisson + vectorisation. D'abord je referme M6 : LM Studio **tourne** (llama-server, Qwen2.5-Coder-14B sur 4 GPU) mais son serveur API a lâché le port 1234. Je le relance.

[assistant] M6 relancé mais il n'écoute que sur `127.0.0.1` — le RJ45 reste aveugle. Je corrige, et en parallèle j'ouvre le volet moisson.

[assistant] **M6 pleinement rétabli** : RJ45 → HTTP 200 en 12,7 ms. Je passe à la moisson session + vectorisation.

[assistant] Cible identifiée : **59 241 chunks sans embedding** (200 969 / 260 210) et **1 507 sessions** (1,8 Go) à moissonner. Je cherche les séries outillées.

[assistant] Parfait enchaînement : `dispatch_embed_deporte.py` vectorise **sur M6** (0 token, 0 chaleur) — le nœud que je viens de rétablir. Je lis la fin du script puis je lance.

[assistant] M6 embeddings OK — 768 dimensions, 294 ms. Je lance la vectorisation déportée des 59 241 chunks en arrière-plan.

[assistant] Vectorisation en marche : **244 chunks/min, 100 % sur M6-direct**, M4 ne fait que du réseau. Je vérifie la thermique et j'ouvre le volet moisson des sessions.

[assistant] Point d'attention : M4 est à **83 °C** — pas à cause de la vectorisation (déportée), donc autre chose chauffe. Je vérifie, et je prépare l'ingest des sessions.

[assistant] Découverte : un **`llama-server` tourne en local sur M4** (69,7 % CPU, 12,5 % RAM) — c'est lui le chauffage, pas ma vectorisation (4,7 %). J'identifie.

[assistant] Le `llama-server` local vient de **ma propre `capture-session.sh`** (Ollama gemma3:4b) — il se déchargera seul. Je regarde l'extracteur de sessions déjà éprouvé pour ne pas réécrire.

[assistant] Vectorisation à 748/59 241. La série `moisson-m1` est paramétrable (`MOISSON_CORPUS`/`MOISSON_DOMAINE`) — je regarde si son extracteur peut viser M4 lui-même.

[assistant] Extracteur mature (filtres secrets/PII/télémétrie/protocole, parcours récursif des sous-agents). Je le réutilise tel quel en le pointant sur M4 via un montage symbolique — sans réécrire de script.

[assistant] Racine virtuelle opérationnelle (1 507 sessions visibles). Je lance la moisson des sessions M4 vers un domaine dédié.

[assistant] Pendant que la moisson tourne, je referme le volet MCP/Docker demandé initialement.