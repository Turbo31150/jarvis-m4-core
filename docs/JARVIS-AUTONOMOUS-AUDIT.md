# JARVIS — AUDIT AUTONOME

> Photographie **mesurée** du système au 13/08/2026. Tout ce qui suit provient
> d'une commande exécutée sur la machine, pas d'une supposition. Ce qui n'a pas
> pu être vérifié porte la mention `UNKNOWN`.

## 1. Prévol

| Élément | Valeur mesurée | Commande |
|---|---|---|
| Répertoire | `/home/pamerys/jarvis` (8,3 Go) | `du -sh .` |
| Remote git | `https://github.com/Turbo31150/jarvis-m4-core.git` | `git remote -v` |
| Branche | `refonte-prof-ia-symbiose` | `git branch --show-current` |
| Modifications non commitées | 78 entrées | `git status --porcelain \| wc -l` |
| OS / kernel | Linux 6.17.0-40-generic | `uname -r` |
| CPU / RAM | 12 cœurs / 15 Gi (7,6 Gi de swap déjà consommés) | `nproc`, `free -h` |
| GPU | 1× RTX 3050 Laptop, **4096 MiB** de VRAM | `nvidia-smi` |
| Disque `/` | 468 Go, 79–84 % utilisé | `df -h` |
| Python / Node | 3.12.3 / v22.23.1 | `--version` |
| tmux | 3.4, session `jarvis-dual` déjà vivante | `tmux ls` |
| Claude Code | 2.1.223 | `claude --version` |
| OpenClaw | 2026.7.1-2 (0790d9f), gateway `:18789` → `{"ok":true}` | `openclaw --version`, `curl` |

> **Écart avec l'ordre de mission** : le dépôt de référence annoncé
> (`jarvis-master-orchestrateur`) n'est pas celui présent ici. Le seul remote
> configuré est `jarvis-m4-core`. Aucun clone n'a été fait : travailler dans le
> dépôt réel était la seule option non destructive.

## 2. Backends d'inférence réellement joignables

Sondés par `jarvis-dual discover` (aucun port supposé) :

| Alias | URL | Statut | Modèles exposés |
|---|---|---|---|
| `lmstudio` | `http://127.0.0.1:1234` | UP (`llmster` PID 67025) | 4 |
| `ollama` | `http://127.0.0.1:11434` | UP | 5 |
| `lmstudio_m6` | `http://10.42.0.1:1234` | UP (câble direct) | 5 |
| `lmstudio_m1` | `http://192.168.0.250:1234` | DOWN (`OSError`) | — |

CLI `lms` **absente** du PATH (seul le binaire GUI `lm-studio` existe) : toute la
découverte passe donc par l'API HTTP, pas par la CLI.

### Modèle fantôme confirmé

`qwen/qwen3.5-9b` est listé par `/v1/models` mais renvoie à l'inférence :

```
HTTP 400 — Failed to load model "qwen/qwen3.5-9b". Error: Error loading model.
```

**Un modèle listé n'est pas un modèle disponible.** C'est le premier problème
réel trouvé par le diagnostic, et la raison pour laquelle `model_status()` ne
renvoie jamais `AVAILABLE` comme preuve de fonctionnement.

## 3. Structure du dépôt

62 entrées à la racine. Composants pertinents pour l'orchestration :

| Composant | Rôle réel | Classement |
|---|---|---|
| `multiagent/jarvis-router.py` | routeur multi-agents | KEEP (hors périmètre dual) |
| `scripts/model_router.sh` | routage bash task→modèle + fallback Ollama/cloud | KEEP — c'est l'ancêtre du routeur ; conservé tel quel |
| `scripts/dashboard.py` | tableau de bord existant | KEEP |
| `scripts/watchdog_critical.sh`, `m1-failover-watchdog.sh` | surveillance système/cluster | KEEP (portée ≠ workers) |
| `scripts/bench_massive.sh` | benchmark de masse | KEEP |
| `cli/jarvis_master.py`, `cli/cascade.py` | CLI et cascade existantes | KEEP |
| `bin/j` | lanceur | KEEP |
| **absent** | doctor unifié, adapter provider, worker, dispatcher dual, checkpoint, journal structuré, replay | → créés dans `dual/` |

