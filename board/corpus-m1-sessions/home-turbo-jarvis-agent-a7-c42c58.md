[user] Tu mènes une recherche technique rigoureuse sur un problème de dissipation thermique. Tu ne connais rien de la conversation qui précède. Livrable : un rapport écrit dans un fichier.

## La question de recherche

**Deux GPU dont les ventilateurs sont à l'arrêt, montés sur risers PCIe, dissipant passivement : quelle charge de calcul soutenue peuvent-ils porter sans dépasser leurs seuils constructeur, et quelle est l'usure réelle induite par un régime permanent à 85-88 °C ?**

## Les mesures déjà faites sur cette machine

Machine : hôte turbo-MS-7C56, Ubuntu, 5 GPU NVIDIA, pilote 595.84. **Tu peux et dois refaire ces mesures pour les vérifier** (lecture seule uniquement, voir interdits).

| smi | Carte | Canaux ventilo | Duty réel | RPM | Temp | Watts |
|---|---|---|---|---|---|---|
| 0 | RTX 2060 (MSI) | 1 | 56-58 % | 1892-1970 | 63-69 °C | 65-131 |
| 1 | GTX 1660 SUPER (réf.) | 2 | 0 % / **52 %** | 0 / **1842** | **59-62 °C** | 45-56 |
| 2 | GTX 1660 SUPER (ASUS) | 2 | 0 % / 0 % | 0 / 0 | **81-86 °C** | 41-50 |
| 3 | GTX 1660 SUPER (MSI) | 1 | 0 % | 0 | **83-87 °C** | 42-67 |
| 4 | RTX 3080 | 2 | 46-48 % / 0 % | 1829-1880 | 68-72 °C | 134-171 |

Faits établis, à ne pas re-démontrer :
- **Le pilote sait lire ces ventilateurs** : le GPU 1 est la même puce TU116 et rapporte 52 % / 1842 RPM. Ce n'est donc ni un défaut de rapport ni un `Coolbits` manquant.
- **23 °C d'écart à puissance égale** entre le GPU 1 (ventilé) et les GPU 2/3 (non ventilés), silicium identique, même plafond 

[assistant] I'll start by taking my own measurements on the machine, then research the literature in parallel.

[assistant] GPU 2 just went idle (P8, 5.8 W) — that gives me a natural cooldown curve without running any load. Starting a passive logger.

[assistant] Fan enumeration decoded. Now checking control state, PCIe riser health, and kernel logs.