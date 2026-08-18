# Prompt Engineering Avancé

> Référence `prompt-engineering` · 39 €

## Plan

## Module 1 – Fondamentaux du Prompt Engineering

**Objectif d’apprentissage** : Être capable de concevoir, tester et itérer un prompt de base en respectant les critères de clarté, de concision et de contrôle de la température, avec un taux de réussite ≥ 80 % sur un jeu de 20 requêtes ciblées.  

**Notions couvertes**  
- Syntaxe et structure des prompts (instruction, contexte, contraintes)  
- Paramètres de génération (temperature, top‑p, max_tokens) et leurs effets mesurables  
- Méthodes de validation : tests unitaires de prompts avec `assert` sur la sortie  
- Gestion des biais de modèle via le wording et les exemples négatifs  

## Module 2 – Prompting avancé pour la programmation

**Objectif d’apprentissage** : Générer automatiquement du code fonctionnel dans au moins trois langages (Python, JavaScript, Rust) à partir d’une description fonctionnelle, avec un taux de succès de compilation ≥ 90 % sur 30 exercices.  

**Notions couvertes**  
- Prompting en chaîne (chain‑of‑thought) pour la décomposition de problèmes  
- Utilisation de « few‑shot » avec exemples de code annotés  
- Contrôle de style de code (PEP 8, linting) via instructions explicites  
- Gestion des dépendances et des imports dans les réponses du modèle  

## Module 3 – Prompt Engineering pour les données structurées

**Objectif d’apprentissage** : Produire des transformations de données (JSON ↔ CSV, schémas SQL) à partir de prompts, avec une précision de parsing ≥ 95 % sur un jeu de 50 cas réels.  

**Notions couvertes**  
- Formats de sortie explicites et validation JSON Schema  
- Prompting conditionnel pour le filtrage et l’agrégation de données  
- Utilisation de balises de démarcation (```json, ```csv) pour garantir le formatage  
- Techniques de désambiguïsation des champs ambigus  

## Module 4 – Optimisation et évaluation des prompts

**Objectif d’apprentissage** : Mettre en place un pipeline d’A/B testing automatisé pour comparer au moins trois variantes de prompts, et sélectionner la version offrant le meilleur score F1 (≥ 0,85) sur une tâche de classification texte.  

**Notions couvertes**  
- Métriques d’évaluation (BLEU, ROUGE, Exact Match, F1) appliquées aux réponses de modèle  
- Outils d’automatisation (Python `pytest`, `promptsource`, `OpenAI`/`Anthropic` SDK)  
- Techniques d’optimisation : prompt compression, token budgeting, “self‑refinement”  
- Analyse de variance (ANOVA) pour déterminer la significativité des différences  

## Module 5 – Intégration sécurisée et gouvernance des prompts

**Objectif d’apprentissage** : Déployer un service d’inférence capable de filtrer les prompts et les réponses selon une politique de sécurité définie, avec un taux de détection de contenus non conformes ≥ 99 % sur 1 000 requêtes test.  

**Notions couvertes**  
- Filtrage lexical et logique (regex, listes noires, listes blanches)  
- Mise en place de garde‑fous via “prompt

---

## Module 1 — contenu

## 1. Structure de base d’un prompt  

| Élément | Rôle | Exemple minimal |
|--------|------|-----------------|
| **Instruction** | Action attendue du modèle (verbe d’ordre). | `Résume le texte suivant en 3 phrases.` |
| **Contexte** | Données ou informations nécessaires à la tâche. | `Texte : « … »` |
| **Contraintes** | Limites de forme, de style ou de longueur. | `Maximum 200 caractères, sans ponctuation finale.` |

> **Règle 1** – L’ordre d’apparition doit être *instruction → contexte → contraintes*.  
> **Règle 2** – Chaque ligne se termine par un point ; les listes sont précédées de `-` ou de numéros.

### 1.1 Exemple complet  

```text
Instruction : Rédige un tweet promotionnel pour le nouveau smartphone X200.
Contexte : Le X200 possède un écran OLED 6,7", un processeur Snapdragon 8 Gen 2, et une batterie de 5000 mAh.
Contraintes : 280 caractères max, inclure le hashtag #X200, ton enthousiaste, éviter les superlatifs non vérifiables.
```

