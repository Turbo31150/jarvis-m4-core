# 🏛️ JARVIS OS — MANIFESTE D'UNIFICATION TOTALE (2026)

> **Système d'Exploitation d'IA Distribuée & Souveraine · 100% Locale · 0-Token Payant**  
> **Nœud Maître Actuel** : Machine M4 (`pamerys` — ASUS TUF Gaming F15)  
> **Nœud Distant H24** : Machine M1 (`10.42.0.230` via lien direct USB-C ASIX — latence 1.38 ms)

---

## ⚡ 1. Commandes Rapides Unifiées (Terminal & CLI)

Toutes les commandes sont accessibles directement depuis n'importe quel terminal ou session Claude Code :

| Commande | Rôle & Action Immédiate | 0-Token ? |
|---|---|:---:|
| `jarvis-status` | **Tableau de bord temps réel** : sonde les 8 ports critiques, les 4 daemons et la taille des bases SQLite. | ✅ Oui |
| `table-ronde "<question>"` | **Grand Conseil Délibératif** : 7 agents IA spécialisés + Arbitre Suprême avec calcul du consensus (0-100%) et citations FTS5. | ✅ Oui |
| `board-top "<question>"` | **Moteur délibératif alternatif** avec affichage direct des preuves vectorielles. | ✅ Oui |
| `bloc "<mots-clés>"` | **Recherche sémantique instantanée** dans les **110 811 blocs** de la Bibliothèque Vivante. | ✅ Oui |
| `bash ~/jarvis/scripts/ask-cascade.sh "<prompt>"` | **Inférence unifiée avec repli automatique** : M1 USB-C (10.42.0.230) $\rightarrow$ Ollama local $\rightarrow$ Gemma/Qwen. | ✅ Oui |
| `bash ~/jarvis/scripts/jarvis-daily-harvest.sh` | **Moisson quotidienne automatique** : scanne GitHub Trending, HN et met à jour la bibliothèque (Timer 06:00). | ✅ Oui |
| `python3 ~/jarvis/scripts/prospection_recruteurs_toulouse.py` | **Générateur d'outreach B2B** pour les 18 recruteurs et ESNs tech ciblés à Toulouse. | ✅ Oui |

---

## 💾 2. Écosystème des Bases de Données (SQL3 & Vector Store)

Toutes les bases sont optimisées en mode **WAL** avec checkpointing automatique :

```
~/jarvis/
├── jarvis_master.db         <- Base Maître (6.5 Go · 86 tables · Tâches, clusters, recruteurs)
├── board/board.db           <- Conseil d'Experts (3.1 Go · 157 257 chunks 100% vectorisés Nomic 768dim)
├── data/
│   ├── prospection_reelle.db<- Pipeline B2B (18 recruteurs Toulouse + 48 grands comptes qualifiés)
│   └── etoile.db            <- Mémoire conversationnelle & dispatch OpenClaw
└── databases/               <- Répertoire unifié de symlinks pour accès rapide
~/.claude/bibliotheque/
└── bibliotheque.db          <- Bibliothèque Vivante FTS5 (57.5 Mo · 110 811 blocs 0-token)
```

---

## 🛡️ 3. Daemons & Auto-Healing Résilient H24

Le watchdog [`/home/pamerys/jarvis/scripts/jarvis-watchdog-resilient.sh`](file:///home/pamerys/jarvis/scripts/jarvis-watchdog-resilient.sh) tourne en continu et auto-relance les services critiques sous 30s :

1. **Ollama (`:11434`)** : Inférence locale `qwen2.5:7b` / `gemma3:4b`.
2. **Whisper Bridge (`:9742` $\rightarrow$ `:9743`)** : ASR vocal temps réel sans latence.
3. **Chat Proxy (`:18800`)** : Passerelle Telegram et messagerie LLM.
4. **Board Server (`:8766`)** : API REST du conseil d'experts.
5. **MCP Server (`:8901`)** : Hub d'outils agents FastAPI.
6. **Biblio Filler Daemon** : Remplissage perpétuel 0-token de la base de connaissances.

---

## 👥 4. Le Grand Conseil des 7 Experts IA (+ 1 Arbitre)

```
                       ┌────────────────────────────┐
                       │     QUESTION UTILISATEUR   │
                       └─────────────┬──────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
  🏛️ L'Architecte             ⚡ L'Arbitre 0-Token        🛡️ L'Expert Sécurité
  (Modularité/Pérennité)      (Coût nul/Inférence locale) (Zero-Trust/Étanchéité)
         │                           │                           │
         ▼                           ▼                           ▼
  🤖 L'Expert Swarms          📊 L'Ingénieur Data         🎙️ L'Expert Vocal
  (OpenClaw/MCP/Hygiene)      (FTS5/Postgres/Embeddings)  (WhisperFlow temps réel)
         │                           │                           │
         └───────────────────────────┼───────────────────────────┘
                                     ▼
                          💼 Le Stratège Business
                          (B2B/Factur-X 2026/Closing)
                                     │
                                     ▼
                          ⚖️ L'ARBITRE SUPRÊME
                  (Synthèse + Consensus 0-100% + Plan)
```

---

## 🌐 5. Répertoire des Dépôts GitHub (`Turbo31150`)

| Dépôt GitHub | Rôle & Contenu | Branche |
|---|---|:---:|
| [**`Turbo31150/jarvis-board-multi-ia`**](https://github.com/Turbo31150/jarvis-board-multi-ia) | Moteur Table Ronde 7 agents, board core FTS5, CLI `board-top` et studio vidéo | `master` |
| [**`Turbo31150/jarvis-n8n-workflows`**](https://github.com/Turbo31150/jarvis-n8n-workflows) | Catalogue complet des flux n8n découpés et documentés Notion-Ready | `main` |
| [**`Turbo31150/BASE-SQL3`**](https://github.com/Turbo31150/BASE-SQL3) | Schémas, architecture SQLite distribuée et synchronisation SQL3 | `main` |
| [**`Turbo31150/franckdelmas.dev`**](https://github.com/Turbo31150/franckdelmas.dev) | Site vitrine avec section Ingénierie IA Souveraine & Recrutement Toulouse | `main` |
| [**`Turbo31150/jarvis-mcp`**](https://github.com/Turbo31150/jarvis-mcp) | Outils et serveurs Model Context Protocol (MCP) | `main` |
| [**`Turbo31150/machine-m4-pamerys`**](https://github.com/Turbo31150/machine-m4-pamerys) | Configuration machine M4, réglages système et sauvegardes | `main` |
