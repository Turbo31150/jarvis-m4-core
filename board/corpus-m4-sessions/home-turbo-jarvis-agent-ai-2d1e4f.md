[assistant] Le fichier est écrit. Phase rouge du TDD d'abord : je simule la régression (un shim redevenu passe-plat silencieux, sans jamais toucher un GPU).

[assistant] Phase rouge conforme : les 8 échecs sont exactement les contrôles de refus, pour la bonne raison. Phase verte maintenant, contre le verrou de production.

[assistant] Le `.bak-gpulock` contient `disabledGpus=[2,3]` — un état que mes tests n'écrivent jamais : LM Studio réécrit son fichier en direct pendant que le verrou le corrige. Cela rend la section 11 potentiellement instable. J'ajoute une reprise sur les contrôles qui partagent ce fichier avec l'application vivante.

[assistant] Suite livrée et vérifiée.

## Ce qui a été fait

**`/home/turbo/jarvis/tests/test-gpu-verrou.sh`** (exécutable) — 50 contrôles fermes + 7 lacunes documentées, en 14 sections.

**TDD respecté** — phase rouge d'abord : la suite lancée contre un shim régressé (passe-plat silencieux, écritures neutralisées pour ne toucher aucun GPU) échoue à **8 contrôles**, exactement les bons : les 7 refus `77` et le message `Deverrouille`. Tout le reste (lecture, environnement, services, restaurateur de dérive) reste vert — l'échec est isolé au contrat du shim. Puis phase verte contre la production : **50/50, code retour 0**, reproductible sur 3 exécutions consécutives.

Le shim substitué se pilote par `GPU_GUARD_SHIM=<chemin>` ; les contrôles PATH/sudo se marquent alors « ignoré » au lieu de mentir.

## Couverture

Lecture transparente (rc + sortie octet-pour-octet sur `-L`, `--help`, 3 requêtes csv, dont une dont les *valeurs* contiennent « power » et « compute » — piège de faux positif) · refus sans code, mauvais code, forme longue, drapeau en 2ᵉ position, `-rgc`, `drain` · refus maintenu **sous sudo** avec vérification que le GPU 2 est resté `Default` · acceptation avec `1202` testée sur l'indice **99 inexistant** (le portillon s'ouvre, aucune carte n'est touchée) · journal `/var/log/jarvis-gpu-guard.log` (3 verdicts) · hash salé et propriété root du fichier de référence · les deux fichiers d'environnement + attribut immuable · les 2 services `masked`, le timer `enabled`+`active` · les 5 U