## 2. Paramètres de génération  

| Paramètre | Valeur typique | Effet observable |
|-----------|----------------|------------------|
| `temperature` | 0.0 – 1.0 (ex. 0.0, 0.2, 0.7) | 0.0 → réponses déterministes, 0.7 → plus de diversité, 1.0 → créativité maximale. |
| `top_p` (nucleus) | 0.8 – 1.0 (ex. 0.9) | Limite le vocabulaire aux tokens cumulant 90 % de probabilité. |
| `max_tokens` | 50 – 500 selon la tâche | Coupe la réponse à la longueur maximale. |
| `presence_penalty` | 0.0 – 2.0 (ex. 0.5) | Décourage la répétition de mots déjà présents dans le prompt. |

**Mesure** : Pour chaque paramètre, comparer le nombre moyen de tokens générés (`len(response["choices"][0]["text"].split())`) et le taux de variation (`std` sur 10 appels).  

## 3. Validation automatisée des prompts  

### 3.1 Test unitaire avec `assert`

```python
import json
import openai  # version 1.x, compatible avec l'API ChatCompletion

openai.api_key = "sk-..."

def call_model(prompt: str, **kwargs) -> str:
    """Enveloppe l’appel OpenAI et renvoie le texte brut."""
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        **kwargs,
    )
    return resp.choices[0].message.content.strip()

def test_resume():
    prompt = (
        "Instruction : Résume le texte suivant en 2 phrases.\n"
        "Contexte : Le texte décrit la montée en puissance de l’énergie solaire en Europe, "
        "avec un taux de croissance annuel de 12 % depuis 2015.\n"
        "Contraintes : 200 caractères max, sans abréviations."
    )
    answer = call_model(prompt, temperature=0.0, max_tokens=80)
    # 1. Vérifier la longueur
    assert len(answer) <= 200, "Réponse trop longue"
    # 2. Vérifier le nombre de phrases (détecté par le point final)
    assert answer.count('.') == 2, "Nombre de phrases incorrect"
    # 3. Vérifier l’absence d’abréviations (exemple : « vs », « etc. »)
    for bad in ["vs", "etc.", "i.e.", "e.g."]:
        assert bad not in answer.lower(), f"Abbreviation found: {bad}"

if __name__ == "__main__":
    test_resume()
    print("✅ Test résumé passé")
```

*Commentaires*  
- `temperature=0.0` garantit la reproductibilité du test.  
- `max_tokens` doit être supérieur à la longueur attendue + un buffer (≈ 20 %).  
- Les assertions sont explicites ; le message d’erreur indique la cause exacte.

### 3.2 Boucle de test sur un jeu de 20 requêtes  

```python
def batch_test(prompts, **kwargs):
    successes = 0
    for p, check in prompts:
        out = call_model(p, **kwargs)
        if check(out):
            successes += 1
    return successes / len(prompts)

# Exemple de jeu (2 éléments illustratifs)
test_set = [
    (
        "Instruction : Donne le prix moyen du Bitcoin le 1er janvier 2023.\nContraintes : réponse numérique uniquement.",
        lambda r: r.isdigit()
    ),
    (
        "Instruction : Traduis en français la phrase suivante.\nContexte : \"Artificial intelligence is transforming industry.\"\nContraintes : aucune ponctuation finale.",
        lambda r: r.endswith("industrie") and not r.endswith(".")
    ),
    # … 18 autres tuples (prompt, fonction de validation) …
]

score = batch_test(test_set, temperature=0.0, max_tokens=60)
assert score >= 0.80, f"Taux de réussite {score:.2f} < 80 %"
```

## 4. Gestion des biais via le wording  

| Biais fréquent | Symptom | Correction concrète |
|----------------|---------|---------------------|
| **Biais de genre** | Réponses systématiquement masculines. | Utiliser des pronoms neutres (`iel`, `celle‑ci`) ou

---

## Module 2 — contenu

