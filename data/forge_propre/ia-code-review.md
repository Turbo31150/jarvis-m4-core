# Code Review IA Automatisé

> Référence `ia-code-review`

## Plan

## Module 1 – Architecture d’un système de revue de code IA  
**Objectif mesurable :** Concevoir, sur papier, l’architecture complète d’un outil de revue de code automatisée capable d’analyser du code Python, JavaScript ou Java et de produire un rapport structuré.  
**Notions couvertes**  
- Modèle client‑serveur : API REST, file d’attente (RabbitMQ) et workers de traitement.  
- Sélection et déploiement de modèles de langage (ex. : CodeBERT, GPT‑4o) via Hugging Face Transformers.  
- Gestion du contexte de projet : parsing du graphe d’imports, résolution de dépendances avec `pip`, `npm` ou `Maven`.  
- Stratégies de scalabilité : mise en cache des embeddings, partitionnement des requêtes, autoscaling Kubernetes.  

## Module 2 – Extraction et pré‑traitement des artefacts source  
**Objectif mesurable :** Implémenter un pipeline qui, à partir d’un dépôt Git, génère des tokens, AST et métriques de complexité pour chaque fichier, avec un taux de couverture élevé sur un jeu de dépôts.  
**Notions couvertes**  
- Analyse lexicale et syntaxique avec `tree-sitter` et `javaparser`.  
- Calcul de métriques cyclomatiques, profondeur d’imbrication et duplication de code (CPD).  
- Normalisation des identifiants (camelCase ↔ snake_case) et anonymisation des literals.  
- Sérialisation des artefacts en JSONL pour l’alimentation du modèle IA.  

## Module 3 – Prompting et fine‑tuning de modèles de revue de code  
**Objectif mesurable :** Produire, à partir d’un jeu d’entraînement de plusieurs milliers de revues humaines, un modèle capable de générer des commentaires pertinents avec un bon score BLEU et un faible taux de faux positifs.  
**Notions couvertes**  
- Construction de prompts chainés (system, user, assistant) pour guider la génération.  
- Techniques de fine‑tuning LoRA et QLoRA sur modèles de grande taille.  
- Métriques d’évaluation : BLEU, ROUGE‑L, précision/recall sur catégories de défauts (sécurité, performance, lisibilité).  
- Gestion des biais de données (over‑representation de styles de code).  

## Module 4 – Génération et structuration du rapport de revue  
**Objectif mesurable :** Développer un format de sortie (Markdown + JSON) qui classe les commentaires par sévérité et propose des correctifs automatiques, avec un taux d’acceptation utilisateur élevé lors d’un test A/B.  
**Notions couvertes**  
- Taxonomie de défauts (OWASP Top 10, SonarQube rules).  
- Priorisation dynamique basée sur le score de criticité et la fréquence d’occurrence.  
- Synthèse de correctifs : génération de diff via `libcst` ou `jdt.core`.  
- Export multi‑format : Markdown, SARIF, GitHub Checks API.  

## Module 5 – Intégration continue et gouvernance du système IA  
**Objectif mesurable :** Intégrer l’outil dans un pipeline CI/CD (GitHub Actions ou GitLab CI) et mettre en place un tableau de

---

## Module 1 — contenu

## 1.1 Modèle client‑serveur

| Élément | Rôle | Technologie typique | Points de contrôle |
|--------|------|---------------------|--------------------|
| **Client** | Envoie le code source (ou un identifiant de commit) et récupère le rapport. | Front‑end web (React) ou CLI (Python `requests`). | Authentification JWT, taille maximale du payload (ex. 5 MiB). |
| **API Gateway** | Expose une API REST, valide le schéma, orchestre les appels. | FastAPI / Express.js + OpenAPI. | Validation du JSON, limitation de débit (rate‑limit). |
| **Broker** | Découple la réception du client et le traitement lourd. | RabbitMQ (exchange `direct`, queue `code_review_tasks`). | Accusé de réception (`ack`) uniquement après que le worker a stocké le résultat. |
| **Worker** | Décode le message, prépare le contexte, invoque le modèle, persiste le rapport. | Python 3.11, `pika` (RabbitMQ), `transformers` (CodeBERT, GPT‑4o). | Chargement du modèle en singleton, gestion du GPU (CUDA_VISIBLE_DEVICES). |
| **Store** | Persistance des artefacts (AST, métriques, rapports). | PostgreSQL + JSONB, ou MinIO (objet). | Indexation sur `commit_sha`, TTL (ex. 30 jours). |
| **Cache** | Accélère les requêtes redondantes (embeddings, dépendances résolues). | Redis (hash `project_context:{sha}`) ou **Memcached**. | Invalidation lors d’un nouveau push. |
| **Scheduler / Autoscaler** | Ajuste le nombre de workers selon la charge. | Kubernetes HPA (Horizontal Pod Autoscaler) basé sur `rabbitmq_queue_messages_ready`. | Min = 1, Max = 10 (exemple). |

