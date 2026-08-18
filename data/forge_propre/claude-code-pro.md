# Claude Code Pro

> Référence `claude-code-pro` · 49 €

## Plan

## Module 1 – Architecture et principes de Claude 2  
**Objectif mesurable** : L’apprenant pourra expliquer le fonctionnement interne de Claude 2 et identifier les composants clés d’une requête, avec un taux de réussite élevé à un quiz de 20 questions.  
- Modèle de transformeur à attention multi‑têtes (decoder‑only)  
- Mémoire contextuelle : grande fenêtre de contexte et gestion du « truncation »  
- Méthodes d’inférence : décodage greedy, top‑p (nucleus) et temperature  
- Alignement par RLHF (Reinforcement Learning from Human Feedback) et supervision fine‑tuned  
- Limites de hallucination et métriques de factualité (BLEU, ROUGE, BERTScore)

## Module 2 – Prompt Engineering avancé pour la génération de code  
**Objectif mesurable** : L’apprenant rédigera des prompts qui produisent du code fonctionnel (tests unitaires passés) dans la plupart des cas d’usage différents, validés par un script d’évaluation automatisé.  
- Structuration du prompt : rôle, contexte, consignes, exemples (few‑shot)  
- Techniques de chain‑of‑thought et de self‑refinement  
- Utilisation de balises de langage (```python```, ```//```…) et de directives de style (PEP 8, Google Style)  
- Gestion des dépendances et des imports via prompt  
- Détection et correction d’erreurs de compilation générées par le modèle

## Module 3 – Intégration de Claude dans les environnements de développement  
**Objectif mesurable** : L’apprenant configurera et utilisera l’API Claude dans VS Code et GitHub Copilot like, en automatisant au moins deux flux de travail (ex. génération de stub, revue de PR) avec succès démontré par des logs d’exécution.  
- Authentification OAuth 2.0 et gestion des tokens d’accès  
- Appels REST / gRPC à l’API Claude (endpoints : /v1/completions, /v1/stream)  
- Extensions VS Code : création d’un “Claude Assistant” (Webview, commands)  
- CI/CD : intégration dans les pipelines GitHub Actions (ex. linting, génération de doc)  
- Sécurité des prompts : filtrage des données sensibles (PII, secrets)

## Module 4 – Tests, validation et debugging automatisés du code généré  
**Objectif mesurable** : L’apprenant mettra en place un pipeline de test qui détecte et corrige automatiquement la majorité des défauts de syntaxe et logique dans le code produit par Claude.  
- Génération de tests unitaires avec pytest via prompt  
- Utilisation de coverage py et mutation testing (mutmut) pour évaluer la robustesse  
- Boucle de feedback : re‑prompting basé sur les sorties d’erreur (traceback)  
- Analyse statique (flake8, mypy) intégrée au processus de génération  
- Gestion des dépendances de version (requirements.txt, poetry)

## Module 5 – Optimisation des coûts et gouvernance de l’IA générative  
**Objectif mesurable** : L’apprenant pourra réduire la dépense d’API Claude de façon notable tout en maintenant la qualité du code, et documentera une politique de gouvernance conforme au

---

## Module 1 — contenu

## 1.1 Architecture interne de Claude 2  

| composant | rôle | référence |
|-----------|------|-----------|
| **Decoder‑only Transformer** | génère le texte token par token à partir d’une séquence d’entrée (pas d’encodeur séparé). | Vaswani et al., *Attention is All You Need*, 2017 |
| **Bloc multi‑head attention** | chaque tête calcule `Attention(Q,K,V) = softmax(QKᵀ/√d_k) V`. Le modèle agrège plusieurs têtes puis projette le résultat. | même source |
| **Feed‑Forward Network (FFN)** | deux couches linéaires séparées par GELU, dimension interne proportionnelle au modèle. | idem |
| **Layer‑Norm + résidu** | stabilise l’entraînement, ajoute l’entrée du bloc à sa sortie. | idem |
| **Positional embeddings** | encode la position relative des tokens (rotary embeddings dans Claude 2). | Su et al., *RoFormer*, 2021 |
| **Paramètres** | modèle de grande dimension avec plusieurs milliards de poids. | Anthropic, doc technique 2023 |