## 2.1 Prompting en chaîne (Chain‑of‑Thought)  

| Étape | Action du prompt | Raison |
|------|------------------|--------|
| 1️⃣  | **Décrire le problème** en une phrase claire. | Fournit le contexte global au modèle. |
| 2️⃣  | **Décomposer** le problème en sous‑tâches numérotées. | Le modèle suit une logique séquentielle, ce qui réduit les hallucinations. |
| 3️⃣  | **Résoudre chaque sous‑tâche** séparément, en rappelant les résultats précédents. | Chaque réponse s’appuie sur les variables déjà créées. |
| 4️⃣  | **Assembler** le code final en réutilisant les fragments générés. | Garantit la cohérence globale. |
| 5️⃣  | **Vérifier** la syntaxe (lint) et les imports. | Empêche les erreurs de compilation. |

**Prompt type** (Python) :

```text
You are an expert Python developer. Write a function that computes the nth Fibonacci number using memoization.

1. Define the function signature.
2. Create a cache dictionary.
3. Implement the recursive logic that checks the cache before computing.
4. Return the result.
Provide only the code block, formatted as markdown ```python.
```

### Pourquoi ça marche  
- Le modèle reçoit une **structure explicite** (numérotation) qui agit comme un plan.  
- Chaque sous‑étape limite le **espace de recherche** du modèle, ce qui diminue la variance due à la température.  
- La consigne “Provide only the code block” élimine le texte superflu qui pourrait être interprété comme du code.

---

## 2.2 Few‑shot avec exemples annotés  

### Format du prompt

```text
# Exemple 1 – Tri d’une liste en Python
def sort_list(lst):
    """Return a new list with the elements of lst sorted in ascending order."""
    return sorted(lst)

# Exemple 2 – Lecture d’un fichier JSON en JavaScript
function readJson(path) {
  // Returns the parsed JSON object from a file at `path`.
  const fs = require('fs');
  const data = fs.readFileSync(path, 'utf8');
  return JSON.parse(data);
}
```

**Prompt complet** (générer une fonction Rust qui calcule le PGCD) :

```text
Given the following annotated examples in Python and JavaScript, write an equivalent function in Rust that computes the greatest common divisor (GCD) of two unsigned 64‑bit integers using Euclid's algorithm. Include a doc‑comment, proper `use` statements, and a unit test named `test_gcd`. Return only a markdown code block ```rust.
```

### Points clés  

| Élément | Rôle |
|---------|------|
| **Annotation** (`"""doc"""` ou `// comment`) | Guide le style de documentation du modèle. |
| **Import explicite** (`use std::cmp::max;`) | Force le modèle à inclure les dépendances nécessaires. |
| **Unit test** | Permet de vérifier automatiquement la compilation + le comportement. |
| **Nombre d’exemples** | 2 – 3 exemples suffisent; plus augmente le coût token sans gain proportionnel. |

---

## 2.3 Contrôle de style de code  

### Instructions explicites à insérer  

```text
- Respecte la convention PEP 8 (indentation de 4 espaces, noms snake_case).
- N’utilise pas de `print` dans le code retourné.
- Ajoute un `# noqa: E501` si une ligne dépasse 79 caractères.
- Termine chaque fonction par une doc‑string de type Google.
```

### Validation automatisée (Python)  

```python
import subprocess, json, textwrap, re

def lint_python(code: str) -> list[str]:
    """Run flake8 on a code string and return the list of warnings."""
    proc = subprocess.run(
        ["flake8", "--stdin-display-name", "generated.py", "-"],
        input=code.encode(),
        capture_output=True,
    )
    return proc.stdout.decode().splitlines()

