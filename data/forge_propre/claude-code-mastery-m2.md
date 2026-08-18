# Claude Code Mastery M2

> Référence `claude-code-mastery-m2` · 177 €

## Plan

## Module 1 – Architecture et optimisation des modèles de langage

- **Objectif mesurable** : Concevoir, entraîner et optimiser un modèle de type transformer de 6 M à 125 M paramètres, en atteignant la perplexité de référence sur le jeu de validation GLUE.
- **Notions couvertes**  
  1. Architecture transformer : couches d’attention multi‑têtes, normalisation de couche, positionnal encoding.  
  2. Stratégies de pré‑entraînement : masked language modelling, causal LM, objectives de densité de probabilité.  
  3. Techniques d’optimisation : AdamW, scheduler cosine decay, gradient clipping, mixed‑precision (FP16).  
  4. Gestion du sur‑apprentissage : early stopping, weight decay, dropout, label smoothing.  
  5. Métriques de performance : perplexité, exact‑match, F1 sur benchmarks standard (GLUE, SuperGLUE).

## Module 2 – Fine‑tuning et adaptation de domaine

- **Objectif mesurable** : Réaliser un fine‑tuning supervisé d’un modèle pré‑entraîné sur un corpus spécialisé (ex. juridique) et obtenir une amélioration du score F1 sur un jeu de test interne.
- **Notions couvertes**  
  1. Méthodes de fine‑tuning : full‑model, adapter layers, LoRA (Low‑Rank Adaptation).  
  2. Construction de jeux de données d’adaptation : tokenisation cohérente, équilibrage des classes, data augmentation textuelle.  
  3. Gestion du déséquilibre de labels : focal loss, re‑weighting, oversampling.  
  4. Évaluation en continu : validation croisée k‑fold, suivi de métriques avec TensorBoard/Weights & Biases.  
  5. Déploiement de modèles fine‑tuned via ONNX ou TorchScript.

## Module 3 – Prompt Engineering et chaînes de raisonnement

- **Objectif mesurable** : Concevoir des prompts qui augmentent la précision de réponses factuelles sur le benchmark TruthfulQA, en respectant les contraintes de longueur (≤ 256 tokens).
- **Notions couvertes**  
  1. Principes de prompt design : rôle, instruction, exemplaires, contraintes de format.  
  2. Techniques de few‑shot et chain‑of‑thought prompting.  
  3. Analyse de sensibilité aux variations lexicales et à la température.  
  4. Méthodes d’automatisation du prompt optimisation (grid search, reinforcement learning from human feedback – RLHF).  
  5. Gestion des biais de sortie : filtres de toxicité, post‑processing avec regex et modèles de classification.

## Module 4 – Déploiement à grande échelle et monitoring

- **Objectif mesurable** : Mettre en production un service d’inférence capable de servir un volume important de requêtes avec un temps de latence moyen limité et un taux d’erreur très faible sur une instance GPU A100.
- **Notions couvertes**  
  1. Optimisation du graphe d’inférence : quantisation INT8, pruning, TensorRT, compilation Torch‑Dynamo.  
  2.


---

## Module 1 — contenu

## 1. Architecture Transformer  

### 1.1 Composants fondamentaux  

| Composant | Fonction | Formule clé |
|----------|----------|------------|
| **Embedding token** | Convertit chaque token d’indice *i* en vecteur *eₖ* ∈ ℝᵈ | *eₖ = Wₑ·one‑hot(i)* |
| **Positional encoding** | Injecte l’ordre séquentiel | *pₖ = sin(k/10000^{2j/d})* (sinus) ou *pₖ = learnable* |
| **Multi‑head self‑attention** | Calcule l’attention sur *h* sous‑espaces | *Attention(Q,K,V) = softmax(QKᵀ / √dₖ)·V* |
| **Layer‑norm** | Stabilise le flux de gradients | *LN(x) = (x‑μ)/σ · γ + β* |
| **Feed‑forward (FFN)** | Deux couches linéaires séparées par GELU | *FFN(x) = W₂·GELU(W₁·x + b₁) + b₂* |
| **Residual connection** | Facilite le passage du gradient | *x' = LN(x + Sublayer(x))* |

Un bloc **TransformerEncoderLayer** (ou **DecoderLayer** en causal LM) comprend :

```
x → LN → Multi‑head → +x → LN → FFN → +x
```

### 1.2 Dimensionnement pour 6 M – 125 M paramètres  

| Taille du modèle | d_model | n_head | n_layer | d_ff | Paramètres ≈ |
|------------------|--------|-------|--------|------|--------------|
| 6 M              | 384    | 6     | 6      | 1536 | 6 200 000 |
| 30 M             | 768    | 12    | 12     | 3072 | 30 000 000 |
| 125 M            | 768    | 12    | 24     | 3072 | 125 000 000 |

Le nombre de paramètres ≈ *n_layer·[ (2·d_model·d_k) + (2·d_model·d_v) + (4·d_model·d_ff) + 4·d_model ]*  
avec *d_k = d_v = d_model / n_head*.

---

## 2. Stratégies de pré‑entraînement  

| Objectif | Forme de perte | Exemple de jeu de données | Particularité |
|----------|----------------|---------------------------|----------------|
| **Masked Language Modeling (MLM)** | Cross‑entropy sur tokens masqués | Wikipedia + BookCorpus | Masquage aléatoire combinant tokens masqués, tokens remplacés aléatoirement et tokens conservés |
| **Causal Language Modeling (CLM)** | Cross‑entropy unidirectionnelle | OpenWebText | Pas de masquage, le modèle prédit le token suivant |
| **Seq2Seq denoising (e.g. T5)** | Cross‑entropy sur séquence corrompue | C4 | Corruption via span‑masking, permutation |