### 1.1.1 Flux de données (simplifié)

```
input tokens → embedding + positional → L × [MHA → Add & Norm → FFN → Add & Norm] → LM head → logits → token sampling
```

---

## 1.2 Mémoire contextuelle  

* **Fenêtre de contexte** : très large, permettant de traiter de longues séquences.  
* **Truncation** : si le prompt + les tokens déjà générés dépassent la fenêtre, les tokens les plus anciens sont supprimés (policy « first‑in‑first‑out »).  
* **Sliding‑window** (optionnel) : on peut garder les derniers tokens et ré‑injecter les résumés des parties supprimées via un prompt de rappel.  

> **Piège** : lorsqu’on dépasse la fenêtre, le modèle « oublie » les informations précédentes ; les réponses peuvent devenir incohérentes si le rappel n’est pas explicite.

---

## 1.3 Méthodes d’inférence  

| méthode | formule de sélection | usage typique |
|---------|----------------------|---------------|
| **Greedy** | `argmax_i p_i` | génération déterministe, rapide, mais souvent monotone. |
| **Top‑p (nucleus)** | garde le plus petit ensemble `S` tel que la probabilité cumulée dépasse une valeur élevée, puis échantillonne dans `S`. | équilibre diversité et cohérence. |
| **Temperature** | modifie les logits : `p_i ∝ exp(logit_i / T)`. Une température basse rend la distribution plus pointue, une température élevée la rend plus plate. | réglage fin de la créativité ; une température modérée est souvent bon compromis. |
| **Top‑k** (occasionnel) | conserve les `k` plus probables tokens. | utile quand on veut limiter le vocabulaire. |

> **Piège** : combiner une température élevée avec un top‑p élevé peut générer des sorties incohérentes ; il faut tester chaque combinaison.

---

## 1.4 Alignement par RLHF  

1. **Pré‑entraînement** (large‑scale language modeling) → minimise la perte de cross‑entropy sur un corpus très vaste.  
2. **Supervised Fine‑Tuning (SFT)** : jeux de prompts‑réponses humains (dix millions d’exemples) ; le modèle apprend à imiter les réponses souhaitées.  
3. **Reward Model (RM)** : un classifieur entraîné à prédire le score humain (échelle 0‑1) à partir de `(prompt, réponse)`.  
4. **Proximal Policy Optimization (PPO)** : le modèle de politique (Claude) est ajusté pour maximiser l’espérance du reward tout en restant proche de la politique SFT (`KL‑penalty`).  

> **Piège** : le RM peut refléter les biais du jeu de données d’évaluation ; une mauvaise calibration entraîne des réponses “plausibles mais fausses”.

---

## 1.5 Hallucinations et métriques de factualité  