# Exemple d’utilisation
prompt = """... (prompt) ..."""
generated = call_openai(prompt)          # fonction fictive qui interroge le modèle
warnings = lint_python(generated)
assert not warnings, f"Lint errors: {warnings}"
```

### Pièges fréquents  

| Piège | Symptôme | Correction |
|-------|----------|------------|
| **Import manquant** | `NameError: name 'fs' is not defined` (JS) | Ajouter explicitement `const fs = require('fs');` dans le prompt. |
| **Indentation mixte** | `IndentationError` (Python) | Spécifier `Use 4 spaces for indentation` dans les consignes. |
| **Nom de variable ambiguë** | `variable 'data' used before assignment` | Donner des noms explicites (`input_json`, `output_csv`). |
| **Température > 0.3** | Variations de style d’une exécution à l’autre | Fixer `temperature=0.0` pour les tâches de génération de code. |
| **Omission du test** | Aucun bloc `#[test]` (Rust) | Inclure “Include a unit test” dans la consigne. |

---

## 2.4 Gestion des dépendances et des imports  

| Langage | Méthode recommandée |
|--------|----------------------|
| **Python** | `import` au début du bloc, suivi d’un commentaire `# required`. Exemple : `import math  # required for sqrt`. |
| **JavaScript (Node)** | `const <module> = require('<module>'); // required`. |
| **Rust** | `use std::collections::HashMap;

---

## Module 3 — contenu

## Module 3 – Prompt Engineering pour les données structurées  

### 1. Principes de base  

| Élément | Rôle | Exemple de formulation |
|---------|------|-----------------------|
| **Format de sortie explicite** | Indique au modèle le type exact attendu (JSON, CSV, SQL). | `Réponds uniquement avec du JSON valide contenant les champs demandés.` |
| **Balises de démarcation** | Empêchent les « hallucinations » de formatage. | ```json\n{ … }\n``` |
| **Validation schema** | Permet de vérifier la conformité à la structure attendue. | `jsonschema.validate(instance, schema)` |
| **Prompt conditionnel** | Ajoute des clauses `if … else` dans le texte du prompt pour filtrer ou agréger. | `Si la colonne "status" vaut "active", ne garde que ces lignes.` |

### 2. Construction d’un prompt fiable pour une transformation JSON → CSV  

```text
Tu es un assistant qui convertit du JSON en CSV.  
Le JSON d’entrée sera fourni entre les balises ```json``` et ```json``` et respectera le schéma suivant :

{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "id": {"type": "integer"},
      "nom": {"type": "string"},
      "date_naissance": {"type": "string", "format": "date"},
      "score": {"type": "number"}
    },
    "required": ["id","nom","date_naissance","score"]
  }
}

Convertis chaque objet en une ligne CSV avec les colonnes dans l’ordre : id,nom,date_naissance,score.  
N’ajoute aucun texte supplémentaire, uniquement le CSV entre les balises ```csv``` et ```csv`.  
Si un champ est nul, laisse la cellule vide.
```

#### Pourquoi chaque partie fonctionne  

1. **Déclaration de rôle** (`Tu es un assistant…`) oriente le modèle vers la tâche.  
2. **Schéma JSON** donne un contrat formel, limitant les interprétations.  
3. **Ordre des colonnes** élimine l’ambiguïté d’ordre.  
4. **Balises** (` ```csv `) forcent le modèle à respecter le format.  
5. **Gestion du null** précise le comportement attendu pour les valeurs manquantes.

### 3. Exemple de code complet (Python 3.10+)  

```python
import json
import csv
import io
from jsonschema import validate, ValidationError
import openai  # SDK OpenAI, version >=1.0.0

# 1. Schéma JSON utilisé dans le prompt (doit être identique)
JSON_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "nom": {"type": "string"},
            "date_naissance": {"type": "string", "format": "date"},
            "score": {"type": "number"},
        },
        "required": ["id", "nom", "date_naissance", "score"],
    },
}

# 2. Prompt template (f‑string pour insérer les données)
PROMPT_TEMPLATE = """\
Tu es un assistant qui convertit du JSON en CSV.
Le JSON d’entrée sera fourni entre les balises ```json``` et ```json``
et respectera le schéma suivant :

{schema}

Convertis chaque objet en une ligne CSV avec les colonnes dans l’ordre : id,nom,date_naissance,score.
N’ajoute aucun texte supplémentaire, uniquement le CSV entre les balises ```csv``` et ```csv`.
Si un champ est nul, laisse la cellule vide.

