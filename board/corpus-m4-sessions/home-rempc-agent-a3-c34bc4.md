[user] Mission d'analyse chiffrée pour un contentieux prud'homal, côté employeur. On cherche à déterminer sur quoi est calculée une prime mensuelle versée à un ambulancier de nuit.

CONTEXTE : M. DRIOUECH, ambulancier de nuit, perçoit chaque mois une ligne « Prime » au bulletin, d'un montant très variable. On veut savoir si cette prime suit **le chiffre d'affaires généré** ou **le nombre de nuits / d'heures travaillées**. L'enjeu est majeur : dans le premier cas c'est une libéralité indexée sur le CA (favorable), dans le second c'est une rémunération d'heures déguisée (très défavorable).

DONNÉES CONNUES — montants de la ligne « Prime » sur les bulletins 2026, dans l'ordre des bulletins du PDF (à rapprocher des mois, l'ordre est probablement chronologique janvier → juillet, avec juin manquant) :
816,00 · **183,00** · 880,00 · 850,00 · 930,00 · 765,00 €
Le mois à 183 € est l'anomalie la plus intéressante à expliquer.

SOURCES — les 6 feuilles de route mensuelles de 2026 dans /home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/feuille de route/2026/ :
FDR janv 2026.pdf · FDR fev 2026.pdf · FDR mars 2026.pdf · Fdr Avril 2026.pdf · Fdr Mai 2026.pdf · Fdr juillet 2026.pdf

MÉTHODE (scans image pur, vision indispensable) :
1. `pdftoppm -r 150 -png "<fichier>" /tmp/prime2026/<mois>` (crée le dossier). Les pages peuvent être orientées à 90° — redresse-les si besoin.
2. Lis CHAQUE page avec l'outil Read.
3. Sur chaque feuille (= une nuit), relève UNIQUEMENT :
   - la **date** de la feuille ;
   - s

[assistant] Prior methodology exists (2024/2025 CSVs). Let me convert the 2026 PDFs to images.

[assistant] Let me check the existing bulletins audit for the prime/month mapping, and start reading pages.

[assistant] Critical finding already: the bulletins audit gives the real month↔prime mapping. Let me verify with one page read first.

[assistant] Pages are rotated 90°. Amounts confirmed in euros with decimals (93,05 / 102,36). Let me fix orientation.

[assistant] Pages readable after rotation. Let me generate higher-res versions plus dedicated crops of the amounts column, then write the report skeleton.

[assistant] Important course correction received. Let me check the 2025 sources and verify the prime↔month mapping against the authoritative bulletins audit.

[assistant] Confirmed — March 2026 "Numéro SAMU" column is empty. Let me write the report skeleton now.

[assistant] 2025 renders in progress. Let me launch the 2026 extraction agents in parallel now.

[assistant] All 2025 pages rendered and rotated. Let me calibrate on one 2025 page before delegating.

[user] [Image: original 2408x1655, displayed at 2000x1375. Multiply coordinates by 1.20 to map to original image.]

[assistant] 2025 pages are far more legible, and the red marginal total acts as a checksum. Let me launch the 2025 extraction agents.

[assistant] 10 extraction agents running. Meanwhile, let me compute the reference denominators from the existing 2025 dataset.

[assistant] Denominators computed and they match the independent count exactly (89 nights, 410 missions). Let me record this in the report while agents run.

[assistant] Strong data arriving. Let me record it incrementally while the remaining agents finish.

[assistant] All 10 dépouillements complete. Let me consolidate and compute the ratios rigorously.

[assistant] Rapport écrit dans `/home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/05-CONFIDENTIEL-CONSEIL/AUDIT-07-CORRELATION-PRIME.md`.

**CONCLUSION — la prime ne suit NI les nuits NI les heures ; le seul inducteur corrélé est le CA, mais sans formule et sans significativité statistique.**

1. **Deux rectifications majeures des données transmises.** Les listes de primes étaient en ordre **inverse** (source authentique : AUDIT-02 § 1.2). Le mois à **183 € est MAI 2026**, pas février (17 j de CP, 5 feuilles seulement). En 2026 : 01=765, 02=930, 03=850, 04=880, 05=183, 06=816 ; le bulletin **07/2026 n'existe pas**, et il n'y a **pas de FDR juin 2026**.
2. **2026 est inexploitable seul** : la colonne « Numéro SAMU » n'est renseignée que jusqu'au **08/02/2026**. Zéro montant sur les 45 feuilles de mars, avril, mai et juillet — confirmé page par page et par détection d'encre rouge.
3. **Périmètre déplacé sur les 7 mois de 2025** (102 feuilles, 460 missions) où les montants sont portés partout.
4. **Nature de la colonne établie, pas supposée** : sur janvier 2025, 13 nuits sur 15 bouclent **au centime** entre la somme des lignes et le total rouge en marge. Ce sont bien des **euros avec décimales** (116,80 · 539,47 · 147,39 · 249,71 = 1 053,37), portés après coup par un tiers.
5. **Ratio le plus stable = Prime / Recette** : CV **8,74 %** contre 11,28 % (prime/heure), 12,30 % (prime/nuit), 13,34 % (prime/mission). Classement robuste sur tous les sous-échantillons testés.
6. **Corrélations — le résul