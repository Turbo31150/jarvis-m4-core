# REPORT — profil `ecole`

## Mission
Câbler une cascade d'inférence 0-token qui **sonde les backends avant de router**, au lieu
de faire confiance à des adresses codées en dur. Déclencheur : la machine M4 a figé au
démarrage et la webapp n'arrivait plus à générer.

## Statut
DONE — vérifié de bout en bout (sonde, inférence réelle, cache, garde-fou RGPD, route HTTP).

## Fichiers modifiés
- `cascade.py` — **nouveau**. Routeur 0-token : sonde, cascade ordonnée, cache SQL, garde-fou RGPD.
- `server.py` — branchement du module (`/api/cascade`, `/api/cascade/status`).

## Constat qui motivait tout
`ai_local.py` routait vers des backends **morts depuis longtemps**, sans jamais s'en rendre compte :

| Backend câblé | État mesuré | Explication |
|---|---|---|
| `M1_HOST = 10.42.0.1:1234` | **MORT** | Cette IP est l'interface USB-C **de M4 lui-même** (`enxf8e43b9b67d4`). La webapp se parlait à elle-même. |
| `M2 = 192.168.1.26:1234` | **MORT** | Mauvais sous-réseau : M4 est en `10.42.0.x` / Tailscale `100.124.121.16`. |
| Ollama local `127.0.0.1:11434` | vivant | Seul survivant — mais il chauffe la machine. |

Deux backends vivants n'étaient **pas** câblés : Rémi-ASUS (Tailscale) et M6 (via tunnel).

## Ce que fait `cascade.py`
Ordre : **cache SQL → déporté → local**, le local en dernier parce qu'il chauffe.

| Rang | Backend | Déporté | Tiers | Note |
|---|---|---|---|---|
| 1 | `remi-asus` (`gemma3:4b`) | oui | **oui** | Tailscale `100.113.121.61` |
| 2 | `remi-asus-27b` (`gemma3:27b`) | oui | **oui** | Plus gros modèle du parc, 17,4 Go |
| 3 | `m6-tunnel` (`qwen2.5:1.5b`) | oui | non | Tunnel SSH vers `turbo@10.42.0.230` |
| 4 | `m4-local` (`gemma3:4b`) | non | non | Chauffe : écarté au-dessus de 82 °C |

- **Sonde avant routage**, résultat mis en cache 60 s — aucune boucle, aucun démon.
- **Garde thermique** : au-delà de 82 °C, le backend local est retiré des candidats.
- Modèles d'embedding et `qwen3:*` (reasoning-runaway, réponse vide) exclus de la génération.

## Garde-fou RGPD (le point le plus important)
`ask(..., nominatif=True)` est **obligatoire** dès qu'un prompt contient un nom d'élève ou de
famille, une appréciation ou une observation. Effets :
- tout backend `tiers=True` (Rémi — machine qui n'appartient pas au foyer) est **écarté** ;
- le cache est **désactivé d'office**, sinon une réponse nominative deviendrait relisible
  par une autre requête via le cache partagé.

Vérifié : en mode nominatif, les candidats retombent de `[remi-asus, remi-asus-27b, m6-tunnel,
m4-local]` à `[m6-tunnel, m4-local]` — les deux machines du foyer.

## Commandes exécutées
```bash
python3 cascade.py --status                 # sonde les 4 backends
python3 cascade.py "…"                      # inférence via la cascade
systemctl --user restart jarvis-webapp      # jamais pkill (casse l'app)
curl -s http://127.0.0.1:7777/api/cascade/status
```

## Tests
| Test | Résultat |
|---|---|
| Sonde des backends | 4/4 détectés, `premier_utilisable = remi-asus` |
| Inférence réelle déportée | OK — réponse pédagogique correcte, 7,7 s à 78 s selon le prompt |
| Coût pour M4 pendant l'inférence | **CPU 54 °C, load 0,47** — zéro chaleur locale |
| Cache (2ᵉ appel identique) | OK — `[cache · 0 ms]`, réponse identique, entrée écrite en base |
| Garde-fou RGPD | OK — backends tiers écartés, `cache=False` forcé |
| Route HTTP `/api/cascade/status` | OK |
| Webapp toujours debout | OK — page d'accueil HTTP 200 |

## Erreurs rencontrées (et corrigées)
- **Cache muet** : mon code interrogeait `cle`/`reponse`/`cree_le`, alors que la table
  existante est en anglais — `ai_cache(key, question, answer, backend, hits, ts)`, ~745 entrées.
  L'erreur SQL était avalée en silence, donc chaque question refaisait 77 s d'inférence.
  Corrigé et revérifié.
- **Fuite RGPD introduite puis refermée** : Rémi avait d'abord été placé en tête de cascade
  sans distinguer les machines tierces. Le champ `tiers` et le mode `nominatif` ont été
  ajoutés après lecture du `CLAUDE.md` de ce profil.

## Décisions
- Le local passe **en dernier**, pas en premier : sur ce poste, la chaleur est la ressource rare.
- Aucun repli vers une IA facturée : si toute la cascade échoue, `AIUnavailable` est levée.
- `ai_local.py` n'a pas été modifié — ses backends morts sont documentés mais intacts.
  Une consolidation reste à arbitrer (voir TODO).

## Prochaine action
Arbitrer entre consolider `ai_local.py` sur `cascade.py` ou garder les deux — il existe
déjà plusieurs routeurs dans le parc, et en empiler un de plus a un coût.