```json
{payload}
```
"""

def call_openai(prompt: str) -> str:
    """Appel simple à l'API ChatCompletion (model gpt‑4o-mini)."""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,   # force la déterminisme
        max_tokens=2000,
    )
    return response.choices[0].message.content

def extract_csv(model_output: str) -> str:
    """Extrait le texte entre les balises ```csv```."""
    start = model_output.find("```csv")
    if start == -1:
        raise ValueError("Balise d'ouverture CSV manquante")
    start = model_output.find("\n", start) + 1
    end = model_output.find("```", start)
    if end == -1:
        raise ValueError("Balise de fermeture CSV manquante")
    return model_output[start:end].strip()

def json_to_csv(json_data: list[dict]) -> str:
    """Pipeline complet : validation → prompt → extraction → vérif."""
    # 1. Validation stricte
    try:
        validate(instance=json_data, schema=JSON_SCHEMA)
    except ValidationError as exc:
        raise ValueError(f"JSON invalide : {exc.message}")

    # 2. Construction du prompt
    payload = json.dumps(json_data, ensure_ascii=False, indent=2)
    prompt = PROMPT_TEMPLATE.format(schema=json.dumps(JSON_SCHEMA, indent=2), payload=payload)

    # 3. Appel modèle
    raw_output = call_openai(prompt)

    # 4. Extraction CSV
    csv_text = extract_csv(raw_output)

    # 5. Validation CSV (exemple simple : même nombre de colonnes)
    reader = csv.reader(io.StringIO(csv_text))
    header = next(reader, None)
    expected_header = ["id", "nom", "date_naissance", "score"]
    if header != expected_header:
        raise ValueError(f"En‑tête CSV inattendu : {header}")

    # Retourner le CSV complet (en‑tête + lignes)
    return "\n".join([",".join(expected_header)] + ["\n".join(row) for row in reader])

