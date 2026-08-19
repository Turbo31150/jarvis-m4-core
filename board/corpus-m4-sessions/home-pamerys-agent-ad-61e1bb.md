[user] Objectif : produire une structure de données exploitable du PROGRAMME MATERNELLE 2026 (France, B.O. n°19 du 7 mai 2026, applicable rentrée 2026-2027, 5 domaines d'apprentissage officiels), pour l'intégrer à l'app Pousseline (niveaux PS/MS/GS).

Étapes :
1. Cherche d'abord en LOCAL (0 token) : `grep -ri "domaine\|maternelle\|B.O\|BO n" /home/pamerys/jarvis/webapp/*.py` et lis toute structure PROGRAMME déjà présente dans banque_annuelle.py (niveaux PS/MS/GS) + les fichiers mémoire /home/pamerys/.claude/projects/-home-pamerys/memory/programme-maternelle-2026.md et poste-saint-orens-ms-gs.md s'ils existent.
2. Complète avec tes connaissances des 5 domaines officiels du programme maternelle français (1. Mobiliser le langage dans toutes ses dimensions ; 2. Agir, s'exprimer, comprendre à travers l'activité physique ; 3. Agir, s'exprimer, comprendre à travers les activités artistiques ; 4. Construire les premiers outils pour structurer sa pensée ; 5. Explorer le monde) et leurs sous-domaines.
3. Rends un objet Python `PROGRAMME_MATERNELLE_2026` (dict) : pour PS, MS, GS → chaque domaine → liste de 4-6 notions/attendus concrets par période, formulés comme des intitulés de fiches d'exercices (courts, actionnables). Aligne-toi sur le style des notions déjà dans banque_annuelle.py.
4. Note les écarts entre la structure actuelle de banque_annuelle.py (matières maternelle utilisées) et les 5 domaines officiels 2026, et propose le remapping.

Rends : le dict Python complet (prêt à coller) + 

[assistant] Je lis le dict PROGRAMME complet et le bloc de mapping 2026 pour m'aligner sur le style.

[assistant] J'ai tout le contexte nécessaire. Note importante détectée : le programme 2026 utilisé par Pousseline (memory + `DOMAINES_2026` dans le code) porte les **intitulés officiels remaniés du BO n°19**, différents des 5 domaines "classiques" 2015 cités dans ta consigne. Je m'aligne sur les intitulés réels 2026 du code (et je signale l'écart).

Voici le livrable.

---

## Dict Python `PROGRAMME_MATERNELLE_2026` (prêt à coller)

Structure : `niveau → domaine officiel 2026 → période (P1..P5) → 4-6 notions` (intitulés de fiches, style aligné sur `PROGRAMME` existant). Les clés de domaine sont **identiques aux chaînes de `DOMAINES_2026`** déjà dans `banque_annuelle.py` → mapping 1:1, zéro friction.

```python
# ── PROGRAMME MATERNELLE 2026 — détail par période ───────────────────────────
# BO n°19 du 7 mai 2026 (arrêté MENE2608627A), rentrée 2026-2027.
# niveau → domaine officiel 2026 → période P1..P5 → notions (titres de fiches).
# Clés de domaine = DOMAINES_2026 (mapping direct). Explorer le monde porte 2 volets
# balisés en préfixe : [T/E] = se repérer dans le temps et l'espace ; [V/M/O] = vivant, matière, objets.
D = DOMAINES_2026  # [0]=langage, [1]=maths, [2]=physique, [3]=artistique, [4]=explorer le monde

PROGRAMME_MATERNELLE_2026 = {
    "PS": {
        D[0]: {  # Développement et structuration du langage oral et écrit
            "P1": ["Se présenter, nommer", "Comptines et jeux de doigts", "Écouter une histoire courte", "Reconnaître son prénom (photo)", "Vocabulaire de la cla