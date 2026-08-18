# Fine-tuning LLMs — LoRA & QLoRA

> Référence `llm-finetuning` · 99 €

## Plan

## Module 1 : Principes fondamentaux du fine‑tuning d’un LLM  
**Objectif mesurable** : L’apprenant peut expliquer, à l’aide d’un diagramme, les différences entre le pré‑entraînement, le fine‑tuning complet et le fine‑tuning à paramètres faibles, et justifier le choix du dernier pour des modèles de >7 B paramètres.  
**Notions couvertes**  
1. Architecture de base des transformeurs (attention, feed‑forward, normalisation).  
2. Paramètres entraînables vs paramètres gelés : impact sur la mémoire et le temps de calcul.  
3. Méthodes de fine‑tuning à paramètres faibles : adapters, prefix‑tuning, LoRA.  
4. Trade‑off entre performance (perplexité, métriques de tâche) et coût d’inférence.  
5. Cadre d’évaluation (train/validation split, métriques de classification et génération).

## Module 2 : LoRA – Low‑Rank Adaptation  
**Objectif mesurable** : L’apprenant implémente une couche LoRA sur un modèle Hugging Face (ex. `bert-base-uncased`) et montre, à l’aide d’un benchmark de 100 k tokens, une réduction de la consommation GPU d’au moins 30 % sans perte de plus de 0,5 % de précision sur la tâche GLUE MRPC.  
**Notions couvertes**  
1. Décomposition en rang faible : matrices \(A\in\mathbb{R}^{d\times r}\) et \(B\in\mathbb{R}^{r\times d}\) (r ≪ d).  
2. Intégration de LoRA dans les projections Q, K, V et/ou le feed‑forward.  
3. Initialisation et mise à l’échelle des poids (\(\alpha\) scaling).  
4. Gestion des états (`state_dict`) pour le checkpointing.  
5. Compatibilité avec les optimizers standards (AdamW, Lion).

## Module 3 : QLoRA – Quantisation + LoRA  
**Objectif mesurable** : L’apprenant quantifie un modèle de 13 B paramètres en 4 bits (GPT‑NeoX) avec la bibliothèque `bitsandbytes`, y ajoute LoRA, et obtient un score BLEU ≥ 28 sur WMT‑14 En‑Fr avec un coût d’inférence ≤ 0,8 $ / 1 M tokens.  
**Notions couvertes**  
1. Types de quantisation : 8‑bit, 4‑bit (NF4), et leurs exigences matérielles.  
2. `bitsandbytes` : `bnb.nn.Linear4bit`, gestion du `torch.cuda.amp` et du `gradient_checkpointing`.  
3. Interaction entre quantisation et mise à jour de rang faible : préservation de la précision des gradients.  
4. Stratégies de déquantisation partielle pour les couches critiques.  
5. Évaluation du « effective bits » et impact sur le taux de compression.

## Module 4 : Pipeline d’entraînement distribué et optimisation des ressources  
**Objectif mesurable** : L’apprenant configure un entraînement LoRA/QLoRA sur 2 GPU A100 40 GB via `accelerate` ou `deepspeed`, atteint une utilisation GPU moyenne ≥ 85 % et complète 10 époques sur un dataset de 500 k exemples en ≤ 6 heures.  
**Notions couvertes**  
1. Partitionnement de modèle (ZeRO‑2/3) et off‑loading CPU/CPU

---

## Module 1 — contenu

## 1.1 Architecture de base des transformeurs  

| composant | fonction | forme matricielle (entrée = X, sortie = Y) |
|-----------|----------|------------------------------------------|
| **Self‑attention** | calcule une représentation contextuelle de chaque token | `Y = softmax(QKᵀ / √d) V` avec `Q = XW_Q`, `K = XW_K`, `V = XW_V` (`W_* ∈ ℝ^{d_model×d_k}`) |
| **Feed‑forward (FFN)** | projection non linéaire position‑indépendante | `Y = max(0, XW₁ + b₁)W₂ + b₂` avec `W₁ ∈ ℝ^{d_model×d_ff}`, `W₂ ∈ ℝ^{d_ff×d_model}` |
| **Layer‑norm** | stabilise la variance des activations | `Y = (X - μ)/σ * γ + β` (paramètres scalaires `γ,β ∈ ℝ^{d_model}`) |
| **Residual** | facilite le flux de gradient | `Y = X + Sublayer(Y)` |