# Exemple d’utilisation
if __name__ == "__main__":
    sample = [
        {"id": 1

---

## Module 4 — contenu

## Module 4 – Optimisation et évaluation des prompts  

### 4.1 Métriques d’évaluation appliquées aux réponses de modèle  

| Métrique | Définition | Calcul (exemple Python) | Usage typique |
|----------|------------|--------------------------|---------------|
| **Exact Match (EM)** | Proportion de réponses identiques à la référence (case‑sensitive). | `em = (pred == ref).mean()` | Tâches de génération de code ou de réponses factuelles où la sortie doit être strictement identique. |
| **F1 (token‑level)** | Harmonie entre précision et rappel sur les tokens (ou n‑grams). | ```python\nfrom sklearn.metrics import f1_score\nf1 = f1_score(ref_tokens, pred_tokens, average='binary')\n``` | Classification texte, extraction d’entités, QA. |
| **BLEU** | Score de n‑gram overlap, pénalité de longueur. | ```python\nimport sacrebleu\nbleu = sacrebleu.corpus_bleu(preds, [refs]).score\n``` | Traduction, paraphrase, génération de résumés. |
| **ROUGE‑L** | Longest Common Subsequence (LCS) F‑measure. | ```python\nfrom rouge_score import rouge_scorer\nscorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)\nrouge_l = scorer.score(ref, pred)['rougeL'].fmeasure\n``` | Résumés, génération de texte libre. |
| **Exact‑Match‑Code** | Comparaison structurée du code via `ast` (Python) ou `tree‑sitter`. | ```python\nimport ast, difflib\nref_ast = ast.parse(ref_code)\npred_ast = ast.parse(pred_code)\nmatch = ast.dump(ref_ast) == ast.dump(pred_ast)\n``` | Génération de code où l’ordre des imports ou les espaces ne doivent pas pénaliser. |

**Bonnes pratiques**  
- Normaliser les textes (Unicode NFKC, suppression des espaces en fin de ligne) avant le calcul.  
- Pour les métriques basées sur les tokens, choisir le même tokeniseur que le modèle (ex. `tiktoken` pour OpenAI).  
- Conserver les scores bruts **et** les scores agrégés (moyenne, médiane) pour détecter les cas extrêmes.

---

### 4.2 Pipeline d’A/B testing automatisé  

#### 4.2.1 Architecture générale  

```
┌─────────────────┐      ┌─────────────────────┐
│  Prompt variant │──►   │  Inference Engine   │──►  Model output
└─────────────────┘      └─────────────────────┘
        │                         │
        ▼                         ▼
   pytest test_abl.py        metrics.py
        │                         │
        └───────►  results.csv ◄─┘
```

- **Prompt variant** : fichier `.yaml` ou `.json` contenant `id`, `system`, `user`, `temperature`, `max_tokens`.  
- **Inference Engine** : wrapper minimal autour de l’API (OpenAI `ChatCompletion` ou Anthropic `Message`).  
- **pytest** : chaque variante est un paramètre du test `@pytest.mark.parametrize`.  
- **metrics.py** : fonctions de calcul des métriques (voir 4.1).  
- **results.csv** : lignes `variant_id,example_id,EM,F1,BLEU,ROUGE_L,latency_ms`.  

#### 4.2.2 Exemple de code complet (Python 3.11)  

```python
# test_abl.py
import json
import time
import pytest
import openai  # pip install openai
from metrics import exact_match, f1_token, bleu_score, rouge_l_score

# ----------------------------------------------------------------------
# 1. Chargement des variantes de prompt (YAML ou JSON)
# ----------------------------------------------------------------------
def load_variants(path="prompts/variants.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)  # [{ "id": "v1", "system": "...", "user": "...", ... }, ...]

VARIANTS = load_variants()

# ----------------------------------------------------------------------
# 2. Jeu de test (exemple_id, user_input, reference_output)
# ----------------------------------------------------------------------
TEST_CASES = [
    ("ex1", "Convert the list [1,2,3] to a CSV line.", "1,2,3"),
    ("ex2", "Write a Python function that returns the factorial of n.", "def fact(n):\n    return 1 if n==0 else n*fact(n-1)"),
    # … 18 autres cas similaires …
]

# ----------------------------------------------------------------------
# 3. Fonction d’inférence unique (dé‑duplication du client HTTP)
# ----------------------------------------------------------------------
def call_model(system: str, user: str, temperature: float, max_tokens: int):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system},
                  {"role": "user",   "content": user}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()

# ----------------------------------------------------------------------
# 4. Paramétrage du test A/B
# ----------------------------------------------------------------------
@pytest.mark.parametrize("variant", VARIANTS, ids=lambda v: v["id"])
def test_variant(variant):
    results = []
    for ex_id, user_input, reference in TEST_CASES:
        start = time.time()
        pred = call_model(
            system=variant["system"],
            user=user_input,
            temperature=variant.get("temperature", 0.0),
            max_tokens=variant.get("max_tokens", 512),
        )
        latency = (time.time() - start) * 1000  # ms

        # ----- métriques -----

---

## Module 5 — contenu

## Module 5 – Intégration sécurisée et gouvernance des prompts  

### 5.1 Principes de gouvernance des LLM  

| Concept | Définition | Référence technique |
|--------|------------|----------------------|
| **Prompt Whitelisting** | Liste explicite de modèles de requêtes autorisées (ex. regex ou AST). | OpenAI `moderations` API – <https://platform.openai.com/docs/guides/moderation> |
| **Prompt Blacklisting** | Filtrage de mots/phrases jugés inacceptables. | RFC 6901 – JSON‑Pointer pour ciblage de champs. |
| **Output Guardrails** | Post‑traitement qui rejette ou masque les réponses non conformes. | Anthropic “Claude‑3‑Guardrails” – <https://docs.anthropic.com/claude/docs/guardrails> |
| **Rate‑Limiting & Auditing** | Limitation du nombre de requêtes par utilisateur et journalisation détaillée. | OWASP API Security Top 10 – A5 “Broken Function Level Authorization”. |

### 5.2 Architecture de service d’inférence sécurisée  

```
┌───────────────┐      ┌─────────────────┐      ┌─────────────────────┐
│   Client API  │─────►│  Prompt Filter  │─────►│  LLM Inference Engine│
└───────────────┘      └───────┬─────────┘      └───────┬───────────────┘
                         │                         │
                         ▼                         ▼
                ┌─────────────────┐      ┌─────────────────────┐
                │  Output Guard   │◄─────│  Post‑process Layer │
                └─────────────────┘      └─────────────────────┘
                         │
                         ▼
                ┌─────────────────────┐
                │  Audit & Reporting   │
                └─────────────────────┘
```

* **Prompt Filter** : applique whitelist, blacklist, validation de schéma (JSON Schema).  
* **LLM Engine** : appel à `openai.ChatCompletion.create` ou équivalent.  
* **Output Guard** : validation du format (`json`, `csv`, etc.) et contrôle de toxicité via l’API de modération.  
* **Audit** : stockage immuable (ex. AWS CloudTrail, Elasticsearch) des `request_id`, `user_id`, `prompt_hash`, `decision`.  

### 5.3 Implémentation concrète (Python 3.11)  

```python
import re
import json
import hashlib
import logging
from typing import Any, Dict, Tuple

import openai  # pip install openai
from jsonschema import validate, ValidationError  # pip install jsonschema

# ----------------------------------------------------------------------
# 1️⃣ Configuration statique (à charger depuis un secret manager en prod)
# ----------------------------------------------------------------------
WHITELIST_REGEX = re.compile(
    r"^(?i)(?:summarize|translate|extract|convert)\s+.*$", re.MULTILINE
)  # n’accepte que les verbes d’action autorisés
BLACKLIST_TERMS = {"virus", "malware", "exploit", "ddos"}  # mots interdits
PROMPT_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["summarize", "translate", "extract", "convert"]},
        "input": {"type": "string", "minLength": 1},
        "target_language": {"type": "string"},
    },
    "required": ["action", "input"],
    "additionalProperties": False,
}
MAX_TOKENS = 1024
TEMPERATURE = 0.0  # déterministe pour la conformité

