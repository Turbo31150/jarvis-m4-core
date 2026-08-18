# Cursor & VS Code IA Intégrée

> Référence `cursor-vscode` · 49 €

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
**Objectif mes

---

## Module 1 — contenu

## 1. Installation du serveur CLI Cursor  

| Étape | Commande | Vérification |
|------|----------|--------------|
| 1. Prérequis Node ≥ 18 | `node -v` → *v18.x* ou plus | Si la version est inférieure, télécharger depuis <https://nodejs.org> |
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

  // Température de génération : 0 → déterministe, 1 → créatif
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

---

## Module 2 — contenu

## Module 2 : Interaction de base avec le modèle IA dans l’éditeur  

### 2.1 Invocation du completement et du chat inline  

| Action | Raccourci (VS Code) | Description | Résultat attendu |
|--------|--------------------|-------------|-------------------|
| **Complétion instantanée** | `Ctrl+Space` (ou `⌃␣` sur macOS) | Enveloppe le curseur dans le fichier actif, envoie le texte du fichier + le contexte du projet à Cursor. | Une liste déroulante contenant 1 à N suggestions de code. |
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
| **Définir le style** | `// cursor: use async/await, keep line length ≤ 88` | Limite les suggestions à des conventions précises. |
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
  - **request_id** (UUID)  
  - **prompt** (texte envoyé)  
  - **model**, **temperature**, **max_tokens**  
  - **response** (texte retourné)  
  - **latency_ms**  

Utilisez `grep <request_id> cursor.log` pour isoler une requête précise.  

#### Cas typique de latence élevée  

| Symptom | Cause probable | Action corrective |
|---------|----------------|-------------------|
| > 2 s avant affichage | Modèle `gpt‑4o‑preview` avec `temperature=1.0` | Baisser `temperature` à 0.2 ou passer à `gpt‑4o‑mini`. |
| Réponse tronquée | `max_tokens` trop faible (ex. : 128) | Augmenter à 512 ou plus via `cursor.json`. |

### 2.6 Pièges concrets  

| Piège | Description | Solution |
|-------|-------------|----------|
| **Contexte dépassé** | Le fichier dépasse la fenêtre de contexte (≈ 8 k tokens). | Utiliser `// cursor: summarize this file` puis travailler sur le résumé, ou scinder le fichier. |
| **Prompt ambigu** | “Generate a

---

## Module 3 — contenu

## Module 3 : Exploitation avancée – Refactoring, optimisation et documentation automatisée  

### 3.1 Prompt de refactoring ciblé  

| Étape | Action | Détails techniques |
|------|--------|--------------------|
| 1 | Ouvrir le fichier à refactoriser | `Ctrl+P` → saisir le nom du fichier. |
| 2 | Insérer le **prompt de refactoring** en commentaire au-dessus du bloc concerné | ```js // cursor: refactor to reduce cyclomatic complexity ``` <br>ou <br>```python # cursor: refactor to reduce cyclomatic complexity``` |
| 3 | Sélectionner le bloc (ou placer le curseur dans le bloc) | `Shift+Alt+↑/↓` pour étendre la sélection. |
| 4 | Lancer la génération IA | `Alt+Enter` (Chat inline) ou `Ctrl+Space` (Completion) selon la configuration. |
| 5 | Examiner les suggestions dans la **Palette** (`Ctrl+Shift+P` → « Cursor: Show suggestions ») |
| 6 | Appliquer la version retenue | `Enter` sur la suggestion ou `Ctrl+Shift+Enter` pour insérer directement. |

> **Note** : le modèle utilise le contexte du fichier complet. Si le fichier dépasse la fenêtre de contexte (≈ 8 k tokens), ajouter `// cursor: context‑window: 16384` dans le `cursor.json` ou réduire la portée du prompt à un petit bloc.

### 3.2 Optimisation des performances  

#### 3.2.1 Asynchronisme (JS)  

```js
// cursor: replace synchronous loops with async/await where possible
async function fetchAll(urls) {
  const results = [];
  for (const url of urls) {
    // IA propose d’utiliser Promise.all pour paralléliser
    // → on accepte la suggestion
  }
  return results;
}
```

Après exécution du prompt, l’IA propose :

