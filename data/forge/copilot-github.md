# GitHub Copilot Masterclass

> Référence `copilot-github` · 39 €

## Plan

## Module 1 – Installation et configuration de GitHub Copilot  
**Objectif mesurable** : Configurer Copilot dans VS Code, JetBrains et GitHub Codespaces et vérifier son activation via la génération d’une fonction JavaScript valide à chaque démarrage.  
**Notions couvertes**  
1. Prérequis d’abonnement et gestion des licences.  
2. Installation de l’extension Copilot (VS Code, IntelliJ IDEA, PyCharm).  
3. Configuration des paramètres (suggestion inline, déclencheur manuel, filtres de langue).  
4. Utilisation des secrets GitHub pour l’authentification en mode entreprise.  
5. Validation de la connexion via la commande `Copilot: Show Auth Status`.

## Module 2 – Prompt engineering et contrôle de la génération  
**Objectif mesurable** : Formuler trois types de prompts (description fonctionnelle, commentaire de fonction, test‑driven) et obtenir des suggestions dont le taux de conformité syntaxique ≥ 95 % sur un projet Python de 200 lignes.  
**Notions couvertes**  
1. Structure d’un prompt efficace (verbe d’action, contraintes, exemples).  
2. Utilisation des commentaires de type “///” et “#region” pour guider la génération.  
3. Paramétrage du “temperature” et du “top‑p” via les réglages avancés.  
4. Gestion des suggestions multi‑ligne et insertion sélective.  
5. Détection et résolution des hallucinations de code (exemple : appels à des API inexistantes).

## Module 3 – Intégration dans le flux de travail de développement  
**Objectif mesurable** : Intégrer Copilot dans un pipeline CI/CD (GitHub Actions) et démontrer que 80 % des suggestions acceptées passent les tests unitaires automatisés sans modification manuelle.  
**Notions couvertes**  
1. Utilisation de Copilot Labs pour la génération de tests unitaires.  
2. Configuration du workflow GitHub Actions avec `actions/setup-node` / `actions/setup-python`.  
3. Validation des suggestions via `npm test` ou `pytest`.  
4. Gestion des conflits de merge lorsque Copilot modifie des fichiers déjà versionnés.  
5. Stratégies de revue de code (code owners, approbation obligatoire) pour les contributions Copilot.

## Module 4 – Sécurité, conformité et limites techniques  
**Objectif mesurable** : Identifier et corriger au moins trois vulnérabilités (ex. injection SQL, XSS, usage de fonctions dépréciées) introduites par Copilot dans un projet Node.js, en suivant les recommandations du OWASP Top 10.  
**Notions couvertes**  
1. Analyse des licences des snippets générés (MIT, Apache 2.0, GPL).  
2. Détection de code sensible (clés API, mots de passe) via les alertes GitHub Secret Scanning.  
3. Utilisation de linters (ESLint, Bandit) pour filtrer les suggestions non conformes.  
4. Mise en place de règles de refus de

---

## Module 1 — contenu

## Module 1 – Installation et configuration de GitHub Copilot  

### 1. Prérequis d’abonnement et gestion des licences  

| Élément | Valeur attendue | Vérification |
|--------|------------------|-------------|
| Compte GitHub | GitHub .com ou GitHub Enterprise Cloud | Connexion à <https://github.com> |
| Licence Copilot | **Copilot for Individuals** (abonnement mensuel/annuel) ou **Copilot for Business** (licence organisation) | Dans *Settings → Billing → GitHub Copilot* du compte ou de l’organisation |
| Niveau d’accès | `read:packages`, `write:packages`, `repo` (full) pour les actions GitHub | `gh auth status` doit afficher `GitHub Copilot` parmi les scopes |

> **Note** : la licence Business nécessite l’acceptation du **GitHub Acceptable Use Policy** et la mise en place d’une **policy de conformité** (ex. : restrictions de génération de code sous licence GPL).

### 2. Installation de l’extension Copilot  