Chaque bloc (attention + FFN) possède **≈ 2 × d_model × d_k + 2 × d_model × d_ff** poids entraînables. Pour un modèle de 13 B paramètres, `d_model≈5 120`, `d_ff≈20 480`, `d_k≈d_v≈640`. La taille quadratique du produit `QKᵀ` impose une mémoire O(seq_len²).

---

## 1.2 Paramètres entraînables vs paramètres gelés  

| scénario | paramètres mis à jour | impact mémoire GPU | impact temps d’entraînement |
|----------|----------------------|---------------------|-----------------------------|
| **Pré‑entraînement** | **Tous** (≈ 100 % du modèle) | besoin de charger le modèle complet en FP16/FP32 → 2 × taille du modèle en VRAM | chaque itération coûte `O(N_params)` opérations de gradient |
| **Fine‑tuning complet** | **Tous** (souvent FP16) | même que pré‑entraînement, mais le dataset est plus petit → moins d’étapes, mais même besoin de VRAM | généralement 2‑3× plus lent que LoRA pour un même nombre d étapes |
| **Fine‑tuning à paramètres faibles** | **< 1 %** (ex. LoRA: `r≈8` → 0,1 % des poids) | seules les matrices additionnelles (`A,B`) sont stockées en FP16, le reste reste gelé en FP16/FP32 | mise à jour très rapide, le backward ne touche que les petites matrices, gradient computation ≈ O(r·d) au lieu de O(d²) |

> **Vérifiable** : dans le papier *LoRA* (Hu et al., 2021) les auteurs rapportent 0,1 % de paramètres entraînables pour LLaMA‑13B (≈ 13 M paramètres au lieu de 13 B) avec une réduction de la consommation GPU de 30 % à 40 % sur un batch de 8 seq_len = 512.

---

## 1.3 Méthodes de fine‑tuning à paramètres faibles  

| méthode | principe | où insérer les poids additionnels | nombre de paramètres (ex. LLaMA‑13B, r=8) |
|--------|----------|----------------------------------|--------------------------------------------|
| **Adapters** | petite couche MLP (down‑proj + up‑proj) insérée après chaque FFN | `FFN_out → Down (d→r) → Up (r→d) → Add` | `2·d·r ≈ 81 M` (≈ 0,6 %) |
| **Prefix‑tuning** | préfixe appris ajouté aux clés/valeurs de l’attention | `K,V ← concat([Prefix_K,V], K,V)` | `2·n_layers·r·d_k` (≈ 0,2 %) |
| **LoRA** | ajout d’une mise à jour de rang faible directement sur les matrices linéaires | `W ← W + α·(A·B)` où `A∈ℝ^{d×r}`, `B∈ℝ^{r×d}` | `2·d·r` (≈ 0,1 %) |

*Pourquoi LoRA* : aucune modification du flux d’inférence (les matrices `A,B` sont fusionnées en un seul produit au moment du forward), compatible avec le checkpointing et les optimizers standards, et la surcharge mémoire est minimale.

---

## 1.4 Trade‑off performance ↔ coût d’inférence  

| métrique | fine‑tuning complet | LoRA (r=8) | Adapters (r=64) |
|----------|----------------------|------------|-----------------|
| **Perplexité (GPT‑NeoX‑20B, WikiText‑103)** | 13,2 | 13,4 (+1,5 %) | 13,3 (+0,8 %) |
| **Temps d’inférence (batch = 1, seq_len = 1024)** | 38 ms | 39 ms (≈ 2 % de plus) | 42 ms |
| **Mémoire GPU (FP16)** | 24 GB | 22 GB (‑8 %) | 23 GB (‑4 %) |

> **Constat** : la perte de performance est généralement < 2 % pour r ≤ 8, alors que la réduction de VRAM et le gain de vitesse d’entraînement sont significatifs. Au

---

## Module 2 — contenu

## 2.1 LoRA : principe mathématique

- **Décomposition low‑rank** : pour chaque matrice de projection dense \(W\in\mathbb{R}^{d_{\text{out}}\times d_{\text{in}}}\) on introduit deux matrices entraînables  
  \[
  \Delta W = \frac{\alpha}{r}\; B\,A,\qquad
  A\in\mathbb{R}^{r\times d_{\text{in}}},\;B\in\mathbb{R}^{d_{\text{out}}\times r},
  \]
  avec \(r\ll \min(d_{\text{in}},d_{\text{out}})\) et \(\alpha\) facteur de mise à l’échelle.  
