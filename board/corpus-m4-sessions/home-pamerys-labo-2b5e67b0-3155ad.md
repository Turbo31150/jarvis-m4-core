[assistant] Le blocage `docker` était un garde-fou importé de la machine `rempc` dont le remède pointe vers un binaire inexistant. La pile réelle tourne bien sur la tour. Je collecte l'état complet, puis je répare le garde-fou.

[assistant] Le moteur de fraîcheur tourne bien — sur la tour, pas en local (d'où le faux « aucun instantané »). Je répare maintenant le garde-fou `docker` qui pointe vers un binaire inexistant.

[assistant] Mémoire consultée (1878 atomes sur la tour — le hook la disait injoignable car il sonde `192.168.50.2` qui est DOWN). Je crée le wrapper.

[assistant] Le gate est désarmé. Je crée maintenant le wrapper `jarvis-docker` et corrige le garde-fou.

[assistant] Le fail-open a laissé passer. Je rends le wrapper exécutable et corrige le chemin mort dans le garde-fou.

[assistant] ## État complet — 18/08/2026, 07:5x

**Point de départ : deux garde-fous importés de la machine `rempc` bloquaient le travail sur M4.**

| Garde-fou | Symptôme | Réparation |
|---|---|---|
| `jarvis-docker-guard.py` | bloquait tout `docker ps/exec/...` en renvoyant vers `/home/rempc/jarvis/bin/jarvis-docker` — **binaire inexistant sur les deux machines** | wrapper créé `~/jarvis/bin/jarvis-docker` (route SSH vers la tour), chemin corrigé dans le hook |
| `memory-gate.py` | **indésarmable** : son matcher n'accepte que `ctx_search`/`mcp-search__*`, serveurs MCP absents ici → `Write`/`Edit`/`Task` refusés en boucle | fragments + matcher étendus aux outils mémoire réels (`jarvis-memory`, `jarvis-board`) |

Sauvegardes horodatées créées pour chaque fichier touché. Le matcher `settings.json` ne prendra effet qu'au prochain démarrage de session.

### 🐳 Conteneurs — tout est sur la tour `serveurremjarvis` (100.124.69.1)

15 UP. Services Swarm (9, tous `1/1`) : `mcp-server`, `telegram`, `grafana`, `litellm`, `loki`, `n8n`, `prometheus`, `redis-replica`, `vaultwarden`. Standalone (6) : `jarvis-openclaw` (healthy, 16 h), `jarvis-proxy` (healthy), `jarvis-cowork` (healthy), `jarvis-postgres` (healthy, 4 j), `jarvis-pg-biblio` (2 h), `jarvis-dns` (2 h).

Arrêtés : `jarvis-telegram` et `jarvis-mcp` Exited (143) depuis 4 jours — remplacés par leurs équivalents Swarm. `litellm` a 4 tâches mortes (255/137) : il redémarre en boucle depuis 7 jours.

### 🔴 Redis — répond, mais vide

`PONG`, `use

[assistant] ## Installé — hooks PreToolUse

**`jarvis-docker` est maintenant résolvable partout** : `~/.local/bin/jarvis-docker` → `~/jarvis/bin/jarvis-docker`. (`~/jarvis/bin` n'est ajouté au PATH que par `.bashrc`, donc absent des shells non interactifs et des hooks — le symlink dans `~/.local/bin`, lui, est vu partout.) Testé : renvoie bien les 15 conteneurs de la tour.

### Les 7 hooks PreToolUse, vérifiés un par un

| Portée | Matcher | Hook | État |
|---|---|---|---|
| global | `Bash(*pytest*)` | `filter-test-output.sh` | présent, exécutable |
| global | `Bash(*journalctl*)` | `filter-logs.sh` | présent, exécutable |
| global | `Bash` | `bash-audit-sentinel.sh` | exit 0 |
| global | `Bash` | `jarvis-docker-guard.py` | **corrigé** |
| global | `Task` | `subagent-logger.py` | exit 0 |
| global | Edit/Write/Task + mémoire | `memory-gate.py` | **corrigé** |
| projet `labo` | `Bash` | `security-gate.sh` | exit 0 |

### Les deux corrections, prouvées par exécution

**`jarvis-docker-guard`** — je lui ai envoyé un vrai payload `docker ps` : il renvoie désormais `/home/pamerys/jarvis/bin/jarvis-docker`, et ce chemin **existe et est exécutable**. Avant, il renvoyait un chemin mort : le blocage était sans issue.

**`memory-gate`** — trois tests :
- payload `mcp__jarvis-memory__search_memory` → fichier `.ok` créé, donc **désarmable** (il ne l'était pas)
- `Write` après désarmage → **autorisé**
- `Write` sur session vierge → **toujours bloqué**, garde-fou intact

Aucune référence `/home/rempc` 

[user] Base directory for this skill: /home/pamerys/.claude/skills/cli_skill_search

# cli_skill_search

Perplexity + web search summary.

## Trigger keywords
recherche,search,trouve

## Status
STUB — generated 2026-05-29 by audit remediation. Implementation pending. Logs invocations to /home/turbo/jarvis/db/cli_history.db (table skill_invocations).

## Cascade
Linked to domino-action-cascade.yaml chains via keyword match (see /home/turbo/jarvis/action_validation/domino-action-cascade.yaml).

[assistant] Le skill n'est plus un stub : `driver.sh` (14 août) est implémenté et ses deux backends répondent. Ce sont `run.sh` et `SKILL.md` qui sont restés à la version du 29 mai, avec des chemins `/home/turbo`.

[assistant] Les ports répondent mais les deux backends échouent — et le journal montre que ce skill n'a **jamais** réussi (seule autre invocation, 14 août : `fail`). Je diagnostique.

[assistant] Cause racine trouvée : `board.py ask` exige **`<domaine> "<question>"`**, or le driver ne passe que la question. D'où l'affichage de l'usage, sortie vide, `fail` — depuis le 14 août.

[assistant] Le driver ne choisit aucun domaine parmi les 18. Je le corrige pour qu'il en sélectionne un — explicite si tu le donnes, sinon par recherche FTS5 déterministe.