La perte standard est :

\[
\mathcal{L} = -\frac{1}{|M|}\sum_{i\in M}\log p_\theta (x_i \mid x_{\setminus i})
\]

où *M* est l’ensemble des positions masquées.

---

## 3. Techniques d’optimisation  

### 3.1 Optimiseur  

*AdamW* (L2‑regularisation séparée du moment) :

```python
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=5e-4,
    betas=(0.9, 0.999),
    weight_decay=0.01,   # décote L2
    eps=1e-8
)
```

### 3.2 Scheduler (cosine decay with warm‑up)  

```python
from transformers import get_cosine_schedule_with_warmup

scheduler = get_cosine_schedule_with_warmup(
    optimizer,
    num_warmup_steps=int(0.01 * total_steps),
    num_training_steps=total_steps
)
```

### 3.3 Mixed‑precision (FP16)  

```python
scaler = torch.cuda.amp.GradScaler()
for batch in loader:
    optimizer.zero_grad()
    with torch.cuda.amp.autocast():
        loss = model(**batch).loss
    scaler.scale(loss).backward()
    scaler.unscale_(optimizer)
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    scaler.step(optimizer)
    scaler.update()
    scheduler.step()
```

### 3.4 Gradient clipping  

`torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)`

### 3.5 Accumulation de gradients (utile quand le batch ne tient pas en VRAM)  

```python
grad_accum_steps = 4
for i, batch in enumerate(loader):
    loss = model(**batch).loss / grad_accum_steps
    loss.backward()
    if (i + 1) % grad_accum_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
        scheduler.step()
```

---

## 4. Gestion du sur‑apprentissage  

| Technique | Paramètre clé | Effet observé |
|-----------|---------------|---------------|
| **Early stopping** | patience (exemple) | Stop avant divergence validation |
| **Weight decay** | 0
---

## Module 2 — contenu

## 2.1 Méthodes de fine‑tuning  

| Méthode | Principe | Avantages | Inconvénients | Cas d’usage typique |
|---|---|---|---|---|
| **Full‑model fine‑tuning** | Tous les poids du modèle pré‑entraîné sont mis à jour. | Meilleure capacité d’adaptation quand le domaine est très différent. | Consomme beaucoup de VRAM ; risque de sur‑apprentissage. | Corpus de plusieurs millions de tokens, domaine très spécialisé. |
| **Adapter layers** | Ajout de petites couches (bottleneck de dimension modérée) entre les blocs du transformer, seules ces couches sont entraînées. | Mémoire GPU bien inférieure à celle du full‑model ; réutilisation facile pour plusieurs domaines. | Nécessite un wrapper (ex. `adapter-transformers`). | Plusieurs domaines simultanés, contraintes de stockage. |
| **LoRA (Low‑Rank Adaptation)** | Décompose chaque mise à jour de poids `ΔW` en `A·B` où `A∈ℝ^{d×r}`, `B∈ℝ^{r×d}` avec `r≪d`. Les matrices `A` et `B` sont les seules à être entraînées. | Mémoire très réduite par rapport au modèle complet ; aucune modification du graphe d’inférence. | Implémentation dépend du framework (PyTorch, 🤗 Transformers). | Scénarios de MLOps où le même binaire doit servir plusieurs clients. |

### Implémentation LoRA avec 🤗 Transformers + PEFT  

```python
# --------------------------------------------------------------
# Fine‑tuning LoRA d'un modèle BERT sur un jeu de classification
# juridique (deux classes).  Le code est fonctionnel avec
# transformers>=4.34 et peft>=0.5.0.
# --------------------------------------------------------------
import torch
from datasets import load_dataset, DatasetDict
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_int8_training

# 1️⃣ Chargement du modèle de base (BERT‑base)
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

# 2️⃣ Jeu de données factice – remplacez par votre corpus juridique
raw = {
    "train": [
        {"text": "Le contrat est résilié en cas de force majeure.", "label": 1},
        {"text": "Le locataire doit payer le loyer avant le 5 du mois.", "label": 0},
    ],
    "validation": [
        {"text": "Le bailleur peut augmenter le loyer chaque année.", "label": 0},
        {"text": "La clause de non‑concurrence est valable 2 ans.", "label": 1},
    ],
}
datasets = DatasetDict({
    "train": load_dataset("json", data_files={"train": raw["train"]}, split="train"),
    "validation": load_dataset("json", data_files={"validation": raw["validation"]}, split="train"),
})

# 3️⃣ Tokenisation (attention à `padding='max_length'` pour uniformiser les batch)
def tokenize(batch):
    return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=128)

datasets = datasets.map(tokenize, batched=True)
datasets.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

# 4️⃣ Préparer le modèle pour l’entraînement en int8 (facultatif, réduit VRAM)
base_model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=2,
    torch_dtype=torch.float16,          # FP16 pour mixed‑precision
    device_map="auto",
)
base_model = prepare_model_for_int8_training(base_model)

# 5️⃣ Configuration LoRA – rank r=8, alpha=16, dropout=0.05
lora_cfg = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["query", "value"],   # couches d’attention à adapter
    lora_dropout=0.05,
    bias="none",
    task_type="SEQ_CLS",
)

# 6️⃣ Appliquer LoRA au modèle
model = get_peft_model(base_model, lora_cfg)

# 7️⃣ Arguments d’entraînement – scheduler cosine,
```