- **Poids effectifs** pendant le forward :  
  \[
  y = (W + \Delta W)\,x = Wx + \frac{\alpha}{r}\,B(Ax).
  \]  
  Le terme \(Wx\) reste gelé (pas de gradient) ; seul \(B\) et \(A\) sont mis à jour.  
- **Complexité** :  
  - paramètres additionnels : \((d_{\text{out}}+d_{\text{in}})\times r\) (ex. BERT‑base : \(d=768\), \(r=8\Rightarrow 12\,288\) paramètres par couche).  
  - mémoire GPU : le tampon \(Ax\) est de taille \(r\), donc négligeable comparé à la sortie complète de dimension \(d_{\text{out}}\).  

## 2.2 Où placer LoRA dans BERT‑base

| composant | dimensions | projection concernée | recommandation LoRA |
|-----------|------------|----------------------|----------------------|
| **Self‑attention** | Q/K/V : \(d_{\text{model}}\times d_{\text{head}}\) | matrices \(W_Q, W_K, W_V\) | LoRA sur chaque tête (ou uniquement Q+V) |
| **Feed‑Forward** | \(W_1\in\mathbb{R}^{d_{\text{ff}}\times d_{\text{model}}}\), \(W_2\in\mathbb{R}^{d_{\text{model}}\times d_{\text{ff}}}\) | deux projections linéaires | LoRA sur \(W_1\) (gain le plus important) |
| **LayerNorm / bias** | – | non‑trainable par LoRA | laissé gelé |

Dans la plupart des implémentations (PEFT, `bitsandbytes`), on ne modifie que les poids linéaires (`nn.Linear`).  

## 2.3 Implémentation concrète avec **PEFT** (Hugging Face)

> **Pré‑requis**  
> ```bash
> pip install transformers==4.38.0 peft==0.6.2 torch==2.2.0 accelerate==0.27.0 datasets==2.16.0
> ```

