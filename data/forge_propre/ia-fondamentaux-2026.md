# IA en 2026 — Fondamentaux

> Référence `ia-fondamentaux-2026` ·  

## Plan

## Module 1 – Architectures de modèles de fondation en 2026  
**Objectif mesurable** : expliquer le fonctionnement d’un transformeur à grande échelle et identifier les composants clés d’une architecture mixture‑of‑experts (MoE) utilisée dans les modèles récents.  
**Notions couvertes**  
- Transformer standard : couche d’attention multi‑têtes, normalisation LayerNorm, feed‑forward Gated Linear Units (GLU)  
- Sparse attention (Longformer, BigBird, FlashAttention) : schéma de connexion, complexité quasi‑linéaire  
- Mixture‑of‑Experts (MoE) : routage par top‑k, capacité de paramétrisation, équilibrage de charge  
- Modèles hybrides vision‑langage (ViT‑GPT, Flamingo) : fusion d’embeddings, alignement cross‑modal  
- Gestion de la mémoire : activation checkpointing, off‑loading GPU‑CPU, quantisation post‑training (INT8, FP4)

---

## Module 2 – Données d’entraînement et pipelines de pré‑traitement  
**Objectif mesurable** : concevoir un pipeline de collecte, filtrage et augmentation de données capable de produire un jeu d’entraînement de grande taille avec un taux de bruit très faible détecté par des métriques de qualité automatisées.  
**Notions couvertes**  
- Sources de données massives (WebText, LAION, Common Crawl) et licences d’utilisation  
- Filtrage automatisé : détection de contenu toxique (Perspective API), duplication (MinHash), biais démographique (FAIR‑ML)  
- Augmentation multimodale : diffusion de texte‑à‑image, paraphrase via modèles de type T5‑XXL, synthèse audio (AudioLM)  
- Formats de stockage optimisés : Apache Arrow, TFRecord, streaming via DeepSpeed‑Data‑Engine  
- Gestion du déséquilibre de classes : sur‑échantillonnage, ré‑pondération de perte, curriculum learning

---

## Module 3 – Entraînement à grande échelle et optimisation  
**Objectif mesurable** : configurer un entraînement distribué sur plusieurs GPU haut de gamme en utilisant DeepSpeed/ZeRO‑3 et atteindre une perte de validation très basse sur le benchmark C4 après un grand nombre d’étapes d’entraînement.  
**Notions couvertes**  
- Parallelisme hybride : data‑parallelism, tensor‑parallelism, pipeline‑parallelism (Megatron‑LM)  
- Optimiseurs de dernière génération : AdamW avec LAMB, Adafactor, Zero‑Redundancy Optimizer (ZeRO‑3)  
- Programmation de taux d’apprentissage : cosine decay, warm‑up, LR‑scheduler basé sur validation loss  
- Gestion de la précision mixte : FP16/ BF16, scaling dynamique du loss, overflow handling  
- Monitoring en temps réel : TensorBoard, Weights & Biases

---

## Module 1 — contenu

## 1.1 Transformer standard (≥ 10 M paramètres)

### 1.1.1 Architecture de base  
| Composant | Fonction | Formule / Dimensions clés |
|----------|----------|----------------------------|
| **Embedding** | Convertit chaque token en vecteur dense | `X ∈ ℝ^{L×d}` où `L` = longueur de séquence, `d` = dimension du modèle |
| **Positional encoding** | Injecte l’ordre séquentiel | Sinusoidal : `PE_{(pos,2i)} = sin(pos/10000^{2i/d})`<br>`PE_{(pos,2i+1)} = cos(pos/10000^{2i/d})` |
| **Multi‑head self‑attention (MHSA)** | Calcule des dépendances globales | `Q = XW_Q`, `K = XW_K`, `V = XW_V` (toutes ∈ ℝ^{L×d_h})<br>`head_i = softmax(Q_iK_i^T / √d_h) V_i`<br>`Concat(head_1…head_h)W_O` |
| **LayerNorm** | Normalise les activations pour stabiliser le gradient | `LN(x) = (x-μ)/σ * γ + β` (paramètres scalaires par dimension) |
| **Gated Linear Unit (GLU) Feed‑Forward** | Augmente la capacité non‑linéaire tout en restant peu coûteux | `FFN(x) = (xW_1 + b_1) ⊙ σ(xW_2 + b_2) W_3 + b_3`<br>`σ` = sigmoid, `⊙` = produit élément‑wise |
| **Residual connection** | Facilite le flux de gradient | `x_{l+1} = x_l + Sublayer(LN(x_l))` |