#### 2.1 VS Code (Windows/macOS/Linux)  

```bash
# Via le Marketplace intégré
code --install-extension GitHub.copilot
# Ou depuis le terminal
npm install -g @githubnext/github-copilot-cli   # pour usage CLI (optionnel)
```

*Vérifier* : `Extensions` → *GitHub Copilot* → statut **Enabled**.  

#### 2.2 JetBrains (IntelliJ IDEA, PyCharm, WebStorm)  

1. Ouvrir **Settings → Plugins**.  
2. Rechercher **GitHub Copilot** et cliquer **Install**.  
3. Redémarrer l’IDE.  

*Vérifier* : `Help → About` doit afficher la version du plugin (ex. : 1.2.3).  

#### 2.3 GitHub Codespaces  

Dans le fichier de configuration du codespace (`devcontainer.json`) ajouter :

```json
{
  "features": {
    "ghcr.io/devcontainers/features/github-copilot:1": {}
  }
}
```

Après le premier démarrage, le serveur de Copilot s’installe automatiquement.  

### 3. Configuration des paramètres  

| Paramètre | VS Code (settings.json) | JetBrains (settings) | Valeur recommandée |
|-----------|------------------------|----------------------|---------------------|
| `github.copilot.enable` | `"github.copilot.enable": true` | `Enable Copilot` | `true` |
| `github.copilot.inlineSuggest.enable` | `"github.copilot.inlineSuggest.enable": true` | `Inline suggestions` | `true` |
| `github.copilot.suggestOnTriggerCharacters` | `"github.copilot.suggestOnTriggerCharacters": true` | `Trigger on . , ( , etc.` | `true` |
| `github.copilot.suggestionDelay` | `"github.copilot.suggestionDelay": 100` | `Delay (ms)` | `100` |
| `github.copilot.languageFilters` | `"github.copilot.languageFilters": ["javascript","python","go"]` | `Languages` | Liste des langages du projet |

#### 3.1 Déclencheur manuel  

- VS Code : `Ctrl+Enter` (ou `Cmd+Enter` macOS) insère la suggestion actuelle.  
- JetBrains : `Alt+Enter` ouvre le menu *Copilot* → *Accept Suggestion*.  

#### 3.2 Filtres de langue  

```json
{
  "github.copilot.languageFilters": [
    "javascript",
    "typescript",
    "python",
    "go"
  ]
}
```

Seules les langues listées seront analysées par le modèle.  

### 4. Authentification en mode entreprise (GitHub Secrets)  

1. Créer un **PAT** (Personal Access Token) avec le scope `read:org` et `read:user`.  
2. Dans le dépôt ou l’organisation : `Settings → Secrets and variables → Actions → New repository secret`.  
   - Nom : `COPILOT_TOKEN`  
   - Valeur : le PAT généré.  

3. Dans VS Code ou JetBrains, ouvrir la palette de commandes (`Ctrl+Shift+P`) et exécuter :  

   ```
   Copilot: Sign In
   ```  

   Lorsque le prompt demande le token, coller `${{ secrets.COPILOT_TOKEN }}` (ou le copier‑coller manuellement).  

> **Vérification** : la commande `Copilot: Show Auth Status` doit renvoyer `Authenticated as <username>` et le champ `Token source: GitHub Actions secret`.  

### 5. Validation de la connexion  

1. Ouvrir un fichier **`test.js`** vierge.  
2. Saisir le commentaire suivant :  

   ```js
   // Crée une fonction qui renvoie la somme de deux nombres
   ```  

3. Attendre la suggestion inline (gris clair). Appuyer sur `Ctrl+Enter`.  

#### Exemple de fonction générée (commentée)  

```js
/**
 * Calcule la somme de deux nombres.
 *
 * @param {number} a - Premier opérande.
 * @param {number} b - Second opérande.
 * @returns {number} La somme a + b.
 */
function add(a, b) {
  // Validation de type (facultatif mais recommandé)
  if (typeof a !== 'number' || typeof b !== 'number') {
    throw new TypeError('Les deux arguments doivent être des nombres.');
  }
  return a + b;
}

// Exemple d’utilisation
console.log(add(3, 5)); // → 8
```

