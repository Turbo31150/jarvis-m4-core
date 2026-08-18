# GitHub Actions & CI/CD IA

> Référence `github-cicd` · 39 €

## Plan

## Module 1 – Concevoir et déclencher des workflows GitHub Actions  
**Objectif mesurable** : à l’issue du module, le participant crée, versionne et exécute un workflow YAML complet déclenché par push, pull‑request et schedule, et valide son exécution via les logs GitHub.  

**Notions couvertes**  
1. Structure du fichier `workflow.yml` : `name`, `on`, `jobs`, `steps`.  
2. Syntaxe YAML et validation avec `actionlint`.  
3. Triggers (`push`, `pull_request`, `workflow_dispatch`, `schedule`).  
4. Jobs parallèles et dépendances (`needs`).  
5. Utilisation d’actions officielles (`actions/checkout`, `actions/setup-python`).  

---

## Module 2 – Gérer les environnements, les secrets et le caching  
**Objectif mesurable** : le participant configure des environnements de pré‑production et production, stocke et récupère des secrets via le coffre GitHub, et met en place un cache efficace pour les dépendances Python et les modèles pré‑entraînés.  

**Notions couvertes**  
1. Définition d’environnements (`environment:`) et protection des déploiements.  
2. Stockage des secrets (`Settings → Secrets → Actions`) et accès via `${{ secrets.MY_KEY }}`.  
3. Cache des dépendances (`actions/cache`) avec clés de versionnement.  
4. Gestion des artefacts (`actions/upload-artifact`, `actions/download-artifact`).  
5. Variables d’environnement de workflow (`env:`) et expressions conditionnelles.  

---

## Module 3 – Intégrer les tests automatisés d’applications IA  
**Objectif mesurable** : le participant intègre dans le pipeline des tests unitaires, d’intégration et de validation de données, et fait échouer le workflow en cas de régression détectée.  

**Notions couvertes**  
1. Exécution de suites de tests `pytest` avec couverture (`pytest-cov`).  
2. Tests de validation de données avec `great_expectations` ou `pandera`.  
3. Scénarios de test multi‑matrice (Python 3.8‑3.11, GPU vs CPU).  
4. Reporting des résultats (`actions/upload-artifact`, `actions/upload-sarif`).  
5. Gestion des échecs : `continue-on-error`, `if: failure()`.  

---

## Module 4 – Déployer automatiquement des modèles IA  
**Objectif mesurable** : le participant crée un pipeline qui construit une image Docker contenant le modèle, la pousse vers Docker Hub ou GitHub Container Registry, puis la déploie sur un cluster Kubernetes via `kubectl` ou sur AWS Lambda via `serverless`.  

**Notions couvertes**  
1. Construction d’image Docker avec `docker/build-push-action`.  
2. Authentification aux registres (`docker/login-action`).  
3. Déploiement Kubernetes (`kubectl apply`, `kustomize`).  
4. Déploiement serverless (`serverless framework`, `aws lambda`).  
5. Versionnage des modèles (`model registry` simple via tags Git).  

---


---

## Module 1 — contenu

## 1. Structure d’un fichier `workflow.yml`

| Niveau | Clé | Valeur attendue | Exemple |
|--------|-----|----------------|---------|
| 0 | `name` | Chaîne libre, identifie le workflow dans l’UI GitHub | `name: CI / CD – Python IA` |
| 0 | `on` | Déclencheurs (push, pull_request, workflow_dispatch, schedule, …) | `on: [push, pull_request]` |
| 0 | `jobs` | Conteneur d’un ou plusieurs jobs | `jobs:` |
| 1 | `<job_id>` | Identifiant unique (lower‑case, pas d’espaces) | `build:` |
| 2 | `name` | Nom affiché dans l’UI | `name: Build & lint` |
| 2 | `runs-on` | Runner (ex. `ubuntu-latest`, `self-hosted`) | `runs-on: ubuntu-latest` |
| 2 | `needs` | (optionnel) tableau d’identifiants de jobs précédents | `needs: [test]` |
| 2 | `steps` | Liste ordonnée d’étapes | `steps:` |
| 3 | `- name` | Description de l’étape | `- name: Checkout source` |
| 3 | `- uses` | Action officielle ou tierce | `uses: actions/checkout@v4` |
| 3 | `- run` | Commande shell (bash sur Linux/macOS) | `run: python -m pip install -r requirements.txt` |
| 3 | `- env` | (optionnel) variables d’environnement locales à l’étape | `env: PYTHONPATH: ${{ github.workspace }}/src` |