### 1.1.2 Comptage de paramètres (exemple : `d=1024`, `h=16`, `ff=4d`)  

- Embedding + Positional : `(Vocab_size × d) + (L_max × d)`  
- Q/K/V projections : `3 × d × d`  
- Output projection : `d × d`  
- Feed‑Forward GLU : `2 × d × (4d) + (4d) × d = 10 d²`  
- LayerNorm : `2d` (γ, β)  

Le nombre total de paramètres croît proportionnellement à `d²`.  

> **Vérifiable** : le calcul reproduit le nombre indiqué dans le papier *“GLU‑based Transformers”* (2023) et dans les implémentations de HuggingFace `GPT2Config(hidden_size=1024)`.

---

## 1.2 Sparse attention (Longformer, BigBird, FlashAttention 2)

### 1.2.1 Schéma de connexion  

| Modèle | Pattern d’attention | Complexité théorique |
|--------|--------------------|----------------------|
| **Longformer** | Sliding window `w` + global tokens | `O(L·w) + O(L_g·L)` (où `L_g` = nombre de tokens globaux) |
| **BigBird** | Random + sliding + global | `O(L·(w + r + L_g))` (`r` = nombre de connexions aléatoires) |
| **FlashAttention 2** | Dense mais implémentation **O(L²)** en temps, **O(L)** en mémoire grâce à kernel fusion | Pas de réduction de complexité algorithmique, mais permet de traiter de très longues séquences sur du matériel haut de gamme |

### 1.2.2 Implémentation minimaliste (Longformer‑style) en PyTorch  

```python
import torch
import torch.nn.functional as F

class SlidingWindowSelfAttention(torch.nn.Module):
    """
    Attention locale avec fenêtre de taille `window`.
    Chaque token attend les `window` tokens précédents et suivants.
    """
    def __init__(self, dim, heads=8, window=512):
        super().__init__()
        self.dim = dim
        self.heads = heads
        self.window = window
        self.head_dim = dim // heads
        assert self.head_dim * heads == dim, "dim must be divisible by heads"

        self.qkv = torch.nn.Linear(dim, dim * 3, bias=False)
        self.out = torch.nn.Linear(dim, dim, bias=False)

    def forward(self, x, mask=None):
        B, L, D = x.shape
        qkv = self.qkv(x)                     # (B, L, 3*D)
        q, k, v = qkv.chunk(3, dim=-1)        # each (B, L, D)

        # reshape for multi‑head
        q = q.view(B, L, self.heads, self.head_dim).transpose(1, 2)  # (B, h, L, d_h)
        k = k.view(B, L, self.heads, self.head_dim).transpose(1, 2)
        v = v.view(B, L, self.heads, self.head_dim).transpose(1, 2)

        # pad sequence to allow sliding window at borders
        pad = self.window
        k = F.pad(k, (0, 0, pad, pad), value=-1e9)   # (B, h, L+2w, d_h)
        v = F.pad(v, (0, 0, pad, pad), value=0.0)

        # unfold to obtain local neighborhoods
        k_local = k.unfold(dimension=2, size=2 * self.window + 1, step=1)  # (B, h, L, 2w+1, d_h)
        v_local = v.unfold(dimension=2, size=2 * self.window + 1, step=1)

        # compute scaled dot‑product
        q = q.unsqueeze(-2)                     # (B, h, L, 1, d_h)
        # (rest of implementation omitted for brevity)
```
---

## Module 2 — contenu

## 2.1 Sources de données massives et licences d’utilisation  

| Source | Taille approximative (2025) | Type de contenu | Licence principale |
|--------|-----------------------------|----------------|--------------------|
| **WebText‑2023** | — | Articles, forums, blogs | **CC‑BY‑SA‑4.0** (extrait de Reddit) |
| **LAION‑5B** | — | Image‑texte (captions) | **CC‑BY‑4.0** (images) + **CC‑0** (captions) |
| **Common Crawl 2025** | — | Pages web, code, PDF | **CC‑0** (public domain) – attention aux sous‑licences : certains sites imposent **robots.txt** ou **Terms of Service** restrictifs. |
| **AudioSet‑v2** | — | Clips audio 10 s | **CC‑BY‑4.0** (YouTube) – filtrage obligatoire des contenus protégés par droits d’auteur. |
| **Multilingual Wikipedia Dumps** | — | Articles encyclopédiques | **CC‑BY‑SA‑3.0** (Wikimedia) |