```js
async function fetchAll(urls) {
  const promises = urls.map(url => fetch(url).then(r => r.json()));
  const results = await Promise.all(promises);
  return results;
}
```

*Pourquoi c’est plus performant* : `Promise.all` lance toutes les requêtes en parallèle, réduisant le temps total de `O(n·t)` à `O(max(t_i))`.

#### 3.2.2 Mémoïsation (Python)  

```python
# cursor: add memoization to speed up repeated calls
def fib(n: int) -> int:
    """Compute the nth Fibonacci number recursively."""
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
```

IA répond :

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n: int) -> int:
    """Compute the nth Fibonacci number recursively."""
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
```

*Vérification* : `timeit` montre une réduction de 99 % du temps d’exécution pour `fib(35)`.

### 3.3 Génération de docstrings conformes  

| Langage | Style | Prompt | Exemple de sortie |
|--------|-------|--------|-------------------|
| Python | **PEP 257** | `// cursor: generate docstring PEP257` | ```python def add(a: int, b: int) -> int: """Add two integers.\n\nArgs:\n    a (int): First operand.\n    b (int): Second operand.\n\nReturns:\n    int: Sum of *a* and *b*.\n""" return a + b ``` |
| JavaScript | **JSDoc** | `// cursor: generate JSDoc` | ```js /** * Calculates the area of a circle.\n * @param {number} radius - Radius of the circle.\n * @returns {number} Area of the circle.\n */ function area(radius) { return Math.PI * radius ** 2; } ``` |

#### Validation automatisée  

- **Python** : `flake8 --select=D` (checks docstring presence) + `pydocstyle`.  
- **JS** : `eslint --rule 'jsdoc/require-jsdoc': 'error'` (via `eslint-plugin-jsdoc`).  

```bash
# Python
flake8 src/ --select=D
# JavaScript
eslint src/ --rule 'jsdoc/require-jsdoc': 'error'
```

### 3.4 Vérification de conformité  

| Outil | Commande | Ce qui est vérifié |
|-------|----------|--------------------|
| **ESLint** | `eslint src/ --fix` | Syntaxe, style, règles JSDoc (si plugin installé). |
| **Flake8** | `flake8 src/` | PEP8, complexité cyclomatique (`C901`), docstrings (`D`). |
| **Radon** (Python) | `radon cc -a src/` | Complexité cyclomatique moyenne. |
| **Plato** (JS) | `plato -r -d report src/` | Complexité, maintainability. |

**Exemple de workflow** :

```bash
# 1. Lancer le refactoring IA
cursor generate --file src/utils.py --prompt "refactor to reduce cyclomatic complexity"

# 2. Linter + métriques
flake8 src/
radon cc -a src/
pydocstyle src/

# 3. Si tout passe, commit
git add src/
git commit -m "Refactor utils.py – complexity ≤ 10, docstrings added"
```

### 3.5 Mode « explain » – Justification des modifications  

```bash
cursor explain --file src/api.js --line 42
```

Sortie typique :

```
Modification : remplacé la boucle for…while par Promise.all.
Raison : parallélisation des requêtes HTTP → réduction du temps d’attente de 3 s à 0.4 s (benchmarks

---

## Module 4 — contenu

## 4.1. Principe d’intégration CI / CD avec Cursor  

- **Cursor CLI** : `cursor generate` accepte les mêmes paramètres que l’extension VS Code (prompt, modèle, température).  
- **GitHub Actions** exécute le CLI dans un conteneur Linux (ou Windows/macOS) où les variables d’environnement sont injectées via `secrets`.  
- Le job doit :  
  1. récupérer le code (`actions/checkout@v3`),  
  2. installer Node / npm, le CLI Cursor et les dépendances du projet,  
  3. lancer la génération,  
  4. vérifier que les tests unitaires et le lint passent,  
  5. publier le diff et, en cas d’échec, annuler les changements.  

---

## 4.2. Fichier de workflow complet  

```yaml
# .github/workflows/cursor-ci.yml
name: IA‑Assist – génération de code

on:
  pull_request:
    types: [opened, synchronize, labeled, unlabeled]
    # Le job ne démarre que si le PR possède le label « ai-assist »
    # Le filtre est appliqué dans le job grâce à la condition ci‑dessous.