> **Note** : chaque niveau d’indentation correspond à deux espaces (YAML strict).  

---

## 2. Syntaxe YAML et validation avec `actionlint`

* **Indentation** : uniquement des espaces, jamais de tabulations.  
* **Chaînes contenant `:` ou `#`** doivent être entourées de guillemets (`"` ou `'`).  
* **Valeurs booléennes** : `true` / `false` (sans majuscules).  
* **Liste inline** : `[push, pull_request]` ou multi‑lignes `- push\n- pull_request`.  

**Installation d’`actionlint` (Linux/macOS) :**

```bash
# via Go
go install github.com/rhysd/actionlint/cmd/actionlint@latest
# ou via Docker (sans installation Go)
docker run --rm -v "$(pwd)":/repo -w /repo rhysd/actionlint
```

**Commande de validation** :

```bash
actionlint .github/workflows/ci.yml
```

`actionlint` signale les erreurs de syntaxe, les clés inconnues et les incohérences de version d’action.

---

## 3. Triggers (déclencheurs)

| Trigger | Syntaxe minimale | Exemple d’usage |
|---------|------------------|-----------------|
| `push` | `push:` | `push: { branches: [main] }` |
| `pull_request` | `pull_request:` | `pull_request: { types: [opened, synchronize] }` |
| `workflow_dispatch` | `workflow_dispatch:` | Permet le lancement manuel depuis l’UI |
| `schedule` | `schedule:` | `schedule: - cron: '0 3 * * *'` (3 h UTC chaque jour) |
| `release` | `release:` | `release: { types: [published] }` |

**Piège** : le déclencheur `push` ne réagit pas aux tags par défaut. Il faut ajouter `tags: ['v*']` ou `branches: ['*']` selon le besoin.

---

## 4. Jobs parallèles et dépendances (`needs`)

* **Parallélisme** : tous les jobs d’un même niveau s’exécutent simultanément (dans la limite du quota de runners).  
* **Dépendance** : `needs` force l’attente de la fin réussie (ou échouée, selon `if`) des jobs listés.  

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps: …
  test:
    runs-on: ubuntu-latest
    needs: lint          # test démarre après lint
    steps: …
  build:
    runs-on: ubuntu-latest
    needs: [lint, test]  # build attend les deux précédents
    steps: …
```

**Piège** : `needs` accepte un tableau ou une chaîne. `needs: lint, test` (sans crochets) est **invalid** ; il faut `needs: [lint, test]` ou deux lignes `needs: lint` puis `needs: test` (mais le second écrase le premier).

---

## 5. Utilisation d’actions officielles

| Action | Version recommandée (au 14 / 08 / 2026) | Fonction |
|--------|----------------------------------------|----------|
| `actions/checkout` | `@v4` | Récupère le code source du repository |
| `actions/setup-python` | `@v5` | Installe une version précise de Python |
| `actions/cache` | `@v4` | Met en cache des répertoires (ex. `~/.cache/pip`) |
| `actions/upload-artifact` | `@v4` | Export d’un répertoire ou fichier en tant qu’artéfact |
| `actions/download-artifact` | `@v4` | Récupère un artéfact d’un job précédent |

**Exemple complet commenté**  

```yaml


---

## Module 2 — contenu

## Module 2 – Gérer les environnements, les secrets et le caching  

### 2.1 Définition d’environnements et protection des déploiements  

| Élément | Syntaxe dans le workflow | Effet | Vérifiable dans l’UI |
|--------|--------------------------|-------|----------------------|
| `environment:` | `environment: production` (au niveau du job) | Le job s’exécute dans l’environnement nommé *production*. | **Settings → Environments** → liste des environnements créés. |
| `environment:` avec `url` | `environment: { name: staging, url: https://staging.example.com }` | Ajoute un champ *Environment URL* visible dans le run. | UI du run → “Environment URL”. |
| Protection (reviewers, wait‑timer, required status checks) | Configurée dans **Settings → Environments → <env> → Protection rules** | Empêche le déploiement tant que les conditions ne sont pas respectées. | Le bouton *Deploy* reste gris tant que les règles ne sont pas satisfaites. |

