[assistant] **Je suis sur M6** (hostname `turbo`, user `turbo`).

| | |
|---|---|
| CPU | Intel i5-4460 @ 3.2 GHz |
| RAM | 11 Go (6 utilisés, 4 dispo) |
| GPU | NVIDIA RTX 2060 |
| IP câble | 10.42.0.230 |
| Tailscale | 100.112.114.32 |

Ce n'est **pas** M1 — malgré le `CLAUDE.md` qui parle de "La Créatrice" (Ryzen 5700X3D / 6 GPUs / 46 Go). Cette machine-ci est bien M6, le nœud branché en Ethernet direct.

[assistant] Fait, les deux.

**1. Raccourci renommé** — `jarvis-demarrage.desktop` (Bureau + menu, `.bak` gardé) :
- `JARVIS · Démarrage M1` → **`JARVIS · Démarrage M6 (RTX 3080)`**
- Commentaire ajouté : `Nœud local M6 — i5-4460, 11 Go RAM, RTX 2060 12G + RTX 3080 (10.42.0.230)`

**2. Terminal direct M4 créé** — `jarvis-shell-m4.desktop` (Bureau + menu + **épinglé en 1ère position du dock**) :
- Nom : `Shell M4 · Asus TUF Gaming (lien direct)`
- `Exec` : `ssh m4` → 10.42.0.1 par le câble Ethernet, clé `jarvis_cluster` + cert, **connexion sans mot de passe testée OK**
- Icône générée : `~/.local/share/icons/jarvis-m4.png`

M4 vérifié en direct : `pamerys-m4`, i5-11400H, 15 Go RAM, **RTX 3050 Laptop**, ping 1,4 ms.

Deux points à te signaler :

- **La RTX 3080 n'est pas pilotée.** `lspci` la voit bien (`08:00.0 GA102 [GeForce RTX 3080 LHR]`), mais `nvidia-smi` ne liste que la 2060. Le driver nvidia n'est pas attaché à la 3080 (vfio/blacklist ou carte non initialisée). Elle est donc inutilisable pour l'inférence en l'état — je peux diagnostiquer si tu veux.
- **`jarvis-shell-m6.desktop` fait un SSH vers 10.42.0.230, c'est-à-dire cette machine.** C'est un raccourci en boucle sur lui-même. Je le laisse tel quel, dis-moi si tu veux que je le transforme en terminal local simple ou que je le supprime.

[assistant] Trouvé. Et c'est le même problème que les icônes.

## La 3080 est tombée du bus — Xid 79

```
17:50:09  boot — les 2 GPU chargent OK
17:50:24  la 3080 (08:00.0) devient GPU d'affichage primaire → fb0, écran HDMI-A-2
17:57:09  NVRM: Xid (PCI:0000:08:00): 79, GPU has fallen off the bus.
17:57:09  Xorg (EE) fatal → gnome-shell CRASH (/var/crash/_usr_bin_gnome-shell.1000.crash)
depuis    2550× "nvidia-modeset: ERROR: GPU:1: Error while waiting for GPU progress" (toutes les 5 s)
```

État PCI actuel de la carte :
```
Control: Mem- BusMaster-          ← décodage mémoire et bus mastering coupés
Region 1: 256M [disabled]
Region 3:  32M [disabled]
```
Elle est électriquement muette. Le driver *est* bien attaché (`Kernel driver in use: nvidia`, elle est dans `/proc/driver/nvidia/gpus/`) — ma piste "driver non chargé" d'hier était fausse, la carte a lâché **après** l'init.

## Pourquoi ça arrive

```
00:1c.4 (port PCH)
  └─ 04:00.0  ASMedia ASM1184e — switch PCIe x1 Gen2 4 ports
       └─ 05:05.0  LnkSta: Speed 5GT/s, Width x1
            └─ 08:00.0  RTX 3080
```

La 3080 **n'est pas dans un slot x16** : elle est derrière un splitter de minage, sur un lien **x1 Gen2 (~500 Mo/s)**. Une carte 320 W sur un i5-4460 via riser ASM1184e, c'est la configuration qui produit exactement ce Xid 79. Les suspects, dans l'ordre : alimentation (8-pins mal enfoncés ou en daisy-chain, PSU sous-dimensionnée), puis contact/riser, puis thermique.

La 2060, elle, est dans le vrai slot x16 (`01:00.0`) et se p

[user] migre se que tu voi sur cette amachine m6 sur la machine a laquelle i ;est relier par cabler rj45 quyi est la premieee m4ine m4e m4

[assistant] Le lien est Gigabit et l'injection du 14/08 est déjà en place sur M4 — donc c'est un **rattrapage de 3 jours**, pas une migration à zéro. M4 a déjà `jarvis` (40G), `Workspaces` (14G), `.claude` (4,3G), `.openclaw`, `google-chrome-m1`. Il reste ~126 Go libres.

Avant de lancer, un cadrage qui change vraiment ce que je fais :