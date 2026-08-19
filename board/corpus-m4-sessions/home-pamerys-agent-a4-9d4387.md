[user] Lecture seule. Objectif : extraire la SPEC du "moteur de templates local sans IA" de l'ancienne app prof Windows, pour le réintégrer dans Pousseline afin qu'elle génère TOUJOURS un résultat même quand la cascade IA est down (fin des HTTP 503).

Lis ces fichiers (disque Windows monté RO) :
- /mnt/windows/Users/clair/generateur_commentaires_scolaires.py
- /mnt/windows/Users/clair/generateur_commentaires_v3.py
(si absent, liste /mnt/windows/Users/clair/ et prends les scripts generateur_*.py)

Extrais et rends en markdown compact :
1. Structure des templates (banque de phrases par matière × niveau × niveau-d'élève ?), comment ils sont stockés (dict Python ? JSON ?).
2. Les 5 styles de formulation (noms + différence de ton).
3. La logique d'accord genre F/M (_accorder, _pronom) : comment ça marche, résumé de l'algo.
4. La fonction qui assemble une appréciation SANS IA (nom + entrées/sorties).
5. **Plan d'intégration dans Pousseline** (/home/pamerys/jarvis/webapp/) : où brancher un fallback dans ai_local.generate() ou prof_routes pour que, si ai_local.AIUnavailable est levée, on retombe sur un moteur templates local au lieu de renvoyer 503. Propose un squelette de fichier `templates_repli.py` (fonctions, pas tout le code).
Factuel, bref, tableaux. Ne recopie pas tout le code.

[assistant] I have the full picture of both generators. Now let me inspect the Pousseline integration points.

[assistant] Let me read the key parts of `ai_local.py` (the generate function and cascade) and check how prof_routes uses it.

[assistant] Let me quickly identify which endpoints those 503 sites correspond to, to map the fallback.

[assistant] Let me look at the bulletin endpoint (the most direct match for the template engine) to know its inputs.

[assistant] J'ai tout ce qu'il faut. Voici la SPEC extraite et le plan d'intégration.

---

# SPEC — Moteur de templates local (sans IA)

Sources lues (disque Windows RO) :
- `/mnt/windows/Users/clair/generateur_commentaires_scolaires.py` (v2.0, 532 l.)
- `/mnt/windows/Users/clair/generateur_commentaires_v3.py` (v3.0, 738 l.) — le plus complet, avec styles + appréciation structurée.

## 1. Structure des templates

Stockage : **100% dict Python en dur** (méthode `_charger_modeles()` qui `return {...}`). Aucun JSON externe ; le JSON n'est utilisé que pour **exporter** un bulletin fini et sauver/charger la liste d'élèves (`json.dump`/`json.load`).

Arborescence de la banque de phrases (3 niveaux d'imbrication) :

```
modeles[matiere][niveau_scolaire][niveau_eleve] = [ "phrase {prenom} {Il}…", ... ]
```

| Axe | Valeurs | Source |
|-----|---------|--------|
| `matiere` | francais, mathematiques, anglais, histoire_geo(graphie), sciences, eps, arts(_plastiques), musique, technologie, decouverte_monde, motricite, langage, philosophie | clés dict |
| `niveau_scolaire` | maternelle, primaire, college, lycee | `NIVEAUX_SCOLAIRES` |
| `niveau_eleve` (niveau de l'élève) | excellent, tres_bon, bon, assez_bon, moyen, insuffisant, difficile | `NIVEAUX_ELEVE` |
| feuille | **liste de phrases-modèles** avec placeholders `{prenom}`, `{Il}`, `{il}`, `{son}`, `{ses}`, `{lui}`, `{sa}`, `{accord}` | — |

Sélection = `random.choice()` dans la liste feuille. Tables annexes : `MATIERES_PAR_NIVEAU` (quelles matiè