**Piège** : si le même nom d’environnement est utilisé dans plusieurs workflows, les règles de protection s’appliquent à tous les jobs qui le déclarent. Vérifiez que chaque workflow qui doit pouvoir déployer possède les autorisations nécessaires (ex. : équipe *DevOps*).  

---

### 2.2 Stockage et récupération des secrets  

| Action | Syntaxe | Exemple concret |
|--------|---------|-----------------|
| Déclarer un secret | **Settings → Secrets → Actions** → *New repository secret* | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` |
| Lire un secret | `${{ secrets.NOM_DU_SECRET }}` | `aws configure set aws_access_key_id ${{ secrets.AWS_ACCESS_KEY_ID }}` |
| Masquage automatique | Tout texte issu d’une variable `secrets.*` est remplacé par `***` dans les logs. | Aucun besoin d’appeler `::add-mask::`. |

**Piège** : les secrets sont **en clair** dans le code source s’ils sont interpolés dans une chaîne non‑protégée (ex. `echo "key=${{ secrets.MY_KEY }}"`). Utilisez toujours le format `${{ secrets.MY_KEY }}` directement dans les arguments des actions ou dans les scripts, jamais dans une variable d’environnement qui serait affichée par `set -x`.  

---

### 2.3 Cache des dépendances  

#### 2.3.1 Principe de `actions/cache`  

```yaml
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: >-
      pip-${{ runner.os }}-${{ hashFiles('requirements.txt') }}
    restore-keys: |
      pip-${{ runner.os }}-
```

- **`path`** : répertoire à mettre en cache.  
- **`key`** : chaîne unique ; on utilise `hashFiles` sur le fichier qui décrit les dépendances.  
- **`restore-keys`** : préfixe de récupération en cas d’absence de clé exacte (ex. version mineure différente).  

#### 2.3.2 Cache des modèles pré‑entraînés  

```yaml
- name: Cache HuggingFace models
  uses: actions/cache@v3
  with:
    path: ${{ env.HF_HOME }}/.cache
    key: >-
      hf-model-${{ runner.os }}-${{ hashFiles('model_requirements.txt') }}
    restore-keys: |
      hf-model-${{ runner.os }}-
```

- `HF_HOME` : variable d’environnement définie plus bas (`env:`).  
- Le cache évite de retélécharger les gros blobs à chaque run.  

**Piège** : la taille maximale d’un cache est limitée ; un cache qui dépasse cette limite échoue silencieusement et le job continue sans cache. Surveillez la taille avec `du -sh ${{ env.HF_HOME }}/.cache` dans un step de debug.  

---

### 2.4 Gestion des artefacts  

| Action | Usage | Exemple |
|--------|-------|---------|
| `actions/upload-artifact` | Conserver un fichier ou un répertoire entre jobs ou pour le téléchargement post‑run. | `path: coverage.xml` |
| `actions/download-artifact` | Récupérer un artefact produit par un job antérieur du même workflow. | `name: coverage-report` |

```yaml
# Job 1 – tests
- name: Run pytest & generate coverage
  run: |
    pytest --cov=src --cov-report=xml
- name: Upload coverage artifact
  uses: actions/upload-artifact@v3
  with:
    name: coverage-report
    path: coverage.xml
```

```yaml
# Job 2 – reporting
needs: test
- name: Download coverage artifact
  uses: actions/download-artifact@v3
  with:
    name: coverage-report
    path: ./artifacts
- name: Publish SARIF to GitHub
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: ./artifacts/coverage.xml
```

**Piège** : les artefacts sont conservés pendant une période par défaut. Un job qui dépend d’un artefact produit il y a longtemps échouera. Planifiez le nettoyage ou la régénération régulière.  

---

### 2.5 Variables d’environnement de workflow et expressions conditionnelles  

```yaml
env:
  PYTHON_VERSION: "3.11"
  HF_HOME: ${{ runner.temp }}/hf_cache   # répertoire temporaire du runner
