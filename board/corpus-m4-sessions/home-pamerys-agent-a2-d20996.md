[user] Explore le module de banque d'exercices de l'app enseignante Pousseline dans /home/pamerys/jarvis/webapp/banque_annuelle.py.

Objectif : comprendre précisément comment ENRICHIR la maternelle (PS/MS/GS) "à fond".

Rapporte de façon concise :
1. La structure du dictionnaire PROGRAMME (ou équivalent) : comment sont définis les niveaux, matières/domaines, notions, et le nombre de fiches cible par niveau (PS/MS/GS notamment).
2. Les matières/domaines actuellement couverts pour PS, MS, GS, et lesquels correspondent (ou pas) aux 6 domaines du programme maternelle 2026 (1.Langage oral+écrit, 2.Premiers outils mathématiques, 3.Activités physiques, 4.Activités artistiques, 5.Se repérer temps/espace, 6.Monde vivant/matière/objets).
3. Comment on ajoute des notions / augmente la cible d'un niveau (la procédure d'extension du curriculum), et où (numéro de ligne, nom de la variable).
4. Comment une fiche est générée (route API /api/banque/batch, /api/banque/pdf, fonction de génération, appel à ai_local) — le flux exact.
5. La table SQL 'banque' dans ecole.db : colonnes exactes.

Ne modifie rien. Donne les chemins fichier:ligne. Sois bref et factuel.

[assistant] Je vais explorer le module banque-annuelle pour comprendre sa structure et fonctionnement.

[assistant] Parfait, j'ai toute l'information. Laisse-moi faire une analyse rapide avec un local pour bien structurer ma réponse :

[assistant] Parfait. Synthèse des routes API et du flux générationnel :

## RAPPORT FINAL

### 1. **Structure du dictionnaire PROGRAMME (lignes 27-341)**

**Fichier** : `/home/pamerys/jarvis/webapp/banque_annuelle.py:27-341`

**Format** : `{niveau: {domaine/matière: [notions]}}`

**Maternelle PS/MS/GS** (3 × 5 domaines × 5 notions = 75 fiches cible chacun) :
- **PS (ligne 29-65)** : 5 domaines, 25 notions → 5 fiches cible par domaine
  - Langage oral, Langage écrit, Nombres, Formes et grandeurs, Explorer le monde
- **MS (ligne 66-102)** : idem structure
- **GS (ligne 103-139)** : idem structure

Chaque notion est un index dans une liste. La période (P1-P5) est calculée par `_periode(idx, total)` (ligne 382-387) : `período = ceil(idx / (total/5)) + 1`, auto-répartition sur 5 périodes.

**Élément** : `NIVEAUX = list(PROGRAMME.keys())` → `['PS', 'MS', 'GS', 'CP', 'CE1', 'CE2', 'CM1', 'CM2']` (ligne 343)

### 2. **Couverture réelle vs. B.O. 2026 maternelle**

| **Domaine B.O. 2026** | **Couverture actuellement** | **Statut** |
|---|---|---|
| **1. Langage oral & écrit** | Langage oral, Langage écrit (2 fiches séparées) | ⚠️ Dépliée, pas fusions |
| **2. Premiers outils mathématiques** | Nombres (5) + Formes et grandeurs (5) | ✅ Couverts mais 2 matières |
| **3. Activités physiques** | ❌ MANQUANT | ❌ À ajouter |
| **4. Activités artistiques** | ❌ MANQUANT (partiellement dans Explorer le monde) | ⚠️ Incomplet |
| **5. Se repérer temps/espace** | Partiel dans "Explorer le monde" | ⚠️ Mélangé |
