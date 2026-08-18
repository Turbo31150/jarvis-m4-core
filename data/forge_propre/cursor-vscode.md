# Cursor & VS Code IA Intégrée

> Référence `cursor-vscode` · 49 €

## Plan

## Module 1 : Installation, configuration et mise à jour de Cursor dans VS Code  
**Objectif mesurable** : L’apprenant sera capable d’installer Cursor, de le configurer pour un projet Python/JavaScript et de vérifier la version active via la ligne de commande.  
**Notions couvertes**  
1. Installation du serveur Cursor (`npm i -g @cursor-dev/cli`) et du plugin VS Code (`cursor-vscode`).  
2. Paramétrage du fichier `cursor.json` (model, temperature, context‑window).  
3. Gestion des clés API (OpenAI, Anthropic) dans les variables d’environnement.  
4. Utilisation de la commande `cursor --version` et mise à jour avec `cursor update`.  
5. Activation/désactivation du mode IA par espace de travail (`.vscode/settings.json`).

---

## Module 2 : Interaction de base avec le modèle IA dans l’éditeur  
**Objectif mesurable** : L’apprenant pourra générer, compléter et refactoriser du code en utilisant les raccourcis Cursor, et vérifier la pertinence du résultat par un test unitaire automatisé.  
**Notions couvertes**  
1. Invocation du completement (`Ctrl+Space`) et du chat inline (`Alt+Enter`).  
2. Utilisation du prompt contextuel (`// cursor: …`) pour guider la génération.  
3. Gestion des suggestions multiples et sélection via la palette (`Ctrl+Shift+P`).  
4. Insertion de snippets IA et validation par exécution de `npm test` ou `pytest`.  
5. Débogage des suggestions : affichage du log de requête (`cursor --log`).

---

## Module 3 : Exploitation avancée – Refactoring, optimisation et documentation automatisée  
**Objectif mesurable** : L’apprenant sera capable de transformer un module existant en suivant trois critères de qualité (complexité cyclomatique, conformité aux standards ESLint/PEP8, couverture de docstrings) grâce à Cursor.  
**Notions couvertes**  
1. Prompt de refactoring (`// cursor: refactor to reduce cyclomatic complexity`).  
2. Optimisation des performances (suggestions de vecteurs, async/await, memoization).  
3. Génération de docstrings conformes à PEP 257 ou JSDoc.  
4. Vérification de la conformité avec `eslint --fix` ou `flake8`.  
5. Utilisation du mode « explain » pour obtenir une justification de chaque modification.

---

## Module 4 : Intégration du flux de travail CI/CD avec Cursor  
**Objectif mesurable** : L’apprenant pourra automatiser la génération de code IA dans un pipeline GitHub Actions et valider que le job passe les tests unitaires et le linting.  
**Notions couvertes**  
1. Script d’appel CLI `cursor generate` dans un job `run` de GitHub Actions.  
2. Gestion sécurisée des secrets API via `secrets.CURSOR_API_KEY`.  
3. Conditionnement de l’exécution (ex. : uniquement sur les PR avec le label `ai‑assist`).  
4. Rapports de diff automatisés (`git diff --name-only`) et commentaires de PR.  
5. Nettoyage des artefacts et rollback en cas d’échec du job.

---

## Module 5 : Personnalisation du modèle et gestion des limites d’usage  
**Objectif mes**

---

## Module 1 — contenu

## 1. Installation du serveur CLI Cursor  

| Étape | Commande | Vérification |
|------|----------|--------------|
| 1. Prérequis Node ≥ 18 | `node -v` → *une version récente* ou plus | Si la version est inférieure, télécharger depuis <https://nodejs.org> |
| 2. Installation globale du CLI | `npm i -g @cursor-dev/cli` | `which cursor` (Linux/macOS) ou `where cursor` (Windows) doit renvoyer le chemin du binaire |
| 3. Vérification de l’installation | `cursor --help` | L’aide du CLI s’affiche, confirmant que le binaire est dans le `$PATH` |

> **Piège** : sous Windows, le répertoire global de npm (`%APPDATA%\npm`) n’est pas toujours ajouté au `PATH`. Ajoutez‑le manuellement ou ré‑ouvrez le terminal après l’installation.

---

## 2. Installation du plugin VS Code  