# ----------------------------------------------------------------------
# 2️⃣ Fonctions utilitaires
# ----------------------------------------------------------------------
def hash_prompt(prompt: str) -> str:
    """SHA‑256 du prompt, utilisé comme identifiant immutable."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def is_whitelisted(prompt: str) -> bool:
    """Vérifie que le prompt correspond à la whitelist regex."""
    return bool(WHITELIST_REGEX.match(prompt.strip()))


def contains_blacklist(prompt: str) -> bool:
    """Renvoie True si un terme interdit est présent (case‑insensitive)."""
    lowered = prompt.lower()
    return any(term in lowered for term in BLACKLIST_TERMS)


def validate_json_schema(payload: Dict[str, Any]) -> Tuple[bool, str]:
    """Valide le payload contre PROMPT_SCHEMA. Retourne (ok, message)."""
    try:
        validate(instance=payload, schema=PROMPT_SCHEMA)
        return True, "OK"
    except ValidationError as exc:
        return False, f"Schema error: {exc.message}"


def moderate_output(content: str) -> bool:
    """
    Utilise l’API de modération OpenAI.
    Retourne True si le contenu est sûr (pas de toxicité > 0.5).
    """
    resp = openai.Moderation.create(input=content)
    flagged = any(
        result["flagged"] for result in resp["results"]
    )
    return not flagged


# ----------------------------------------------------------------------
# 3️⃣ Pipeline complet
# ----------------------------------------------------------------------
def process_request(raw_prompt: str, user_id: str) -> Dict[str, Any]:
    """
    Étapes :
    1. Filtrage whitelist / blacklist
    2. Parsing JSON (exemple de format attendu)
    3. Validation schéma
    4. Appel LLM
    5. Guardrail de sortie
    6. Audit
    """
    request_id = hash_prompt(raw_prompt + user_id)

    # 1️⃣ Whitelist / blacklist
    if not is_whitelisted(raw_prompt):
        logging.warning(f"{request_id}|{user_id}|reject|whitelist")
        return {"error": "Prompt non autorisé (whitelist).", "request_id": request_id}
    if contains_blacklist(raw_prompt):
        logging.warning(f"{request_id}|{user_id}|reject