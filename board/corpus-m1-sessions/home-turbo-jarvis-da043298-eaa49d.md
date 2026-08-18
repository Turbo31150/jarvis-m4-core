[user] Base directory for this skill: /home/turbo/.claude/skills/remplir-bibliotheque

# Bibliothèque Vivante Infinie — remplissage 0-token

Porté du pattern « banque annuelle » de M4 : remplissage par lots, idempotent,
anti-surchauffe GPU, cache SQL, todoliste dynamique qui se régénère toute seule.

Moteur : **LM Studio M1 `:1234`** (qwen3.5-9b) prioritaire → fallback `jarvis_dispatcher.ask()` (Ollama).
Cœur : `~/jarvis/cli/biblio_filler.py`.

## 1. Voir l'avancement
```bash
python3 ~/jarvis/cli/biblio_filler.py --status
```

## 2. Remplir un lot maintenant (à la demande)
```bash
bash ~/.claude/skills/remplir-bibliotheque/scripts/remplir.sh 6      # 6 items
```

## 3. Remplissage perpétuel (daemon)
```bash
systemctl --user status  biblio-filler.service     # état
systemctl --user start   biblio-filler.service     # lancer l'infini
systemctl --user stop    biblio-filler.service     # arrêter
journalctl --user -u biblio-filler.service -f      # suivre en direct
```
Le daemon boucle : lot de 3 toutes les 90 s, pause si GPU ≥ 84 °C, auto-alimente la
todoliste quand elle se vide.

