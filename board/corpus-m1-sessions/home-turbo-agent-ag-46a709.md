[assistant] GPU0 est bien reproduit à 89-95 % — je capture le processus responsable pendant qu'il charge.

[assistant] Coupable identifié : un `llama-server` LM Studio chargé à 22:39 sur GPU0. J'inspecte sa ligne de commande complète et la config LM Studio.

[assistant] `--main-gpu 0 --tensor-split 1` : LM Studio épingle 100 % du modèle sur GPU0. Je vérifie la numérotation CUDA et où ce réglage est stocké.

[assistant] Cause racine trouvée : `CUDA_VISIBLE_DEVICES=0` sur le worker. Je lis les deux fichiers de config qui la portent.

[assistant] Je vérifie maintenant si la 3080 a réellement la place, et pourquoi LM Studio a ignoré sa propre priorité `[3,0,1,2]`.

[assistant] Investigation terminée, rien n'a été modifié. Voici le rapport.

## Correction du relevé de départ

Le relevé transmis ne correspond plus à l'état réel, et un point est faux de façon structurante : **GPU0 ne contient pas 7 Go en permanence**. À ma première mesure il était à **460 MiB, 12 % util, 63 °C**. C'est LM Studio en mode JIT : il charge le modèle à la demande et le décharge. Le pic à 91 % s'est reproduit sous mes yeux à 22:39:43, quand une instance `llama-server` a été chargée. Autre écart : il n'y a **qu'une seule instance** `qwen/qwen3.5-9b`, pas deux ; `gpt-oss-20b` et `nomic-embed` sont listés par l'API mais `not-loaded`, donc absents de la VRAM.

## Processus → GPU → VRAM

| PID | Processus | GPU0 (2060) | GPU1 (1660S) | GPU3 (3080) |
|---|---|---|---|---|
| 1957604 | `llama-server` LM Studio — Qwen3.5-9B-Q4_K_M | **6616 MiB** | — | — |
| 3351 | `whisper-server.py` (Lumen, intouchable) | — | 2148 MiB | 2296 MiB |
| 2638953 | `llama-server` ollama — `gemma3:4b` | — | 1032 MiB | 1240 MiB |
| 101747 | `gnome-remote-desktop-daemon` | 91 MiB | — | — |
| 4445 + GNOME | Xorg, gnome-shell, applets | ~370 MiB | 4 MiB | 4 MiB |
| | **Total / libre** | 7077 / **4748** | 3190 / **2560** | 3564 / **6314** |

GPU2 reste à 10 MiB et 0 % — l'exclusion matérielle tient. Il monte quand même à 51-60 °C sans rien faire, ce qui est la signature du ventilateur mort.

## Diagnostic GPU0 en deux phrases

Le worker `llama-server` de LM Studio est lancé avec `CUDA_VISIBLE_DEVICES=0` et `--

[assistant] Rapport transmis à `main` via SendMessage. Résumé de ce qu'il contient :

**Cause racine de GPU0** : le worker `llama-server` de LM Studio (PID 1957604) est lancé avec `CUDA_VISIBLE_DEVICES=0` et `--main-gpu 0 --tensor-split 1`, ce qui épingle 100 % des couches de Qwen3.5-9B (6616 MiB) sur la RTX 2060 qui pilote aussi le bureau. Ce n'est pas le réglage voulu : `hardware-config.json` déclare une priorité `[3, 0, 1, 2]` mettant la 3080 en premier, mais GPU3 n'a que 6314 MiB libres — **il manque ~300 MiB**, d'où le repli automatique sur GPU0.

**Trois corrections apportées au relevé de départ** : GPU0 n'est pas saturé en permanence (LM Studio est en JIT, il était à 460 MiB / 12 % au premier échantillon, le pic s'est reproduit à 22:39:43) ; il n'y a qu'une seule instance qwen, pas deux ; et le seuil de 75 °C est déjà respecté à 72 °C — le vrai problème est le plafond de puissance atteint (147 W / 150 W) avec 81-95 % d'utilisation soutenue sur le GPU d'affichage.

**Point le plus urgent, indépendant du reste** : GPU2 au ventilateur mort n'est pas exclu de LM Studio (`disabledGpus: []`, et le parent tourne avec `CUDA_VISIBLE_DEVICES=0,2,3,4,5`). Rien ne l'empêche aujourd'hui d'y charger un modèle si GPU0 et GPU3 se remplissent.

Le plan en 3 étapes (exclure GPU2, retirer le mmproj vision de 880 Mo inutile en texte, laisser la priorité déjà configurée replacer le modèle sur la 3080 une fois `gemma3:4b` expiré) est proposé mais **non exécuté** — l'investigation est restée strictement