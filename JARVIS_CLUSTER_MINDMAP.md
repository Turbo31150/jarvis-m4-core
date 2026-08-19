# 🗺️ CARTE MENTALE & ARCHITECTURE UNIFIÉE DU CLUSTER JARVIS

---

## 1. Topologie Globale du Cluster 4 Machines

```mermaid
graph TB
    subgraph CLUSTER["🌐 CLUSTER SOUVERAIN JARVIS"]
        M4["💻 Nœud M4 (Orchestrateur Principal)<br/>IP: 100.124.121.16<br/>NVMe: /data (476G) + / (476G)<br/>Tmux: jarvis-4m | Boot: jarvis-boot-master"]
        M1["⚡ Nœud M1 / M6 (Cluster GPU Inférence)<br/>IP: 100.112.114.32 / Direct: 10.42.0.230<br/>LM Studio 0.0.0.0:1234 (DeepSeek-R1, Qwen 3.5)<br/>Embeddings 768D (Nomic Embed)"]
        REMPC["🖥️ Nœud Rémi PC (Asus)<br/>IP: 100.113.121.61<br/>Cascade Feeder & CoreDNS"]
        REMSERV["🗄️ Nœud Rémi Serveur (Tour)<br/>IP: 100.124.69.1<br/>Swarm Manager & Miroir Permanent"]
    end

    subgraph BRIDGES["⚡ SERVICES & PONTS CRITIQUES (H24)"]
        P9761["Web API (Port 9761)"]
        P8420["Monitor (Port 8420)"]
        P3001["Lumen Token (Port 3001)"]
        P9742["Whisper Bridge (Port 9742)"]
        P18800["Chat Proxy JS (Port 18800)"]
        P9108["BrowserOS Headless CDP (Port 9108)"]
        P5678["N8N Workflows (Port 5678)"]
    end

    subgraph BOARD["🏛️ GOUVERNANCE & RAG SOUVERAIN"]
        BOARDDB[("board.db<br/>3.16 Go | 19 Domaines<br/>81 Experts | 272k Chunks 768D")]
        BIBLIO[("bibliotheque.db<br/>Bibliothèque Vivante<br/>142 Docs Fondamentaux")]
        PROSPECT[("prospection_reelle.db<br/>Cibles & Opportunités<br/>Grands Comptes & SEO")]
    end

    subgraph STORAGE["💾 STOCKAGE PERSISTANT & BACKUPS"]
        NVME["NVMe Cache (/data/jarvis-cache)"]
        SSDM1["SSD USB-C Samsung 870 EVO (/media/pamerys/JARVIS-M1)"]
        COLD["Cold Storage (/storage/backups & remi-mirror)"]
    end

    M4 <-->|Tailscale Mesh / USB-C ASIX| M1
    M4 <-->|Tailscale Mesh| REMPC
    M4 <-->|Tailscale Mesh| REMSERV

    M4 --> BRIDGES
    M4 --> BOARD
    M4 --> STORAGE
```

---

## 2. Chaîne de Démarrage & Persistance au Boot

1. **Service Systemd de Boot ([`jarvis-boot-master.service`](file:///etc/systemd/system/jarvis-boot-master.service)) :**
   - Calibrage du gouverneur CPU et politique énergétique `balance_performance`.
   - Raccordement des liens NVMe et montage SSD USB-C M1.
   - Initialisation automatique de la session `tmux jarvis-4m` reliant les 4 machines.
2. **Superviseur H24 ([`jarvis-h24-daemon.service`](file:///etc/systemd/system/jarvis-h24-daemon.service)) :**
   - Surveillance continue et auto-restart des ponts 9761, 8420, 3001, 9742, 18800.
3. **Conteneurs Docker (`unless-stopped`) :**
   - `jv-ia-browseros` (CDP 9108) et `jarvis-n8n` (5678).

---

## 3. Matrice des 7 Portails IA Web Câblés

| # | Plateforme IA | URL | Mode de Contrôle |
|---|---|---|---|
| 1 | **NotebookLM** | `https://notebooklm.google.com` | Headless CDP / Ingestion RAG & Podcasts |
| 2 | **Google Gemini** | `https://gemini.google.com` | Inférence Multimodale & Synthèse |
| 3 | **Google AI Studio** | `https://aistudio.google.com` | Prototypage rapide 2.0 / 1.5 Pro |
| 4 | **OpenAI ChatGPT** | `https://chatgpt.com` | Benchmarks & Prompts |
| 5 | **Manus AI Agent** | `https://app.manus.im` | Délégation de missions de crawl |
| 6 | **Mistral Le Chat** | `https://chat.mistral.ai` | Inférence Européenne Souveraine |
| 7 | **Perplexity AI** | `https://www.perplexity.ai` | Moisson de veille sourcée |

---

## 4. Stratégie de Prospection & SEO LinkedIn

- **Ciblage Décideurs :** Directeurs IA, CTO et Achats (Airbus, Thales, BPCE, Continental).
- **SEO & Mots-clés :** *Orchestration Multi-Agents, LLM Souverain, FinOps IA, RAG 768D, EU AI Act*.
- **Table Ronde :** Intégration de l'expert `agent-browseros-action` pour exécuter les publications et captures web à 0 token payant.