## 4. Où va le contenu
| Type | Destination |
|---|---|
| Commandes | Postgres `cmdlib` (container `jv-infra-biblio-db`) + `Documents/Commande_Directe_Bibliotheque/command_list.md` (section « 🌱 Bibliothèque vivante ») |
| Fiches connaissance | SQLite `jarvis_master.db` table `biblio_knowledge` + `~/jarvis/data/biblio_knowledge/*.md` |
| Todoliste | `jarvis_master.db` table `biblio_topics` |
| Cache 0-token | `

[assistant] **Routage** : biblio 44 023 blocs · daemon `biblio-filler` actif · LMS M1 `qwen3.5-9b` ✅ · Ollama ✅ → équipe montée sur le chantier en cours `feat/content-perf-engine`.

[assistant] **+ protocole 0-token illimité** — les 3 agents sont déjà contraints backends locaux uniquement. Je vérifie le point de rupture réel de l'« illimité » : la file de topics.

[assistant] Le 400 était transitoire (JIT load au boot) — le payload passe maintenant. Le vrai blocage : le daemon a testé LMS à 16:25:28 alors que LM Studio n'était pas encore chaud, il est collé en fallback et n'a produit **aucun lot en 5 min**. Je le relance sur le chemin 0-token.

[assistant] **État — protocole armé** `[OL/local]`

| Brique | État | Preuve |
|---|---|---|
| Bibliothèque vivante | ✅ relancée sur LMS chaud | `done 80110→80112`, `pending 8` |
| Daemon `biblio-filler` | ✅ produit à nouveau | était bloqué en fallback depuis 16:25 |
| Backends 0-token | ✅ LMS 200 · Ollama 200 | `qwen-nothink.sh` → « OK » |
| Équipe multi-agents | 🔄 3 agents en vol | fichiers TSV disjoints, zéro conflit |

**Équipe montée** (chacun son fichier, fusion par mes soins ensuite) :
- `perf-video` → `lib/perf-video-blocs.tsv` — patterns YouTube / Shorts / Reels
- `perf-ecrit` → `lib/perf-ecrit-blocs.tsv` — LinkedIn / blog SEO / carousel
- `audit-moteur` → `lib/perf-engine-blocs.tsv` — audit réel du moteur `content-perf-engine`

**Ce que le sondage a révélé** (ce que la doc ne disait pas) :
1. Le daemon avait sondé LM Studio **à 16:25:28, 3 s après le boot** — refus de connexion, donc bascule fallback. Il y est resté collé : **0 lot produit en 5 minutes** alors que sa cadence est de 50 s. Un « infini » qui tourne à vide.
2. Le `HTTP 400` était transitoire (JIT load) — le payload `/v1/completions` du filler repasse maintenant sans erreur.
3. Le `content` vide de qwen3.5-9b est toujours là sur `/v1/chat/completions` (reasoning runaway) — c'est bien pour ça que le filler passe par `/v1/completions` avec `<think></think>` pré-fermé.

`★ Insight ─────────────────────────────────────`
Le défaut n'est pas le code mais **l'ordre de démarrage** : un service qui sonde sa dépendance une se

[user] Base directory for this skill: /home/turbo/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/dispatching-parallel-agents

# Dispatching Parallel Agents

## Overview

You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

When you have multiple unrelated failures (different test files, different subsystems, different bugs), investigating them sequentially wastes time. Each investigation is independent and can happen in parallel.

**Core principle:** Dispatch one agent per independent problem domain. Let them work concurrently.

## When to Use

```dot
digraph when_to_use {
    "Multiple failures?" [shape=diamond];
    "Are they independent?" [shape=diamond];
    "Single agent investigates all" [shape=box];
    "One agent per problem domain" [shape=box];
    "Can they work in parallel?" [shape=diamond];
    "Sequential agents" [shape=box];
    "Parallel dispatch" [shape=box];

    "Multiple failures?" -> "Are they independent?" [label="yes"];
    "Are they independent?" -> "Single agent investigates all" [label="no - related"];
    "Are they independent?" -> "Can they work in parallel?" [label="yes"];
    "Can they work in parallel?" -> "Parallel dispatch" [label="yes"];
    "Can the

[assistant] Je vérifie l'état de la 1ʳᵉ vague avant d'en dispatcher une seconde sur des domaines réellement disjoints.

[assistant] Load à **10,00** — M1 porte déjà 3 agents + le daemon + LM Studio. La skill est explicite : on ne dispatche pas en parallèle quand les agents se disputent une ressource partagée. Je dispatche donc **un seul** agent supplémentaire, sur un domaine strictement disjoint et **sans appel LLM** (donc sans coût GPU) : le durcissement du démarrage, seul défaut structurel trouvé.

[assistant] **Vague 2 dispatchée — 4 agents en vol**, domaines disjoints, fichiers disjoints (aucun état partagé) :

| Agent | Domaine | Écrit dans | LLM |
|---|---|---|---|
| `perf-video` | patterns YouTube / Shorts / Reels | `lib/perf-video-blocs.tsv` | local |
| `perf-ecrit` | LinkedIn / blog SEO / carousel | `lib/perf-ecrit-blocs.tsv` | local |
| `audit-moteur` | audit réel `content-perf-engine` | `lib/perf-engine-blocs.tsv` | local |
| `durcir-boot` | démarrage service 0-token | drop-in systemd utilisateur | **aucun** |

**Anti-conflit appliqué** — `durcir-boot` a interdiction écrite de toucher `cli/biblio_filler.py`, puisque `audit-moteur` le lit en ce moment. Il se limite au drop-in systemd, sur un nom de fichier neuf pour ne pas écraser les 5 drop-ins existants.

**Ce que je n'ai pas fait, et pourquoi** : la skill invite à dispatcher un agent par domaine indépendant, mais elle exclut le cas où les agents se disputent une ressource partagée. Ici la ressource est le GPU/CPU de M1, déjà à **load 10,00** avec 3 agents + le daemon + LM Studio. J'ai donc plafonné la vague 2 à un seul agent, choisi précisément parce qu'il ne consomme aucun GPU. Ajouter 3 moissonneurs LLM de plus aurait allongé le temps total au lieu de le réduire — et sur ce M1, la famine VRAM est un mode de panne connu.

Chaque agent a une consigne de preuve : sortie réelle ou aveu d'échec, jamais de succès déclaré non vérifié.

Je fusionnerai et dédupliquerai les TSV dans `BLOCS-INDEX.tsv` (clé `nom,source`) à leur re

[assistant] **0-token confirmé** : `fallbacks: 0` sur 100 s, `done 80112 → 80114`, la bibliothèque produit bien via LM Studio.

Sur l'alerte RAM 84 % — le coupable n'est pas l'équipe :