```
---

## Module 3 — contenu

## Module 3 – Intégrer les tests automatisés d’applications IA  

### 1. Objectif mesurable  
À l’issue du module, le participant doit :  

* Ajouter à son pipeline GitHub Actions l’exécution de suites **unitaires** (`pytest`), **d’intégration** et de **validation de données** (`great_expectations` ou `pandera`).  
* Faire échouer le workflow dès qu’une régression (test qui retourne un code différent de 0 ou une couverture insuffisante) est détectée.  
* Produire des artefacts de rapport (JUnit XML, SARIF) utilisables dans l’interface GitHub.  

---

### 2. Concepts indispensables  

| Concept | Description technique vérifiable |
|--------|-----------------------------------|
| **pytest** | Framework de test Python >= 6.2.5. Les tests sont découverts automatiquement dans les fichiers `test_*.py` ou `*_test.py`. |
| **pytest‑cov** | Plugin qui ajoute l’option `--cov=src` et génère `coverage.xml` (format Cobertura) et `htmlcov/`. |
| **great_expectations** | Bibliothèque de validation de données ≥ 0.15.0. Un *expectation suite* est stockée sous `great_expectations/expectations/`. |
| **pandera** | Alternative légère (≥ 0.10.0) qui utilise des schémas `DataFrameSchema`. |
| **matrix strategy** | Permet d’exécuter le même job sur plusieurs versions de Python (`3.8`, `3.9`, `3.10`, `3.11`) et sur des runners avec GPU (`runs-on: self-hosted` + `labels: [gpu]`). |
| **actions/upload-artifact** | Publie les fichiers générés (`coverage.xml`, `junit.xml`, `expectations_report.html`) comme artefacts du run. |
| **actions/upload-sarif** | Publie un fichier SARIF (`pytest-sarif`) pour que GitHub Code Scanning affiche les résultats dans l’onglet *Security*. |
| **continue‑on‑error** | Force le job à poursuivre les étapes suivantes même si une étape échoue (utile pour publier les artefacts avant le `fail`). |
| **if: failure()** | Condition d’exécution d’une étape uniquement en cas d’échec du job précédent. |
| **coverage‑fail‑under** | Option `--cov-fail-under` qui fait échouer `pytest` si la couverture globale est insuffisante. |

---

### 3. Implémentation pas à pas  

#### 3.1. Structure du dépôt  

```
repo/
├─ src/                     # code IA
│   └─ model.py
├─ tests/
│   ├─ unit/
│   │   └─ test_model.py
│   └─ integration/
│       └─ test_pipeline.py
├─ data/
│   └─ raw/
│       └─ sample.csv
├─ great_expectations/
│   ├─ expectations/
│   │   └─ sample_expectations.json
│   └─ checkpoints/
│       └─ sample_checkpoint.yml
├─ pyproject.toml           # dépendances (pytest, great_expectations, pandera, pytest-cov, pytest-sarif)
└─ .github/
    └─ workflows/
        └─ ci.yml
```

#### 3.2. Dépendances à déclarer (`pyproject.toml`)

```toml
[project]
name = "my-ia-app"
version = "0.1.0"
requires-python = ">=3.8"

[project.dependencies]
pandas = "^2.2"
numpy = "^1.26"

[project.optional-dependencies]
test = [
    "pytest>=6.2.5",
    "pytest-cov>=4.1",
    "pytest-sarif>=0.2.0",
    "great_expectations>=0.15.0",
    "pandera>=0.10.0",
]
```

*Installation dans le workflow* : `pip install .[test]`.

#### 3.3. Exemple de workflow complet (`.github/workflows/ci.yml`)

```yaml
name: CI – Tests IA

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  workflow_dispatch:

jobs:
  test:
    # 1️⃣ Stratégie de matrice : plusieurs versions Python, GPU optionnel
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
        include:
          - python-version: 3.11
            runner: self-hosted
            labels: [gpu, ubuntu-latest]
          - python-version: 3.8
            runner: ubuntu-latest
            labels: [ubuntu-latest]
    runs-on: ${{ matrix.runner || 'ubuntu-latest' }}
    name: Tests (Python ${{ matrix.python-version }}${{ matrix.labels && ' + GPU' || '' }})

    # 2️⃣ Variables d’environnement globales
    env:
      PYTHONPATH: ${{ github.workspace }}/src
      DATA_PATH: ${{ github.workspace }}/data/raw

    steps:
      # ----------------------------------------------------------------------
      # 0️⃣ Checkout du code source
      - name: Checkout repository
        uses: actions/checkout@v4

      # 1️⃣ Installation de la version Python demandée
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      # 2️⃣ Cache des dépendances
      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('pyproject.toml') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      # 3️⃣ Installation du projet et des dépendances de test
      - name: Install project with test extras
        run: |
          python -m pip install --upgrade pip
          pip install .[test]

      # 4️⃣ Lancement des tests unitaires avec couverture et génération de SARIF
      - name: Run pytest with coverage and SARIF output
        run: |
          pytest --cov=src --cov-report=xml --cov-report=html \
                 --junitxml=junit.xml \
                 --sarif-file=pytest.sarif

      # 5️⃣ Publication des artefacts de test
      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: htmlcov/

      -