### 1.1.1 Flux de traitement

1. **POST** `/review` → API Gateway (FastAPI)  
   - Payload : `{ "repo_url": "...", "commit": "...", "language": "python" }`  
   - Vérifie le JWT, la taille, le format.  
   - Publie le message sur l’échange `code_review` avec la clé `task`.

2. **RabbitMQ** place le message dans la queue `code_review_tasks`.

3. **Worker** (déployé en pod) consomme le message :
   - Clone le dépôt (`git clone --depth 1 --branch <commit>`).  
   - Résout les dépendances (`pip install -r requirements.txt --target /tmp/deps`).  
   - Construit le graphe d’imports via `modulegraph` (Python) ou `npm ls` (JS).  
   - Sérialise le contexte dans Redis (`SET project_context:{sha} <json>`).  
   - Tokenise le code, génère les embeddings avec le modèle chargé (`model.encode(...)`).  
   - Formule le prompt (voir Module 3) et invoque le modèle (`model.generate(...)`).  
   - Stocke le rapport JSON dans PostgreSQL (`INSERT …`).  
   - Envoie un webhook ou met à jour le statut GitHub Checks.

4. **Client** interroge `/review/{id}` pour récupérer le rapport (polling ou webhook).

---

## 1.2 Déploiement du modèle de langage

```python
# file: model_loader.py
import os
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

_MODEL_NAME = os.getenv("MODEL_NAME", "microsoft/codebert-base")
_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_INSTANCE = None  # singleton

def get_model():
    """Retourne le modèle et le tokenizer déjà chargés."""
    global _INSTANCE
    if _INSTANCE is None:
        # 1️⃣ Téléchargement (exécuté une seule fois, cache HF)
        tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
        model = AutoModelForCausalLM.from_pretrained(
            _MODEL_NAME,
            torch_dtype=torch.float16 if _DEVICE.type == "cuda" else torch.float32,
            device_map="auto"  # répartit les couches sur les GPUs disponibles
        )
        _INSTANCE = (model, tokenizer)
    return _INSTANCE
```

*Commentaires*  

* `torch_dtype` : en GPU on privilégie `float16` pour réduire la bande passante mémoire.  
* `device_map="auto"` (Transformers ≥ 4.30) évite de coder manuellement la répartition des couches.  
* Le singleton garantit qu’un seul processus charge le modèle ; les workers multiples utilisent le même fichier de poids partagé (lecture‑seule).  

---

## 1.3 Gestion du contexte de projet

### 1.3.1 Analyse du graphe d’imports (Python)

