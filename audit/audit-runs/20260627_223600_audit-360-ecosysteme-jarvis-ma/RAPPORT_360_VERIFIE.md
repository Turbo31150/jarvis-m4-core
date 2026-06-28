All data is provided. I will write the report directly as my output.

# RAPPORT D'AUDIT 360 — JARVIS OS
## Écosystème JARVIS + machine F15/M4 — 27 juin 2026

---

## Résumé exécutif

JARVIS est un écosystème personnel ambitieux et globalement fonctionnel (~8500 LOC Python, 50 scripts shell, Lumen en Node, stack Docker n8n/portainer/registry, ~30 services systemd user), avec un cœur opérationnel (lumen, orchestrator, sql-bridge, cowork, ARIA, GPU Guardian) qui tourne. Mais l'audit révèle une **dette de sécurité et de fiabilité critique** qui doit être traitée avant toute exposition commerciale.

### Top 5 risques (à traiter en J+7)
| # | Risque | Sév | Axe |
|---|--------|-----|-----|
| 1 | **Secrets en clair commités dans Git** : clés SSH privées (commit 4b5d447), mot de passe Postgres `jarvis2026`, token Swarm `SWMTKN-1`, mot de passe MOK `1234`, règle sudo `NOPASSWD:ALL` | Critical | Sécurité |
| 2 | **Aucun pare-feu actif** (ufw inactif, iptables ACCEPT) avec 10+ services sur `0.0.0.0` (n8n 5678, webapp 7777, uvicorn 8910/8911, gpu_guardian 9090, RDP 3389/3390, swarm 2377) | Critical | Sécurité |
| 3 | **n8n exposé sans authentification** (`N8N_BASIC_AUTH_ACTIVE=false`, HTTP 200) → RCE + exfiltration des credentials de workflows | Critical | Sécurité |
| 4 | **Cluster LLM M1/M2/M3 totalement hors ligne** depuis 22h+, pas de failover effectif → SPOF total sur l'unique `llama-server` local | Critical/High | OPS |
| 5 | **Core dump de 5.8 Go** non investigué + script de prod cassé (`cluster_nav.py` SyntaxError) + escalade `NOPASSWD:ALL` | High | Tech/Sécu |

### Top opportunités
| # | Opportunité | Horizon |
|---|-------------|---------|
| 1 | **Activer la prospection freelance déjà câblée** : 525 missions scrapées (codeur_merged.json), CV prêt (TJM 550-700€). Revenu immédiat réaliste 3-6 k€/mois | J+7 |
| 2 | **Packager Lumen en SaaS** (transcription/traduction 50+ langues, abouti) freemium 9-29€/mois | J+30 |
| 3 | **Aligner le discours sur des preuves vérifiables** (172 outils MCP, 74 scripts trading) avant tout entretien — l'écart 928 agents vs réalité mono-machine détruit la crédibilité | J+7 |
| 4 | **Portfolio GitHub** (4 repos publics propres) en canal d'acquisition (bloc "Hire me" + Calendly) | Q1-Q4 |

**Verdict** : actif technique réel et montrable, mais **non production-ready sur la sécurité**. La priorité absolue est la rotation des secrets compromis + le pare-feu, avant toute démo publique ou exposition réseau.

---

## Axe Technique

### Critical
**Clés SSH privées et secrets dans l'historique Git**
*Preuve* : `git log --all --diff-filter=A` liste `infra/config/ssh-access/jarvis_ed25519` (clé privée), `jarvis-direct.key`, `access.token`, `data/failover.env`, `*.enc` introduits au commit `4b5d447`. Présents sur `origin/main` même retirés du HEAD. `git ls-files` montre encore `cluster-map.enc` et `connect-bundle-*.enc` trackés.
*Reco* : considérer toutes les clés/tokens comme **COMPROMIS**. Régénérer la paire ed25519 et tous les tokens, purger l'historique (`git filter-repo --invert-paths`), force-push, révoquer l'ancienne clé sur `authorized_keys` M1/M2/OL1.