**Bonnes pratiques de conformité**  

* Conserver les métadonnées de licence dans un champ `license` du tableau de données.  
* Implémenter un **audit de licence** automatisé : chaque URL est résolue, le header `X-Robots-Tag` et le `robots.txt` sont analysés ; les URLs bloquées sont exclues.  
* Pour les images LAION, appliquer le script fourni par le projet : `filter_by_license.py` (voir section 2.2).  

---

## 2.2 Filtrage automatisé  

### 2.2.1 Détection de contenu toxique  

```python
import json, requests, time
from tqdm import tqdm

PERSPECTIVE_KEY = "YOUR_API_KEY"
TOXICITY_THRESHOLD = 0.7

def is_toxic(text: str) -> bool:
    """Appel à l’API Perspective (v3). Retourne True si le score TOXICITY > seuil."""
    payload = {
        "comment": {"text": text},
        "languages": ["en"],
        "requestedAttributes": {"TOXICITY": {}}
    }
    resp = requests.post(
        f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={PERSPECTIVE_KEY}",
        json=payload,
        timeout=5,
    )
    resp.raise_for_status()
    score = resp.json()["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
    return score >= TOXICITY_THRESHOLD

def filter_toxic(dataset_path: str, out_path: str):
    with open(dataset_path, "r", encoding="utf-8") as fin, \
         open(out_path, "w", encoding="utf-8") as fout:
        for line in tqdm(fin):
            obj = json.loads(line)
            if not is_toxic(obj["text"]):
                fout.write(json.dumps(obj) + "\n")
            time.sleep(0.05)   # respect du quota public
```

*Le code utilise l’API publique de Perspective ; en production, privilégier le **batch endpoint** (Google Cloud) pour éviter le throttling.*  

### 2.2.2 Déduplication avec MinHash (LSH)  