1. Ouvrir la palette de commandes (`Ctrl+Shift+P`).  
2. Saisir **Extensions : Installer des extensions** → rechercher **“Cursor – AI‑assistant”** (identifiant `cursor-dev.cursor`).  
3. Cliquer **Installer**.  
4. Redémarrer VS Code (ou `Developer: Reload Window`).  

> **Piège** : le plugin ne s’active que si le CLI est détectable dans le même environnement que VS Code. Si vous utilisez VS Code installé via Snap sur Linux, le `$PATH` du Snap ne voit pas le CLI global. Installez le CLI dans le même environnement (`snap run --shell code` puis `npm i -g …`).

---

## 3. Configuration du projet avec `cursor.json`  

Le fichier `cursor.json` doit être placé à la racine du workspace. Exemple minimal :

```jsonc
{
  // Modèle à utiliser (OpenAI ou Anthropic). Valeurs courantes :
  // "gpt-4o-mini", "claude-3-haiku-20240307"
  "model": "gpt-4o-mini",

  // Température de génération : une valeur basse donne un résultat déterministe, une valeur élevée donne un résultat plus créatif
  "temperature": 0.2,

  // Taille de la fenêtre de contexte (tokens). 16384 est la limite actuelle de GPT‑4o‑mini.
  "contextWindow": 16384,

  // Répertoire racine du projet (facultatif, par défaut = cwd)
  // "root": "./src"
}
```

### 3.1 Gestion des clés API  

Les clés sont lues depuis les variables d’environnement :

| Variable | Exemple de valeur | Usage |
|----------|------------------|-------|
| `OPENAI_API_KEY` | `sk-xxxxxxxxxxxxxxxxxxxx` | Modèle OpenAI |
| `ANTHROPIC_API_KEY` | `sk-ant-xxxxxxxxxxxxxxxxxxxx` | Modèle Anthropic |

```bash
# Linux/macOS
export OPENAI_API_KEY="sk-..."
# Windows PowerShell
$env:OPENAI_API_KEY="sk-..."
```

> **Piège** : ne jamais placer la clé directement dans `cursor.json`. Le CLI refuse le fichier s’il détecte une clé en clair, afin d’éviter les fuites dans les dépôts Git.

---

## 4. Vérification de la version active  

```bash
cursor --version
```

Sortie attendue : `cursor-cli 0.12.3` (ou version supérieure).  

Mise à jour :

```bash
cursor update
```

Après la mise à jour, relancer `cursor --version` pour confirmer.

> **Piège** : le CLI peut être installé dans deux emplacements différents (global et local via `npx`). `cursor update` ne met à jour que l’installation globale. Si vous avez invoqué `npx cursor …`, la mise à jour n’a aucun effet.

---

## 5. Activation/désactivation du mode IA par espace de travail  

VS Code lit les paramètres du workspace depuis `.vscode/settings.json`. Exemple :

```jsonc
{
  // Active le serveur Cursor uniquement pour ce workspace
  "cursor.enabled": true,

  // Désactive la suggestion automatique (utile en phase de test)
  "cursor.autoSuggest": false,

  // Chemin relatif du fichier de configuration du projet
  "cursor.configFile": "cursor.json"
}
```

### 5.1 Désactivation globale (dans les paramètres utilisateur)  

```jsonc
{
  "cursor.enabled": false   // désactive le plugin pour tous les workspaces
}
```

> **Piège** : le paramètre `cursor.enabled` dans les *settings* utilisateur a la priorité sur le même paramètre déclaré dans le workspace. Si vous avez désactivé globalement, le plugin restera inactif même si le workspace le ré‑active.  

---

## 6. Exemple complet : projet Python minimal  

Structure du répertoire :

```
my‑project/
├─ .vscode/
│   └─ settings.json
├─ cursor.json
├─ main.py
└─ requirements.txt
```

### 6.1 `cursor.json`

```jsonc
{
  "model": "gpt-4o-mini",
  "temperature": 0.0,
  "contextWindow": 16384
}
```

### 6.2 `.vscode/settings.json`

```jsonc
{
  "cursor.enabled": true,
  "cursor.autoSuggest": true,
  "cursor.configFile": "cursor.json"
}
```

### 6.3 `main.py` (code de démonstration)

