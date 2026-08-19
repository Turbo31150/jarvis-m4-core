[assistant] Je démarre par les vérifications read-only, en parallèle : état du coffre, présence de sops/age/clé, et suivi git de settings.json.

[assistant] Le garde thermique bloque tout Bash (CPU à 90-96°C) — c'est un vrai garde-fou M4, je ne le contourne pas. Je bascule sur les outils non-Bash (Read + filesystem MCP), qui suffisent pour une analyse read-only. Je lis les fichiers clés et je charge les outils filesystem en parallèle.

[assistant] J'ai les noms de clés sensibles. Je vérifie maintenant l'état du coffre, la clé age, les binaires et le suivi git de `~/.claude` — tout via filesystem MCP (pas de Bash).

[assistant] Le coffre est déjà opérationnel (clé age présente, `.sops.yaml` + fichiers `.enc.env` dont `ollama` et `openclaw`). Je lis la config de chiffrement et le README pour caler la procédure exacte sur l'existant, sans rien déchiffrer.

[assistant] Dernières vérifs pour le plan : permissions réelles de `settings.json` (exposition en clair) et la façon dont `claude` est relancé en arrière-plan (service `cc-terminal-watch`), qui détermine où injecter le wrapper.

[assistant] J'ai tout le nécessaire. Je rends le plan au team lead sans afficher aucune valeur de secret.

[assistant] Plan livré au team-lead. Résumé de ce que j'ai produit (en lecture seule, sans déchiffrer ni afficher aucune valeur) :

**Secrets à migrer** — dans le bloc `env` : `OLLAMA_API_KEY`, `PINECONE_API_KEY`, `GATEWAY_TOKEN`, `OPENCLAW_GATEWAY_TOKEN`. Et deux autres découverts dans le même fichier (bloc `_mcpServers_disabled`) : `GITHUB_PERSONAL_ACCESS_TOKEN` et `EXTENSION_SECRET`. Le reste du bloc env (hosts, URLs, chemins, flags) n'est pas sensible.

**État du coffre** — déjà opérationnel : `~/jarvis/secrets-vault/` avec `.sops.yaml` (recipient age, AES256-GCM), clé privée `~/.config/sops/age/keys.txt` en 600, `.gitignore` qui n'autorise que les `*.enc.env`. `ollama.enc.env` et `openclaw.enc.env` existent déjà (migration partielle probable), mais pas de `pinecone.enc.env`.

**Risque de fuite** — faible : `settings.json` est en chmod 600 et `~/.claude` n'est pas un dépôt git. Le risque résiduel est le stockage en clair (backups/snapshots), ce qui justifie la migration.

**Conception clé** — l'auth Claude Code ne dépend d'aucune de ces clés (elles servent aux hooks/MCP). Comme le bloc `env` de settings.json n'accepte que des valeurs littérales (pas de `$(...)`), la solution propre est un wrapper de lancement `claude-secure` qui fait `set -a; eval "$(sops -d …)"; exec claude` — déchiffrement en mémoire, les hooks héritent de l'env. Retrait des valeurs de settings.json seulement après test SET/UNSET réussi, avec `settings.json.bak` pour rollback.

**Point d'attention transmis** : rout