---

## Module 4 — contenu

## Module 4 – Déployer automatiquement des modèles IA  

### 4.1. Construction d’image Docker avec `docker/build-push-action`

| Étape | Action GitHub | Description | Points de contrôle |
|------|---------------|-------------|---------------------|
| 1️⃣ | `docker/setup-buildx-action` | Active BuildKit et crée un builder multi‑plateforme. | Vérifier que `docker version` renvoie `BuildKit` activé. |
| 2️⃣ | `docker/login-action` | Authentifie le runner auprès du registre (Docker Hub ou GHCR). | Le secret `DOCKERHUB_TOKEN` ou `GHCR_TOKEN` doit être **en‑clair** (`${{ secrets.GHCR_TOKEN }}`). |
| 3️⃣ | `docker/build-push-action` | Construit l’image, la tague et la pousse. | Utiliser les **labels** `org.opencontainers.image.version` et `org.opencontainers.image.revision`. |

#### Exemple de workflow complet (Docker Hub)

```yaml
name: Build & Push Model Image

on:
  push:
    tags:
      - 'v*'               # déclenchement sur les tags de version (ex. v1.2.0)

jobs:
  build-image:
    runs-on: ubuntu-latest
    permissions:
      contents: read          # lecture du repo
      packages: write        # push vers Docker Hub
    steps:
      # 1️⃣ Checkout du code
      - name: Checkout repository
        uses: actions/checkout@v4

      # 2️⃣ Setup Buildx (multi‑arch)
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      # 3️⃣ Login à Docker Hub (secret pré‑créé)
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USER }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      # 4️⃣ Build & push
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USER }}/my-ml-model:${{ github.ref_name }}
            ${{ secrets.DOCKERHUB_USER }}/my-ml-model:latest
          labels: |
            org.opencontainers.image.title=My ML Model
            org.opencontainers.image.version=${{ github.ref_name }}
            org.opencontainers.image.revision=${{ github.sha }}
          cache-from: type=registry,ref=${{ secrets.DOCKERHUB_USER }}/my-ml-model:cache
          cache-to: type=registry,ref=${{ secrets.DOCKERHUB_USER }}/my-ml-model:cache,mode=max
```

*Commentaires*  
- `github.ref_name` vaut le nom du tag (`v1.2.0`).  
- Le cache Docker (`cache-from` / `cache-to`) accélère les builds incrémentaux.  
- Le `push: true` indique à l’action de pousser l’image après le build.  

#### Variante GHCR (GitHub Container Registry)

```yaml
      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GHCR_TOKEN }}

      - name: Build & push to GHCR
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository_owner }}/my-ml-model:${{ github.ref_name }}
```

### 4.2. Authentification aux registres

| Registre | Secret requis | Scope d’accès dans le workflow |
|----------|--------------|--------------------------------|
| Docker Hub | `DOCKERHUB_USER` + `DOCKERHUB_TOKEN` | `packages: write` |
| GHCR | `GHCR_TOKEN` (PAT avec `write:packages`) | `packages: write` |
| Amazon ECR | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` + `AWS_REGION` | `id-token: write` (si OIDC) |

**Piège** : le token Docker Hub expiré bloque le push sans message explicite dans les logs. Vérifier la date d’expiration dans **Docker Hub → Security → Personal Access Tokens**.

### 4.3. Déploiement Kubernetes avec `kubectl`  

#### 4.3.1. Prérequis du runner

```yaml
- name: Install kubectl
  uses: azure/setup-kubectl@v3
  with:
    version: 'v1.28.0'   # version compatible avec votre cluster
```

#### 4.3.2. Authentification OIDC (GitHub → GKE / EKS)

```yaml
- name: Configure GKE credentials
  uses: google-github-actions/get-gke-credentials@v2
  with:
    project_id: ${{ secrets.GCP_PROJECT }}
    location: ${{ secrets.GKE_ZONE }}
    cluster_name: ${{ secrets.GKE_CLUSTER }}