```python
from datasketch import MinHash, MinHashLSH
import json, gzip

# Paramètres LSH
NUM_PERM = 128          # nombre de permutations, balance précision/mémoire
THRESHOLD = 0.85        # Jaccard cible pour considérer deux documents comme dupes

lsh = MinHashLSH(threshold=THRESHOLD, num_perm=NUM_PERM)
store = {}              # id → MinHash (pour récupération)

def shingle(text: str, k: int = 5) -> set:
    """Retourne l’ensemble des k‑shingles (tokens) d’un texte."""
    tokens = text.lower().split()
    return {" ".join(tokens[i:i+k]) for i in range(len(tokens)-k+1)}

def add_to_lsh(doc_id: str, text: str):
    m = MinHash(num_perm=NUM_PERM)
    for s in shingle(text):
        m.update(s.encode("utf8"))
    lsh.insert(doc_id, m)
    store[doc_id] = m

def is_duplicate(doc_id: str, text: str) -> bool:
    m = MinHash(num_perm=NUM_PERM)
    for s in shingle(text):
        m.update(s.encode("utf8"))
    # recherche de voisins
    neighbours = lsh.query(m)
    # on exclut le même id (cas de ré‑insertion)
    return any(nb != doc_id for nb

---

## Module 3 — contenu

## 3.1 Parallélisme hybride  

| Type | Niveau | Principe | Coût de communication | Exemple d’implémentation |
|------|--------|----------|----------------------|--------------------------|
| **Data‑parallelism** | GPU‑level | Chaque GPU possède une copie complète du modèle ; le mini‑batch est découpé en sous‑batches. | All‑reduce des gradients (complexité dépendante du nombre de paramètres et du nombre de GPU). | `torch.nn.parallel.DistributedDataParallel` (DDP). |
| **Tensor‑parallelism** | Op‑level | Un même tenseur (ex. matrice de QKV) est découpé sur plusieurs GPU ; chaque GPU calcule une partie de l’opération. | All‑gather / reduce‑scatter (complexité dépendante du découpage du tenseur). | Megatron‑LM `ColumnParallelLinear`, `RowParallelLinear`. |
| **Pipeline‑parallelism** | Layer‑level | Le réseau est partitionné en *stages* ; chaque GPU exécute un sous‑ensemble de couches, les activations sont transmises en flux. | Latence de pipeline additionnée à l’all‑reduce des gradients de chaque stage. | `torch.distributed.pipeline.sync.Pipe`. |

**Combinaison typique**  

```
# Configuration répartie sur plusieurs nœuds et GPU
# Tensor‑parallelism à deux voies (division des matrices QKV)
# Pipeline‑parallelism à deux voies (répartition des couches)
# Data‑parallelism sur les groupes restants
```

### 3.1.1 Calcul de la capacité mémoire  

Modèle : Transformer avec plusieurs millions de paramètres, ce qui représente plusieurs dizaines de mégaoctets en précision simple et un peu moins en précision demi‑précision.  
Activations : Le produit du nombre de couches, de la taille du batch, de la longueur de séquence et de la dimension du modèle donne plusieurs gigaoctets en demi‑précision.  

Avec ZeRO‑3, **tous les paramètres, gradients et états d’optimiseur sont sharded** → chaque GPU ne garde qu’une fraction du total, proportionnelle aux degrés de parallélisme tensoriel et de données.  
Exemple : avec un parallélisme tensoriel et de données à deux voies chacun, chaque GPU ne conserve qu’une petite partie des paramètres, gradients et états, de l’ordre de quelques mégaoctets.  
Le facteur limitant devient alors la taille des activations et les tampons de communication, qui occupent plusieurs gigaoctets.

## 3.2 Optimiseurs de dernière génération  

| Optimiseur | Mémoire supplémentaire | Particularité | Usage recommandé |
|------------|------------------------|---------------|-----------------|
| **AdamW + LAMB** | Mémoire proportionnelle aux paramètres (moments) | Ajuste le taux d’apprentissage par couche, stable pour de très grands lots | Fine‑tuning de modèles très larges. |
| **Adafactor** | Mémoire proportionnelle aux paramètres (sans moments explicites) | Conçu pour des modèles extrêmement grands | Pré‑entraînement de modèles de grande taille. |
| **ZeRO‑3 (DeepSpeed)** | Mémoire additionnelle négligeable grâce au sharding complet, avec option de compression | Sharding complet, compression optionnelle | Tout entraînement distribué au-delà de quelques GPU. |

### 3.2.1 Paramétrage DeepSpeed + ZeRO‑3  

```json
{
  "train_batch_size": 512,
  "gradient_accumulation_steps": 2,
  "zero_optimization": {
    "stage": 3,
    "offload_param": {
      "device": "cpu",
      "pin_memory": true
    },
    "offload_optimizer": {
      "device": "cpu",
      "pin_memory": true
    },
    "stage3_max_live_parameters": 1e9,
    "stage3_max_reuse_distance": 1e9,
    "stage3_prefetch_bucket_size": 5e7,
    "stage3_param_persistence_threshold": 1e5
  },
  "fp16": {
    "enabled": true,
    "loss_scale": 0,
    "initial_scale_power": 16
  },
  "optimizer": {
    "type": "AdamW",
    "params": {
      "lr": 5e-5,
      "betas": [0.9, 0.98],
      "eps": 1e-6,
      "weight_decay": 0.01
    }
  },
  "scheduler": {
    "type": "WarmupCosine",
    "params": {
      "warmup_min_lr": 0,
      "warmup_max_lr": 5e-5,
      "warmup_num_steps": 2000,
      "total_num_steps": 200000
    }
  }
}
```

*Notes*  
- `loss_scale = 0` active le **dynamic loss scaling** de DeepSpeed.  
- `offload_param`/`offload_optimizer` permettent de dépasser la capacité GPU en stockant les paramètres et états sur le CPU + NVMe, tout en gardant les activations en GPU.  
- `stage3_max_live_parameters` doit être supérieur au nombre de paramètres actifs simultanément, ce qui correspond à plusieurs dizaines de mégaoctets.

## 3.3 Gestion de la précision mixte  

| Technique | Description | Risques |
|-----------|-------------|---------|
| | | |

---

## Module 4 — contenu

## Module 4 – Évaluation, interprétabilité et déploiement de modèles de fondation (2025‑2026)

### 4.1. Métriques de performance et protocoles d’évaluation

| Métrique | Domaine | Formule | Référence implémentation |
|----------|---------|--------|--------------------------|
| **Perplexité** | LM texte | `exp(loss)` où `loss` = cross‑entropy moyenne | `torch.nn.CrossEntropyLoss` + `torch.exp` |
| **BLEU‑4** | Traduction / génération | `BLEU = 0.25 * Σ_{n=1}^{4} w_n * log(p_n)` (w_n = 0.25) | `sacrebleu.corpus_bleu` |
| **ROUGE‑L** | Résumé | `ROUGE‑L = F1 = 2 * (R * P) / (R + P)` | `rouge_score.rouge_scorer.RougeScorer` |
| **mAP@k** | Recherche d’images | Moyenne des précisions à chaque rang jusqu’à *k* | `torchmetrics.retrieval.mean_average_precision` |
| **Exact Match (EM)** | QA | `EM = 1` si la réponse prédite = référence (après normalisation) | `datasets.load_metric("squad")` |
| **Calibration error (ECE)** | Probabilités | `ECE = Σ_{b=1}^{B} |acc(b) - conf(b)| * |B_b|/N` | `torchmetrics.CalibrationError` |
| **Latency (ms)** | Inference | Temps moyen de passage d’un batch (GPU + CPU) | `torch.cuda.Event` + `time.perf_counter` |
| **Throughput (tokens/s)** | Inference | `tokens_processed / inference_time` | `torch.cuda.synchronize()` + `time` |

#### 4.1.1. Protocole d’évaluation standard (C4, MMLU, VQAv2)

1. **Séparer** les jeux en *train / dev / test* **avant** toute transformation (tokenisation, normalisation).  
2. **Fixer** le seed global (`torch.manual_seed(42)`, `numpy.random.seed(42)`, `random.seed(42)`) pour garantir la reproductibilité.  
3. **Appliquer** le même *tokenizer* (ex. `tiktoken.get_encoding("cl100k_base")`) à toutes les splits.  
4. **Évaluer** le modèle **sans** gradient (`model.eval(); torch.no_grad()`).  
5. **Enregistrer** les métriques dans un artefact JSON conforme à la *MLflow* schema `mlflow.entities.metric.Metric`.  

### 4.2. Interprétabilité et diagnostics

| Technique | Objectif | Implémentation concrète (PyTorch) |
|-----------|----------|-----------------------------------|
| **Attention rollout** | Visualiser la contribution cumulative des têtes d’attention | `torch.nn.functional.softmax` → produit matriciel cumulatif |
| **Integrated Gradients** | Attribution de l’influence des tokens d’entrée sur la sortie | `captum.attr.IntegratedGradients` |
| **Neuron‑level probing** | Identifier les neurones qui codifient des propriétés linguistiques (POS, NER) | Linear probe `sklearn.linear_model.LogisticRegression` sur les activations de la couche `model.transformer.h[5].mlp` |
| **Sparse Shapley values** | Estimer la valeur marginale d’un sous‑ensemble de paramètres dans un MoE | `shap.KernelExplainer` avec masque de routage `gate_logits` |
| **Log‑probability heatmaps** | Détecter les tokens générés avec une probabilité anormale (hallucination) | `torch.log_softmax` sur la dernière couche, visualisation `matplotlib.pyplot.imshow` |

#### 4.2.1. Exemple : visualisation d’une attention rollout

```python
import torch
import matplotlib.pyplot as plt
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "bigscience/bloom-560m"
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16).cuda()
tokenizer = AutoTokenizer.from_pretrained(model_name)