```python
# 1️⃣ Imports
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
from datasets import load_dataset, load_metric
from peft import LoraConfig, get_peft_model, prepare_model_for_int8_training

# 2️⃣ Chargement du modèle et du tokenizer
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
base_model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=2,               # GLUE MRPC : 2 classes
    torch_dtype=torch.float16, # GPU A100 optimisé FP16
)

# 3️⃣ Pré‑parer le modèle pour le fine‑tuning à faible précision (facultatif)
base_model = prepare_model_for_int8_training(base_model)   # garde les poids en int8 mais garde les gradients FP16

# 4️⃣ Configuration LoRA
lora_cfg = LoraConfig(
    r=8,                # rang faible
    lora_alpha=32,      # facteur d’échelle (α)
    target_modules=["query", "value"],   # noms des sous‑modules dans BERT
    lora_dropout=0.05,  # dropout appliqué aux matrices LoRA
    bias="none",        # on ne forme pas les biais
    task_type="SEQ_CLS",# type de tâche pour PEFT
)

# 5️⃣ Injection de LoRA
model = get_peft_model(base_model, lora_cfg)

# 6️⃣ Vérification du nombre de paramètres entraînables
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
total_params = sum(p.numel() for p in model.parameters())
print(f"Trainable : {trainable_params:,} / Total : {total_params:,}  ({trainable_params/total_params:.2%})")
# → typiquement ≈0.1 % pour r=8

# 7️⃣ Pré‑traitement des données GLUE MRPC
raw_ds = load_dataset("glue", "mrpc")
def preprocess(example):
    return tokenizer(example["sentence1"], example["sentence2"], truncation=True, padding="max_length", max_length=128)
tokenized_ds = raw_ds.map(preprocess, batched=True)

# 8️⃣ Métrique
metric = load_metric("glue", "mrpc")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = torch.argmax(torch.tensor(logits), dim=-1)
    return metric.compute(predictions=preds, references=labels)

# 9️⃣ Arguments d’entraînement (Accelerate gère le multi‑GPU)
training

---

## Module 3 — contenu

## 3.1 Quantisation : principes et typologies  

| Type | Taille de poids | Format | Avantages | Contraintes matérielles |
|------|----------------|--------|-----------|--------------------------|
| **8‑bit (int8)** | 1 byte/paramètre | `torch.int8` (symmetric) | Gain de ≈ 4× sur la mémoire, support natif sur les GPU RTX 30 et A100 via `torch.cuda.amp` | Nécessite un calibrage de l’échelle (`scale`) sur chaque couche ; perte de précision ≈ 0.1 % sur perplexité pour les LLM > 6 B. |
| **4‑bit (NF4)** | 0.5 byte/paramètre | `bitsandbytes.NF4` (non‑uniform) | Gain de ≈ 8×, compatible avec les A100 40 GB et 80 GB, préserves les valeurs centrales du poids | Nécessite `bitsandbytes` ≥ 0.41, `torch.cuda.amp` désactivé pour les couches linéaires 4‑bit ; gradient approximatif (FP16) → possible instabilité si `lr` trop élevé. |
| **4‑bit (FP4)** | 0.5 byte/paramètre | `bitsandbytes.FP4` (uniform) | Similaire à NF4 mais plus simple à implémenter | Perte de précision plus importante que NF4 (≈ 0.3 % de perplexité supplémentaire). |

**Pourquoi NF4 ?**  
- Distribution des poids d’un LLM pré‑entraîné suit une loi gaussienne centrée. NF4 utilise des points de quantisation non‑uniformes qui maximisent la densité autour de 0, réduisant l’erreur moyenne quadratique (MSE) de quantisation de ≈ 30 % par rapport à FP4.  
- Les travaux de Dettmers *et al.* (2023) montrent que NF4 maintient la performance sur les tâches de génération (BLEU, ROUGE) à moins de 0.2 % de perte par rapport à la version FP16.

### 3.1.1 Gestion du `state_dict` avec quantisation  

- `bitsandbytes` enregistre les poids quantifiés sous la clé `"weight"` (type `torch.int8` ou `torch.uint8`).  
- Le `state_dict` contient également `"weight_quant_state"` (scales, zeros).  
- Pour charger un checkpoint quantifié :  

```python
model = MyModel.from_pretrained("EleutherAI/gpt-neox-13b")
model = model.to("cpu")                     # nécessaire pour le chargement initial
model = bnb.nn.quantize_model(model, quant_type="nf4")  # conversion en‑place
model.load_state_dict(torch.load("ckpt.pt"), strict=False)
```

## 3.2 Intégration de LoRA sur un modèle quantifié  

### 3.2.1 Formalisme LoRA  

Pour chaque matrice de projection `W ∈ ℝ^{d×k}` (ex. `q_proj`, `k_proj`, `v_proj`, `out_proj`), LoRA introduit :

\[
\Delta W = \frac{\alpha}{r} \, A B,
\]

- `A ∈ ℝ^{d×r}` et `B ∈ ℝ^{r×k}` sont apprises, `r ≪ d,k` (typiquement `r = 4` ou `8`).  
- Le poids effectif pendant le forward est `W + ΔW`.  
- `α` contrôle le facteur d’échelle (souvent `α = r`).

### 3.2.2 Interaction quantisation / LoRA  

- La matrice `W` reste quantifiée (NF4).  
- `ΔW` est stockée en **FP16** (ou **bfloat16** sur GPU A100) et **n’est pas quantifiée**.  
- Au forward, `W` est déquantisé à la volée (`bnb.nn.Linear4bit` réalise cela) puis additionné à `ΔW`.  
- La mise à jour des gradients ne touche que `A` et `B`. `W` reste figé, ce qui évite le coût de re‑quantisation.

### 3.2.3 Implémentation avec **PEFT** (v0.7.2)  

```python
# 1️⃣ Chargement du modèle 13 B en FP16 (pour le checkpoint d'origine)
from transformers import AutoModelForCausalLM, AutoTokenizer
import bitsandbytes as bnb
from peft import LoraConfig, get_peft_model

model_name = "EleutherAI/gpt-neox-13b"
tokenizer = AutoTokenizer.from_pretrained(model_name)

# 2️⃣ Quantisation NF4 (définit les Linear4bit à la place des Linear)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,          # charge en FP16 avant quantif.
    low_cpu_mem_usage=True,
    device_map="auto"
)

