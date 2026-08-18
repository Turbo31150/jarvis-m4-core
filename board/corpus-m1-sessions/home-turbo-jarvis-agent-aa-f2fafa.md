[assistant] Le classement automatique masque deux cas : je creuse les blocs `gh api` (réseau) et la source dominante `commande-directe`.

[assistant] J'ai toutes les mesures. Voici le rapport.

---

# AUDIT — Bibliothèque vivante JARVIS (lecture seule, 2026-08-04)

**VERDICT (3 lignes)**
Le corpus n'hallucine quasiment pas au sens strict — **3,2 % de cibles mortes, 7,1 % d'inapplicables** (mesuré mécaniquement sur les 46 972 blocs par `biblio-doctor.py`, confirmé par mon échantillon de 60 : 0 chemin mort, 0 outil absent). Mais **seuls ~13 % des blocs sont un geste opérationnel réel** : 26,4 % sont des templates à trous non exécutables, 14,8 % de simples commentaires `# /chemin`, 17,5 % des `xdg-open` d'un document, 16,4 % des `gh api` qui affichent un fichier distant. **Rappel en tête de liste : 5/8 (62,5 %)** — `bloc.sh` trouve toujours quelque chose, mais le 1er résultat est hors-sujet une fois sur trois.
Autrement dit : ce n'est pas un corpus halluciné, c'est un **catalogue de fichiers déguisé en bibliothèque de gestes**.

## 1. Volumétrie réelle

| Mesure | Valeur |
|---|---|
| Lignes `BLOCS-INDEX.tsv` | 47 046 (46 549 il y a 20 min → **+~25 blocs/min**, le filler tourne) |
| Lignes malformées (≠ 4 colonnes) | **0** |
| Doublons exacts (nom, source) | **0** |
| Doublons ligne entière | **0** |
| Blocs < 5 caractères | 138 (149 selon doctor, seuil 8) |
| Sources distinctes | **150** (et non 14 comme le documente le CLAUDE.md) |
| Danger | 🟢 38 497 (82,7 %) · 🟠 4 339 (9,3 %) · 🔴 3 712 (8,0 %) |

Top sources : `commande-directe` 12 859 (27,6 %) · `github-jarvisos` 7 467 (16 %) · `script` 6 862 · `doc` 3 995 · `report` 3 9

[assistant] Rapport transmis à `main`.

Points saillants du rendu :
- **Hallucination stricte : 0 % sur l'échantillon de 60** (0 outil absent, 0 chemin absent, 5 blocs `gh api` confirmés existants sur le réseau) ; **3,17 % de cibles mortes / 7,07 % d'inapplicables** sur les 46 972 blocs du corpus entier.
- **26,7 % de l'échantillon n'est pas exécutable en l'état** ; sur le corpus, seuls **12,8 % sont une commande opérationnelle réelle**.
- **Rappel en tête de liste : 5/8 = 62,5 %** (échecs : « publier linkedin », « redémarrer n8n », « cluster ssh »).
- **Séries : 197/197** exécutables, avec shebang, `bash -n` sans erreur — le seul étage fiable.
- **Aucun contrôle qualité avant insertion** dans `cli/biblio_filler.py:365`, et **aucun champ date/TTL** dans le schéma : la péremption d'un bloc n'est mesurable par aucun moyen actuel.

Rien n'a été modifié.