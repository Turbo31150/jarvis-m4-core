# 159 €/mois

> Référence `claude-code-mastery-bundle` · 159 €

## Plan

**Formation : « 159 €/mois » (référence claude-code-mastery-bundle, prix 159 €)**  

## Module 1 – Architecture des modèles de langage à grande échelle  
**Objectif mesurable :** L’apprenant pourra concevoir et documenter une architecture de modèle de langage de type Transformer contenant au moins 12 M de paramètres, en justifiant chaque choix d’hyper‑paramètre.  
**Notions couvertes**  
1. Structure du Transformer (couches d’attention multi‑têtes, normalisation, résidus).  
2. Paramétrisation du modèle : dimensions d’embedding, nombre de têtes, profondeur.  
3. Stratégies de parallélisation (pipeline, data‑parallel, tensor‑parallel).  
4. Gestion de la mémoire GPU (activation checkpointing, mixed‑precision).  
5. Métriques de capacité (paramètres, FLOPs, temps d’inférence).

## Module 2 – Pré‑traitement et tokenisation avancée  
**Objectif mesurable :** L’apprenant sera capable de mettre en place une pipeline de tokenisation BPE ou SentencePiece adaptée à un corpus de 50 Go, en évaluant le taux de couverture ≥ 99,5 %.  
**Notions couvertes**  
1. Algorithmes de tokenisation (BPE, Unigram, WordPiece).  
2. Construction de vocabulaires à partir de données brutes.  
3. Normalisation Unicode (NFKC, NFKD) et nettoyage de texte.  
4. Gestion des séquences longues (sliding window, truncation).  
5. Analyse de la couverture et impact sur la perplexité.

## Module 3 – Fine‑tuning supervisé et instruction‑following  
**Objectif mesurable :** L’apprenant pourra fine‑tuner un modèle pré‑entraîné sur une tâche de classification texte avec une amélioration de +10 % du score F1 par rapport au baseline, en moins de 4 heures d’entraînement sur un serveur 8 GPU.  
**Notions couvertes**  
1. Sélection du jeu de données et création de prompts d’instruction.  
2. Techniques de mise à jour des poids (full‑model, LoRA, Q‑LoRA).  
3. Gestion du déséquilibre de classes (re‑weighting, focal loss).  
4. Évaluation continue (early‑stopping, validation croisée).  
5. Optimisation de l’apprentissage (AdamW, cosine‑annealing, gradient‑accumulation).