```python
# file: import_graph.py
import ast
from collections import defaultdict
from pathlib import Path

def build_import_graph(root: Path) -> dict[str, set[str]]:
    """
    Parcourt récursivement root/*.py et retourne un dict:
        module_name -> {imported_module, …}
    """
    graph = defaultdict(set)

    for py_file in root.rglob("*.py"):
        module = py_file.relative_to(root).with_suffix("").as_posix().replace("/", ".")
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue  # ignore files that cannot be parsed
        for



---

## Module 2 — contenu

## 2.1. Vue d’ensemble du pipeline d’extraction  

| Étape | Outil / bibliothèque | Entrée | Sortie | Raison |
|------|----------------------|--------|--------|--------|
| 2.1.1 Clonage du dépôt | `git clone --depth 1 <url>` | URL Git | Répertoire local | Limite le trafic réseau, conserve l’historique minimal. |
| 2.1.2 Détection des fichiers sources | `os.walk` + filtres d’extension (`.py`, `.js`, `.java`) | Arborescence | Liste de chemins absolus | Nécessaire pour alimenter les analyseurs spécifiques. |
| 2.1.3 Tokenisation & AST | **Tree‑sitter** (Python, JS) ; **javaparser** (Java) | Contenu brut | Tokens + AST (JSON) | Permet une analyse syntaxique fiable, indépendamment du formatage. |
| 2.1.4 Métriques de complexité | **radon** (Python) ; **escomplex** (JS) ; **java‑metrics** (Java) | AST | Cyclomatic, profondeur d’imbrication, lignes de code, etc. | Quantifie la maintenabilité. |
| 2.1.5 Détection de duplication | **jscpd** (multi‑langage) | Fichiers tokenisés | Blocs dupliqués (début, fin, fichier) | Identifie le copy‑paste, source fréquente de bugs. |
| 2.1.6 Normalisation & anonymisation | Scripts Python custom | Tokens/AST | Identifiants normalisés, littéraux remplacés par `<STR>`, `<NUM>` | Réduit le bruit lexical pour le modèle IA. |
| 2.1.7 Sérialisation JSONL | `jsonlines` | Dictionnaire d’attributs | Un fichier `.jsonl` (une ligne = un fichier) | Format d’entrée standard pour les modèles de langage. |

> **Note technique** : la combinaison *Tree‑sitter + jscpd* garantit que les duplications sont détectées sur la base d’AST et non de texte brut, ce qui évite les faux positifs liés aux différences de mise en forme.

---

## 2.2. Installation des dépendances  

```bash
# Python 3.9+ (vérifié avec pip 23.3)
python -m venv .venv && source .venv/bin/activate
pip install -U pip setuptools wheel
pip install gitpython tree-sitter==0.20.1 tree_sitter_languages==0.3.0 \
            radon==5.1.0 jscpd==3.5.0 jsonlines==3.1.0

# Java parser (javaparser) via Maven (installé localement)
mvn dependency:get -Dartifact=com.github.javaparser:javaparser-core:3.25.4
```

*Toutes les versions citées sont les dernières stables au 14 août 2026 et sont compatibles avec les OS Linux x86_64 et macOS arm64.*

---

## 2.3. Implémentation détaillée (Python)

### 2.3.1. Découverte des fichiers source  

```python
import os
from pathlib import Path
from typing import List

def list_source_files(root: Path) -> List[Path]:
    """Retourne la liste des fichiers .py, .js, .java sous `root`."""
    exts = {".py", ".js", ".java"}
    files = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            p = Path(dirpath) / f
            if p.suffix.lower() in exts:
                files.append(p)
    return files
```

### 2.3.2. Tokenisation et génération d’AST avec Tree‑sitter  

```python
from tree_sitter import Language, Parser
import json

# Construction du binaire Tree‑sitter (une seule fois)
LANG_SO = Path("build/my-languages.so")
if not LANG_SO.exists():
    Language.build_library(
        # Chemin du binaire à créer
        str(LANG_SO),
        # Répertoires contenant les grammaires
        [
            "tree-sitter-python",
            "tree-sitter-javascript",
        ],
    )
PY_LANG = Language(str(LANG_SO), "python")
JS_LANG = Language(str(LANG_SO), "javascript")