| métrique | ce qu’elle mesure | limites |
|----------|-------------------|----------|
| **BLEU** | n‑gram overlap (1‑4) avec référence(s). | sensible aux variations lexicales, pas de véracité. |
| **ROUGE‑L** | plus longue sous‑séquence commune. | même limitation que BLEU. |
| **BERTScore** | similarité sémantique via embeddings (cosine). | dépend du modèle de base, ne détecte pas les erreurs factuelles. |
| **FactCC** (202

---

## Module 2 — contenu

## Module 2 – Prompt Engineering avancé pour la génération de code  

### 2.1. Structuration du prompt  

| Élément | Rôle | Syntaxe recommandée |
|--------|------|---------------------|
| **Rôle** | Définit le point de vue du modèle (ex. « You are a senior Python developer »). | `You are a senior Python developer.` |
| **Contexte** | Donne les informations de domaine, les contraintes d’environnement, les versions de bibliothèques. | `The project uses Python 3.11, FastAPI 0.104, and PostgreSQL 15.` |
| **Consignes** | Liste les exigences fonctionnelles et non‑fonctionnelles (style, tests, performance). | `- Write a function that …\n- Follow PEP 8.\n- Include type hints.` |
| **Exemples (few‑shot)** | Fournit un ou deux exemples d’entrée/sortie pour ancrer le format attendu. | ```\n# Example 1\nInput: …\nOutput: …\n``` |
| **Délimiteurs de code** | Encadre le code avec des fences de langage afin que le modèle ne mélange pas texte et code. | ````python\n...code...\n```` |
| **Balises de style** | Indique explicitement le guide de style à appliquer. | `Apply Google Python Style Guide.` |
| **Prompt final** | Concatène les blocs dans l’ordre : rôle → contexte → consignes → exemples → tâche. | `You are a senior Python developer.\nThe project uses …\n- Write …\n- Follow …\n# Example …\nWrite the function …` |

> **Bon à savoir** : chaque ligne séparée par un double saut de ligne augmente la probabilité que le modèle considère le bloc comme une unité sémantique distincte.

### 2.2. Techniques de Chain‑of‑Thought (CoT)  

1. **Décomposition explicite** – demander au modèle de « penser à haute voix » avant de produire le code.  
   ```text
   Step 1: Identify inputs and outputs.
   Step 2: Choose the appropriate data structures.
   Step 3: Sketch the algorithm in pseudocode.
   Step 4: Translate to Python with type hints.
   ```  
2. **Utilisation du token `'''THINK'''`** (ou tout marqueur unique) pour séparer la réflexion du code. Le modèle a montré une amélioration notable du taux de réussite sur les tâches de génération de fonctions complexes (benchmark OpenAI 2023).  
3. **Self‑refinement** – après la première génération, ré‑injecter le code et les erreurs éventuelles dans un second prompt :  
   ```text
   The previous code raised the following error: <traceback>.
   Refactor the function to fix the error while preserving the original API.
   ```

### 2.3. Directives de style et de documentation  

| Directive | Exemple concret | Impact mesurable |
|-----------|----------------|------------------|
| **PEP 8** | `import os\n\ndef foo(bar: int) -> None:` | `flake8` score élevé |
| **Google Style** | Docstring format : `"""Summary.\n\nArgs:\n    x (int): …\n\nReturns:\n    bool: …\n"""` | `pydocstyle` passe |
| **Type hints** | `def add(a: int, b: int) -> int:` | `mypy` passe avec `--strict` |
| **Explicit imports** | `from pathlib import Path` (avoid `import *`) | Réduction des warnings `flake8 F403` |
| **Dependency declaration** | `# requirements.txt\nfastapi==0.104.0\nuvicorn[standard]==0.23.2` | CI : `pip install -r requirements.txt` ne génère pas de conflits de version |

### 2.4. Gestion des dépendances via le prompt  

- **Demander la version exacte** : `Specify the exact version of any third‑party library you import.`
- **Inclure un bloc `requirements.txt`** dans la réponse :  
  ```text
  # requirements.txt
  fastapi==0.104.0
  sqlalchemy==2.0.20
  ```
- **Utiliser `poetry add`** si le projet est géré par Poetry :  
  ```text
  Add the following line to pyproject.toml under [tool.poetry.dependencies]:
  fastapi = "^0.104.0"
  ```

### 2.5. Détection et correction d’erreurs de compilation  

1. **Boucle de validation** :  
   - Prompt 1 → génération du code.  
   - Exécution `python -m py_compile <file>` (ou `mypy` pour typage).  
   - Capture du traceback.  
   - Prompt 2 → « Correct the syntax error(s) shown below ».  
2. **Prompt de correction typique** :  
   ```text
   The following code fails to compile:
   <code block>

   Fix the syntax errors without changing the function signature.
   ```  
3. **Utilisation de `--logprobs`** (si l’API le permet) pour repérer les tokens les plus incertains ; les remplacer par des suggestions explicites dans le prompt (ex. « use `:` after the function name »).

### 2.6. Exemple