# Remplace toutes les couches Linear par Linear4bit (in‑place)
def quantize_module(module):
    for name, child in module.named_children():
        if isinstance(child, torch.nn.Linear):
            setattr(
                module,
                name,
                bnb.nn.Linear4bit(
                    child.in_features,
                    child.out_features,
                    bias=child.bias is not None,
                    compute_dtype=torch.float16,
                    quant_type="nf4"
                )

---

## Module 4 — contenu

## 4. Pipeline d’entraînement distribué et optimisation des ressources  

### 4.1. Principes de base  

| Concept | Description | Référence |
|--------|-------------|-----------|
| **Data‑parallelism** | Chaque GPU possède une copie complète du modèle (ou de la partie LoRA) et traite un sous‑lot différent. Les gradients sont agrégés (All‑Reduce) à chaque itération. | [Dean et al., 2012] |
| **Model‑parallelism (ZeRO‑2/3)** | ZeRO‑2 décale les états d’optimiseur (moments, états de pré‑conditionnement) hors du GPU ; ZeRO‑3 décale **tous** les paramètres du modèle. Permet d’entraîner des modèles qui dépassent la capacité mémoire d’un GPU. | [Microsoft DeepSpeed, 2021] |
| **Off‑loading CPU / NVMe** | Les tensors déplacés vers la RAM ou le disque sont stockés en format 16‑bit (FP16) ou 8‑bit (INT8) pour réduire le trafic PCIe. | [DeepSpeed Off‑load] |
| **Mixed‑precision (AMP)** | `torch.cuda.amp.autocast` convertit les opérations en FP16/ BF16 pendant le forward, tout en gardant les poids master en FP32. | [PyTorch AMP] |
| **Gradient checkpointing** | Re‑calcule les activations intermédiaires pendant le backward au lieu de les stocker, réduisant la consommation mémoire d’environ 30‑50 % au prix d’un sur‑coût de calcul (~10‑15 %). | [Chen et al., 2016] |

### 4.2. Architecture du pipeline LoRA/QLoRA distribué  

```
┌─────────────────────┐      ┌─────────────────────┐
│   Dataset (sharded) │─────►│  DataLoader (DistributedSampler) │
└─────────────────────┘      └─────────────────────┘
          │                               │
          ▼                               ▼
┌─────────────────────┐      ┌─────────────────────┐
│   Accelerator (Accelerate)  │  │   DeepSpeed Engine (optional) │
└─────────────────────┘      └─────────────────────┘
          │                               │
          ▼                               ▼
┌─────────────────────┐      ┌─────────────────────┐
│   Model + LoRA (PEFT) │────►│  Forward → Loss → Backward │
└─────────────────────┘      └─────────────────────┘
          │                               │
          ▼                               ▼
┌─────────────────────┐      ┌─────────────────────┐
│   Optimizer (AdamW) │────►│   ZeRO‑2/3 (state off‑load) │
└─────────────────────┘      └─────────────────────┘
          │                               │
          ▼                               ▼
┌─────────────────────┐      ┌─────────────────────┐
│   Scheduler (LR)    │────►│   All‑Reduce (torch.distributed) │
└─────────────────────┘      └─────────────────────┘
```

- **LoRA** : seules les matrices `A` et `B` (rank `r`) sont placées en mémoire GPU. Les poids originaux du modèle restent **gelés** (`requires_grad=False`).  
- **QLoRA** : le modèle de base est quantifié en 4‑bit via `bitsandbytes`; les matrices LoRA restent en FP16/FP32 pour éviter la perte de précision des gradients.  
- **Accelerate** : gère le lancement multi‑GPU, le `DistributedSampler`, le `torch.distributed` backend, et l’AMP.  
- **DeepSpeed** : optionnel mais recommandé pour ZeRO‑3 et off‑loading CPU/NVMe.  

### 4.3. Configuration `accelerate` (exemple minimal)  

```yaml
# accelerate_config.yaml
compute_environment: LOCAL_MACHINE
distributed_type: MULTI_GPU
num_processes: 2                # 2 GPU A100
machine_rank: 0
main_process_port: 29500
mixed_precision: fp16         # AMP
gradient_accumulation_steps: 2
zero_stage: 2                  # ZeRO‑2 (off‑load optimizer states)
offload_optimizer_device: cpu  # CPU off‑load, RAM > 64 GB recommandé
offload_param_device: none      # les paramètres LoRA restent sur GPU
```

**Lancement**  

```bash
accelerate launch \
  --config_file accelerate_config.yaml \
  train_lora_qlora.py \
  --model_name_or_path bigscience/llama-13b \
  --train_file data/train.jsonl \
  --validation_file data/val.jsonl \
  --output_dir ./checkpoints \
  --per_device_train_batch_size 4 \
  --per_device_eval_batch_size 8 \
  --learning_rate 2e-4 \
  --num_train_epochs 10 \
  --lr_scheduler_type cosine \
  --gradient_checkpointing \
  --use_qlora \
  --bits 4 \
  --lora_r 64 \
  --lora_alpha 16
```

### 4.4. Exemple de script d’entraînement complet (commenté)  

```python
# train_lora_qlora.py
import argparse, os, json, math
import torch
from torch

---

## Module 5 — contenu

## Module 5 : Mise en production et optimisation d’inférence pour LoRA / QLoRA  

### 5.1. Fusion des poids LoRA dans le modèle de base  

| Étape | Action | Commande / Code |
|------|--------|-----------------|
| 5.1.1 | Charger le modèle et les adapters LoRA (bitsandbytes 4‑bit) | ```python<br>import torch<br>from transformers import AutoModelForCausalLM, AutoTokenizer<br>import bitsandbytes as bnb<br>model_name = "EleutherAI/gpt-neox-20b"<br>tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)<br>model = AutoModelForCausalLM.from_pretrained( model_name, device_map="auto", torch_dtype=torch.float16, load_in_4bit=True, quant_type="nf4", bnb_4bit_compute_dtype=torch.float16 )<br># charger les poids LoRA (format .pt ou .safetensors)<br>lora_path = "lora_adapter.safetensors"<br>model.load_adapter(lora_path, adapter_name="lora")<br>model.set_active_adapters("lora")``` |
| 5.1.2 | Fusionner les matrices LoRA (A·B) dans les poids d’origine | ```python<br># la fonction `merge_adapter` est fournie par PEFT (v0.7+)<br>from peft import PeftModel<br>model = PeftModel.from_pretrained(model, lora_path, is_trainable=False)<br>model = model.merge_and_unload()  # les poids LoRA sont ajoutés aux matrices du modèle<br># libérer la RAM GPU inutilisée<br>torch.cuda.empty_cache()``` |
| 5.1.3 | Sauvegarder le modèle fusionné (optionnel) | ```python<br>model.save_pretrained("gptneox-20b-merged")<br>tokenizer.save_pretrained("gptneox-20b-merged")``` |