Exécuter `node test.js` → sortie `8`. Si la

---

## Module 2 — contenu

## Module 2 – Prompt engineering et contrôle de la génération  

### 2.1 Structure d’un prompt efficace  

| Élément | Rôle | Exemple concret |
|--------|------|-----------------|
| **Verbe d’action** | indique clairement ce que Copilot doit produire. | `implémente`, `génère`, `corrige` |
| **Contrainte fonctionnelle** | limite le périmètre (type de retour, complexité, dépendances). | `renvoie un `dict` contenant les clés `id` et `value` uniquement` |
| **Exemple de code** | fournit un modèle que Copilot peut reproduire. | ```python\n# Exemple : def add(a: int, b: int) -> int:\n#     return a + b\n``` |
| **Contexte** | décrit l’environnement (framework, version, style). | `Projet Django 3.2, respect du PEP 8, tests pytest` |
| **Indicateur de fin** | signale où la génération doit s’arrêter (`# END`). | `# END` |

**Prompt minimal** :  
```
# Implémente une fonction `parse_csv` qui lit un fichier CSV et renvoie une liste de dictionnaires.
# Chaque dictionnaire doit contenir les colonnes `name` (str) et `age` (int).
# Utilise le module csv de la bibliothèque standard.
# Retourne [] si le fichier est vide.
def parse_csv(path: str) -> list[dict]:
```

Copilot complète le corps en respectant les contraintes.  

### 2.2 Utilisation des commentaires de type “///” et “#region”  

- `///` (ou `#`) sert à injecter des métadonnées que Copilot lit comme partie du prompt.  
- `#region`…`#endregion` délimite un bloc de génération, utile pour éviter les insertions hors du scope.  

**Exemple** :  

```python
#region parse_csv
/// Fonction : parse_csv
/// Entrée  : chemin vers un fichier CSV (str)
/// Sortie  : list[dict] avec les clés `name` (str) et `age` (int)
def parse_csv(path: str) -> list[dict]:
    # TODO: implémentation
#endregion
```

Copilot ne remplira que le `# TODO` et respectera la délimitation.  

### 2.3 Paramétrage du “temperature” et du “top‑p”  

| Paramètre | Valeur typique | Effet |
|----------|----------------|------|
| `temperature` | 0.0 – 0.5 (prédictif) ou 0.7 – 1.0 (créatif) | 0.0 → réponses déterministes, 1.0 → plus de variété |
| `top_p` | 0.9 (défaut) ou 0.5 (plus conservateur) | Fraction cumulative de probabilité du vocabulaire retenu |

Dans VS Code : `Fichier → Préférences → Paramètres → Extensions → GitHub Copilot → Advanced`.  
- Pour du code de production, **temperature = 0.0** et **top_p = 0.9** garantissent la conformité syntaxique.  
- Pour des prototypes ou des suggestions de refactorisation, on peut augmenter à **temperature = 0.6**.  

### 2.4 Gestion des suggestions multi‑ligne et insertion sélective  

1. **Déclenchement** : `Ctrl+Alt+\\` (Windows/Linux) ou `⌥+⌘+\\` (macOS).  
2. **Navigation** : `Alt+[` / `Alt+]` pour parcourir les variantes.  
3. **Insertion partielle** :  
   - Sélectionner le texte suggéré avec la souris ou `Shift+Alt+→`.  
   - Appuyer sur `Tab` pour accepter uniquement la sélection.  

> **Astuce** : Utiliser le raccourci `Ctrl+Shift+Enter` (ou `⌘+Shift+Enter`) pour insérer la suggestion **sans** le commentaire de fin (`# END`).  

### 2.5 Détection et résolution des hallucinations de code  

**Hallucination** = code généré qui compile mais ne correspond à aucune API réelle.  

#### Étapes de détection  