jobs:
  cursor-generate:
    if: >-
      contains(github.event.pull_request.labels.*.name, 'ai-assist')
    runs-on: ubuntu-latest
    permissions:
      contents: write      # pour push du diff
      pull-requests: write # pour commenter le PR

    steps:
      # 1️⃣ Checkout du code
      - name: Checkout repository
        uses: actions/checkout@v3
        with:
          fetch-depth: 0   # nécessaire pour le diff complet

      # 2️⃣ Installation de Node.js et du CLI Cursor
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install Cursor CLI
        run: npm i -g @cursor-dev/cli

      # 3️⃣ Installation des dépendances du projet (exemple Python)
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Python deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      # 4️⃣ Export de la clé API (sécurisée)
      - name: Export Cursor API key
        env:
          CURSOR_API_KEY: ${{ secrets.CURSOR_API_KEY }}
        run: echo "CURSOR_API_KEY=${CURSOR_API_KEY}" >> $GITHUB_ENV

      # 5️⃣ Génération IA – on cible les fichiers modifiés uniquement
      - name: Run Cursor generation
        id: cursor
        env:
          CURSOR_API_KEY: ${{ env.CURSOR_API_KEY }}
        run: |
          # Liste des fichiers Python modifiés dans le PR
          MODIFIED=$(git diff --name-only ${{ github.event.pull_request.base.sha }} ${{ github.sha }} | grep '\.py$' || true)

          if [ -z "$MODIFIED" ]; then
            echo "No Python files to process."
            exit 0
          fi

          # Boucle sur chaque fichier et génère les docstrings manquants
          for f in $MODIFIED; do
            echo "Processing $f"
            cursor generate \
              --model=gpt-4o-mini \
              --temperature=0.2 \
              --prompt="Add missing PEP 257 docstrings to this file." \
              "$f" \
              --in-place
          done

      # 6️⃣ Lint + tests – on bloque le pipeline si l’un d’eux échoue
      - name: Run flake8 lint
        run: flake8 .
        continue-on-error: false

      - name: Run pytest
        run: pytest -q
        continue-on-error: false

      # 7️⃣ Publier le diff (si des modifications ont eu lieu)
      - name: Detect changes
        id: changes
        run: |
          git diff --name-only > changed_files.txt
          if [ -s changed_files.txt ]; then
            echo "changed=true" >> $GITHUB_OUTPUT
          else
            echo "changed=false" >> $GITHUB_OUTPUT
          fi

      - name: Commit & push generated changes
        if: steps.changes.outputs.changed == 'true'
        env:
          GIT_AUTHOR_NAME: github-actions
          GIT_AUTHOR_EMAIL: github-actions@github.com
        run: |
          git config user.name "$GIT_AUTHOR_NAME"
          git config user.email "$GIT_AUTHOR_EMAIL"
          git add -u
          git commit -m "🤖 IA : docstrings générés par Cursor"
          git push origin HEAD:${{ github.head_ref }}

      - name: Comment PR with diff summary
        if: steps.changes.outputs.changed == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const changed = fs.readFileSync('changed_files.txt', 'utf8')
                              .trim()
                              .split('\n')
                              .filter(Boolean);
            const body = `## 🤖 Cursor IA – modifications\n` +
                         changed.map(f => `- \`${f}\``).join('\n');
            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.payload.pull_request.number,
              body
            });

      # 8️⃣ Nettoyage (facultatif

---

## Module 5 — contenu

## Module 5 : Personnalisation du modèle et gestion des limites d’usage  

### 5.1 Sélection et configuration d’un modèle personnalisé  

| Paramètre | Description | Valeur typique |
|-----------|-------------|----------------|
| `model` | Identifiant complet du modèle (ex. `gpt-4o-mini`, `claude-3-5-sonnet-20241022`, ou ID d’un modèle fine‑tuned OpenAI) | `gpt-4o-mini` |
| `temperature` | Niveau de stochasticité : 0 = déterministe, 1 = très créatif | `0.2` |
| `maxTokens` | Nombre maximal de tokens renvoyés par l’IA (limite imposée par le fournisseur) | `1024` |
| `topP` | Nucleus sampling : proportion cumulative de probabilité à retenir | `0.95` |