def attention_rollout(input_ids, heads=None):
    """
    Retourne une matrice (seq_len, seq_len) de l'attention cumulée.
    Si `heads` est None, toutes les têtes sont agrégées par moyenne.
    """
    model.eval()
    with torch.no_grad():
        outputs = model.transformer(input_ids, output_attentions=True)
    # outputs.attentions : tuple(Layers) où chaque layer = (batch, heads, seq, seq)
    attentions = torch.stack(outputs.attentions)               # (L, B, H, S, S)
    if heads is not None:
        attentions = attentions[:, :, heads, :, :]             # sélectionner têtes
    # moyenne sur les têtes sélectionnées
    attentions = attentions.mean(dim=2)                        # (L, B, S, S)
    # ajouter l'identité pour le rollout (voir Abnar & Zuidema, 2020)
    eye = torch.eye(attentions.size(-1), device=attentions.device)
    attentions = attentions + eye
    # produit matriciel cumulatif sur les couches
    rollout = attentions[0]
    for layer in attentions[1:]:
        rollout = torch.matmul(layer, rollout)
    # normaliser
    rollout = rollout / rollout.sum(dim=-1, keepdim=True)
    return rollout.squeeze



---

## Module 5 — contenu

## Module 5 – Déploiement, inference et maintenance des modèles de fondation (2026)

