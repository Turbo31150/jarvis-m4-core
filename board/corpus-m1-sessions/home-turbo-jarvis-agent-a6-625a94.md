[user] Recherche technique rigoureuse sur un problème thermique. Livrable : un rapport dans un fichier. Tu ne connais rien de la conversation qui précède.

## Question

**Deux GPU dont les ventilateurs sont à l'arrêt, montés sur risers PCIe, dissipant passivement : quelle charge soutenue peuvent-ils porter sans dépasser leurs seuils constructeur, et quelle usure induit un régime permanent à 85-88 °C ?**

## Mesures déjà faites (hôte turbo-MS-7C56, 5 GPU NVIDIA, pilote 595.84) — refais-les pour vérifier

| smi | Carte | Canaux ventilo | Duty | RPM | Temp | W |
|---|---|---|---|---|---|---|
| 0 | RTX 2060 (MSI) | 1 | 56-58 % | ~1900 | 63-69 °C | 65-131 |
| 1 | GTX 1660S (réf.) | 2 | 0 % / **52 %** | 0 / **1842** | **59-62 °C** | 45-56 |
| 2 | GTX 1660S (ASUS) | 2 | 0 % / 0 % | 0 / 0 | **81-86 °C** | 41-50 |
| 3 | GTX 1660S (MSI) | 1 | 0 % | 0 | **83-87 °C** | 42-67 |
| 4 | RTX 3080 | 2 | 46-48 % / 0 % | ~1850 | 68-72 °C | 134-171 |

**Attention** : `nvidia-smi --query-gpu=fan.speed` ne lit que le **canal 0** — d'où des faux « 0 % ». Interroge NVML canal par canal (`nvmlDeviceGetNumFans`, `nvmlDeviceGetFanSpeed_v2`) et corrèle au tachymètre `nvidia-settings`.

Faits établis, à ne pas re-démontrer :
- Le pilote **sait** lire ces ventilateurs (GPU 1 : même puce TU116, rapporte 52 % / 1842 RPM). Ni défaut de rapport, ni `Coolbits` manquant — aucun Coolbits actif et 3 ventilateurs tournent quand même.
- **23 °C d'écart à puissance égale** entre GPU 1 (ventilé) et GPU 2/3 (non ventilés), si

[assistant] I'll start by verifying the measurements directly on the host, then research the reliability physics.

[assistant] Key finding already: `targetSpeed` differs from `speed_v2`. Let me verify the NVML policy constants and get the tachometers.

[assistant] Critical data: GPU 2 shows **58 PCIe replays**, and all three 1660S are on **Gen2 x1** links. Let me check the kernel log and process load.

[assistant] Excellent data. Let me start a longer capture to catch natural load transitions — that gives me the thermal time constant without applying any test load.

[assistant] Prior memory confirms an external fan is already installed and Turbo's rule is "all GPUs stay online". Let me refine the fan diagnosis.

[assistant] Let me look for historical thermal data to establish long-term exposure, and check the capture.

[assistant] Confirmed: **θ ≈ 0.70 °C/W passive** — matching the estimate. Now let me fit a first-order thermal model to separate the time constant (peak vs sustained).

[assistant] The system-ID fit is not identifiable at this sampling rate. Let me look for a natural power step in the raw trace instead.

[assistant] Real transient captured. Let me check for historical fan-speed records to test whether these fans ever spun.

[assistant] Historical peak found: **GPU 2 hit 90 °C** — 1 °C under spec. Let me capture the raw command outputs for the report.

[assistant] GPU 2's PCIe link just dropped to **Gen1** and replays climbed 58→61. Let me confirm the link instability.

[assistant] Confirmed: GPU 2's link oscillates Gen1↔Gen2 with replays incrementing live. Let me finalize the thermal computation.

[assistant] θ = **0.700 °C/W** — two independent cards agreeing within 2%. Let me quantify the burst-vs-sustained distinction from the transients.

[assistant] τ = **149 s (R²=0.98)**. Let me settle the fan diagnostic with a check on Coolbits and fan-channel wiring.

[assistant] Measurements complete. Let me write the report's measurement sections while the literature research finishes.

[assistant] Research complete. Let me compute the Arrhenius factors for my actual measured temperature pair, then finish the report.

[assistant] État vérifié inchangé : plafonds à 70 W, `compute_mode=Default` sur les 5 cartes, compteurs `Thermal Slowdown` toujours à 0, ventilateurs boîtier toujours à 0. Aucune modification matérielle, aucune charge de test.

## Rapport

**`/home/turbo/jarvis/board/recherche/03-gpu-passif-risers.md`** (918 lignes, 21 références)

## Conclusions

1. **0,7 °C/W confirmé par mesure** : GPU 2 = 0,691, GPU 3 = 0,694 °C/W — deux marques, deux puissances, accord à 0,4 %. Carte ventilée : 0,267 (rapport 2,6×, cohérent avec les datasheets de dissipateurs).
2. **τ = 149 s mesuré** (R² = 0,982) sur une mise au repos naturelle, plus une composante rapide ≈ 0,22 °C/W. D'où : rafale pleine charge < 60 s = +11 °C ; au-delà de 2,5 min on est en soutenu.
3. **Ces cartes ne peuvent pas soutenir leur propre plafond** : 70 W permanents → 96 °C = seuil de shutdown. Le bridage à 70 W ne les protège pas, seul le rapport cyclique les sauve.
4. **Usure : quatre mécanismes, quatre réponses.** Arrhenius donne ×5-8 sur le silicium — mais Summit (27 648 GPU, 2,5 ans, télémétrie 1 Hz) ne trouve **aucune corrélation température/panne**. Coffin-Manson rend le régime continu *favorable*. Le vrai angle mort est le VRM/condensateurs, dont aucun capteur ne donne la température.
5. **91 °C = limite de fonctionnement garanti**, pas de longévité. Aucun constructeur ne documente cette distinction — l'affirmation inverse, courante en forum, n'est pas sourcée.
6. **Découverte majeure, jamais exploitée** : `nvmlDeviceGetMinMaxF