### High
| Constat | Preuve | Reco |
|---------|--------|------|
| **Mot de passe Postgres hardcodé** | `scripts/sqlite_pg_bridge.py:14` → `"password":"jarvis2026"` | Externaliser via `os.environ['PG_PASSWORD']` depuis `.secrets/` + changer le mot de passe (exposé dans l'historique) |
| **Script de prod cassé (SyntaxError)** | `py_compile scripts/cluster_nav.py` échoue ligne 12 `invalid decimal literal` (guillemets `awk` non échappés) → module inexécutable | Corriger l'échappement (quotes simples / triple-quotes) + pre-commit hook `py_compile`/`ruff` |
| **Core dump 5.8 Go à la racine** | `core` = 6 141 210 624 octets (~94% du dossier), aussi en historique git (blob `71339a64`) | Supprimer, purger l'historique, investiguer le segfault, `ulimit -c 0` |

### Medium
- **Service `bt-headset` bloqué en `activating` depuis 1h42** : `ExecStartPre='until systemctl is-active pipewire-pulse; do sleep 1'` = boucle infinie. 5 unités `not-found`, ~12 services dead. → Ajouter `TimeoutStartSec`, nettoyer les unités fantômes.
- **Zéro test, zéro CI, aucun manifeste de dépendances racine** : pas de `requirements.txt`/`pyproject.toml` racine, imports non déclarés (faster_whisper, paramiko, mcp…), pas de README. → `requirements.txt` pinné, ruff, README archi, tests fumée.
- **Dépôt alourdi (80 Mo packés)** : `fr_FR-siwis-medium.onnx` (63 Mo), core, scrapes JSON. `.gitignore` arrivé tardivement (`8fe768c`). → `git filter-repo` pour purger onnx/enc/db/clés.

### Low
- **Duplication code** : `voice_widget.py` / `voice-widget.py` / `voice_pilot.py` (md5 différents). 16 TODO/FIXME, 3 `bare except:`. → Consolider, remplacer bare except.
- **Docker Swarm workers tous Down** : nœuds `jarvis-m2` dupliqués + inconnus. → Nettoyer (`docker node rm`), basculer en compose standalone (cohérent doctrine M4 autonome).

---

## Axe OPS/SRE

### Critical
**Cluster LLM distant (M1/M2/M3) complètement hors ligne**
*Preuve* : `cluster-health.log` → `M1_LM:DOWN(0)`, `M2_LM:DOWN(0)`, `M3_OL:DOWN(0)` depuis 22h+. `curl 192.168.1.85:1234/v1/models` timeout. Logs swarm : "M1/M2 hors ligne" répétés sur 2h.
*Reco* : vérifier connectivité réseau (ping, ports 1234/11434), redémarrer LM Studio, valider le fallback M1→M2→OL1 dans `lm-ask.sh` (OL1:UP(3) disponible).

### High
| Constat | Preuve | Reco |
|---------|--------|------|
| **openclaw-gateway en boucle de restart (67 tentatives)** | `restart counter is at 67`, exit `1/FAILURE`, restart toutes les 5s, dead depuis 21:26 | Debugger `openclaw/dist/index.js`, vérifier `ollama-cloud.conf`, `Restart=no` + `OnFailure=jarvis-failure-handler`, rediriger logs |
| **Services critiques disabled/static non triggerables** | `jarvis-cowork-loop` disabled, `jarvis-domino` disabled, `jarvis-backup`/`health-check` static | `systemctl --user enable` ces services, tester le déclenchement par timers |
| **Unit files corrompus (bad)** | `jarvis-fileserver` et `jarvis-health` STATE=bad, ExecStart pointe `/home/pamerys/Workspaces/jarvis-linux/…` inexistant | Corriger chemins (`s/Workspaces/jarvis//`) ou supprimer |
| **SPOF Ollama local** (instance unique) | PID 2235494 `llama-server` unique, pas de restart policy | `Restart=always RestartSec=5`, watchdog, switchover OL1 |

### Medium
- **5 containers Docker exited** (portainer/registry exit 2 & 255) → `docker logs`, volume potentiellement corrompu, `docker service update --force`.
- **RAM 7.5/15 Go (49%), swap 3.8/11 Go actif** → réduire context Ollama (`-c 2048`), disabler GNOME en headless.
- **GPU 87°C, fan 4700 rpm, état WARM** → baisser OC/quantization, vérifier airflow.
- **Backups à T-3h41, timers décalés** → vérifier `ExecStart` de `jarvis-backup.service`, forcer exécution.
- **`failover.env` existe mais jamais sourcé** (`grep` retourne 0) → documenter le mécanisme, injecter via `EnvironmentFile=`.

### Low
- Spam GNOME 38× `bash-scope launch errors` (gsd-media-keys) — non bloquant.

---

## Axe Sécurité/Souveraineté

### Critical
| Constat | Preuve | Reco |
|---------|--------|------|
| **Aucun pare-feu actif, services sur 0.0.0.0** | `ufw inactif`, `iptables -P INPUT ACCEPT`. `ss -tlnp` : 5678, 7777, 8910, 8911, 9090, 18801, 8788, 2377, 5000, 3389/3390 en `0.0.0.0` | `ufw default deny incoming`, n'autoriser que 22 depuis LAN, binder les listeners sur `127.0.0.1` ou reverse-proxy authentifié |
| **n8n exposé sans authentification** | `N8N_BASIC_AUTH_ACTIVE=false`, `0.0.0.0:5678`, `curl` → HTTP 200. n8n exécute du code + stocke credentials → compromission totale | Activer auth owner, `N8N_ENCRYPTION_KEY` hors dépôt, bind `127.0.0.1`, reverse-proxy TLS, conteneur non-root |
| **Secrets en clair commités** | `sqlite_pg_bridge.py:14` (Postgres `jarvis2026`), `swarm-join-node.sh:8` (token `SWMTKN-1`), `fix-nvidia-yolo.sh:20` (MOK `1234`). Trackés dès commit `cc969f4` | Révoquer/régénérer Postgres, `docker swarm join-token --rotate worker`, changer MOK. Externaliser vers `.secrets/`, purger l'historique (filter-repo/BFG), rotation accès GitHub |

### High
| Constat | Preuve | Reco |
|---------|--------|------|
| **Escalade privilèges permanente : sudoers NOPASSWD:ALL** | `fix-nvidia-yolo.sh:9` écrit `turbo ALL=(ALL) NOPASSWD: ALL` dans `/etc/sudoers.d/` | Supprimer le fichier, retirer la ligne, limiter NOPASSWD aux commandes précises (nvidia-smi, mokutil) |
| **Durcissement SSH rédigé mais non appliqué** | `sshd_hardening.conf` correct mais `/etc/ssh/sshd_config.d/` VIDE, `X11Forwarding yes` actif, SSH sur 0.0.0.0 | Déployer `99-jarvis-hardening.conf`, `sshd -t`, reload. `PasswordAuthentication no`, `AllowUsers turbo`, fail2ban |
| **RDP exposé sur 0.0.0.0** | `ss -tlnp` → `*:3389` et `*:3390` (gnome-remote-desktop) | Restreindre au LAN/VPN WireGuard, NLA, journalisation, ou désactiver |

### Medium
- **Données vocales en clair sans rétention (RGPD)** : `voice_logs/` transcriptions Whisper nominatives `-rw-rw-r--`, non chiffrées (art. 5 & 32 RGPD). → Purge >30j, chiffrement (age/LUKS) ou perms `0600`, registre RGPD.
- **Dépendances cloud extra-UE non cartographiées (CLOUD Act)** : `ollama.com/api/chat`, telegram, abuseipdb, linkedin, codeur. → Cartographier les flux, privilégier cluster local pour le sensible, documenter base légale (RGPD ch. V).

### Low
- **Pas de rotation/centralisation logs (NIS2)** + `ssh -o StrictHostKeyChecking=no` (MITM possible). → logrotate, journald centralisé, pré-provisionner known_hosts.

---

## Axe Business

### High
| Constat | Preuve | Reco |
|---------|--------|------|
| **Chaîne de prospection opérationnelle mais non monétisée** | `codeur-prospect.sh`, `codeur_merged.json` = 525 missions réelles (jusqu'à 10 000€). `ANTIGRAVITY_MASTER.md` = planning hebdo complet. Mais `budget.db` n'a qu'une table `transactions`, zéro facturation | Activer la boucle dès J+7 : 50 missions Python/IA filtrées, 5 propositions/jour, CV TJM 550-700€. Mini-CRM (clients/devis/factures). **Objectif : 3 missions signées sous 30 jours** |
| **Écart crédibilité CV/README vs réalité** | CV annonce "928 agents, 6 GPUs/46GB, 835 pipelines, 21k€/an, 144 MCP". Réel : M4 mono-machine CPU-only, RTX 3050 désactivée, cluster offline, `agent_dispatch_log=0`, `tool_map=172`. `DIVERGENCE_REPORT.md` liste des services SIGKILL | Aligner sur du vérifiable (172 MCP, 74 scripts trading, pipeline vocal <300ms démontrable). Démo live reproductible mono-machine. Un prospect technique qui creuse l'écart détruit la crédibilité |

### Medium
- **Produits monétisables sans offre ni prix** : `lumen` (transcription 50+ langues, React19/Docker/API, MIT) et suite enseignant — aucun pricing/landing. → Packager Lumen en SaaS freemium 9-29€/mois OU suite enseignant B2B2C. Landing + Stripe. Dual-license le cœur monétisé. Cible verticale claire.
- **Dispersion sur 20+ sous-projets** : 20+ répertoires, 7+ plans .md concurrents, cibles mélangées (enseignant/freelance/trader). → Choisir 1 axe revenu Q1 (freelance IA, ROI le plus rapide) + 1 produit vitrine (Lumen). Archiver le reste dans `lab/`. Une page d'offres unique.

### Low
- **Portfolio GitHub sous-exploité** : 4 repos publics propres, aucun lien commercial. → Bloc "Hire me / Services" + Calendly dans chaque README, 1 article technique/mois, SEO "cluster LLM local". Effort quasi nul.

---

## Roadmap

### J+7 — Quick-wins (sécurité d'abord, revenu en parallèle)
1. **[SÉCU/CRITICAL] Rotation de tous les secrets compromis** : régénérer paire ed25519, mot de passe Postgres, `docker swarm join-token --rotate worker`, MOK. Révoquer l'ancienne clé sur tous les nœuds.
2. **[SÉCU/CRITICAL] Activer ufw** : `ufw default deny incoming`, autoriser 22 (LAN), binder n8n/uvicorn/webapp/RDP sur `127.0.0.1` ou LAN.
3. **[SÉCU/CRITICAL] Authentifier n8n** + `N8N_ENCRYPTION_KEY` hors dépôt + bind 127.0.0.1.
4. **[SÉCU/HIGH] Supprimer `/etc/sudoers.d/turbo-nopasswd`** et déployer le hardening SSH (`99-jarvis-hardening.conf`, reload).
5. **[TECH/HIGH] Externaliser le mot de passe Postgres**, corriger `cluster_nav.py`, supprimer le core dump 5.8 Go.
6. **[OPS/CRITICAL] Restaurer le cluster LLM** (M1/M2/M3) ou valider le fallback OL1. `Restart=always` sur Ollama.
7. **[OPS/HIGH] Debugger openclaw-gateway**, enable les services disabled, corriger les unit files bad.
8. **[BUSINESS/HIGH] Lancer la prospection** : 5 propositions/jour sur les 50 missions filtrées. Aligner le CV sur des chiffres vérifiables.

### J+30
- **[TECH] Hygiène repo** : `requirements.txt` pinné, `pyproject.toml`/ruff, README archi, pre-commit hooks, tests fumée. Nettoyer unités systemd fantômes + bt-headset.
- **[SÉCU] RGPD voice_logs** : purge >30j + chiffrement/perms 0600. Cartographier les flux cloud extra-UE.
- **[OPS] Stabilité** : redéployer containers exited, réduire context Ollama, gérer le thermique GPU, fiabiliser backups, documenter `failover.env`.
- **[BUSINESS] Packager Lumen** en SaaS freemium (landing + Stripe). Choisir 1 axe revenu + 1 vitrine, archiver le reste dans `lab/`.

### J+90
- **[SÉCU/NIS2]** logrotate + centralisation logs (journald/syslog), retirer `StrictHostKeyChecking=no`, pré-provisionner known_hosts. Documenter registre RGPD + base légale transferts hors UE.
- **[OPS]** Watchdog/healthchecks formalisés, matrice services attendus vs présents documentée.

### Q1-Q4 — Consolidation
- **[TECH]** Réécriture complète de l'historique Git (`git filter-repo` : core, onnx, enc, db, clés) → clone réduit de 80 Mo à quelques Mo. Trancher : Swarm multi-nœuds vs compose standalone (doctrine M4 autonome).
- **[BUSINESS]** Portfolio GitHub en canal d'acquisition (Hire me + Calendly + 1 article/mois, SEO). Mesurer trafic repo → leads.
- **[GOUVERNANCE]** Mettre en place CI/CD, pinning systématique, doctrine de gestion des secrets pérenne.

---
**Synthèse** : JARVIS est un actif crédible et largement fonctionnel, mais porté par une dette de sécurité critique (secrets compromis, pas de pare-feu, n8n ouvert) qui doit être soldée en J+7 avant toute exposition. La monétisation freelance est activable immédiatement avec l'outillage existant ; la condition est d'aligner le discours commercial sur la réalité auditée.