[assistant] Balayage niveau 1 fait. Je creuse maintenant /opt en profondeur et je cherche les cibles.

[assistant] Balayage terminé (lecture seule, aucun lien touché).

## Liens symboliques morts

| Lien | Cible morte | Statut | Chemin correct |
|---|---|---|---|
| `/home/turbo/.local/bin/jarvis-content` | `…/Workspaces/jarvis-linux/scripts/jarvis-content.py` | **RÉPARABLE** | `/home/turbo/Workspaces/jarvis-linux/infra/scripts/tools/jarvis-content.py` |
| `/home/turbo/.local/bin/jarvis-visual` | `…/Workspaces/jarvis-linux/scripts/jarvis-visual.py` | **RÉPARABLE** | `/home/turbo/Workspaces/jarvis-linux/src/legacy/jarvis-visual.py` |
| `/home/turbo/.local/bin/jpte-master` | `/home/turbo/jarvis/scripts/jpte-master.sh` | **RÉPARABLE** | `/home/turbo/IA/Core/jarvis/scripts/jpte-master.sh` (aussi `/home/turbo/Workspaces/jarvis-core/scripts/jpte-master.sh`) |
| `/home/turbo/.local/bin/nlm` | `/home/turbo/jarvis/scripts/nlm.sh` | **RÉPARABLE** | `/home/turbo/IA/Core/jarvis/scripts/nlm.sh` |
| `/home/turbo/.local/bin/browser-ctl` | `…/src/jarvis/integrations/browser_control/openclaw_skill.py` | **SOUS RÉSERVE** | le dossier `browser_control/` existe mais ne contient que `mcp_server.py`. Seul `openclaw_skill.py` du repo est dans `…/integrations/requestly/` — **module différent**, pas un simple déplacement |
| `/home/turbo/bin/jarvis-dispatch` | `…/jarvis-linux/infra/scripts/tools/jarvis-ssh-dispatch.sh` | **PERDU** | aucun `jarvis-ssh-dispatch.sh` sous jarvis-linux ni jarvis |
| `/home/turbo/.local/bin/jdispatch` | `…/infra/scripts/tools/antigravity-dispatch.py` | **PERDU** | aucun fichier de ce no

[assistant] **Rapport final — liens symboliques morts (lecture seule, aucun lien modifié)**

| Lien | Cible morte | Statut | Chemin correct |
|---|---|---|---|
| `/home/turbo/.local/bin/jarvis-content` | `/home/turbo/Workspaces/jarvis-linux/scripts/jarvis-content.py` | RÉPARABLE | `/home/turbo/Workspaces/jarvis-linux/infra/scripts/tools/jarvis-content.py` |
| `/home/turbo/.local/bin/jarvis-visual` | `/home/turbo/Workspaces/jarvis-linux/scripts/jarvis-visual.py` | RÉPARABLE | `/home/turbo/Workspaces/jarvis-linux/src/legacy/jarvis-visual.py` |
| `/home/turbo/.local/bin/jpte-master` | `/home/turbo/jarvis/scripts/jpte-master.sh` | RÉPARABLE | `/home/turbo/IA/Core/jarvis/scripts/jpte-master.sh` (alt. `/home/turbo/Workspaces/jarvis-core/scripts/jpte-master.sh`) |
| `/home/turbo/.local/bin/nlm` | `/home/turbo/jarvis/scripts/nlm.sh` | RÉPARABLE | `/home/turbo/IA/Core/jarvis/scripts/nlm.sh` |
| `/home/turbo/.local/bin/browser-ctl` | `/home/turbo/jarvis-linux/src/jarvis/integrations/browser_control/openclaw_skill.py` | SOUS RÉSERVE | dossier présent mais ne contient que `mcp_server.py` ; seul `openclaw_skill.py` du repo est `/home/turbo/Workspaces/jarvis-linux/src/jarvis/integrations/requestly/openclaw_skill.py` — **module différent, pas un déplacement** |
| `/home/turbo/bin/jarvis-dispatch` | `/home/turbo/jarvis-linux/infra/scripts/tools/jarvis-ssh-dispatch.sh` | PERDU | aucun fichier de ce nom |
| `/home/turbo/.local/bin/jdispatch` | `/home/turbo/Workspaces/jarvis-linux/infra/scripts/tools/antig