```python
# main.py
def factorial(n: int) -> int:
    """Calcul du factoriel de n (n ≥ 0)."""
    # cursor: improve this function to handle negative inputs gracefully
    result
```

---

## Module 2 — contenu

## Module 2 : Interaction de base avec le modèle IA dans l’éditeur  

### 2.1 Invocation du completement et du chat inline  

| Action | Raccourci (VS Code) | Description | Résultat attendu |
|--------|--------------------|-------------|-------------------|
| **Complétion instantanée** | `Ctrl+Space` (ou `⌃␣` sur macOS) | Enveloppe le curseur dans le fichier actif, envoie le texte du fichier + le contexte du projet à Cursor. | Une liste déroulante contenant une ou plusieurs suggestions de code. |
| **Chat inline** | `Alt+Enter` (ou `⌥↩`) | Ouvre une zone de texte inline au-dessus du curseur ; le texte saisi est traité comme prompt. | Réponse du modèle affichée sous forme de bloc de code ou de texte. |
| **Activation/désactivation temporaire** | `Ctrl+Shift+P → “Cursor: Toggle AI”` | Permet de désactiver l’assistance IA pour le fichier courant sans toucher aux paramètres globaux. | Aucun appel API tant que le mode est désactivé. |

> **Note technique** : le serveur CLI `cursor` utilise la variable d’environnement `CURSOR_API_KEY`. Si elle n’est pas définie, les raccourcis affichent *“API key missing”* et n’envoient aucune requête.

### 2.2 Prompt contextuel (`// cursor: …`)  

Le modèle lit les commentaires commençant par `// cursor:` (ou `# cursor:` en Python) comme partie du prompt.  
Exemple :

```python
# cursor: generate a function that returns the nth Fibonacci number,
# using memoization and type hints.
def fibonacci(n: int) -> int:
    pass
```

Lorsque le curseur se trouve sur `pass` et que l’on lance `Alt+Enter`, Cursor remplace le corps par une implémentation conforme au commentaire.  

#### Bonnes pratiques  

| Situation | Prompt recommandé | Pourquoi |
|-----------|-------------------|----------|
| **Définir le style** | `// cursor: use async/await, keep line length reasonable` | Guide le modèle vers le style souhaité. |
| **Contraindre les dépendances** | `// cursor: do not import external libraries` | Évite l’ajout de paquets non déclarés dans `requirements.txt`. |
| **Demander un test** | `// cursor: also generate a pytest for this function` | Permet de valider immédiatement la pertinence du code. |

### 2.3 Gestion des suggestions multiples  

1. Après `Ctrl+Space`, la palette de suggestions s’ouvre.  
2. `Ctrl+Shift+P → “Cursor: Show All Suggestions”` affiche la liste complète dans le *Quick Pick*.  
3. Sélectionner une suggestion avec les flèches puis `Enter`.  
4. Si aucune suggestion ne convient, choisir **“Regenerate”** (icône ↻) pour obtenir une variante.  

### 2.4 Insertion de snippets IA et validation automatisée  

#### Exemple complet (JavaScript)  

```javascript
// cursor: generate a function that validates an email address
// and returns true/false. Include a Jest test suite.
function isValidEmail(email) {
  // cursor: implementation
}
```

1. Placez le curseur sur la ligne `// cursor: implementation`.  
2. `Alt+Enter` → Cursor insère :

```javascript
function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}
```

3. Ajoutez le test (prompt dans le même fichier ou séparé) :

```javascript
// cursor: generate Jest tests for isValidEmail
```

Résultat attendu :

```javascript
describe('isValidEmail', () => {
  test('valid email passes', () => {
    expect(isValidEmail('alice@example.com')).toBe(true);
  });
  test('invalid email fails', () => {
    expect(isValidEmail('alice@@example..com')).toBe(false);
  });
});
```

4. Lancer les tests : `npm test`. Si le test échoue, ré‑ouvrir le prompt `Alt+Enter` et demander une correction : `// cursor: fix failing test`.  

### 2.5 Débogage des suggestions : journalisation (`cursor --log`)  

- Exécuter `cursor --log > cursor.log` dans le terminal du workspace.  
- Le fichier `cursor.log` contient :  
  - **request_id** (UUID