1. **Recherche de symboles** : `Ctrl+Shift+F` sur le nom de la fonction/classe suspecte.  
2. **Vérification de la documentation** : `python -c "import pkg; help(pkg)"` ou consulter le site officiel.  
3. **Tests unitaires** : écrire un test minimal qui échoue si l’API n’existe pas.  

#### Exemple d’hallucination  

```python
def fetch_user_data(user_id: int) -> dict:
    # Copilot a ajouté un appel à une API inexistante `httpx.get_json`
    response = httpx.get_json(f"https://api.example.com/users/{user_id}")
    return response
```

`httpx.get_json` n’existe pas (la méthode réelle est `httpx.get(...).json()`).  

#### Correction  

```python
import httpx

def fetch_user_data(user_id: int) -> dict:
    response = httpx.get(f"https://api.example.com/users/{user_id}")
    response.raise_for_status()
    return response.json()
```

### 2.6 Pièges concrets à éviter  

| Situation | Pourquoi c’est un piège | Correctif |
|-----------|------------------------|-----------|
| **Prompt trop vague** (`"Écris une fonction qui lit un fichier"`). | Copilot peut choisir n’importe quel format (JSON, CSV, binaire). | Préciser le format, le type de retour et les contraintes d’erreur. |
| **Oublier le `# END`** dans un bloc `#region`. | Copilot continue à générer au-delà du bloc, modifiant du code existant. | Toujours placer `# END` ou `#endregion` pour délimiter la portée. |
| **Temperature > 0.7 en production**. | Augmente le taux

---

## Module 3 — contenu

## Module 3 – Intégration dans le flux de travail de développement  

### 3.1 Utilisation de Copilot Labs pour la génération de tests unitaires  

| Action | Commande / UI | Résultat attendu |
|--------|----------------|-------------------|
| Ouvrir le panneau **Copilot Labs** | `Ctrl+Shift+P` → *Copilot Labs: Open* | Fenêtre latérale “Copilot Labs” s’affiche |
| Générer des tests pour une fonction | Sélectionner le code source → bouton **Generate Tests** | Fichier `*_test.py` (ou `*.test.js`) contenant des tests basés sur le *signature* et les *doc‑strings* de la fonction |
| Appliquer les tests | Clic **Apply** | Les tests sont ajoutés au dépôt, prêts à être exécutés par `pytest` ou `npm test` |

> **Vérifiable** : Copilot Labs utilise le modèle `gpt‑4‑code‑interpreter` (décrit dans la documentation officielle de GitHub Copilot Labs, version 2024‑03).  

#### Exemple (Python)  

```python
# src/calcul.py
def moyenne(liste: list[float]) -> float:
    """
    Retourne la moyenne arithmétique des valeurs de *liste*.
    - Si la liste est vide, renvoie 0.0.
    - Les valeurs non numériques sont ignorées.
    """
    total = sum(v for v in liste if isinstance(v, (int, float)))
    count = sum(1 for v in liste if isinstance(v, (int, float)))
    return total / count if count else 0.0
```

*Après sélection du bloc et clic **Generate Tests** dans Copilot Labs* :

```python
# tests/test_calcul.py
import pytest
from src.calcul import moyenne

@pytest.mark.parametrize(
    "input,expected",
    [
        ([1, 2, 3], 2.0),                     # cas nominal
        ([], 0.0),                            # liste vide
        ([1, "a", 3.5], 2.25),                # filtre des non‑numériques
        ([0, -5, 5], 0.0),                   # somme nulle
    ],
)
def test_moyenne(input, expected):
    assert moyenne(input) == pytest.approx(expected)
```

Le test passe avec `pytest -q` : `4 passed in 0.03s`.  

### 3.2 Configuration du workflow GitHub Actions  

#### 3.2.1 Structure minimale du workflow  

