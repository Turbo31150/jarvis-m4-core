[user] Tu diagnostiques un problème de refroidissement GPU sur une machine Linux (Ubuntu, hôte turbo-MS-7C56, utilisateur turbo). Tu ne connais rien de la conversation qui précède.

## Le constat

5 GPU NVIDIA. Deux d'entre eux tournent à 86-88 °C avec le **ventilateur rapporté à 0 %** :

```
0, RTX 2060,       69C, fan 58%, 98W
1, GTX 1660 SUPER, 58C, fan  0%, 45W
2, GTX 1660 SUPER, 88C, fan  0%, 59W   ← sujet
3, GTX 1660 SUPER, 88C, fan  0%, 58W   ← sujet
4, RTX 3080,       70C, fan 49%, 145W
```

`nvidia-smi -q -i 2` rapporte `SW Thermal Slowdown : Active` et `GPU Shutdown Temp : 96 C`. Ces cartes throttlent donc déjà, avec 8 °C de marge avant coupure matérielle.

Contexte connu : ces GTX 1660 SUPER sont montées **sur risers PCIe**. Un service `gpu-powerlimit-noventilo.service` existe déjà et les bride à 70 W (59 W mesurés — il fonctionne). Un timer `jarvis-gpu-cb.timer` surveille toutes les 5 min. Le propriétaire de la machine assume de faire tourner tous les GPU en ligne, températures élevées comprises.

## La question à trancher

**Le ventilateur à 0 % est-il un ventilateur physiquement mort, un ventilateur non piloté, ou un ventilateur simplement non rapporté par le pilote ?** Ces trois cas appellent des réponses opposées, et on ne sait pas lequel est vrai.

Pistes à explorer, tu juges lesquelles sont pertinentes :
- Le pilote NVIDIA expose-t-il un contrôle de ventilateur pour ces cartes ? (`nvidia-settings -q all | grep -i fan`, `nvidia-smi -q -d PERFORMANCE`)
- Existe-t-il 

[assistant] Now let me gather the fan/thermal specifics, Xorg config, sensors, and the script — in parallel.

[assistant] Key signal already: GPU 1 is also at 0 % fan but only 62 °C. Let me check the memory notes and the driver's fan-control surface.

[assistant] The driver enumerates fan objects with real RPM tachometers. Let me map every fan to its GPU.

[assistant] Fan→GPU mapping is ambiguous from nvidia-settings. Let me resolve it authoritatively via NVML.

[assistant] Readings conflict between the two tools. Let me sample both simultaneously, three times, to settle it.

[assistant] Mapping is now unambiguous. Let me verify throttle state, thermal headroom, and the fan-control hardware surface.

[assistant] ## Verdict

**Ventilateurs physiquement à l'arrêt sur les GPU 2 et 3 — mort ou débranchés, pas un défaut de pilotage ni de rapport.** Mais le constat de départ contient un faux positif : le GPU 1 a bien un ventilateur qui tourne.

### La preuve : NVML par canal de ventilateur

`nvidia-smi --query-gpu=fan.speed` ne rapporte **que le canal 0** de chaque carte. En interrogeant NVML canal par canal (`nvmlDeviceGetNumFans` + `nvmlDeviceGetFanSpeed_v2`), corrélé au tachymètre de `nvidia-settings` (RPM réels), 3 relevés simultanés à 8 s d'intervalle :

| smi | Carte (sub-vendor) | Canaux | Duty par canal | RPM | Temp | Watts |
|---|---|---|---|---|---|---|
| 0 | RTX 2060 (MSI) | 1 | **56/57/58 %** | 1892→1970 | 63-69 | 65-131 |
| 1 | 1660S (réf. NVIDIA) | 2 | 0 % / **52-53 %** | 0 / **1839-1848** | **59-62** | 45-56 |
| 2 | 1660S (**ASUS**) | 2 | **0 % / 0 %** | 0 / 0 | **81-86** | 41-50 |
| 3 | 1660S (**MSI**) | 1 | **0 %** | 0 | **83-87** | 42-67 |
| 4 | RTX 3080 | 2 | **46-48 %** / 0 % | 1829-1880 / 0 | 68-72 | 134-171 |

Trois faits qui tranchent :

1. **« Non rapporté » est réfuté** : le GPU 1 est la *même* puce TU116, le *même* pilote 595.84, et il rapporte 52 % et 1842 RPM. Le pilote sait lire ces ventilateurs.
2. **« Non piloté / Coolbits manquant » est réfuté** : `Coolbits` n'est déclaré **nulle part d'actif** (seulement dans `/etc/X11/xorg.conf.bak.current`, fichier mort — `/etc/X11/xorg.conf` n'existe pas ; le seul fichier actif est `/etc/X11/xorg.conf.d/10-nvidia-primary