def parse_with_tree_sitter(file_path: Path):
    """Renvoie un dict contenant tokens et AST au format JSON."""
    text = file_path.read_text(encoding="utf-8")
    parser = Parser()
    parser.set_language(PY_LANG if file_path.suffix == ".py" else JS_LANG)
    tree = parser.parse(bytes(text, "utf8"))
    # Extraction récursive des nœuds (exemple simplifié)
    def node_to_dict(node):
        return {
            "type": node.type,
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
            "children": [node_to_dict(c) for c in node.children],
        }
    ast = node_to_dict(tree.root_node)
    # Tokens : on parcourt les feuilles
    tokens = [t.text



---

## Module 3 — contenu

## Module 3 – Prompting et fine‑tuning de modèles de revue de code  

### 3.1 Prompting chainé (system / user / assistant)

| Niveau | Rôle | Exemple de texte |
|--------|------|-------------------|
| **system** | Définit le comportement général du modèle. | `You are a code reviewer specialized in Python, JavaScript and Java. You must point out security, performance and readability issues, and suggest a minimal diff to fix each issue.` |
| **user** | Fournit le contexte du fichier à analyser. | ```json { "filename": "utils.py", "language": "python", "content": "def foo(bar):\n    return bar * 2" }``` |
| **assistant** | Produit la réponse structurée. | ```json { "issues": [ { "line": 1, "severity": "low", "category": "readability", "message": "Function name `foo` is not descriptive.", "suggestion": "Rename to `double_value`." } ] }``` |

#### Construction dynamique du prompt  
```python
def build_prompt(system_msg, file_meta, extra_context=None):
    """
    Assemble a chain‑of‑messages compatible with OpenAI‑compatible APIs.
    """
    messages = [{"role": "system", "content": system_msg}]
    user_content = f"""File: {file_meta["filename"]}\nLanguage: {file_meta["language"]}\n---\n{file_meta["content"]}"""
    if extra_context:
        user_content = extra_context + "\n\n" + user_content
    messages.append({"role": "user", "content": user_content})
    return messages
```

*Vérifiable* : la fonction renvoie une liste de dictionnaires conforme à la spécification de l’API `chat/completions` d’OpenAI (ou d’Anthropic).  

### 3.2 Fine‑tuning LoRA / QLoRA

#### 3.2.1 Pourquoi LoRA  
- **Low‑Rank Adaptation (LoRA)** ajoute deux matrices de rang *r* (souvent 4‑16) aux poids linéaires du modèle.  
- Le nombre de paramètres entraînés est `2 * r * d` (d = dimension du poids).  
- Compatible avec les optimisations de quantisation (QLoRA) qui stockent le modèle en 4‑bit tout en gardant la précision du gradient.

#### 3.2.2 Environnement minimal

```bash
# Python ≥3.9, torch ≥2.0, transformers ≥4.35, peft ≥0.5.0, accelerate ≥0.27
pip install torch transformers peft datasets accelerate
```

#### 3.2.3 Script de fine‑tuning (exemple complet)

```python
# fine_tune_lora.py
import os
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_int8_training

# 1️⃣ Chargement du jeu de données
# Le jeu doit être au format JSONL : {"prompt": "...", "completion": "..."}
dataset = load_dataset("json", data_files={"train": "train_reviews.jsonl",
                                          "validation": "val_reviews.jsonl"},
                       split={"train": "train", "validation": "validation"})

# 2️⃣ Tokenizer
model_name = "mistralai/Mistral-7B-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
tokenizer.pad_token = tokenizer.eos_token  # Mistral n’a pas de pad_token

# 3️⃣ Modèle en 4‑bit (QLoRA)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_4bit=True,
    device_map="auto",
    torch_dtype="auto"
)
model = prepare_model_for_int8_training(model)

# 4️⃣ Configuration LoRA
lora_cfg = LoraConfig(
    r=8,               # rang
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],  # modules linéaires de l’attention
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_cfg)

# 5️⃣ Pré‑traitement (tokenisation)
def tokenize_fn(example):
    # On concatène prompt + completion + EOS
    full = example["prompt"] + example["completion"] + tokenizer.eos_token
    tokenized = tokenizer(full, truncation=True, max_length=1024, padding="max_length")
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

tokenized_ds = dataset.map(tokenize_fn, batched=False, remove_columns=dataset["train"].column_names)

# 6️⃣ Arguments d’entraînement
training_args = TrainingArguments(
    output_dir="./lora_mistral",
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    learning_rate=2e-4,
    fp16=False,               # 4‑bit gère déjà la précision
    logging_steps=50,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    report_to="none"
)

# 7️⃣ Trainer
from transformers import Trainer

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_ds["train"],
    eval_dataset=tokenized_ds["validation"],
    tokenizer=tokenizer,
)

# 8️⃣ Lancement
trainer.train()
model.save_pretrained("./lora_mistral_final")
```

---

## Module 4 — contenu

## 4.1. Taxonomie des défauts  

| Catégorie | Sous‑catégorie (exemple) | Référence | Niveau de sévérité recommandé* |
|-----------|--------------------------|-----------|------------------------------|
| **Sécurité** | Injection SQL, XSS, deserialization unsafe | OWASP Top 10 A1‑A10 | **Critical** |
| **Fiabilité** | Ressource non fermée, fuite de mémoire | SonarQube RSPEC‑1128 | **High** |
| **Performance** | Boucle O(n²), appel réseau bloquant | SonarQube RSPEC‑138 | **Medium** |
| **Lisibilité** | Nom de variable non descriptif, fonction trop longue | SonarQube RSPEC‑100 | **Low** |
| **Maintenabilité** | Duplication de code, dépendance cyclique | SonarQube RSPEC‑1110 | **Medium** |

\*Le niveau de sévérité est calculé par la formule :

```
severity = base_severity(category) * (1 + 0.1 * occurrence_count) * criticality_factor
```

- `base_severity` : 5 (Critical), 4 (High), 3 (Medium), 2 (Low)  
- `criticality_factor` : 1.0 pour les projets « production », 0.8 pour les prototypes.  

Le score final (1‑5) est arrondi à l’entier le plus proche et mappé aux libellés ci‑dessus.

---

## 4.2. Priorisation dynamique  

1. **Collecte des métriques**  
   - `occurrence_count` : nombre d’occurrences du même type de défaut dans le même commit.  
   - `impact_score` : poids attribué par la taxonomie (Critical = 5, …, Low = 2).  
   - `age_days` : nombre de jours depuis l’introduction du fichier (extrait du `git log`).  

2. **Calcul du score de priorité**  

```python
def priority_score(impact_score: int, occurrence: int, age_days: int) -> float:
    """Renvoie un score compris entre 0 et 100."""
    # Normalisation simple
    occ_factor = min(occurrence, 10) / 10.0          # 0‑1
    age_factor = min(age_days, 180) / 180.0        # 0‑1
    return 100 * (impact_score / 5.0) * (0.6 + 0.4 * occ_factor) * (0.7 + 0.3 * age_factor)
```

3. **Tri**  
   ```python
   sorted_issues = sorted(issues, key=lambda i: i["priority"], reverse=True)
   ```

4. **Seuil d’affichage**  
   - `priority >= 70` → affichage en **bloc critique** (exigence de correction avant merge).  
   - `40 ≤ priority < 70` → **bloc recommandé** (suggestion).  
   - `priority < 40` → **bloc informatif** (commentaire uniquement).

---

## 4.3. Schéma JSON de sortie  

```json
{
  "run_id": "2024-08-14T12:34:56Z",
  "repository": "org/example‑repo",
  "commit_sha": "a1b2c3d4",
  "generated_at": "2024-08-14T12:35:02Z",
  "issues": [
    {
      "file_path": "src/main.py",
      "line_start": 42,
      "line_end": 45,
      "severity": "Critical",
      "category": "Security",
      "subcategory": "SQL Injection",
      "message": "Utilisation d’une requête SQL concaténée avec une variable non échappée.",
      "priority": 87.3,
      "suggested_fix": {
        "type": "diff",
        "diff": "@@ -42,6 +42,7 @@\n-    cursor.execute(\"SELECT * FROM users WHERE id = \" + user_id)\n+    cursor.execute(\"SELECT * FROM users WHERE id = %s\", (user_id,))"
      },
      "metadata": {
        "occurrence": 3,
        "age_days": 27,
        "rule_id": "OWASP-A1"
      }
    }
  ],
  "summary": {
    "total_issues": 12,
    "by_severity": {"Critical": 2, "High": 4, "Medium": 5, "Low": 1}
  }
}
```

- Le champ `suggested_fix.diff` doit être conforme au format **unified diff** (RFC 5789).  
- Le champ `metadata.rule_id` référence la règle officielle (ex. : `OWASP-A1`, `RSPEC-1128`).  

---

## 4.4. Génération du rapport Markdown  

```markdown
# Rapport de revue de code – run 2024‑08‑14T12:34:56Z

## 📊 Synthèse
- **Total** : 12 défauts
- **Critical** : 2 **High** : 4 **Medium** : 5 **Low** : 1

## 🚨 Bloc critique
### src/main.py:42‑45
**Sévérité** : Critical – **



---

## Module 5 — contenu

## Module 5 – Intégration continue et gouvernance du système IA  

### 5.1 Architecture CI/CD pour la revue de code IA  

| Élément | Rôle | Implémentation concrète |
|--------|------|------------------------|
| **Repository** | Stockage du code source de l’application et du pipeline | GitHub (ou GitLab) avec branche `main` protégée |
| **Workflow** | Orchestration des jobs (checkout, build, analyse, reporting) | Fichier `.github/workflows/code-review.yml` (ou `.gitlab-ci.yml`) |
| **Docker image** | Environnement reproductible contenant le serveur d’inférence, le worker et les dépendances | `Dockerfile` basé sur `python:3.11-slim` + `pip install -r requirements.txt` |
| **Artefacts** | JSONL d’AST, métriques, rapports de revue | Stockés dans le job `artifacts` de GitHub Actions (max 10 GB) |
| **Cache** | Réduction du temps de chargement des modèles | `actions/cache@v3` sur le répertoire `~/.cache/huggingface` |
| **Secrets** | Jetons d’accès aux registres Docker, API keys | `secrets.GITHUB_TOKEN`, `secrets.DOCKERHUB_USERNAME`, `secrets.DOCKERHUB_TOKEN` |
| **Trigger** | Lancement du pipeline à chaque PR ou push sur `main` | `on: [pull_request, push]` avec `branches: [main]` |
| **Notification** | Retour d’information dans la PR (checks, commentaires) | GitHub Checks API + `actions/github-script` |

---

### 5.2 Exemple complet de workflow GitHub Actions  

```yaml
# .github/workflows/code-review.yml
name: Code Review IA

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout du dépôt
        uses: actions/checkout@v4

      - name: Cache du modèle HuggingFace
        uses: actions/cache@v3
        with:
          path: ~/.cache/huggingface
          key: hf-${{ runner.os }}-${{ hashFiles('requirements.txt') }}

      - name: Construction de l’image Docker
        run: |
          docker build -t code-review:ci .
      
      - name: Lancer le worker de revue
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          docker run --rm \
            -e GITHUB_TOKEN=$GITHUB_TOKEN \
            -v ${{ github.workspace }}:/workspace \
            code-review:ci \
            python -m code_review.worker \
            --repo /workspace \
            --pr ${{ github.event.pull_request.number }}

      - name: Publier le rapport SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: reports/review.sarif.json
          category: "AI‑Code‑Review"

  cleanup:
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Supprimer les images locales
        run: docker image prune -af
```

**Commentaires du script**  

1. `actions/checkout@v4` récupère le code de la PR dans le répertoire de travail.  
2. Le cache `hf-…` évite de retélécharger les poids du modèle (ex. : `CodeBERT`) à chaque run.  
3. L’image Docker `code-review:ci` doit contenir :  
   - Python 3.11, `torch`, `transformers`, `tree-sitter`, `code_review` (package interne).  
   - Un serveur RabbitMQ ou un worker autonome qui consomme la file `code_review_queue`.  
4. Le container reçoit deux variables : le token GitHub (pour poster les checks) et le chemin du dépôt monté en volume.  
5. Le module `code_review.worker` exécute les étapes : extraction des artefacts, appel du modèle, génération du diff et écriture du fichier SARIF `reports/review.sarif.json`.  
6. `github/codeql-action/upload-sarif` rend le rapport visible dans l’onglet *Security* de la PR, mais il peut être utilisé pour tout type de défaut.  
7. Le job `cleanup` garantit la libération de l’espace disque, indispensable sur les runners partagés.  

---

### 5.3 Gestion des secrets et conformité  

| Secret | Valeur attendue | Pourquoi |
|--------|----------------|----------|
| `GITHUB_TOKEN` | Jeton d’accès limité au dépôt (automatiquement fourni) | Autorise la création de checks et de commentaires sans permission supplémentaire. |
| `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` | Identifiants du registre privé (si l’image n’est pas publique) | Permet le `docker pull` dans les runners. |
| `HF_API_TOKEN` | Token d’accès à HuggingFace (modèle privé) | Nécessaire si le modèle n’est pas public. |
| `SLACK_WEBHOOK_URL` (optionnel) | URL de webhook pour alertes CI | Facilite la remontée d’erreurs critiques (ex. : modèle non chargé). |

**Bonne pratique** : ne jamais logger les valeurs de ces secrets. Utiliser `::add-mask::` dans les scripts shell si un affichage accidentel est possible.

---

### 5.4 Gouvernance du modèle IA  

1. **Versionnage du modèle**  
   - Tag Docker `model-v1.2.0` correspond à la version du checkpoint (`codebert-base-mlm`).  
   - Stocker le hash du fichier `config.json` dans le fichier `model_manifest.yaml`.  

2. **Audit des prompts**  
   - Conserver chaque prompt utilisé (system, user, assistant) dans le répertoire `prompts/` versionné.  
   - Ajouter un test unitaires qui charge le prompt et vér