**Aucun fichier existant n'a été modifié ni supprimé.** Le nouveau code vit dans
`dual/` + `bin/jarvis-dual`.

## 4. Agents, skills, MCP

| Élément | Constat |
|---|---|
| `.claude/` du dépôt | `agent-memory/`, `settings.local.json`, `worktrees/` — **0 agent, 0 skill** |
| Agents | 59 fichiers, mais dans `~/.claude/agents/` (global utilisateur) |
| Skills | 30 répertoires, dans `~/.claude/skills/` (global) |
| MCP dans `~/.claude.json` | **1 seul** (`browseros`) |
| MCP vus en session | ~29, fournis par des **plugins**, non versionnés dans ce dépôt |

**Conséquence directe** : le problème « descriptions d'agents dépassant la limite
de contexte » évoqué dans l'ordre de mission ne se joue **pas dans ce dépôt** —
il n'y a aucun agent ici. Optimiser `~/.claude/agents/` reviendrait à modifier la
configuration globale de l'utilisateur depuis un chantier de dépôt : action hors
périmètre, non faite. Elle est documentée comme point restant.

## 5. Contrainte matérielle décisive

| Ressource | Mesure | Conséquence |
|---|---|---|
| VRAM | 4096 MiB au total, 3658 MiB occupés au moment de l'audit | un seul modèle chargé à la fois |
| RAM | 15 Gi dont 7,6 Gi de swap déjà consommés | pas de marge pour deux modèles en CPU |

→ **Le DUAL par deux modèles sur un même LM Studio est impossible sur cette
machine.** Non par choix logiciel, mais par mesure. La seule architecture dual
honnête ici est **deux backends distincts** :

```
worker_a → LM Studio :1234  (ou M6 :1234 via câble direct)
worker_b → Ollama    :11434
```

C'est ce que `config._assign_workers()` impose, avec le commentaire expliquant
pourquoi.

## 6. Problèmes identifiés

| # | Problème | Gravité | Preuve | Traitement |
|---|---|---|---|---|
| P1 | Modèle listé mais non chargeable (`qwen3.5-9b`) | Critique | HTTP 400 au chargement | détecté par `doctor`, worker basculé sur un modèle sondé |
| P2 | Aucun diagnostic unifié | Critique | aucun script `doctor`/`health` global | `dual/doctor.py` |
| P3 | URLs/timeouts dispersés dans les scripts bash | Majeur | `model_router.sh` code ses 3 URLs en dur | `dual/providers.py` + `dual/config.py` centralisent |
| P4 | Aucun état de job persistant → rien de reprenable | Majeur | pas de `data/*jobs*` avant ce chantier | `dual/checkpoint.py` |
| P5 | Attente silencieuse indistinguable d'un succès | Majeur | pas de timeout différencié | 4 timeouts distincts + statuts `timeout_*` |
| P6 | Aucune preuve de parallélisme | Majeur | mode « dual » = 2 terminaux | `benchmark.dual()` mesure l'overlap |
| P7 | MCP du dépôt non versionnés (1 seul déclaré) | Mineur | `~/.claude.json` | documenté, non modifié (config utilisateur) |
| P8 | 78 fichiers non commités sur la branche courante | Mineur | `git status` | non touchés ; commits limités à `dual/` |

## 7. Ce qui n'a pas été fait, et pourquoi

- **Optimisation des agents `~/.claude/agents/`** : hors dépôt, configuration
  globale de l'utilisateur. Modifier 59 fichiers hors périmètre sans demande
  explicite serait destructif.
- **Worker OpenClaw** : le gateway répond, mais son intégration comme worker
  d'inférence exige de valider son protocole réel. Non testé ⇒ pas de code
  prétendant le faire. `BLOCKED`, documenté.
- **Claude Code comme worker** : lancer `claude -p` depuis l'orchestrateur
  facturerait des tokens à chaque tâche, à rebours de la règle 0-token du projet.
  Non implémenté volontairement.