Ces paramètres sont stockés dans le fichier **`.cursorrc.json`** à la racine du projet (ou dans `cursor.json` si vous utilisez la version antérieure). Exemple :

```json
{
  "model": "gpt-4o-mini",
  "temperature": 0.2,
  "maxTokens": 1024,
  "topP": 0.95,
  "apiKeyEnv": "OPENAI_API_KEY"
}
```

#### 5.1.1 Utilisation d’un modèle fine‑tuned OpenAI  

1. Créez le modèle via l’API OpenAI (`/v1/fine_tuning/jobs`).  
2. Récupérez l’ID du modèle (`ft-xxxxxxxxxxxx`).  
3. Remplacez la valeur du champ `model` dans le fichier de configuration :

```json
{
  "model": "ft-xxxxxxxxxxxx",
  "temperature": 0,
  "maxTokens": 512
}
```

> **Vérification** : exécutez `cursor --model` ; la sortie doit afficher l’ID du modèle configuré.

### 5.2 Gestion des quotas et des limites d’usage  

| Limite | Source | Méthode de contrôle |
|--------|--------|----------------------|
| **Coût** (USD) | Facturation OpenAI/Anthropic | `cursor usage --budget 15` (définit un plafond de 15 USD) |
| **Nombre de tokens** | Quota mensuel du compte | `cursor usage --max-tokens 200000` |
| **RPS / RPM** (requests per second / minute) | Limites d’API (ex. 3500 RPM pour GPT‑4o) | Implémentation d’un **rate‑limiter** côté client (ex. `p‑limiter` npm) |
| **Temps de réponse** | SLA du fournisseur | `cursor --timeout 30` (seconds) |

#### 5.2.1 Exemple de rate‑limiter en JavaScript  

```js
// limiter.js – wrapper autour du CLI Cursor
import { execSync } from 'node:child_process';
import Bottleneck from 'bottleneck';

// 3500 requests / minute ≈ 58 req/s → on fixe 55 req/s pour marge
const limiter = new Bottleneck({ minTime: Math.ceil(1000 / 55) });

/**
 * Exécute une commande Cursor en respectant le quota.
 * @param {string} prompt - Prompt à envoyer à l’IA.
 * @returns {string} - Réponse brute du modèle.
 */
export function askCursor(prompt) {
  return limiter.schedule(() => {
    const cmd = `cursor ask "${prompt.replace(/"/g, '\\"')}"`;
    try {
      return execSync(cmd, { encoding: 'utf8' });
    } catch (e) {
      // Gestion d’erreur de dépassement de quota
      if (e.stderr.includes('Rate limit')) {
        throw new Error('Quota API dépassé – réessayez plus tard');
      }
      throw e;
    }
  });
}
```

*Le code ci‑dessus* :  
- importe `Bottleneck` (npm install bottleneck).  
- impose un délai minimal entre deux appels pour rester sous la limite de 3500 RPM.  
- capture les erreurs de dépassement de quota et les remonte sous forme d’exception claire.

### 5.3 Monitoring et audit des consommations  

1. **Journalisation locale** – activez le mode verbeux : `cursor --log > cursor.log`.  
2. **Export JSON** – `cursor usage --json > usage.json` génère :  

```json
{
  "model": "gpt-4o-mini",
  "totalTokens": 13457,
  "promptTokens": 9234,
  "completionTokens": 4223,
  "costUSD": 0.18,
  "timestamp": "2026-08-14T10:12:45Z"
}
```

3. **Alertes automatisées** – script Node :

```js
import fs from 'node:fs';
import path from 'node:path';

const USAGE_FILE = path.resolve('.cursor', 'usage.json');
const BUDGET_USD = 20;

function checkBudget() {
  if (!fs.existsSync(USAGE_FILE)) return;
  const data = JSON.parse(fs.readFileSync(USAGE_FILE, 'utf8'));
  if (data.costUSD > BUDGET_USD) {
    console.warn(`⚠️ Budget dépassé : ${data.costUSD.toFixed(2)} USD > ${BUDGET_USD} USD`);
  }
}
checkBudget();
```

Intégrez ce script dans un **pre‑commit hook