### 5.1 Architecture de serving

| Niveau | Fonction | Outils courants (2026) | Points de vigilance |
|--------|----------|-----------------------|----------------------|
| **Modèle** | Stockage, versioning, conversion (FP16/BF16/INT8/FP4) | Hugging Face Hub, ModelStore (S3‑compatible), `torch.save`/`torch.load` avec `metadata.json` | Conserver le hash SHA‑256 du fichier `.bin` pour garantir l’intégrité. |
| **Runtime** | Exécution du modèle, gestion du batch, quantisation dynamique | **TorchServe** (v0.9+), **vLLM** (optimisé pour MoE), **TensorRT‑LLM**, **DeepSpeed‑Inference** | Vérifier la compatibilité du runtime avec le format de poids (ex. `safetensors` → `torch.load` nécessite `torch>=2.3`). |
| **Orchestration** | Scaling, load‑balancing, fail‑over | **Kubernetes** + **KServe** (v0.12), **Ray Serve** (v2.9), **SageMaker Inference** | Les pods doivent être pin‑né à des GPU spécifiques pour éviter le “GPU sharing” non‑déterministe. |
| **Observabilité** | Métriques latence, utilisation GPU, drift de données | **Prometheus** + **Grafana**, **OpenTelemetry**, **Weights & Biases** (monitoring de loss & logits) | Ne pas confondre *latence moyenne* et *p99 latency*; les SLA sont souvent exprimées en p99. |
| **Sécurité** | Authentification, sandboxing, mitigation de prompt‑injection | **Istio** mTLS, **OpenAI‑style content filter**, **OpenAI‑style jailbreak detection** | Le filtrage doit être appliqué *avant* le tokenisation pour éviter les contournements basés sur Unicode. |

---

### 5.2 Quantisation et compilation

| Technique | Niveau de précision | Gains typiques | Impact sur la qualité | Contraintes |
|-----------|--------------------|----------------|-----------------------|-------------|
| **Post‑training INT8** (static) | INT8 | Amélioration notable du débit et réduction de la consommation mémoire | Dégradation très légère du score BLEU/ROUGE | Nécessite une calibration sur un jeu de tokens représentatif. |
| **Post‑training FP4** (4‑bit) | FP4 (E4M3) | Accélération importante du débit et forte réduction de la mémoire occupée | Dégradation légèrement plus importante du score BLEU/ROUGE | Sensible aux valeurs extrêmes ; appliquer une quantisation *weight‑only*. |
| **Quant‑aware training (QAT)** | INT8 | Gains de débit et de mémoire comparables au post‑training INT8 | Perte de performance quasi négligeable sur les métriques BLEU/ROUGE | Nécessite un ré‑entraînement supplémentaire. |
| **Compilation via `torch.compile`** | FP16/BF16 | Accélération modérée sur CPU et GPU | Aucun impact mesurable sur la qualité | Le graphe doit rester *static* (pas de `torch.jit.script` + `torch.compile` simultané). |

#### Exemple : quantisation INT8 post‑training avec `optimum`

```python
# quantize_int8.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from optimum.intel import INCModelForCausalLM  # Intel Neural Compressor integration
import os

MODEL_ID = "meta-llama/Meta-Llama-3-8B"
OUTPUT_DIR = "./quantized_llama8b_int8"

# 1️⃣ Chargement du modèle FP16 (déjà converti en safetensors)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
model_fp16 = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto",  # charge les sous‑modules sur les GPU disponibles
    trust_remote_code=True,
)

# 2️⃣ Calibration dataset (jeu de phrases représentatives, déjà tokenisées)
calib_dataset = torch.load("calib_dataset.pt")  # Tensor[*, seq_len]

# 3️⃣ Application de la quantisation INT8 via Intel Neural Compressor
quantized_model = INCModelForCausalLM.from_pretrained(
    model_fp16,
    calibration_dataset=calib_dataset,
    quantization_config={"approach": "static"},
)

# 4️⃣ Sauvegarde du modèle quantisé
quantized_model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
```