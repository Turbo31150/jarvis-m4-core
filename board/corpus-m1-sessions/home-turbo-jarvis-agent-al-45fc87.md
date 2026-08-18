[assistant] Le script est corrigé sans toucher LM Studio. Je teste maintenant que le nouveau comportement fonctionne (daemon déjà prêt → doit passer instantanément), et je répare le relais LAN socat qui est la cause du faux "DEGRADED-LAN".

[assistant] Bon, socat est stable et sans les warnings "Unknown key name" désormais. Je lance maintenant la preuve de stabilité (5 sondes espacées de 20 s) et je vérifie que le timer qwen-warm reste correctement configuré.

[assistant] Le timer est maintenant proprement calé : prochain passage 20:54:49, statut SUCCESS. La boucle de vérification périodique fonctionne de nouveau, sans avoir touché LM Studio.

[assistant] Rapport envoyé au team-lead. Résumé de l'intervention :

**Diagnostic** : `127.0.0.1:1234` (backend local LM Studio) était réellement UP et stable depuis 20:23:38 — le driver `run-jarvis-lms-watchdog` classait à tort "DEGRADED-LAN" à cause du relais socat éteint, pas d'un vrai DOWN. Le flap observé par le team-lead (200 à 20:14, 000 à 20:22) correspondait à une dizaine de redémarrages délibérés de `lms-headless.service` entre 20:01 et 20:23, pendant un réglage de `CUDA_VISIBLE_DEVICES` (exclusion du GPU2 à ventilo mort). Avant cela, entre 18:46 et 19:46, LM Studio n'était simplement pas lancé du tout (vrai DOWN, pas du warmup).

**Corrections apportées** :
- `/home/turbo/jarvis/scripts/lms-qwen-warm.sh` — ajout d'une attente readiness (jusqu'à 60 s) avant `lms load` ; skip propre (exit 0) au lieu d'échec sec si le daemon n'est pas encore prêt.
- `/home/turbo/.config/systemd/user/socat-lms-lan.service` — directives `StartLimit*` déplacées en `[Unit]` (étaient ignorées silencieusement) ; service réactivé (il était mort suite aux tests GPU).
- `jarvis-lms-qwen-warm.timer` — réactivé (arrêté à 19:51, jamais relancé).

LM Studio lui-même n'a jamais été touché ni redémarré. Preuve de stabilité : 5 sondes à 20 s d'intervalle, toutes HTTP 200.