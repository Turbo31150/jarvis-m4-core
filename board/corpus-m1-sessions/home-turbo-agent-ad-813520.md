[user] Tu traites le lot L2.7 du backlog JARVIS. Réponds en français. Tu travailles depuis M1 (/home/turbo). N'utilise aucun subagent.

## Objectif
Remettre en service les 3 services Docker Swarm bloqués à 0 réplique.

## PIÈGE CRITIQUE — il existe DEUX Swarms distincts
1. Le Swarm LOCAL de M1 : M1 est Manager, services nommés `jarvis_prod_*` (dont 4 à 0 réplique). **CE N'EST PAS TA CIBLE. N'y touche sous aucun prétexte.**
2. Le Swarm CIBLE : manager = `rem-linux`, alias SSH `jarvis-dva` (root, BatchMode OK), worker = `serveurremjarvis` (100.124.69.1).

Toute commande `docker service ...` doit être lancée SUR le manager :
`ssh -o BatchMode=yes jarvis-dva 'docker service ...'`

## Les 3 services à 0 réplique et leur cause présumée
| Service | Image | Cause établie précédemment |
|---|---|---|
| `jarvis-app-stack_mcp-server` | `jarvis-mcp-server:latest` | `pull access denied` — image absente du registre, existe seulement en local sur un nœud |
| `jarvis-app-stack_telegram` | `jarvis-telegram:latest` | `pull access denied` — idem |
| `jarvis-tanker_vaultwarden` | `vaultwarden/server:latest` | crash-loop `exit 1` toutes les ~15 s |

Vérifie ces causes toi-même avec `docker service ps <nom> --no-trunc` et les logs — elles datent d'une session antérieure et peuvent avoir changé.

## Analyse attendue
- Pour les deux `pull access denied` : détermine sur QUEL nœud l'image existe réellement (`docker images` sur jarvis-dva ET sur serveurremjarvis via l'alias ssh `remjarvis-server` ou `remjarvi

[assistant] Les deux services ont convergé. Vérification finale de l'état et vérification que M1 (swarm local) n'a pas été touché, puis vérification mémoire post-déploiement.

[assistant] mcp-server et telegram sont maintenant 1/1 Running sur rem-linux, la RAM disponible reste stable (~2.2 Go), et Ollama répond toujours normalement sur 11434.

[assistant] C'est bien confirmé : cette commande `docker service ls` locale (sans ssh) interroge le swarm LOCAL de M1 — 4 services `jarvis_prod_*` toujours à 0 réplique, exactement comme annoncé dans le brief, et je n'y ai touché à aucun moment (toutes mes commandes de modification ont été passées via `ssh jarvis-dva`, donc exclusivement sur le swarm cible rem-linux).

[assistant] ## Rapport final — Lot L2.7

**Statut global : DONE_WITH_CONCERNS**

Contexte confirmé au préalable : swarm cible = manager `rem-linux` (alias `jarvis-dva`), worker = `serveurremjarvis`. Toutes les commandes de modification ont été passées exclusivement via `ssh jarvis-dva 'docker service ...'`. Le swarm LOCAL de M1 (`jarvis_prod_*`, 4 services à 0 réplique) n'a subi aucune action — vérifié en fin de session, toujours à l'identique.

### 1. `jarvis-app-stack_mcp-server` — **RÉPARÉ**
- **Cause racine réelle** (différente de la cause présumée initiale) : le service portait la contrainte de placement `node.role == worker`, qui force Swarm à planifier UNIQUEMENT sur `serveurremjarvis`. Or l'image `jarvis-mcp-server:latest` n'existe que localement sur `rem-linux` (le manager), pas sur le worker, ni dans un registre. D'où `pull access denied` en boucle — pas un problème de credentials registre, un problème de placement.
- **Action appliquée** : `docker service update --constraint-rm "node.role == worker" --constraint-add "node.hostname == rem-linux" jarvis-app-stack_mcp-server`. Choix retenu (option la moins risquée du brief) plutôt que `docker save | ssh | docker load` : zéro transfert de données, zéro doublon d'image à maintenir, config-only.
- **Vérification RAM avant action** : limite du service 384 Mo ; RAM disponible sur rem-linux ~2,2-2,4 Go → marge suffisante, Ollama (11434) vérifié fonctionnel après coup.
- **État final vérifié** : `1/1 Running` sur `rem-linux` (`docker se