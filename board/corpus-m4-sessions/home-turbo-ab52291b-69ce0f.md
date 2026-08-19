[assistant] Branché. ✅

**rem-linux** (portable de Rémi, `100.113.121.61` / `jarvis-rem-pc-asus`) est **actif** sur le tailnet, lien direct `86.210.37.236`, ping ~57 ms.

| Vérif | Résultat |
|---|---|
| Tailscale | active, direct (pas de relais DERP) |
| SSH `rempc` | OK (Tailscale SSH) |
| SSH `root` | OK |
| État machine | up 2 j 16 h, session graphique `:1` ouverte, tmux `pts/3` vivant |

Une fenêtre **Terminal rem-linux** vient d'être ouverte sur ton bureau (`rem-term`, session `rempc`, boucle de reconnexion active).

Autres accès dispo si besoin : `rem-term root` (session root), `rem-term --here` (dans le terminal courant).

À noter : le nœud **`jarvis-franck-m1` est offline** — seuls M4, rem-linux et toi êtes joignables actuellement.

[user] # /skillmp — skills de l'écosystème JARVIS

Argument reçu : ``

Deux CLI, une seule racine durable : `~/labo/bibliotheque/skillsmp`.

## 1. Catalogue — `~/jarvis/bin/skillmp.py`

| Intention | Commande |
|---|---|
| chercher | `skillmp.py search <mots> -n 20` |
| détail + code source | `skillmp.py show <slug>` |
| installer | `skillmp.py install <slug> --cible both` |
| lot écosystème JARVIS | `skillmp.py sync-jarvis --seuil 2` |
| lister l'installé | `skillmp.py installed` |
| retirer | `skillmp.py uninstall <slug>` ou `--tout` |
| état du catalogue | `skillmp.py stats` |

## 2. Pipeline d'ingestion — `~/jarvis/bin/skillmp-pipeline.py`

Compacte 6 étages derrière une façade unique :

| Étage | Rôle |
|---|---|
| `expansion` | découvre les skills **hors sitemap** (pages créateur) |
| `catalogue` | fiches JSON-LD des pages skill |
| `source` | code source réel des `SKILL.md` depuis GitHub (6 workers) |
| `site` | reste du site : pages, docs, métiers, créateurs, dépôts |
| `fr` | mots-clés **français** via le cluster local (0 token) |
| `boucle` | injection toutes les 10 min + classification + sync final |

| Intention | Commande |
|---|---|
| état + volumes | `skillmp-pipeline.py status` |
| démarrer | `skillmp-pipeline.py start [étage...]` |
| arrêter | `skillmp-pipeline.py stop [étage...]` |
| injecter maintenant | `skillmp-pipeline.py inject` |
| journal | `skillmp-pipeline.py logs <étage>` |

Sans argument → `stats` puis `status`, et proposer une recherche.

## Cibles d'éc

[assistant] **État `/skillmp`**

**Catalogue** — `~/labo/bibliotheque/skillsmp`
| Métrique | Valeur |
|---|---|
| Skills indexés | **218 372** |
| Avec code source réel | **26 832** (12 %) |
| Avec mots-clés FR | **9 833** |
| Dépôts / auteurs | 30 644 / 19 290 |
| **Installés** (Claude + OpenClaw) | **1 708** |

**Pipeline** — les 6 étages sont **tous arrêtés**, files brutes à 0 (tout a été injecté, rien en attente).

| Étage | État |
|---|---|
| expansion · catalogue · source · site | arrêté, volume 0 |
| fr · boucle | arrêté |

Rien ne tourne, donc rien ne consomme. Le gisement restant est le code source : 191 540 skills catalogués sans `SKILL.md` collecté — c'est l'étage `source` qui les rendrait installables.

**Ce que je peux lancer tout de suite :**
- `skillmp.py search <mots>` — chercher un skill (dis-moi l'intention, FR ou EN)
- `skillmp-pipeline.py start source` — reprendre la collecte de code source (6 workers GitHub)
- `skillmp-pipeline.py start fr` — étendre les mots-clés FR (0 token, cluster local)
- `skillmp.py sync-jarvis --seuil 2` — poser le lot écosystème JARVIS

Quelle intention veux-tu que je cherche ?

[user] moissson en ultra moteur v10m5 TURBO MODE INSTALLA ASSPIRATION SANS s'arreter a la vitesse de cette image méthahore

[assistant] API Error: 500 Internal server error. This is a server-side issue, usually temporary — try again in a moment. If it persists, check https://status.claude.com.

[user] moissson en ultra moteur v10m5 TURBO MODE INSTALLA ASSPIRATION SANS s'arreter a la vitesse de cette image méthahore