```

> **Note** : depuis novembre 2023, GitHub propose l’authentification OIDC native ; il suffit d’ajouter le **service account** dans GCP/AWS avec la bonne **federated identity** et de déclarer `id-token: write` dans `permissions`.

#### 4.3.3. Manifestes Kubernetes (kustomize)

Structure du répertoire `k8s/` :

```
k8s/
├─ base/
│   ├─ deployment.yaml
│   └─ service.yaml


---

## Module 5 — contenu

## Module 5 – Sécuriser, monitorer et assurer la conformité des pipelines CI/CD IA  

### Objectif mesurable  
À l’issue du module, le participant intègre dans le workflow :  
* un scan de sécurité du code (CodeQL) ;  
* un scan de vulnérabilités des dépendances (Trivy) ;  
* une vérification de conformité de licence (license‑check) ;  
* un test de dérive de modèle (détection de drift) ;  
* une stratégie de rollback automatisé lorsqu’une étape critique échoue, avec approbation manuelle pour le déploiement en production.  

---

## 1. Scan de sécurité du code avec CodeQL  

| Étape | Action GitHub | Description |
|------|---------------|-------------|
| 1 | `actions/checkout@v4` | Récupère le dépôt. |
| 2 | `github/codeql-action/init@v2` | Initialise la base de données CodeQL pour le langage ciblé (`python`). |
| 3 | `github/codeql-action/analyze@v2` | Exécute les requêtes de sécurité par défaut et produit un rapport exploitable dans l’onglet **Security**. |

**Points de vérification**  
* Le fichier `codeql.yml` doit déclarer `language: python`.  
* Le job doit être `runs-on: ubuntu-latest` et disposer d’un `permissions: security-events: write`.  

---

## 2. Scan de vulnérabilités des dépendances avec Trivy  

Trivy analyse les images Docker et les fichiers de lock (`requirements.txt`, `poetry.lock`).  

```yaml
# .github/workflows/ci-security.yml (extrait)
- name: Scan des dépendances Python avec Trivy
  uses: aquasecurity/trivy-action@0.12.0
  with:
    scan-type: "fs"
    ignore-unfixed: true          # ne signale que les vulnérabilités corrigées
    severity: "CRITICAL,HIGH"
    format: "sarif"
    output: "trivy-results.sarif"
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

* Le rapport SARIF est automatiquement publié dans l’onglet **Security** grâce à `upload-sarif`.  
* `ignore-unfixed` évite les faux positifs sur des CVE non corrigés dans les versions futures.  

---

## 3. Vérification de conformité de licence  

Utiliser `github/licensee-action` (ou `fossology`) pour s’assurer que toutes les dépendances respectent la politique d’entreprise (ex. : pas de GPL‑3).  

```yaml
- name: Analyse des licences
  uses: github/licensee-action@v2
  with:
    fail-on: "non-permitted"
    permitted-licenses: "MIT,Apache-2.0,BSD-3-Clause"
```

* Le job échoue si une dépendance possède une licence non autorisée.  

---

## 4. Détection de dérive de modèle (model drift)  

Le drift est détecté en comparant les statistiques de jeu de données d’entraînement et de production. Exemple avec **Pandas** et **SciPy** :

```python
# scripts/detect_drift.py
"""
Détecte le drift entre deux jeux de données CSV.
Renvoie le code de sortie 0 si aucune dérive détectée, 1 sinon.
"""
import sys
import pandas as pd
from scipy.stats import ks_2samp

def load(path):
    return pd.read_csv(path)

def ks_test(col_train, col_prod):
    """Kolmogorov‑Smirnov test, seuil p < 0.01."""
    stat, p = ks_2samp(col_train, col_prod)
    return p < 0.01

def main(train_path, prod_path, threshold=0.01):
    train = load(train_path)
    prod = load(prod_path)

    drifted = []
    for col in train.select_dtypes(include=["float", "int"]).columns:
        if ks_test(train[col], prod[col]):
            drifted.append(col)

    if drifted:
        print(f"Drift détecté sur les colonnes : {', '.join(drifted)}")
        sys.exit(1)
    else:
        print("Aucun drift détecté.")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python detect_drift.py <train.csv> <prod.csv>")
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
```

Intégration dans le workflow :

```yaml
- name: Détection de drift
  run: |
    python -m pip install pandas scipy
    python scripts/detect_drift.py data/train_features.csv