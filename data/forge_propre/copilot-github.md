# GitHub Copilot Masterclass

> Référence `copilot-github`

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
**Objectif mesurable** : Formuler trois types de prompts (description fonctionnelle, commentaire de fonction, test‑driven) et obtenir des suggestions dont le taux de conformité syntaxique élevé sur un projet Python de taille moyenne.  
**Notions couvertes**  
1. Structure d’un prompt efficace (verbe d’action, contraintes, exemples).  
2. Utilisation des commentaires de type “///” et “#region” pour guider la génération.  
3. Paramétrage du “temperature” et du “top‑p” via les réglages avancés.  
4. Gestion des suggestions multi‑ligne et insertion sélective.  
5. Détection et résolution des hallucinations de code (exemple : appels à des API inexistantes).

## Module 3 – Intégration dans le flux de travail de développement  
**Objectif mesurable** : Intégrer Copilot dans un pipeline CI/CD (GitHub Actions) et démontrer qu’une large partie des suggestions acceptées passent les tests unitaires automatisés sans modification manuelle.  
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
| **Contrainte fonctionnelle** | limite le périmètre (type de retour, complexité, dépendances). | `renvoie un dict contenant les clés id et value uniquement` |
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

| Paramètre | Description | Effet |
|----------|--------------|------|
| `temperature` | Valeur basse pour des réponses déterministes, valeur élevée pour plus de variété | 0.0 → réponses déterministes, 1.0 → plus de variété |
| `top_p` | Fraction cumulative de probabilité du vocabulaire retenu | 0.9 (défaut) ou valeur plus conservatrice |

Dans VS Code : `Fichier → Préférences → Paramètres → Extensions → GitHub Copilot → Advanced`.  
- Pour du code de production, privilégier une température basse et un `top_p` proche du défaut.  
- Pour des prototypes ou des suggestions de refactorisation, on peut augmenter la température.

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