```yaml
name: CI – Copilot‑validated

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [ "3.10", "3.11" ]
        node-version: [ "18.x" ]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install Python deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}

      - name: Install Node deps
        run: npm ci

      - name: Run tests (Python)
        if: matrix.python-version != ''
        run: pytest -q

      - name: Run tests (Node)
        if: matrix.node-version != ''
        run: npm test --silent
```

- `actions/checkout@v4` garantit que le code généré par Copilot (et les éventuelles modifications de PR) est présent.  
- La matrice assure la compatibilité multi‑version.  
- Les étapes `Run tests` échouent le workflow si **une** assertion échoue, ce qui bloque la fusion automatique.  

#### 3.2.2 Validation de suggestions Copilot dans la CI  

1. **Commit de suggestions** : Copilot insère du code via l’IDE, l’auteur crée un commit.  
2. **Pull request** : Le PR déclenche le workflow ci‑dessus.  
3. **Statut “passed”** : Si ≥ 80 % des suggestions acceptées sont couvertes par les tests générés (ou existants) et que tous les tests passent, le statut est vert.  
4. **Badge** : Ajoutez `![CI](https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg)` au README pour visibilité.  

### 3.3 Gestion des conflits de merge lorsque Copilot modifie des fichiers déjà versionnés  

| Situation | Cause | Solution |
|----------|-------|----------|
| **Conflit sur le même bloc** | Copilot a inséré une fonction alors qu’un développeur a modifié la même fonction dans une branche parallèle. | Utiliser `git merge --no-ff` puis résoudre manuellement le bloc, en conservant les commentaires `// Copilot suggestion` pour audit. |
| **Conflit sur le fichier de configuration** (`.github/workflows/*.yml`) | Copilot a ajouté une étape `actions/setup-node` pendant qu’un autre développeur a modifié la même étape. | Centraliser les modifications dans un *template* YAML et appliquer via `actions/github-script` pour éviter la duplication. |
| **Conflit de formatage** | Copilot suit les paramètres de l’extension (ex. `prettier`), alors que le projet impose `eslint --fix`. | Configurer `editor.formatOnSave` à `false` et laisser le pipeline `npm run lint -- --fix` normaliser le code. |

#### Piège concret  

> **Pitfall** : Copilot propose parfois des imports qui ne sont pas déclarés dans `package.json` ou `requirements.txt`. Si le workflow ne les installe pas, le job

---

## Module 4 — contenu

## 4.1 Analyse des licences des snippets générés  

| Licence | Compatibilité avec un projet MIT | Obligations principales | Risque d’incompatibilité |
|--------|-----------------------------------|--------------------------|--------------------------|
| MIT    | Oui                               | Conserver le copyright et la licence dans chaque fichier contenant le snippet | Aucun |
| Apache 2.0 | Oui (si le projet ne contient pas de code GPL) | Conserver le NOTICE, indiquer les modifications, ne pas utiliser les marques déposées | Nécessite le fichier `NOTICE` |
| GPL‑3.0 | Non (incompatible avec MIT, BSD, Apache) | Distribuer le code complet sous GPL‑3.0, fournir le source | Doit re‑licencier tout le projet sous GPL‑3.0 |

**Procédure automatisée (VS Code)**  

1. Installez l’extension **License Checker** (`streetsidesoftware.code-spell-checker`).  
2. Ajoutez le fichier de configuration `.licensecheckrc.json` :  

```json
{
  "allowedLicenses": ["MIT", "Apache-2.0"],
  "failOnUnknown": true,
  "ignorePatterns": ["**/node_modules/**"]
}
```

3. Exécutez `License Check: Scan Workspace`.  
4. Tout snippet marqué d’une licence non autorisée apparaît dans la vue “Problems”.  

> **Piège** : Copilot peut insérer un commentaire de licence incomplet (`/* MIT */`) qui ne satisfait pas les exigences de redistribution. Vérifiez toujours la présence du texte complet.

---

## 4.2 Détection de code sensible (clés API, mots de passe)  

### 4.2.1 GitHub Secret Scanning  