**Pourquoi fusionner ?**  
- Supprime la surcharge d’un *adapter* pendant l’inférence (pas de `model.set_active_adapters`).  
- Permet d’appliquer des optimisations de bas niveau (TensorRT, ONNX) qui ne reconnaissent pas les modules PEFT.  

### 5.2. Exportation vers ONNX pour un backend d’inférence ultra‑rapide  

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import onnx
import onnxruntime as ort

# 1️⃣ Chargement du modèle fusionné (float16 ou 4‑bit)
model = AutoModelForCausalLM.from_pretrained(
    "gptneox-20b-merged",
    torch_dtype=torch.float16,
    device_map="cpu"   # export en CPU, onnxruntime gère le GPU via CUDA EP
)
tokenizer = AutoTokenizer.from_pretrained("gptneox-20b-merged")

# 2️⃣ Préparer un exemple d’entrée (batch=1, seq_len=16)
sample_text = "Le futur de l'IA est"
inputs = tokenizer(sample_text, return_tensors="pt")
input_ids = inputs["input_ids"]  # shape (1, L)

# 3️⃣ Tracer le modèle avec torch.onnx.export
torch.onnx.export(
    model,
    (input_ids, ),                     # arguments du forward
    "gptneox-20b.onnx",
    input_names=["input_ids"],
    output_names=["logits"],
    dynamic_axes={"input_ids": {0: "batch", 1: "seq_len"},
                  "logits":    {0: "batch", 1: "seq_len"}},
    opset_version=14,
    do_constant_folding=True,
    use_external_data_format=True      # nécessaire >2 GB
)

print("Export ONNX terminé :", onnx.checker.check_model("gptneox-20b.onnx"))
```

**Points critiques**  
- `use_external_data_format=True` évite le dépassement de 2 GB du format protobuf.  
- Le modèle doit être en **float16** ou **int8** ; les poids 4‑bit ne sont pas directement supportés par ONNX, il faut les convertir en float16 avant export.  
- `dynamic_axes` garantit que la longueur de séquence reste variable à l’inférence.  

### 5.3. Optimisation avec TensorRT (GPU)  

```bash
# 1️⃣ Convertir le fichier ONNX en plan TensorRT (FP16)
trtexec --onnx=gptneox-20b.onnx \
        --saveEngine=gptneox-20b_fp16.trt \
        --fp16 \
        --workspace=32768  # 32 GB de VRAM allouée pour les optimisations

# 2️⃣ Vérifier le plan
trtexec --loadEngine=gptneox-20b_fp16.trt --batch=1 --duration=10
```

*Remarque* : TensorRT ne supporte pas les opérateurs `torch.nn.functional.scaled_dot_product_attention` avant la version 8.6. Si le modèle