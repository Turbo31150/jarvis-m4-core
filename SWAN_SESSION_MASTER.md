# 🦢 SWAN / JARVIS — PLAYBOOK MAÎTRE DE DÉMARRAGE & REJEU DE SESSION

---

## 1. Commande de Rejeu Unique (1-Click Replay)

Pour réexécuter l'intégralité de la configuration, des ponts, de la moisson, de la session Tmux et des inférences GPU :

```bash
bash /home/pamerys/jarvis/scripts/jarvis_full_session_replay.sh
```

Ou directement via l'alias disponible dans chaque terminal :
```bash
jarvis-rejouer
```

---

## 2. Injections Noyau, Démarrage Système & Environnement

| Composant | Fichier de Configuration | Rôle & Paramètres |
|---|---|---|
| **Optimisation Noyau** | [`/etc/sysctl.d/99-jarvis-performance.conf`](file:///etc/sysctl.d/99-jarvis-performance.conf) | `swappiness=15`, `dirty_ratio=15`, `file-max=2097152`, `inotify=1048576` |
| **Profil & Variables Globaux** | [`/etc/profile.d/jarvis_env.sh`](file:///etc/profile.d/jarvis_env.sh) | `PYTHONPATH`, URLs Board M1, endpoints CDP, alias (`board`, `table-ronde`, `cluster-4m`) |
| **Service Boot Automatique** | [`/etc/systemd/system/jarvis-boot-master.service`](file:///etc/systemd/system/jarvis-boot-master.service) | Initialisation au démarrage : gouverneur CPU, liens NVMe/SSD, session Tmux 4M |
| **Superviseur H24** | [`/etc/systemd/system/jarvis-h24-daemon.service`](file:///etc/systemd/system/jarvis-h24-daemon.service) | Maintien permanent des ponts 9761, 8420, 3001, 9742, 18800 |

---

## 3. Matrice de Synchronisation SWAN / Notion

Les informations de session, métadonnées de tâches et résultats de délibérations sont persistés dans :

- **Planning Unifié & Tâches :** [`/home/pamerys/jarvis/databases/unified_plan.db`](file:///home/pamerys/jarvis/databases/unified_plan.db)
- **Base Maîtresse :** [`/home/pamerys/jarvis/databases/jarvis_master.db`](file:///home/pamerys/jarvis/databases/jarvis_master.db)
- **Conseil du Board & Table Ronde :** [`/home/pamerys/jarvis/databases/board.db`](file:///home/pamerys/jarvis/databases/board.db) (3.16 Go | 81 experts)
- **Bibliothèque Vivante :** [`/home/pamerys/jarvis/databases/bibliotheque.db`](file:///home/pamerys/jarvis/databases/bibliotheque.db) (142 documents fondamentaux)

---

## 4. Topologie Active du Cluster 4 Machines

```
┌──────────────────────────────────────┬──────────────────────────────────────┐
│  PANE 0 : M4 LOCAL (pamerys-m4)       │  PANE 1 : M1 CLUSTER GPU (turbo-m1)  │
│  Orchestrateur & Bridges H24         │  LM Studio Inférence & Embeddings    │
│  IP : 100.124.121.16                 │  IP : 100.112.114.32 / 10.42.0.230   │
├──────────────────────────────────────┼──────────────────────────────────────┤
│  PANE 2 : RÉMI PC (rem-linux)        │  PANE 3 : RÉMI SERVEUR (serveurrem)  │
│  Cascade Feeder & CoreDNS            │  Miroir Permanent & Swarm Manager    │
│  IP : 100.113.121.61                 │  IP : 100.124.69.1                   │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

> **Accès direct :** `cluster-4m` ou `tmux attach -t jarvis-4m`
