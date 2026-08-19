[user] <local-command-stdout>CLAUDE_CODE_EFFORT_LEVEL=low overrides effort this session — clear it and ultracode takes over</local-command-stdout>

[assistant] Ventilateurs relancés. `[Bash]`

| Réglage | Avant | Après |
|---|---|---|
| platform_profile | balanced | **performance** |
| throttle_thermal_policy | 0 | **1 (turbo)** |
| pwm1/pwm2_enable | 2 / 0 (auto) | **0 / 0 (full speed)** |
| fan1 / fan2 | 2300 / 2400 tr/min | **2700 / 3400 tr/min** |
| Températures | — | 66 °C (sous la cible 82 °C) |

Statut **WORKING** : les deux ventilateurs tournent en mode plein régime forcé, mesuré après 8 s.

Attention : ces réglages sysfs sont volatils — ils repassent en auto au reboot, et le gouverneur `m4-thermal-governor.sh` peut réécrire le profil s'il est actif. Dis-moi si tu veux les rendre persistants (unité systemd au boot).

[assistant] Mesuré sur 24 s en continu : ils tournent. `[Bash]`

| Métrique | Valeur (19:02:45 → 19:03:06) |
|---|---|
| fan1 | 3400 → 3600 tr/min |
| fan2 | 3500 → 3600 tr/min |
| pwm1/pwm2_enable | 0 / 0 (full speed forcé, tient) |
| profil / policy | performance / 1 (turbo) |
| Température | **27 °C** |

Statut **WORKING** — les deux ventilateurs sont à ~3500 tr/min, pas à zéro. Le CPU est à 27 °C : la machine est froide, donc même à consigne « à fond » le firmware ASUS plafonne le régime, c'est pourquoi le bruit est faible.

Deux points à trancher :
- **Deux instances** de `m4-thermal-governor.sh` tournent en parallèle (PID 3878 et 4675) — elles peuvent se battre sur les réglages. À nettoyer ?
- `asus-fan-boost.service` est déjà présent (« permanent 80% ») : je peux y basculer le mode full-speed pour qu'il survive au reboot.

Si tu n'entends vraiment rien alors que le compteur affiche 3500 tr/min, c'est un défaut mécanique (ventilateur bloqué qui renvoie une valeur tachy erronée) — dis-le moi et je pousse un test de charge pour vérifier le flux d'air réel.