## Module 4 – Déploiement scalable et sécurisation des API LLM  
**Objectif mesurable :** L’apprenant pourra déployer une API RESTful hébergeant le modèle fine‑tuné, capable de servir 200 RPS avec latence moyenne ≤ 120 ms, tout en appliquant le chiffrement TLS et le contrôle d’accès OAuth 2.0.  
**Notions couvertes**  
1. Containerisation avec Docker et orchestration Kubernetes (pods, services, autoscaling).  
2. Optimisation d’inférence (ONNX Runtime, TensorRT, quantisation int8).  
3. Gestion des quotas et du throttling (token bucket, rate limiting).  
4. Sécurité des endpoints (TLS, JWT, scopes OAuth 2.0).  
5. Monitoring (Prom

---

## Module 1 — contenu

# Module 1 – Architecture des modèles de langage à grande échelle  

## 1. Structure du Transformer  

| Composant | Fonction | Formule clé | Dimensions typiques |
|-----------|----------|------------|---------------------|
| **Embedding** | Convertit chaque token en vecteur dense | \(E \in \mathbb{R}^{V \times d_{\text{model}}}\) | \(V\) vocabulaire, \(d_{\text{model}}=768\) (BERT‑base) |
| **Positional Encoding** | Injecte l’ordre séquentiel | \(PE_{(pos,2i)} = \sin(pos/10000^{2i/d_{\text{model}}})\) <br> \(PE_{(pos,2i+1)} = \cos(pos/10000^{2i/d_{\text{model}}})\) | même forme que l’embedding |
| **Multi‑Head Self‑Attention (MHSA)** | Calcule l’attention sur toutes les positions | \(\text{Attention}(Q,K,V)=\text{softmax}\!\left(\frac{QK^{\top}}{\sqrt{d_k}}\right)V\) <br> \(Q=W_QX,\;K=W_KX,\;V=W_VX\) | \(h\) têtes, chaque tête : \(d_k=d_v=d_{\text{model}}/h\) |
| **Add & Norm** | Résidu + LayerNorm | \(\text{LN}(X+ \text{Sublayer}(X))\) | \(\text{LN}\) opère sur \(\mathbb{R}^{L\times d_{\text{model}}}\) |
| **Feed‑Forward Network (FFN)** | Deux couches linéaires séparées par GELU | \(\text{FFN}(x)=W_2\;\text{GELU}(W_1x+b_1)+b_2\) | \(W_1\in\mathbb{R}^{d_{\text{model}}\times d_{\text{ff}}}\), \(W_2\in\mathbb{R}^{d_{\text{ff}}\times d_{\text{model}}}\) |
| **Stack** | Répéter le bloc (MHSA + FFN) N fois | N = profondeur du modèle | N typique : 12 (BERT‑base) |

### Paramétrisation de chaque bloc  

- **Paramètres d’attention** (par bloc)  
  \[
  \underbrace{3 \times d_{\text{model}} \times d_{\text{model}}}_{W_Q,W_K,W_V}
  + \underbrace{d_{\text{model}} \times d_{\text{model}}}_{W_O}
  = 4\,d_{\text{model}}^2
  \]
- **Paramètres du FFN** (par bloc)  
  \[
  d_{\text{model}} \times d_{\text{ff}} + d_{\text{ff}} \times d_{\text{model}} = 2\,d_{\text{model}} \times d_{\text{ff}}
  \]
- **Paramètres totaux** (sans embeddings)  
  \[
  N \times \bigl(4d_{\text{model}}^2 + 2d_{\text{model}}d_{\text{ff}}\bigr)
  \]

## 2. Dimensionnement pour ≥ 12 M paramètres  

On veut un modèle **Transformer décodé** (type GPT) avec au moins 12 M de paramètres.  
Choix usuels (inspirés de GPT‑2‑small) :

| Hyper‑paramètre | Valeur proposée | Raison |
|-----------------|----------------|--------|
| \(d_{\text{model}}\) | 768 | Produit \(d_{\text{model}}^2\) = 589 k → facteur clé |
| \(d_{\text{ff}}\) | 3072 (= 4 × \(d_{\text{model}}\)) | Conformité aux architectures originales |
| \(h\) (têtes) | 12 | \(d_k = d_v = 64\) (768/12) – taille de tête efficace sur GPU |
| \(N\) (profondeur) | 12 | 12 blocs donnent ~ 12 M de paramètres (voir calcul) |
| Vocabulaire | 50 k | Taille raisonnable pour un modèle francophone |

### Calcul détaillé  

- **Paramètres d’attention par bloc** : \(4 \times 768^2 = 2 359 296\)  
- **Paramètres du FFN par bloc** : \(2 \times 768 \times 3072 = 4 718 592\)  
- **Paramètres par bloc** : \(2 359 296 + 4 718 592 = 7 077 888\)  
- **Paramètres totaux (12 blocs)** : \(12 \times 7 077 888 = 84 934 656\) → 85 M, bien au‑dessus du seuil.  

Pour rester proche du minimum, on réduit \(d_{\text{model}}\) à **512** et garde le même ratio \(d_{\text{ff}}=4d_{\text{model}}\) :

- Attention : \(4 \times 512^2 = 1 048 576\)  
- FFN : \(2 \times 512 \times 2048 = 2 097 152\)  
- Bloc : \(3 145 728\)  
- 12 blocs : **37 748 736** → > 12 M.  

Si

---

## Module 2 — contenu

## 2.1 Principes fondamentaux de la tokenisation

| Concept | Description vérifiable | Référence |
|---------|------------------------|-----------|
| **Byte‑Pair Encoding (BPE)** | Algorithme itératif qui fusionne les paires de symboles les plus fréquentes dans le texte brut. Chaque fusion crée un nouveau « token » et le vocabulaire est la liste des symboles (unigrammes) + des fusions. | Sennrich et al., *Neural Machine Translation of Rare Words with Subword Units*, 2015 |
| **Unigram (SentencePiece)** | Modèle probabiliste où chaque token possède une probabilité. Le vocabulaire est choisi par maximisation du log‑likelihood sous contrainte de taille. | Kudo, *Subword Regularization: Improving Neural Network Translation Models with Subword Units*, 2018 |
| **SentencePiece** | Implémentation open‑source qui supporte BPE, Unigram, WordPiece et fournit un pré‑processeur (normalisation, tokenisation du texte brut). | https://github.com/google/sentencepiece |
| **Couverture** | Pourcentage de caractères du corpus qui sont représentés par des tokens du vocabulaire. Calcul : `coverage = 1 - (OOV_characters / total_characters)`. | Méthode utilisée dans les rapports de HuggingFace Tokenizers |

---

## 2.2 Pipeline complet de tokenisation pour un corpus de 50 Go

### 2.2.1 Pré‑requis (Python ≥ 3.8)

```bash
pip install sentencepiece tqdm
```

### 2.2.2 Étape 1 – Normalisation Unicode

```python
import unicodedata

def normalize(text: str) -> str:
    """
    Applique la normalisation NFKC (compatibilité + composition) recommandée
    pour les modèles LLM afin de réduire la variance orthographique.
    """
    return unicodedata.normalize('NFKC', text)
```

> **Piège** : NFKD décompose les caractères (ex. « é » → « e´ ») et augmente la taille du vocabulaire. Utiliser NFKC conserve les caractères composés tout en normalisant les variantes.

### 2.2.3 Étape 2 – Nettoyage minimal

```python
import re

def clean(text: str) -> str:
    """
    Supprime les espaces blancs multiples, les balises HTML résiduelles
    et les caractères de contrôle non imprimables.
    """
    text = re.sub(r'\s+', ' ', text)               # compactage des espaces
    text = re.sub(r'<[^>]+>', '', text)            # suppression HTML simple
    text = ''.join(ch for ch in text if ch.isprintable())
    return text.strip()
```

> **Piège** : Ne pas supprimer les caractères de ponctuation qui sont utiles pour la segmentation syntaxique (ex. « ? », « ! »). Le code ci‑dessus ne les retire pas.

### 2.2.4 Étape 3 – Construction du vocabulaire avec **SentencePiece**

```python
import sentencepiece as spm
from pathlib import Path
from tqdm import tqdm

# Chemin du répertoire contenant les fichiers texte bruts
DATA_DIR = Path('/data/corpus_50go')
VOCAB_SIZE = 32000               # taille typique pour 99‑% de couverture sur 50 Go
MODEL_PREFIX = 'spm_50go'

def generate_input_file(tmp_path: Path) -> Path:
    """
    Concatène les fichiers du corpus (déjà normalisés) dans un seul
    fichier texte que SentencePiece consomme. Le fichier est écrit en UTF‑8.
    """
    out_file = tmp_path / 'corpus.txt'
    with out_file.open('w', encoding='utf-8') as fout:
        for file_path in tqdm(sorted(DATA_DIR.rglob('*.txt')), desc='Lecture corpus'):
            with file_path.open('r', encoding='utf-8') as fin:
                for line in fin:
                    line = normalize(line)
                    line = clean(line)
                    fout.write(line + '\n')
    return out_file

def train_spm(input_file: Path):
    """
    Lance l'entraînement du modèle SentencePiece en mode BPE.
    --character_coverage 1.0 garantit que tous les caractères Unicode sont
    pris en compte (utile pour les langues à faible fréquence).
    """
    spm.SentencePieceTrainer.train(
        input=str(input_file),
        model_prefix=MODEL_PREFIX,
        vocab_size=VOCAB_SIZE,
        model_type='bpe',               # ou 'unigram' pour le modèle Unigram
        character_coverage=1.0,
        pad_id=0,
        unk_id=1,
        bos_id=2,
        eos_id=3,
        user_defined_symbols='[CLS],[SEP],[MASK]',  # symboles réservés
        train_extremely_large_corpus=True,           # optimisation pour >10 Go
        input_sentence_size=10000000,               # limite de lignes lues en mémoire
        shuffle_input_sentence=True
    )
    print(f'Modèle entraîné → {MODEL_PREFIX}.model et {MODEL_PREFIX}.vocab')

if __name__ == '__main__':
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        corpus_file = generate_input_file(tmp_path)
        train_spm(corpus_file)
```

**Points de contrôle**  

| Étape | Vérification | Commande / Code |
|------|--------------|-----------------|
| Normalisation | Aucun caractère « é » n’est décomposé en « e´ ». | `unicodedata.normalize('NFKC', 'é') == 'é'` |
|

---

## Module 3 — contenu

## 3.1. Sélection du jeu de données et création de prompts d’instruction  

| Étape | Action concrète | Vérification |
|------|----------------|--------------|
| 3.1.1 | Choisir un jeu de données public déjà découpé en `train/validation` (ex. **IMDb** pour la classification sentiment). | `datasets.load_dataset("imdb")` renvoie deux splits avec 25 000 exemples chacun. |
| 3.1.2 | Normaliser le texte : `NFKC` Unicode, suppression des espaces multiples, conversion en minuscules si le modèle n’est pas case‑sensitive. | `unicodedata.normalize("NFKC", txt)` + `re.sub(r"\s+", " ", txt)`. |
| 3.1.3 | Construire un *prompt* d’instruction compatible avec le format du modèle (ex. LLaMA‑2‑Chat, Falcon‑Chat). Exemple :  

```text
[INST] Vous êtes un classificateur de sentiment. Répondez par "POSITIVE" ou "NEGATIVE".  
Texte : {review} [/INST]
```  

| 3.1.4 | Créer la colonne `input_ids` via le tokenizer du modèle, en tronquant à `max_length=512` et en activant le `padding="max_length"`. | `tokenizer(..., truncation=True, padding="max_length", max_length=512)` produit des tensors de même taille. |
| 3.1.5 | Encoder la cible sous forme de texte (`"POSITIVE"` / `"NEGATIVE"`), puis tokeniser de même. | `tokenizer(target, add_special_tokens=False)` → `labels`. |

> **Note** : le même *prompt* doit être appliqué à tous les exemples ; toute variation introduit du bruit d’instruction.

---

## 3.2. Techniques de mise à jour des poids  

### 3.2.1. Fine‑tuning full‑model  

```python
from transformers import AutoModelForCausalLM, Trainer, TrainingArguments

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")
training_args = TrainingArguments(
    output_dir="./llama2_finetuned",
    per_device_train_batch_size=2,          # 7 B → 2×16 GB GPU
    gradient_accumulation_steps=8,          # équivaut à batch size 16
    num_train_epochs=3,
    learning_rate=2e-5,
    fp16=True,                              # mixed‑precision
    evaluation_strategy="epoch",
    save_total_limit=2,
    logging_steps=50,
)
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
    data_collator=default_data_collator,
)
trainer.train()
```

* **GPU mémoire** : chaque paramètre du modèle occupe 4 bytes en FP32, 2 bytes en FP16. Un modèle 7 B nécessite ~28 GB en FP16 + overhead ≈ 30 GB → impossible sur un seul 16 GB GPU → **gradient accumulation** et **ZeRO‑3** sont requis pour la production.

### 3.2.2. LoRA (Low‑Rank Adaptation)  

```python
import peft
from peft import LoraConfig, get_peft_model

lora_cfg = LoraConfig(
    r=64,               # rang de la matrice low‑rank
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],  # modules d’attention
    lora_dropout=0.05,
    bias="none",
)
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf", torch_dtype=torch.float16, device_map="auto"
)
model = get_peft_model(model, lora_cfg)
model.print_trainable_parameters()   # < ≈ 0.1 % des poids sont entraînables
```

* **Avantage** : seule la matrice `A` (64 × d) et `B` (d × 64) sont mises à jour → ≈ 0.1 % des paramètres, donc 8 GB de VRAM suffisent pour le même batch.  
* **Limite** : LoRA ne modifie pas les embeddings ni la tête de sortie ; si le vocabulaire change, il faut un fine‑tuning complet.

### 3.2.3. Q‑LoRA (Quantized LoRA)  

```python
from transformers import BitsAndBytesConfig

bnb_cfg = BitsAndBytesConfig(
    load_in_4bit=True,          # 4‑bit quantisation
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=bnb_cfg,
    device_map="auto",
)
model = get_peft_model(model, lora_cfg)   # LoRA sur modèle 4‑bit
```

* **Mémoire** : 4‑bit quantisation réduit la taille du modèle à ~

---

## Module 4 — contenu

## 4.1 Containerisation avec Docker  

| Étape | Action | Commande / Dockerfile | Vérification |
|------|--------|-----------------------|--------------|
| 1. Base image | Utiliser une image officielle CUDA 12.1‑runtime‑ubuntu22.04 (compatible avec les drivers 525+). | `FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04` | `docker run --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi` |
| 2. Installation des dépendances système | `apt-get update && apt-get install -y python3-pip git` | `RUN apt-get update && apt-get install -y python3-pip git && rm -rf /var/lib/apt/lists/*` | `dpkg -l | grep python3-pip` |
| 3. Création d’un environnement Python isolé | `python3 -m venv /opt/venv` + activation | `ENV VIRTUAL_ENV=/opt/venv PATH="/opt/venv/bin:$PATH"` | `which python` doit pointer vers `/opt/venv/bin/python` |
| 4. Installation des paquets Python | `pip install fastapi uvicorn[standard] onnxruntime-gpu[openvino] python-jose[cryptography]` | `RUN pip install --no-cache-dir fastapi uvicorn[standard] onnxruntime-gpu python-jose[cryptography]` | `pip show onnxruntime-gpu` |
| 5. Copie du code et du modèle ONNX | `COPY ./app /app` et `COPY ./model/model_int8.onnx /app/` | `WORKDIR /app`<br>`COPY . /app` | `ls /app` doit contenir `main.py` et `model_int8.onnx` |
| 6. Exposition du port | `EXPOSE 8080` | `EXPOSE 8080` | `docker inspect <container>` → `Ports` |
| 7. Entrypoint | Lancer `uvicorn` en mode production | `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]` | `docker logs` montre le serveur démarré sur `0.0.0.0:8080` |

**Dockerfile complet (commenté)**  

```dockerfile
# 1. Image de base avec CUDA 12.1 et support GPU
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# 2. Installation des paquets système requis
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-pip \
        python3-venv \
        git && \
    rm -rf /var/lib/apt/lists/*

# 3. Crée un environnement virtuel dédié
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 4. Installation des dépendances Python (versions fixes pour reproductibilité)
RUN pip install --no-cache-dir \
        fastapi==0.109.0 \
        uvicorn[standard]==0.27.0 \
        onnxruntime-gpu==1.18.0 \
        python-jose[cryptography]==3.3.0

# 5. Copie du code source et du modèle ONNX quantifié int8
WORKDIR /app
COPY ./app /app
COPY ./model/model_int8.onnx /app/

# 6. Port exposé pour l’API REST
EXPOSE 8080

# 7. Démarrage du serveur FastAPI avec 4 workers (optimisé pour CPU‑bound + GPU inference)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
```

### Pièges concrets (Docker)  

| Symptomome | Cause fréquente | Remède |
|------------|-----------------|--------|
| `RuntimeError: CUDA driver version is insufficient` | Image CUDA trop ancienne par rapport aux drivers du nœud | Utiliser la même version majeure que le driver (`nvidia-smi` → driver 525 → CUDA 12.1) |
| `ImportError: libcuda.so.1: cannot open shared object file` | Le conteneur n’est pas lancé avec `--gpus all` | `docker run --gpus all …` ou config `runtime: nvidia` dans le pod |
| `FileNotFoundError: model_int8.onnx` | Le `COPY` ne correspond pas au chemin du build context | Vérifier le répertoire de build (`docker build -t myapi .`) et la structure du répertoire |
| `MemoryError` pendant le chargement du modèle | Pas de `--shm-size` suffisant (Docker default 64 MiB) | `docker run --shm-size=1g …` ou définir `emptyDir` `medium` dans le pod |

---

## 4.2 Orchestration Kubernetes  

### 4.2.1 Manifeste de déploiement (YAML)  

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-api
  labels:
    app: llm-api
spec:

---

## Module 5 — contenu

## Module 5 – Évaluation avancée, interprétabilité et gestion du biais  

### Objectif mesurable  
L’apprenant pourra mettre en place une suite d’évaluations automatisées incluant :  
* métriques de génération (BLEU, ROUGE‑L, BERTScore) ;  
* tests de robustesse (perturbations lexicales, adversariales) ;  
* analyses d’interprétabilité (visualisation d’attention, SHAP) ;  
* détection de biais (disparités de performance selon attributs protégés).  

Il devra identifier **au moins deux** sources de biais dans un modèle LLM fine‑tuné et proposer une mitigation mesurable (ex. ré‑échantillonnage, poids de perte).  

---

## 5.1 Métriques de génération  

| Métrique | Description | Implémentation vérifiable |
|----------|-------------|---------------------------|
| **BLEU** (Papineni et al., 2002) | N‑gram overlap, pénalité de longueur. | `sacrebleu.corpus_bleu` |
| **ROUGE‑L** | Longest Common Subsequence, sensible à l’ordre. | `rouge_score.rouge_scorer.RougeScorer(['rougeL'])` |
| **BERTScore** | Similarité de vecteurs contextualisés (cosine). | `bert_score.score` (modèle `roberta-large`) |

> **Vérification** : les scores doivent être calculés sur le même jeu de test (ex. `xsum` ou `samsum`) avec la même tokenisation que le modèle (`tokenizer.encode`).  

### Code de base (Python 3.9)

```python
# -*- coding: utf-8 -*-
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from datasets import load_dataset
import sacrebleu
from rouge_score import rouge_scorer
from bert_score import score as bert_score

# 1. Chargement du modèle et du tokenizer
model_name = "google/flan-t5-base"
model = AutoModelForSeq2SeqLM.from_pretrained(model_name, torch_dtype=torch.float16).to("cuda")
tokenizer = AutoTokenizer.from_pretrained(model_name)

# 2. Jeu de test (exemple : XSum – 100 premières entrées)
ds = load_dataset("xsum", split="test[:100]")

def generate(reference):
    inputs = tokenizer(reference["document"], truncation=True, max_length=512, return_tensors="pt").to("cuda")
    # génération beam search, 4 beams, max 128 tokens
    outputs = model.generate(**inputs, num_beams=4, max_length=128, early_stopping=True)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# 3. Boucle d’inférence
hypotheses, references = [], []
for ex in ds:
    hyp = generate(ex)
    hypotheses.append(hyp)
    references.append(ex["summary"])

# 4. BLEU (sacreBLEU) – tokenisation interne sacreBLEU (13‑gram)
bleu = sacrebleu.corpus_bleu(hypotheses, [references])
print(f"BLEU = {bleu.score:.2f}")

# 5. ROUGE‑L
scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
rouge_l = [scorer.score(ref, hyp)['rougeL'].fmeasure for ref, hyp in zip(references, hypotheses)]
print(f"ROUGE‑L (moyenne) = {sum(rouge_l)/len(rouge_l):.4f}")

# 6. BERTScore – batch size 8 pour limiter la RAM GPU
P, R, F1 = bert_score(hypotheses, references, lang="en", model_type="roberta-large", batch_size=8, device="cuda")
print(f"BERTScore F1 (moyenne) = {F1.mean().item():.4f}")
```

*Commentaires*  
* `torch_dtype=torch.float16` réduit la consommation GPU de ~30 % sans perte de précision notable pour la génération.  
* `max_length=128` évite les dépassements de mémoire lors du décodage.  
* `use_stemmer=True` dans ROUGE garantit la comparabilité avec les scores publiés.  

---

## 5.2 Tests de robustesse  

### 5.2.1 Perturbations lexicales  
* **Synonymes** : remplacer chaque token par un synonyme tiré de WordNet (`nltk.corpus.wordnet`).  
* **Typo aléatoire** : insérer, supprimer ou remplacer un caractère avec probabilité `p=0.05`.  

### 5.2.2 Attaques adversariales simples  
* **HotFlip** (Ebrahimi et al., 2018) : choisir le token dont le gradient de perte maximise la