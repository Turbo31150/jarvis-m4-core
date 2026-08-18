[assistant] Deux symptômes cumulés : **extinctions brutales** + **le mode secours s'éteint aussi**. Le journal montre déjà des `[Hardware Error] MC27 … Power, Interrupts` en rafale (toutes les ~9 s) juste avant la dernière coupure. Je creuse le matériel avant de toucher quoi que ce soit.

[assistant] 🚨 **Trouvé — et c'est critique : `Tctl = +102,2 °C` sur le CPU.**

Ce n'est pas un problème de mode secours : le CPU dépasse sa limite thermique (Tjmax 90 °C sur ce Ryzen 5000), la protection matérielle coupe l'alimentation. Le mode secours s'éteint pour la même raison — il chauffe autant.

Je regarde les ventilateurs et je bride le CPU immédiatement pour gagner du temps.

[assistant] 🔥 **URGENCE : Tctl 104 °C, Tccd1 100 °C, load 14,7 — et aucun capteur de ventilateur n'est visible.** Le CPU tape le mur thermique, la carte mère coupe le courant. Je refroidis d'abord, j'analyse ensuite.

[assistant] ⛔ **Cause racine trouvée : les 10 ventilateurs sont à 0 RPM.** Plus rien ne refroidit la machine — c'est pour ça que même le mode secours s'éteint (il chauffe autant sans ventilateur).

Je poursuis le refroidissement d'urgence et je vérifie que la lecture des ventilateurs est fiable.

[assistant] Watercooling + 0 RPM partout = **pompe et/ou ventilateurs du radiateur à l'arrêt**. Je mets tout le refroidissement à fond par le pilote PWM.

[assistant] PWM en lecture seule (`pwm=0`, `enable` vide) : le pilote MSI ne peut pas commander les ventilateurs — **le contrôle est verrouillé côté BIOS**. Le seul levier logiciel restant est de supprimer la charge. Je coupe tout ce qui chauffe.

[assistant] Température **figée à 109,8 °C** alors que la charge est coupée et le CPU bridé à 1,99 GHz. Un CPU qui ne redescend pas à vide, c'est un refroidissement à l'arrêt — la pompe watercooling ne tourne plus. Je bascule le routage sur M6 comme demandé.

[assistant] L'équivalent Linux du MSI Center pour piloter les ventilateurs d'une carte MSI, c'est le module DKMS **nct6687d** — le pilote noyau actuel est en lecture seule, c'est lui qui débloque l'écriture PWM. Je vérifie les prérequis puis je l'installe.

[assistant] Config confirmée : **MSI B550-A PRO + Ryzen 7 5700X3D + AIO 3 ventilateurs**. Le B550-A PRO est explicitement supporté par `nct6687d`. Tous les prérequis sont là — j'installe.

[assistant] Pendant la compilation, je bascule le routage sur M6 — décharger M1 fait aussi baisser sa température.

[assistant] La compilation tourne. Je prépare pendant ce temps le service qui forcera les ventilateurs à fond dès le boot, une fois le module en place.

[assistant] Module compilé, signé (MOK) et installé. Je le charge en mode manuel et je pousse les ventilateurs à fond.

[assistant] Le bon paramètre est `msi_fan_brute_force` (écriture des courbes MSI), pas `manual`. Je recharge correctement.

[assistant] Le PWM reste en lecture seule même avec le pilote MSI : **la carte mère ne commande plus aucun ventilateur**. Le verdict est matériel. Je pose un garde-fou pour éviter que les coupures sèches corrompent tes bases.

[assistant] ⚠️ **Attention : le garde-fou est actif et le CPU est à 111 °C — il va déclencher un arrêt propre d'ici ~1 min.** Pour l'annuler : `sudo shutdown -c`.

## Diagnostic : ce n'est pas le mode secours, c'est le refroidissement

Le mode secours s'éteint pour exactement la même raison que Linux normal — **il chauffe autant**. Les preuves convergent :

| Mesure | Valeur | Normal |
|---|---|---|
| `Tctl` CPU | **111 °C** (monte en continu) | < 60 °C au repos |
| `Tccd1` (die) | **106 °C** | Tjmax 5700X3D = **90 °C** |
| `fan1` → `fan10` | **0 RPM partout** | 3 ventilateurs AIO + boîtier |
| PWM tous canaux | **0**, non inscriptible | pilotés par courbe |
| MCE kernel | `Power, Interrupts` en rafale toutes les 9 s | aucune |
| Arrêts | **coupure sèche**, aucun `shutdown` journalisé | arrêt propre |

**La température ne redescend pas alors que j'ai coupé toute la charge et bridé le CPU à 1,99 GHz.** Un processeur à vide qui reste à 111 °C n'est plus refroidi du tout : ta pompe AIO ne tourne plus (ou n'est plus alimentée).

## Ce que j'ai réparé côté logiciel

- **CPU bridé** — gouverneur `powersave`, fréquence plafonnée à 1,99 GHz
- **Charges tuées/gelées** — `llama-server`, LM Studio, ollama, biblio, gzip, python
- **Routage basculé 100 % sur M6** (`10.42.0.230`, ollama + LMS vérifiés OK) — M2, M3, M4 retirés (inexistants), **M1 sorti du routage** vu son état. Sauvegarde : `~/.openclaw/openclaw.json.bak-*`
- **Pilote MSI installé** — `nct6687d` (l'équivalent Linux du MSI Center) compi