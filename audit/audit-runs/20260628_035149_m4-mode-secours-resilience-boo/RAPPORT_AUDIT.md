# RAPPORT D'AUDIT — M4 « mode secours » + 360°
**Date** : 2026-06-28 03:5x · **Cible** : `~/jarvis` + système M4 (F15) · **Mode réel** : scan local + synthèse Opus
**Profil demandé** : full/deep — *dégradé en local* (cause : surchauffe, cf. §4)

---

## 1. Constat d'entrée — le « mode secours » n'en était pas un
La machine **n'est pas cassée**. Au lancement elle tournait déjà normalement :
| Élément | État |
|---|---|
| Firmware | UEFI |
| OS | Ubuntu 24.04.4 LTS (noble) |
| Kernel actif | 6.17.0-29-generic *(installé : `ii`)* |
| Cible systemd | `graphical.target` |
| Display manager | `gdm.service` **active** |
| GNOME | `gnome-shell` + `gnome-session-bin` + `libmutter-14-0` **présents** |
| Réseau | WiFi `wlo1` 192.168.1.149 — **OK** (extender Merville) |

➡️ La chaîne **BIOS → GRUB/shim → kernel → systemd → gdm → GNOME** est **complète et fonctionnelle**.
Aucune réinstallation de paquets boot nécessaire.

## 2. Résilience boot offline (sans réseau / sans cluster)
- ESP montée : `/dev/nvme0n1p1` sur `/boot/efi` (vfat) ✓
- `grub-efi-amd64`, `shim-signed` ✓ — Secure Boot chain OK
- Cache APT local : **187 .deb** disponibles
- **Manque** : méta-paquets `linux-generic` / `linux-image-generic` (le kernel réel **est** installé, mais les futurs kernels ne seront pas tirés automatiquement). Impact : **mineur**, pas un risque de boot immédiat.

## 3. Scan local (Vague 1)
- **428 fichiers**, 6.4 Go · langs : JSON 67, Shell 53, Python 43, Markdown 28, YAML 15, SQL 5
- Git : branche `clean-main`, 4 commits, dernier = *« routage cloud zéro-token: gpt-oss:120b via API ollama.com (clé hors repo) »*, 1 contributeur
- **Secrets : 12 détections → quasi toutes FAUX POSITIFS**
  - `lm-ask.sh:14/64/96` = commentaires (« 0 token facturé »), nom de modèle
  - `abuseipdb-blacklist-sync.sh:6` = `KEY_FILE=$HOME/jarvis/.secrets/abuseipdb.key` → **bonne pratique** (clé hors repo)
  - `watchdog_critical.sh:9` = commentaire `# 8788 (token)`
  - `AUDIT_CONFIG.yaml:14/15` + `jarvis-audit.py:80` = **les patterns de détection eux-mêmes**
  - ⚠️ **À vérifier** : `swarm-join-node.sh:8` (`WORKER_TOKEN=…`), `ANTIGRAVITY_MASTER.md:267/270`
- 9 fichiers contiennent des marqueurs RGPD
- **Le repo actuel est propre.** Les **7 secrets du dernier handoff** (GitHub PAT, Telegram, Pinecone, CoinEx, Perplexity, LM/OpenRouter, Ollama) sont à révoquer **côté fournisseur** (exposition historique/backups), indépendamment de l'état du repo.

## 4. Incident thermique (résolu pendant l'audit) — point central
Le lancement du mode `deep` (4 agents × 3000 tokens) **a fait monter le CPU à 95°C**, parce qu'il s'est ajouté à une **boucle DOMINO déjà active**.

**Cause racine** (confirmée par la mémoire `m4-surchauffe-overclocking`) :
- `jarvis-domino.service` + `jarvis-cowork-loop.service` **respawnent en boucle** des tâches `lm-ask` (codex-cli-builder voulait lancer `apt upgrade` seul, service-auto-repair, browser-session-curator…)
- Sur **M4 isolé**, M1/M2 sont down → toute la cascade `lm-ask` **retombe sur le CPU local** (gemma3:4b / qwen2.5:7b) → saturation `llama-server` 444 % → 95°C
- Résultats des agents **vides** (« ✓ 15 car. ») → cascade inutile **et** dangereuse

**Correctif appliqué (réversible)** :
| Action | État |
|---|---|
| `no_turbo=1` (turbo OFF) | ✓ |
| governor → `powersave` | ✓ |
| `jarvis-domino` / `cowork-loop` / `cowork-dispatcher` | **stop + disable** |
| Modèles Ollama déchargés, enfants lm-ask tués | ✓ |
| **Température 95 → 77°C** | ✓ |

**Règle structurelle** : ❌ ne **jamais** relancer un audit `deep`/multi-agents sur M4 tant qu'il est isolé. Mode `fast`/`local` uniquement, ou synthèse par Opus.

---

## 5. GROSSE TODO — priorisée

### 🔴 P0 — Sécurité / stabilité (à faire en premier)
- [ ] **Révoquer + régénérer les 7 secrets** exposés (handoff) : GitHub PAT, Telegram, Pinecone, CoinEx, Perplexity, LM/OpenRouter, Ollama
- [ ] Vérifier `swarm-join-node.sh:8` (`WORKER_TOKEN`) et `ANTIGRAVITY_MASTER.md:267/270` → si réels, déplacer dans `~/jarvis/.secrets/` + purge historique git
- [ ] **Décider du sort des boucles** `jarvis-domino` / `cowork-loop` : garder désactivées, ou réactiver avec **garde thermique** (semaphore + cap CPU + skip si T°>85°C)

### 🟠 P1 — Thermique durable
- [ ] Vérifier/activer `m4-thermal-guard.sh` (watchdog 90°C) au boot
- [ ] **Pourquoi l'inférence tourne sur CPU et pas sur la RTX 3050 ?** → forcer l'offload GPU Ollama (`OLLAMA_*` / num_gpu) — c'est LA solution de fond
- [ ] Choisir le profil CPU permanent : `powersave` (sûr, actuel) vs `schedutil` (équilibré pour usage GNOME prof) — *turbo reste OFF tant que non tranché*

### 🟡 P2 — Résilience boot offline
- [ ] `sudo apt-get install --download-only linux-generic` (réactive l'auto-MAJ kernel + cache offline)
- [ ] Snapshot timeshift propre une fois la machine stabilisée

### 🟢 P3 — Session GNOME « pamerys » (professeur)
- [ ] Cadrer le besoin (favoris dock, thème, extensions pédagogiques, dossiers cours) — *brainstorming requis*
- [ ] Nettoyer résidus `turbo→pamerys` restants dans la session GNOME
- [ ] dconf dump/load reproductible pour la session enseignant

### ⚪ P4 — Audit (si besoin d'aller plus loin)
- [ ] Veille web ciblée via WebSearch (pas la cascade locale)
- [ ] Brancher connecteurs manquants (MCP LinkedIn) si volet business voulu
