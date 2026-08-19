[user] CONTEXTE URGENT — CESSION SOLEIL (acquéreur Karim HOUFAIR, prix global 1,1M€ = 820k SARL Ambulances du Soleil + 280k SCI du Soleil, encaissé par Holding La Lironde).

FAIT NOUVEAU CONFIRMÉ PAR RÉMI (2026-07-22) : le refus de financement du Crédit Agricole du Languedoc porte sur LA CIBLE, pas sur la structure de Karim. La banque juge **Ambulances du Soleil (SARL) non solvable** — motif explicite de Rémi : « les bilans pas bons ». C'est donc un risque STRUCTUREL : toute banque refusera pour la même raison, tout acquéreur ayant besoin d'un prêt butera pareil.

TA MISSION (2 volets, factuel d'abord, JAMAIS inventer de chiffres — règle no_invention) :

VOLET 1 — FAITS RÉELS (source obligatoire) :
- Sors les VRAIS chiffres des bilans SARL Ambulances du Soleil sur les 3 derniers exercices : CA, EBE/EBITDA, résultat net, dettes financières, CAF/capacité de remboursement, trésorerie, capitaux propres.
- Cherche dans : /media/rempc/DATA/ (dossiers soleil/ambulances/bilan), la mémoire Postgres (docker exec -i jarvis-postgres psql -U jarvis -d jarvis_main), les atomes memory_atoms scope cession_soleil/soleil, et les fichiers ~/Documents/SOLEIL/.
- Chiffre l'impact des litiges prud'hommes (Emma COSTE + Soufiane DRIOUECH, ~102k passif potentiel) sur la solvabilité perçue.
- Pour CHAQUE chiffre : cite la SOURCE (fichier + date). Si un chiffre est introuvable, dis « introuvable » — n'invente pas.

VOLET 2 — DIAGNOSTIC + LEVIERS M&A CONCRETS :
- Pourquoi précisément une banque juge Soleil non

[assistant] I'll start by loading context-mode tools and gathering the real data in parallel.

[assistant] ToolSearch isn't enabled here, so I'll work with Bash and Read directly. Let me discover the actual schema and gather data in parallel.

[assistant] Deadline note: Postgres `projets` has no date; the 08/07/2026 has already passed (today 2026-07-22). I'll flag that. Now let me pull the memory atoms and locate the actual bilan/financial files.

[assistant] I have the 3 key exercises (bilans 2023/2024/2025). Let me pull the full financial content from memory atoms and read the actual bilan PDFs.

[assistant] Rich context confirmed. Now I need the actual SARL P&L/balance-sheet figures (CA, EBE, résultat, dettes, capitaux propres, tréso). Those live in the bilan PDFs. Let me extract them and search for Soufiane DRIOUECH.

[assistant] The clarification atom is the crux. Let me read it fully plus the CA Languedoc banker atom, and extract the real SARL figures from the bilan PDFs and liasse fiscale.

[assistant] Now I have the smoking gun. Let me extract EBE, dotations, charges de personnel and CAF to complete the picture, plus consult the M&A board.

[assistant] Complete financial picture obtained. The EBE is negative and worsening — the structural killer. Let me consult the M&A board and check for gérant remuneration to add back.

[assistant] Board is stale (no LBO-financing corpus) — I'll rely on the hard numbers, which are conclusive. Let me confirm the Soufiane claim amount and reconcile the deadline before writing up.

[assistant] I have everything needed. The board corpus is stale/thin on LBO levers, so the analysis below rests on the verified bilan figures and Postgres memory.

---

# CESSION SOLEIL — Diagnostic financement + leviers M&A

[SOLAL] Deadline 08/07/2026 **DÉPASSÉE (J+14)** — relativisée dans la mémoire (financement bancaire long, closing non fait). Postgres `projets` n'a pas de date verrouillée : je ne réécris rien.
Status : financement Karim bloqué (CA Languedoc juge la CIBLE non solvable). Deal PAS mort (clause 4.1 : caducité = refus documenté de ≥2 banques).

## VOLET 1 — Chiffres réels SARL Ambulances du Soleil

Source unique de ces chiffres : liasses/bilans certifiés `BILAN_SOLEIL_2023/2024/2025.pdf` + `2050_Réel Normal BIC 2026.pdf`, dossier `/media/rempc/DATA/cession-soleil-karim/Soleil/2. Comptes & fiscal/`.

| Poste (€) | 2023 | 2024 | 2025 | Tendance |
|---|---|---|---|---|
| **CA / production vendue** | 964 186 | 919 517 | 856 632 | **-11 % / 2 ans** |
| Valeur ajoutée | 644 809 | 618 927 | 558 564 | en chute |
| **EBE (EBITDA)** | **-36 794** | **-56 347** | **-60 552** | **négatif, s'aggrave** |
| Résultat d'exploitation | -32 211 | -31 190 | -50 871 | négatif |
| **Résultat net** | **-37 282** | **-30 665** | **-50 994** | **3 pertes de suite** |
| **Capitaux propres** | 142 997 | 112 332 | **61 337** | érodés (-57 % / 2 ans, encore >0) |
| **Trésorerie (disponibilités)** | 1 832 | 2 077 | **202** | **quasi nulle** |
| Emprunts éts de crédit | 1 856 | 8 734 | 14 461 | faibl