| Étape | Action | Résultat attendu |
|------|--------|-------------------|
| 1 | Activez **Secret scanning** dans les paramètres du dépôt (`Settings → Security & analysis → Secret scanning`) | GitHub analyse chaque push et crée une alerte lorsqu’un secret est détecté |
| 2 | Ajoutez le fichier `.gitattributes` avec `*.js filter=detect-secrets` (optionnel) | Le filtre `detect-secrets` de `pre-commit` rejette le commit contenant un secret |
| 3 | Dans le workflow CI, lancez `detect-secrets scan` | Le job échoue si un secret apparaît dans le diff |

### 4.2.2 Exemple de snippet généré contenant une clé  

```js
// Copilot a suggéré ce code dans un fichier utils.js
import axios from "axios";

export const fetchData = async () => {
  // ⚠️ Clé API exposée – à retirer immédiatement
  const apiKey = "AKIAxxxxxxxxxxxxxxxx";
  const response = await axios.get(
    `https://api.example.com/data?key=${apiKey}`
  );
  return response.data;
};
```

**Correction**  

```js
import axios from "axios";

/**
 * Récupère les données depuis l’API.
 * La clé est fournie via la variable d’environnement `EXAMPLE_API_KEY`.
 */
export const fetchData = async () => {
  const apiKey = process.env.EXAMPLE_API_KEY; // ← pas de secret en clair
  const response = await axios.get(
    `https://api.example.com/data?key=${apiKey}`
  );
  return response.data;
};
```

*Ajoutez `EXAMPLE_API_KEY` dans les **GitHub Secrets** du dépôt et configurez le workflow pour injecter la variable d’environnement.*

---

## 4.3 Utilisation de linters pour filtrer les suggestions non conformes  

### 4.3.1 ESLint (Node.js)  

1. Installez les plugins de sécurité :  

```bash
npm i -D eslint eslint-plugin-security eslint-plugin-no-unsanitized
```

2. `.eslintrc.json` :  

```json
{
  "env": { "node": true, "es2022": true },
  "extends": ["eslint:recommended", "plugin:security/recommended"],
  "plugins": ["security", "no-unsanitized"],
  "rules": {
    "no-eval": "error",
    "security/detect-object-injection": "error",
    "no-unsanitized/method": ["error", { "methods": ["innerHTML"] }]
  }
}
```

3. Ajoutez un script `npm run lint` et exécutez-le dans le pipeline CI.  

**Résultat** : toute suggestion contenant `eval`, `new Function`, ou une injection de paramètres non échappés déclenche une erreur de lint et bloque le merge.

### 4.3.2 Bandit (Python)  

```bash
pip install bandit
bandit -r src/ -ll
```

Configuration `bandit.yml` :  

```yaml
exclude_dirs:
  - tests
skips:
  - B101  # assert usage autorisée dans les tests uniquement
```

**Piège** : Bandit ne détecte pas les injections via des bibliothèques tierces non reconnues. Complétez l’audit avec **Snyk Code** si le projet utilise des ORM personnalisés.

---

## 4.4 Mise en place de règles de refus de code généré  

### 4.4.1 Branch protection et code owners  

```yaml
# .github/CODEOWNERS
# Copilot‑generated files doivent être approuvés par un humain senior
*.js @frontend-lead
*.py @backend-lead
```

```yaml
# .github/workflows/branch-protection.yml
name: Branch protection
on:
  push:
    branches: [main]
jobs:
  protect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Enforce required reviewers
        uses: peter-evans/required-reviewers@v2
        with:
          reviewers: "frontend-lead,backend-lead

---

## Module 5 — contenu

## Module 5 – Optimisation et maintenance du code généré par GitHub Copilot  

### 5.1 Analyse de la qualité du code produit  

