[user] Applique des correctifs de COHÉRENCE dans le dossier /home/rempc/Bureau/franck/ecosysteme/. Édite les fichiers markdown (Read puis Edit). NE TOUCHE PAS au dossier /home/rempc/Bureau/franck/reference-impl/ (un autre process l'écrit). N'invente rien : applique exactement les correctifs listés.

**FIX 1 — Renumérotation des invariants Σ (le plus important).** Il y a collision : `05-DURCISSEMENT-REDTEAM.md` a publié en premier **Σ.7 = Provenance & quarantaine** (A0+) et **Σ.8 = Policy déterministe/dégradé monotone** (A5+) → ces deux-là sont CANONIQUES, ne les change pas. Dans `06-CONTRATS-RUNTIME-V2.md`, décale TOUS les invariants runtime de +2 selon cette table, et fusionne le doublon provenance :
| Concept | Ancien (06) | Nouveau |
|---|---|---|
| pureté canaux (C1) / secrets 0600 | Σ.7 | Σ.9 |
| codes fermés (C2) / identity least-agency | Σ.8 | Σ.10 |
| monotonie timeout + anti-storm (C4) | (perdu, cf FIX 2) | Σ.11 |
| single-writer mem | Σ.9 | Σ.12 |
| embed-souverain (FTS) | Σ.10 | Σ.13 |
| non-escalade publish (C5/A4) | Σ.11 (doublon provenance) | Σ.14 |
| malformé=non-fiable / migrations idempotentes | Σ.12 | Σ.15 |
| fail-closed critique / CA-id | Σ.13 | Σ.16 |
| no-new-OWN | Σ.14 | Σ.17 |
Répercute les renvois inline dans `06` : §9.3 « Σ7–Σ13 » → « Σ.9–Σ.16 » ; §9.4 « Σ.9 single-writer » → « Σ.12 », « (Σ.10) » FTS → « Σ.13 ». L'ancien « Σ.11 » de 06 (provenance+non-escalade publish) : retire la partie provenance (déjà couverte par Σ.7 de 05, ajoute un renvoi « cf. Σ.7 (0

[assistant] I'll start by exploring the target directory structure and reading the files I need to edit.

[assistant] I need the exact bytes to edit, so I'll Read all the files I need to modify (plus 05 for canonical reference and 03/04 for FORGE numbering reference).