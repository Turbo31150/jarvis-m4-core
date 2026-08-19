[assistant] Je commence par lire le plan, puis je vérifie chaque commande contre la machine réelle.

[assistant] Le plan est lu. Je vérifie maintenant la structure JSON, l'énumération GPU et les unités systemd.

[assistant] STATUT: DONE_WITH_CONCERNS

**Fichier écrit :** `/home/turbo/jarvis/docs/protocole-bascule-topologie-gpu.md`
**Commit :** `8448a8b57d562c7884bd66b011707dfb7e3154ff` — `docs(gpu-bench): protocole de bascule de topologie`, branche `feat/content-perf-engine`, rien poussé.

## Ce qui tient tel quel dans le plan

| Vérification | Résultat |
|---|---|
| Structure JSON `d["json"]` → `cfg["fields"]` → `f["key"]=="load.gpuSplitConfig"` | **correcte** — `d["json"]` est une liste de paires `[nom_backend, cfg]`, deux backends, chacun avec le champ visé |
| Index GPU | **corrects** — 0 = RTX 2060 (12 Go), 4 = RTX 3080 (10 Go), `[1,2,3]` = les trois GTX 1660 SUPER (6 Go) |
| Index LM Studio == index nvidia-smi | **oui** — l'instance en service a `CUDA_DEVICE_ORDER=PCI_BUS_ID` et `CUDA_VISIBLE_DEVICES=0,1,2,3,4` |
| Sortie de la vérification finale (point 5) | **`[[], []]`** — exécutée en lecture seule, sortie réelle conforme à l'attendu du plan |

## Écarts trouvés et corrigés

1. **`~/jarvis/bin/gpu-bench.py` n'existe pas** (livrable des tâches 1-6, en cours ailleurs). Ajouté en prérequis explicite avec un `test -f` de contrôle.

2. **Un deuxième garde-fou défait la bascule, absent du plan.** `lms-sentinelle.timer` (utilisateur, toutes les 2 min) démarre `lms-headless.service` quand `:1234` ne répond pas. Pire : son `pgrep -f "LM-Studio.*AppImage"` (tiret) ne reconnaît pas le processus réel `LM_Studio.AppImage` (tiret bas) — pendant la fenêtre d'arrêt de LM Studio elle conclut « absent » 