| Critère | Méthode de mesure | Outil recommandé | Valeur cible |
|--------|-------------------|------------------|--------------|
| **Couverture de tests** | % de lignes exécutées | `coverage.py` (Python) / `nyc` (Node) | ≥ 85 % |
| **Complexité cyclomatique** | Valeur moyenne par fonction | `radon` (Python) / `eslint complexity` (JS) | ≤ 10 |
| **Détecteurs de vulnérabilités** | Nombre de findings critiques | `bandit` (Python) / `npm audit` (Node) | 0 |
| **Conformité aux conventions** | % de violations | `flake8` (Python) / `eslint` (JS) | ≤ 2 % |
| **Temps d’exécution** | Durée moyenne d’un appel critique | `timeit` (Python) / `benchmark.js` (Node) | ≤ baseline (défini par le ticket) |

> **Règle vérifiable** : `pytest --maxfail=1 --disable-warnings && coverage run -m pytest && coverage report -m` doit renvoyer un taux de couverture ≥ 85 % avant toute fusion.

### 5.2 Refactoring automatisé des suggestions  

1. **Déclencher le refactoring**  
   - Sélectionner le bloc suggéré.  
   - Appuyer `Ctrl+Shift+P` → **Copilot: Refactor**.  
   - Choisir le profil *“Performance + Typage”* (profil configurable dans `settings.json`).  

2. **Profil “Performance + Typage”** (exemple de configuration)  

```json
{
  "github.copilot.refactor.profiles": {
    "performance-typing": {
      "addTypeHints": true,
      "optimizeLoops": true,
      "replaceMapFilterWithComprehension": true,
      "inlineSmallFunctions": true
    }
  }
}
```

3. **Processus de validation**  

| Étape | Action | Vérification |
|------|--------|--------------|
| **A** | Exécuter le refactor | Aucun `SyntaxError` à l’ouverture du fichier |
| **B** | Lancer les tests unitaires | Tous les tests passent (`pytest -q`) |
| **C** | Mesurer le temps d’exécution | `timeit` montre une amélioration ≥ 10 % sur le benchmark ciblé |
| **D** | Commiter avec le préfixe `refactor:` | Exemple : `git commit -m "refactor: optimise get_user_data"` |

### 5.3 Gestion de la dette technique introduite par Copilot  

| Type de dette | Détection | Action corrective |
|---------------|----------|--------------------|
| **Code dupliqué** | `sonarqube` ou `cloc --by-file` | Extraire dans un module partagé, remplacer les appels |
| **Fonctions trop longues** (> 50 lignes) | `radon cc -a` | Appliquer le pattern *Extract Method* via Copilot (`// Copilot: extract method`) |
| **Imports inutilisés** | `flake8 --select=F401` | Supprimer automatiquement (`isort --remove-unused`) |
| **Variables non typées** (Python) | `mypy --strict` | Ajouter les annotations, laisser Copilot générer les signatures (`def foo(arg: int) -> str:`) |

> **Vérifiable** : après chaque merge, le pipeline CI exécute `mypy --strict` et bloque le merge si le nombre d’erreurs > 0.

### 5.4 Monitoring en production des artefacts Copilot  

1. **Instrumentation** – Ajouter un décorateur de mesure à chaque fonction générée par Copilot.  

```python
import time
import logging
from functools import wraps

def monitor(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logging.info(
            "Copilot:%s duration=%.3fms args=%s kwargs=%s",
            func.__name__, elapsed * 1000, args, kwargs
        )
        return result
    return wrapper
```

2. **Application** – Copilot insère automatiquement le décorateur lorsqu’on active le *snippet* `@monitor`.  

```python
@monitor
def compute_statistics(data: list[float]) -> dict[str, float]:
    """
    Retourne la moyenne, l'écart‑type et le min/max d'une liste de nombres.
    """
    # Copilot génère le corps complet
    n = len(data)
    if n == 0:
        raise ValueError("data must not be empty")
    mean = sum(data) / n
    var = sum((x - mean) ** 2 for x in data) / n
    return {
        "mean": mean,
        "std": var ** 0.5,
        "min": min(data),
        "max": max(data),
    }
```

3. **Alerting** – Configurer une règle Grafana/Prometheus sur le champ `duration` > `baseline