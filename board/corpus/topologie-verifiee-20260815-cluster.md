---
name: reference_topologie_verifiee_20260815
description: "Topologie du câble direct MESURÉE le 2026-08-15 depuis M4 — le nœud 10.42.0.230 est M6 (2 GPU) ; corrige l'étiquetage de reference_m6_cable_direct et JARVIS Cluster Topology"
type: reference
autorite: mesure directe (ip/ethtool/ping/ssh/nvidia-smi) + confirmation du proprietaire du materiel
---

# Topologie du lien direct (domaine cluster) — état vérifié le 2026-08-15

**Cette source fait autorité sur le lien direct et ses services.**

## Fait central

Le câble RJ45 direct relie **M4** (machine locale, `pamerys-m4`) à **M6**
(nœud distant, `10.42.0.230`). M6 est la machine serveur **à deux GPU**.

## Piège d'identification — le nom Tailscale est trompeur

Le nœud `10.42.0.230` est enrôlé dans le tailnet sous le nom
**`jarvis-franck-m1`** (`100.112.114.32`) et son `hostname` est `turbo`.
**Ces deux noms sont périmés et ne désignent pas M1.**

Preuve matérielle : ce nœud n'a que **2 GPU** (RTX 2060 12 Go + RTX 3080 10 Go),
alors que M1 est décrit dans `JARVIS Cluster Topology` avec **5 GPU** (RTX 3080
+ RTX 2060 + 3× GTX 1660S, 40 Go de VRAM). Un nœud à 2 GPU ne peut pas être M1.

Corollaire méthodologique : **ni le hostname ni le nom Tailscale ne prouvent
l'identité d'une machine.** Les deux survivent aux réinstallations et aux
changements de matériel. Le comptage GPU et la confirmation du propriétaire
priment.

Sont donc erronés :
- `reference_m6_cable_direct`, qui décrit M6 avec une seule GTX 1660S 6 Go et
  place le câble entre M1 et M6 — les deux points sont faux.
- toute déduction « 3080+2060 ⇒ M1 » : cette signature appartient à M6.

## Mesures (2026-08-15)

| Élément | Valeur mesurée | Commande |
|---|---|---|
| Interface locale (M4) | `enxf8e43b9b67d4` (adaptateur USB-C→Ethernet ASIX) | `ip -br addr` |
| IP locale M4 | `10.42.0.1/24` | `ip -4 addr` |
| IP de M6 | `10.42.0.230` | `ping` |
| Lien | 1000 Mb/s, `Link detected: yes` | `ethtool` |
| Latence | **1,37 ms**, 0 % de perte | `ping` |
| CPU / RAM de M6 | 4 cœurs, 11 Go | `nproc`, `free -g` |
| GPU de M6 | **RTX 2060 12 Go + RTX 3080 10 Go** | `nvidia-smi` |
| Disque de M6 | 915 Go, 505 Go libres | `df -h /` |
| Accès | `ssh -o IdentityAgent=none turbo@10.42.0.230` | — |

Le port RJ45 natif `enp47s0` de M4 n'est **pas** le lien direct : il est câblé
sur la box (`192.168.0.20/24`, DHCP), doublonné par le WiFi `wlo1`.

**Ne pas confondre avec `jarvis-rem-server-tour-pc` (`100.124.69.1`)** : machine
distante chez Rémi, 73 ms via relais DERP, SSH refusé par la politique du
tailnet, aucun service LLM exposé. Non câblable.

## Services LLM exposés par M6 sur 10.42.0.230

- **LM Studio** `:1234` (OpenAI-compatible) — HTTP 200
  - chat : `qwen/qwen3.5-9b` (chargé)
  - embeddings : `text-embedding-nomic-embed-text-v1.5`, **dim 768** (chargé le
    2026-08-15 ; auparavant absent, ce qui mettait la voie vectorielle du board
    hors service en `http_400`)
  - sur disque, non chargés : `qwen2.5-coder-14b`, `deepseek-r1-0528-qwen3-8b`,
    `qwen3-4b`
- **Ollama** `:11434` — HTTP 200 (`gpt-oss:20b-cloud`, `qwen2.5:1.5b`)

Chat (6,55 Go) et embedding (84 Mo) **cohabitent** sans éviction.

## Paramétrage réseau persistant

Profil NetworkManager **`M6-direct`** (`e9ea40d0-…`) :
`interface-name=enxf8e43b9b67d4`, `autoconnect=yes`, `autoconnect-priority=200`,
`ipv4.method=shared`, `ipv4.addresses=10.42.0.1/24`.

Assainissement effectué le 2026-08-15 : suppression d'un profil `M6-direct`
homonyme dormant, et passage en `autoconnect=no` du profil auto-généré rival
« Connexion filaire 2 » qui reprenait l'interface à la place de `M6-direct`.
Reprise après coupure physique vérifiée : le lien remonte seul avec son IP.

## Surveillance

Session tmux permanente `jarvis` (`systemd --user`, `linger=yes`) :
- `link-watch` → `~/jarvis/bin/m6-link-watch.sh`, log `~/jarvis/logs/m6-link-watch.log`
- `board-keepwarm` → `~/jarvis/bin/board-keepwarm.sh`, log `~/jarvis/logs/board-keepwarm.log`

## Note de domaine
Fiche indexee dans `cluster-m1` : toute question de routage ou de topologie du
cable direct doit s appuyer sur ces mesures, pas sur `reference_m6_cable_direct`.
