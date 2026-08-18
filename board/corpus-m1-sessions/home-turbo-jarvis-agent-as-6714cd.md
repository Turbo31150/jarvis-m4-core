[assistant] Le brief contient une erreur : `/home/turbo/jarvis-linux` est un symlink vers `Workspaces/jarvis-linux`, et `scripts/` existe toujours (50 entrées). Je vérifie chaque cible réellement.

[assistant] Terminé. Deux prémisses du brief étaient fausses et changent le résultat : `/home/turbo/jarvis-linux` est un **symlink vivant** vers `Workspaces/jarvis-linux`, et `Workspaces/jarvis-linux/scripts/` **existe toujours** (50 entrées). Deux unités n'étaient donc pas cassées.

| Unité | Ancien chemin | Nouveau chemin | Statut |
|---|---|---|---|
| `/etc/systemd/system/health-patrol.service` | `…/jarvis-linux/scripts/health_patrol.py` | — | **source perdue** |
| `/etc/systemd/system/jarvis-voice-learner.service` | `…/jarvis-linux/venv/bin/python` + `…/scripts/run_voice_learner.py` | `…/jarvis-linux/.venv/bin/python` + `…/infra/scripts/tools/run_voice_learner.py` | **corrigé** |
| `/etc/systemd/system/jarvis-tune.service` | `/home/turbo/jarvis-linux/scripts/system_tune.sh` | `…/jarvis-linux/src/jarvis/core/scripts/monitoring/system_tune.sh` | **corrigé** |
| `~/.config/systemd/user/jarvis-health.service` | `%h/jarvis-linux/scripts/health_check.py` | inchangé | **déjà bon** |
| `~/.config/systemd/user/jarvis-resource-alert.service` | `…/jarvis-linux/scripts/resource-alert-monitor.py` | — | **source perdue** |
| `~/.config/systemd/user/jarvis-domino-autopilot.service` | `/home/turbo/jarvis-linux/scripts/domino_master_autopilot.py` | inchangé | **déjà bon** |
| `~/.config/systemd/user/ollama-bridge.service` | `/home/turbo/jarvis-linux/scripts/lmstudio_bridge.py` | `…/jarvis-linux/src/jarvis/core/scripts/cluster/lmstudio_bridge.py` | **corrigé** |

Points à retenir :

- **`jarvis-voice-

[assistant] | Unité | Ancien chemin | Nouveau chemin | Statut |
|---|---|---|---|
| `/etc/systemd/system/health-patrol.service` | `/home/turbo/Workspaces/jarvis-linux/scripts/health_patrol.py` | — | **source perdue** |
| `/etc/systemd/system/jarvis-voice-learner.service` | `/home/turbo/Workspaces/jarvis-linux/venv/bin/python` + `/home/turbo/Workspaces/jarvis-linux/scripts/run_voice_learner.py` | `/home/turbo/Workspaces/jarvis-linux/.venv/bin/python` + `/home/turbo/Workspaces/jarvis-linux/infra/scripts/tools/run_voice_learner.py` | **corrigé** |
| `/etc/systemd/system/jarvis-tune.service` | `/home/turbo/jarvis-linux/scripts/system_tune.sh` | `/home/turbo/Workspaces/jarvis-linux/src/jarvis/core/scripts/monitoring/system_tune.sh` | **corrigé** |
| `/home/turbo/.config/systemd/user/jarvis-health.service` | `%h/jarvis-linux/scripts/health_check.py` | inchangé | **déjà bon** |
| `/home/turbo/.config/systemd/user/jarvis-resource-alert.service` | `/home/turbo/Workspaces/jarvis-linux/scripts/resource-alert-monitor.py` | — | **source perdue** |
| `/home/turbo/.config/systemd/user/jarvis-domino-autopilot.service` | `/home/turbo/jarvis-linux/scripts/domino_master_autopilot.py` | inchangé | **déjà bon** |
| `/home/turbo/.config/systemd/user/ollama-bridge.service` | `/home/turbo/jarvis-linux/scripts/lmstudio_bridge.py` | `/home/turbo/Workspaces/jarvis-linux/src/jarvis/core/scripts/cluster/lmstudio_bridge.py` | **corrigé** |

3 corrigées, 2 sources perdues, 2 déjà bonnes.

Deux prémisses du brief étaie