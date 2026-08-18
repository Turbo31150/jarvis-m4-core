[assistant] Je lance l'audit read-only de M1. Je vais collecter les données par blocs de commandes de lecture uniquement.

[assistant] Quatre GPU détectés (pas six), je note. Je continue la collecte : services, Docker, LLM, ports, dépôts git.

[assistant] Collecte terminée. Voici l'état des lieux factuel de M1 au 1er août 2026, 17h07 CEST.

---

# AUDIT READ-ONLY — MACHINE M1

Toutes les commandes ont été exécutées en lecture seule, sans privilèges root. Aucune modification n'a été faite.

## 1. Santé système

**Uptime et charge** : la machine tourne depuis 1 jour 16 h 56. Load average 12,88 / 11,81 / 10,02 sur 16 threads CPU, soit environ 80 % de saturation en moyenne courte, avec une tendance à la hausse (la moyenne 1 min est supérieure à la moyenne 15 min). 839 processus au total.

**Mémoire** : 46 Gio de RAM, dont 25 Gio utilisés, 7,9 Gio libres et 18 Gio en tampon/cache — 21 Gio réellement disponibles. Le swap totalise 135 Gio répartis sur trois espaces (partition NVMe de 96 Go priorité 50, partition dm-0 de 16 Go, zram0 de 24 Go) ; 9,2 Gio sont consommés, entièrement sur la partition NVMe. Le zram et dm-0 sont à zéro.

**Espace disque** :

| Montage | Taille | Utilisé | Dispo | % |
|---|---|---|---|---|
| `/` (sdc2) | 915 G | 644 G | 230 G | 74 % |
| `/mnt/jarvis-data` (sdd3) | 466 G | 390 G | 72 G | 85 % |
| `/mnt/backup-os` (sdd1) | 449 G | 350 G | 77 G | 83 % |
| `/mnt/nvme-fast` (nvme0n1p2) | 374 G | 28 K | 374 G | 1 % |
| `/boot/efi` | 1022 M | 6,2 M | 1016 M | 1 % |

Le NVMe rapide de 374 Go est monté mais vide. Les overlays Docker partagent le système de fichiers racine.

**Zombies** : 2 processus zombie, `node` (PID 1328374, parent 1291132) et `openclaw` (PID 3812390, parent 3344262).

**Top 5 CPU** : `llama-serv

[assistant] **AUDIT M1 — 2026-08-01 17:07 CEST — read-only, sans root**

**Santé** — Uptime 1 j 16 h 56. Load 12,88 / 11,81 / 10,02 sur 16 threads (tendance à la hausse). RAM 46 Gio : 25 utilisés, 7,9 libres, 18 cache, 21 disponibles. Swap 135 Gio (96 G NVMe + 16 G dm-0 + 24 G zram), 9,2 Gio consommés, tous sur le NVMe. 839 processus, 2 zombies (`node` PID 1328374, `openclaw` PID 3812390).

Disques : `/` 915 G à 74 % (230 G libres) · `/mnt/jarvis-data` 466 G à **85 %** (72 G) · `/mnt/backup-os` 449 G à **83 %** (77 G) · `/mnt/nvme-fast` 374 G à **1 %** (monté, vide) · `/boot/efi` 1 %.

Top CPU : `llama-server` (ollama) **476 %** et 9,77 Go RSS · `llama-server` (turbo) 67,5 % · `antigravity` 25,1 % · `bash` 23 % · `chrome` 10,4 %. Top RAM : les deux `llama-server` (9,77 Go + 1,52 Go), `chrome` 767 Mo, `antigravity` 760 Mo, `gnome-shell` 590 Mo.

**GPU — 4 cartes, pas 6.** `nvidia-smi` en compte 4 et `lspci` confirme 4 contrôleurs VGA NVIDIA (les 12 lignes NVIDIA sont des sous-fonctions audio/USB-C). Pilote 595.71.05.

| # | Modèle | VRAM libre / totale | Temp | Util |
|---|---|---|---|---|
| 0 | RTX 2060 | 5 163 / 12 288 Mio | 73 °C | 88 % |
| 1 | GTX 1660 S | 2 954 / 6 144 Mio | 61 °C | 14 % |
| 2 | GTX 1660 S | 6 134 / 6 144 Mio | 46 °C | 0 % |
| 3 | RTX 3080 | 6 676 / 10 240 Mio | 69 °C | 5 % |

Total 34 816 Mio, 13 889 utilisés, **20 927 Mio libres**. Seul le GPU 0 travaille ; le GPU 2 est inutilisé.

**Services systemd — 0 en `failed`** (système et utilisateur). 74 services système `