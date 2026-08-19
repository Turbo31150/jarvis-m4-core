[user] Tu es expert-comptable paie, tu travailles pour l'employeur (SARL Ambulance du Soleil) dans un contentieux prud'homal.

SOURCES (PDF avec couche texte, utilise `pdftotext -layout` puis analyse) :
- /home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/Bulletins 2024.pdf
- /home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/Bulletins 2025.pdf
- /home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/Bulletins 2026.pdf
- /home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/Bulletins.pdf
Salarié : DRIOUECH Sofiane, ambulancier de nuit.

MISSION : construis un tableau EXHAUSTIF mois par mois (une ligne par bulletin) avec, quand la donnée existe :
- mois/année, période de paie
- salaire de base (montant + nombre d'heures + taux horaire)
- TOUTES les lignes de majoration/prime/indemnité : libellé exact, base, taux, montant (notamment la ligne "Majoration (nuit, dimanche, férié) mensualisé", les heures supplémentaires s'il y en a, primes de panier/repas, indemnité de précarité, etc.)
- heures supplémentaires payées le cas échéant (nombre + taux + montant)
- congés payés : acquis, pris, solde, indemnité CP
- brut total, net à payer, net imposable
- cumuls annuels

PUIS produis ces synthèses :
1. Le TAUX HORAIRE contractuel réel mois par mois et son évolution (vérifie s'il suit le SMIC / la grille conventionnelle transport sanitaire).
2. Le TOTAL des majorations nuit/dimanche/férié effectivement versées sur toute la période d'emploi (cumul en €), et le total des paniers/repas versés.
3. Le nombre d'heures rémunérées au

[assistant] Extraction works. Let me examine one full bulletin's structure to build a precise parser.

[assistant] Key finding: 2024 PDF has only 3 bulletins. Let me build the full parser and check whether missing months exist elsewhere.

[assistant] Now let me compute all totals, cross-check cumuls, and search the other PDFs for the missing months.

[assistant] Rapport écrit : `/home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/05-CONFIDENTIEL-CONSEIL/AUDIT-02-BULLETINS-PAIE.md`

**PÉRIMÈTRE** — 16 bulletins distincts. `Bulletins.pdf` = doublon exact de `Bulletins 2026.pdf` (couche texte identique). Série : 05-07/2024, 01-07/2025, 01-06/2026.

**CONTRÔLES — TOUS PASSÉS, ÉCART 0,00 €**
- Somme éléments de paie = brut imprimé : 16/16
- Net social + casse-croûte = net payé : 16/16
- Cumuls annuels heures et brut recalculés = imprimés : 16/16, 3 exercices
→ Aucune erreur de calcul, aucune régularisation cachée. Point de crédibilité fort.

**CHIFFRES CLÉS** — Heures rémunérées 2 335,72 h · **heures sup. 0,00 h sur 26 mois** · brut 45 262,09 € · net payé 37 730,17 € · **majorations nuit/dim/férié 2 883,53 €** (6,37 %) · **casse-croûte 2 210,00 €** (221 × 10,00 €) · **« Prime » 13 841,00 € = 30,58 % du brut** · précarité CDD1 739,55 € (10 % exact).

**TAUX HORAIRE** — 11,65 → 11,88 → 12,02 → 12,31 €. Alignement **SMIC strict au centime** (11,65 = SMIC 01/01/2024 ; 11,88 = SMIC 01/11/2024). Zéro marge conventionnelle. Valeurs 2026 à recouper.

**RISQUES MAJEURS CONTRE NOUS**
1. **151,67 h invariable sur 15 bulletins, zéro heure sup**, pour un ambulancier de nuit + « Prime » variable de 183 à 1 145 € sans nature, base ni taux (R.3243-1 4°) → thèse d'heures sup déguisées. Aggravant : la prime s'effondre exactement les mois d'absence.
2. **Aucun décompte des heures de nuit/dimanche/férié** (R.3243-1 3°) : le forfait porte sur 151,67 h à ~10 % du tau