[assistant] Aucun doublon. Écart 75 037 sources vs 70 530 index — je vérifie s'il s'agit de perte ou de dédoublonnage.

[assistant] Le tirage avec source d'entropie fixe est biaisé (10/20 sur une seule source). Je refais un tirage réellement aléatoire.

[assistant] Contrôle terminé — index sain, mais **une reconstruction tourne en ce moment même**.

## 1. État de l'index

`/home/turbo/labo/bibliotheque/lib/BLOCS-INDEX.tsv` (→ `/mnt/jarvis-data/labo/...`)

| | |
|---|---|
| Taille | 16 488 749 o (16,5 Mo) |
| Modifié | 2026-08-06 11:09:41 (il y a ~70 min) |
| Lignes | 70 531 (1 en-tête + **70 530 blocs**) |
| Format | en-tête exact `nom⇥source⇥danger⇥bloc` |
| Lignes ≠ 4 champs | **0** — 100 % des 70 531 lignes ont exactement 4 champs |
| Doublons (nom, source) | **0** — 70 530 couples pour 70 530 blocs |
| Danger | 🟢 52 554 (74,5 %) · 🟠 14 155 (20,1 %) · 🔴 3 821 (5,4 %) |

Intégrité structurelle : parfaite. Aucune ligne tronquée, aucun doublon, aucun besoin de dédoublonnage.

## 2. Répartition par source (156 sources distinctes)

| Blocs | Source | | Blocs | Source |
|---|---|---|---|---|
| 22 968 | commande-directe | | 2 770 | sql |
| 9 081 | skillsmp | | 1 290 | ocow-script |
| 7 469 | github-jarvisos | | 551 | cmd-directe |
| 6 397 | skillsmp-sections | | 479 | skillsmp-taxo |
| 5 336 | script | | 446 | tool-map |
| 4 313 | doc | | 375 | skill-logique |
| 4 031 | report | | 351 | service |

Les 3 premières sources pèsent 56 % de l'index.

## 3. Perte de blocs — VERDICT : aucune

- 130 fichiers `lib/*-blocs.tsv` = 75 037 lignes cumulées, mais seulement **70 327 couples (nom, source) uniques** : l'écart brut de 4 507 est du recouvrement entre fichiers sources, pas une perte.
- Clés présentes dans les sources et **absentes de l'index : 