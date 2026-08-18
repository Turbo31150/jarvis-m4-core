# DeepSeek & Open Source 2026

> Référence `deepseek-open` · 59 €

## Plan

## Module 1 – Installation et configuration de l’écosystème DeepSeek‑Open  
**Objectif mesurable** : Installer et valider un environnement de développement complet (Python 3.11, PyTorch 2.3, CUDA 12.2) capable d’exécuter le modèle DeepSeek‑Open 7B en moins de 5 GB de VRAM.  
**Notions couvertes**  
1. Gestion d’environnements virtuels avec `venv` et `conda` – vérification via `python -c "import torch; print(torch.cuda.is_available())"`  
2. Installation du package `deepseek-open` depuis le dépôt GitHub officiel (commit `v0.3.2`) – validation du checksum SHA‑256 du wheel  
3. Configuration du backend GPU : driver NVIDIA 560.xx, cuDNN 8.9, variables d’environnement `CUDA_VISIBLE_DEVICES`  
4. Test de chargement du modèle `deepseek/open-7b` via `torch.load` – temps de warm‑up < 2 s  
5. Mise en place de l’interface CLI `deepseek-cli` et du serveur HTTP `uvicorn` pour les requêtes REST  

## Module 2 – Utilisation de l’API DeepSeek‑Open pour l’inférence  
**Objectif mesurable** : Générer des réponses cohérentes (BLEU ≥ 30) sur le benchmark `OpenAI‑Evals` en moins de 200 ms d’inférence par token sur une RTX 4090.  
**Notions couvertes**  
1. Structure du modèle Transformer : couches d’attention, normalisation RMS, positionnement rotatif (RoPE)  
2. Paramétrage de `generation_config` (temperature, top‑p, max_new_tokens) – impact mesurable sur perplexité  
3. Gestion du tokenisation avec `tiktoken` – comparaison des tailles de vocabulaire (vocab‑size = 50 272)  
4. Optimisations inference : `torch.compile`, `torch.autocast`, quantisation INT8 via `bitsandbytes`  
5. Déploiement d’une API FastAPI 0.109 avec streaming de tokens – validation du débit (`tokens/s`)  

## Module 3 – Fine‑tuning supervisé du modèle DeepSeek‑Open 7B  
**Objectif mesurable** : Produire un modèle fine‑tuné qui atteint une perte moyenne ≤ 0.85 sur le dataset `Alpaca‑GPT4‑Data` (52 k exemples) en ≤ 6 heures d’entraînement sur un cluster de 4 x A100 80 GB.  
**Notions couvertes**  
1. Pré‑traitement des paires instruction/réponse – format `ChatML` et balises `<|assistant|>`  
2. Script `deepseek-train` : options `--lora-rank`, `--lora-alpha`, `--gradient-checkpointing` – calcul du nombre de paramètres entraînables (< 0.5 % du total)  
3. Stratégies d’apprentissage : LoRA, QLoRA, PEFT – comparaison des exigences en VRAM (LoRA ≈ 2 GB)  
4. Scheduler d’apprentissage `cosine` avec warm‑up 0.1 % – suivi du

---

## Module 1 — contenu

## 1️⃣ Gestion d’environnements virtuels  

| Action | Commande | Vérification |
|--------|----------|--------------|
| Créer un environnement **conda** dédié (Python 3.11) | `conda create -n ds-open python=3.11 -y && conda activate ds-open` | `python --version` → `3.11.x` |
| (Alternative) Créer un **venv** pur | `python3.11 -m venv ds-open && source ds-open/bin/activate` | `which python` pointe vers le répertoire `ds-open` |
| Installer **pip** à jour | `python -m pip install --upgrade pip setuptools wheel` | `pip --version` ≥ 23.3 |
| Vérifier la disponibilité du GPU dans le nouvel env | `python -c "import torch; print(torch.cuda.is_available())"` | `True` (sinon installer les drivers, voir § 3) |

> **Piège** : sous Windows, `conda activate` ne fonctionne pas dans un *cmd* lancé en mode non‑admin si le répertoire d’installation de conda n’est pas dans le `PATH`. Utilisez *Anaconda Prompt* ou ajoutez le chemin manuellement.

---

## 2️⃣ Installation du package `deepseek-open` (commit `v0.3.2`)  

1. **Cloner le dépôt** (tag ou commit exact)  

```bash
git clone https://github.com/deepseek-ai/deepseek-open.git
cd deepseek-open
git checkout v0.3.2   # ou le hash du commit correspondant
```

2. **Construire le wheel** (le projet utilise `setuptools` + `torch`)

```bash
python -m pip install build                # une fois seulement
python -m build --wheel                    # crée dist/deepseek_open-*.whl
```

3. **Vérifier le checksum SHA‑256** (exemple avec le wheel généré)

```bash
sha256sum dist/deepseek_open-*.whl
# → 3a7f5c9e8d...  dist/deepseek_open-0.3.2-py3-none-any.whl
```

> **Piège** : le checksum fourni dans le *release notes* de `v0.3.2` correspond au wheel pré‑compilé pour Linux x86_64. Sous macOS ou Windows, le wheel sera différent ; ne comparez que le hash du fichier que vous avez produit.

4. **Installation**  

```bash
python -m pip install dist/deepseek_open-0.3.2-py3-none-any.whl
# ou, si vous avez besoin du wheel pré‑compilé (Linux) :
# python -m pip install https://github.com/deepseek-ai/deepseek-open/releases/download/v0.3.2/deepseek_open-0.3.2-cp311-cp311-manylinux2014_x86_64.whl
```

5. **Vérifier la version installée**  

```bash
python -c "import deepseek_open; print(deepseek_open.__version__)"
# → 0.3.2
```

---

## 3️⃣ Configuration du backend GPU  

| Élément | Action | Commande / Variable |
|---------|--------|--------------------|
| Driver NVIDIA | Version ≥ 560.XX (compatible CUDA 12.2) | `nvidia-smi` → `Driver Version: 560.xx` |
| CUDA Toolkit | 12.2 (installé via le *runfile* ou le package OS) | `nvcc --version` → `release 12.2` |
| cuDNN | 8.9.x (placé dans `$CUDA_HOME/lib64`) | `cat /usr/include/cudnn_version.h | grep CUDNN_MAJOR` |
| Variable d’environnement | Limiter les GPU visibles | `export CUDA_VISIBLE_DEVICES=0` (ou `0,1` selon le besoin) |
| PyTorch CUDA build | 2.3.0+cu122 | `python -c "import torch; print(torch.version.cuda)"` → `12.2` |

> **Piège** : si vous avez plusieurs installations de CUDA (ex. 12.0 + 12.2), `torch` peut charger la mauvaise version. Supprimez ou renommez les dossiers `cuda-12.0` du `PATH` avant d’installer `torch==2.3.0+cu122`.

Installation de PyTorch avec le bon CUDA :

```bash
python -m pip install torch==2.3.0+cu122 torchvision==0.18.0+cu122 torchaudio==2.3.0+cu122 --extra-index-url https://download.pytorch.org/whl/cu122
```

---

## 4️⃣ Test de chargement du modèle `deepseek/open-7b`  

Le modèle est stocké sur le hub Hugging Face sous le nom `deepseek/open-7b`.  
On utilise `torch.load` directement sur le fichier `.pt` pour mesurer le temps de *warm‑up*.

```python
# file: test_load.py
import time
import torch
from pathlib import Path

# 1️⃣ Chemin du checkpoint (téléchargé préalablement avec `git lfs` ou `huggingface-cli`)
CKPT = Path("/data/models/deepseek/open-7b/pytorch_model

---

## Module 2 — contenu

## 2.1 Structure du modèle Transformer utilisé par DeepSeek‑Open 7B  

| Composant | Description | Référence |
|-----------|-------------|------------|
| **Embedding** | Token → vecteur dense (dimension 4096). Positionnement rotatif (RoPE) appliqué à chaque couche d’attention. | <https://arxiv.org/abs/2104.09864> |
| **Bloc d’attention** | Multi‑head attention (32 têtes). Chaque tête utilise la normalisation RMS (Root‑Mean‑Square LayerNorm) au lieu de LayerNorm classique. | <https://arxiv.org/abs/1910.07467> |
| **MLP** | Deux couches linéaires séparées par GELU. Facteur d’expansion = 4 (4096 → 16384 → 4096). | Architecture standard LLaMA‑2. |
| **Normalisation** | RMSNorm appliquée avant chaque sous‑couche (attention, MLP). | <https://arxiv.org/abs/1910.07467> |
| **Sortie** | Linear → vocabulaire de 50 272 tokens. | DeepSeek‑Open v0.3.2. |

> **Note** : La combinaison RoPE + RMSNorm réduit la variance des gradients et améliore la stabilité en faible précision (FP16/INT8).

---

## 2.2 Paramétrage de `generation_config`

```python
from deepseek_open import GenerationConfig

gen_cfg = GenerationConfig(
    max_new_tokens=256,      # nombre maximal de tokens générés
    temperature=0.7,         # contrôle de la diversité (0.0 = déterministe)
    top_p=0.9,               # nucleus sampling, cumule jusqu'à 90 % de probabilité
    repetition_penalty=1.1,  # décourage les boucles de répétition
    eos_token_id=2,          # token de fin de séquence (</s>)
    pad_token_id=0,          # token de remplissage
)

# Exemple d’utilisation avec le modèle chargé
outputs = model.generate(
    input_ids=token_ids,
    generation_config=gen_cfg,
    do_sample=True,           # active le sampling (temperature/top_p)
)
```

| Paramètre | Impact mesurable | Valeur typique (benchmark) |
|-----------|------------------|-----------------------------|
| `temperature` | Perplexité ↑ quand > 1, ↓ quand < 1 | 0.7‑0.9 |
| `top_p` | Vitesse de génération ↔ (plus bas = moins de calcul) | 0.9 |
| `max_new_tokens` | Temps total = `max_new_tokens × latency_per_token` | 128‑256 |
| `repetition_penalty` | BLEU ↑, taux de répétition ↓ | 1.0‑1.2 |

---

## 2.3 Gestion de la tokenisation avec `tiktoken`

```python
import tiktoken

# Le vocabulaire officiel DeepSeek‑Open 7B (50 272 tokens)
enc = tiktoken.get_encoding("deepseek-open-7b")

def encode_prompt(prompt: str) -> list[int]:
    """Encode un texte en tokens, ajoute le token BOS (<|assistant|>) si absent."""
    tokens = enc.encode(prompt)
    # DeepSeek‑Open attend le token spécial 1 (<|assistant|>) au début d’une réponse
    if not tokens or tokens[0] != 1:
        tokens = [1] + tokens
    return tokens

def decode_output(tokens: list[int]) -> str:
    """Decode une séquence de tokens en texte brut."""
    return enc.decode(tokens, skip_special_tokens=True)
```

* **Taille du vocabulaire** : 50 272. La fonction `enc.encode` renvoie des entiers compris entre `0` et `50271`.  
* **Compatibilité** : Le même encodeur doit être utilisé pour le fine‑tuning afin d’éviter les décalages d’index.

---

## 2.4 Optimisations d’inférence

| Technique | Commande d’activation | Mémoire (approx.) | Latence (token) RTX 4090 |
|-----------|----------------------|-------------------|--------------------------|
| **`torch.compile`** | `model = torch.compile(model, mode="max-autotune")` | + 0.2 GB (graph cache) | ↓ ≈ 15 % |
| **`torch.autocast` (FP16)** | `with torch.autocast("cuda"): …` | - 2 GB (FP16) | ↓ ≈ 30 % |
| **Quantisation INT8 (bitsandbytes)** | `model = model.quantize(bitsandbytes.Int8Params())` | - 4 GB | ↓ ≈ 45 % (dégradation BLEU ≈ ‑1) |
| **`flash_attn`** (optionnel) | `pip install flash-attn==2.5.6` + `model.enable_flash_attn()` | - 0.5 GB | ↓ ≈ 20 % |

```python
import torch
from deepseek_open import DeepSeekModel
from bitsandbytes import Int8Params

# Chargement du modèle en FP16 avec torch.compile
model = DeepSeekModel.from_pretrained("deepseek/open-7b", torch_dtype=torch.float16, device_map="auto")
model = torch.compile(model, mode="max-autotune")

# Optionnel : quantisation INT8 (décommenter si la VRAM < 4 GB)
# model = model.quantize(Int8Params())

def generate(prompt: str, max_new_tokens: int = 128):
    token_ids = encode_prompt(prompt)

---

## Module 3 — contenu

## 3.1 Pré‑traitement des données

| Étape | Action | Commande / Code | Vérification |
|-------|--------|----------------|--------------|
| 3.1.1 | Normaliser les sauts de ligne | `sed -e 's/\r$//' raw.tsv > cleaned.tsv` | `head -n 3 cleaned.tsv` |
| 3.1.2 | Convertir le TSV en JSONL compatible *ChatML* | ```python\nimport csv, json, sys\nwith open('cleaned.tsv') as f, open('train.jsonl','w') as out:\n    reader = csv.DictReader(f, delimiter='\t', fieldnames=['instruction','input','output'])\n    for row in reader:\n        messages = []\n        # system prompt (optionnel)\n        messages.append({\"role\":\"system\",\"content\":\"You are a helpful assistant.\"})\n        # user message\n        user = row['instruction']\n        if row['input']:\n            user += \"\\n\" + row['input']\n        messages.append({\"role\":\"user\",\"content\":user})\n        # assistant message\n        messages.append({\"role\":\"assistant\",\"content\":row['output']})\n        out.write(json.dumps({\"messages\":messages})+\"\\n\")\n``` | `head -n 1 train.jsonl` doit afficher un objet JSON avec la clé `messages` |
| 3.1.3 | Tokeniser et sauvegarder les IDs (optionnel) | ```bash\npython - <<'PY'\nfrom transformers import AutoTokenizer\nimport json, tqdm\n\nmodel_name='deepseek-ai/deepseek-open-7b-base'\ntokenizer=AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)\n\nwith open('train.jsonl') as fin, open('train_ids.jsonl','w') as fout:\n    for line in tqdm.tqdm(fin):\n        obj=json.loads(line)\n        ids=[tokenizer.encode(m['content'], add_special_tokens=False) for m in obj['messages']]\n        obj['input_ids']=ids\n        fout.write(json.dumps(obj)+\"\\n\")\nPY\n``` | `wc -l train_ids.jsonl` doit être égal à `wc -l train.jsonl` |

> **Remarque** : le format *ChatML* attendu par `deepseek-open` est une liste de dictionnaires `{role, content}`. Le rôle `assistant` doit être précédé d’un token spécial `<|assistant|>` qui est ajouté automatiquement par le tokenizer du modèle.

---

## 3.2 Script d’entraînement : `deepseek-train.py`

Le script utilise **HuggingFace Transformers** ≥ 4.38, **PEFT** ≥ 0.8.2 et **bitsandbytes** ≥ 0.43.0.

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fine‑tuning DeepSeek‑Open 7B avec LoRA / QLoRA.
Objectif : ≤ 0.85 loss sur Alpaca‑GPT4‑Data en ≤ 6 h sur 4 × A100 80 GB.
"""

import argparse
import os
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer, get_cosine_schedule_with_warmup
from peft import LoraConfig, get_peft_model, prepare_model_for_int8_training
from tqdm import tqdm

# ----------------------------------------------------------------------
# 1️⃣ Dataset minimaliste (compatible avec le format JSONL produit ci‑dessus)
# ----------------------------------------------------------------------
class AlpacaChatDataset(Dataset):
    def __init__(self, path: str, tokenizer, max_len: int = 2048):
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.samples = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                # concatène les messages avec les tokens spéciaux du modèle
                text = ""
                for msg in obj["messages"]:
                    role = msg["role"]
                    if role == "system":
                        text += "<|system|>" + msg["content"]
                    elif role == "user":
                        text += "<|user|>" + msg["content"]
                    elif role == "assistant":
                        text += "<|assistant|>" + msg["content"]
                self.samples.append(text)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.samples[idx],
            truncation=True,
            max_length=self.max_len,
            padding="max_length",
            return_tensors="pt",
        )
        input_ids = enc["input_ids"].squeeze(0)
        attention_mask = enc["attention_mask"].squeeze(0)
        # Labels = input_ids, mais on masque les tokens de padding
        labels = input_ids.clone()
        labels[attention_mask == 0] = -100
        return {"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels}


# ----------------------------------------------------------------------
# 2️⃣ Argument parser
# ----------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", default="deepseek-ai/deepseek-open-7b-base")
    parser.add_argument("--train_file", required=True, help="Chemin vers train.jsonl")
    parser.add_argument("--output_dir", default="./deepseek-7b-lora")
    parser.add_argument("--batch_size

---

## Module 4 — contenu

## Module 4 – Déploiement à grande échelle, optimisation production et suivi

### 4.1 Architecture de déploiement distribué
| Niveau | Technologie | Rôle | Configuration minimale (RTX 4090) |
|--------|-------------|------|-----------------------------------|
| **Data‑parallel** | **torch.distributed** (NCCL) | Réplication du modèle sur plusieurs GPUs, agrégation des gradients | `torchrun --nproc_per_node=2` |
| **Tensor‑parallel** | **DeepSpeed‑Inference** (ZeRO‑3) ou **vLLM** (tensor‑parallel) | Découpage des poids du modèle sur les GPUs, aucune réplication de paramètres | `--tensor-parallel-size 2` |
| **Pipeline‑parallel** | **DeepSpeed‑Inference** (pipeline‑stage) | Découpage séquentiel des blocs du Transformer, utile quand chaque GPU ne tient pas le modèle complet | `--pipeline-parallel-size 2` |

> **Vérifiable** : le nombre total de paramètres du modèle `deepseek/open-7b` est 7 B ≈ 28 Go FP16. Sur deux RTX 4090 (24 Go VRAM chacune) le découpage tensor‑parallel 2× réduit la charge à ~14 Go/GPUs, ce qui passe sous la limite de 24 Go.

### 4.2 Serveur d’inférence à haut débit avec **vLLM**
vLLM implémente le *spec* OpenAI, le *sampling* asynchrone et le *prefill‑decode* optimisé.

```bash
# 1. Installation (versions vérifiées)
pip install "vllm==0.3.0" "torch==2.3.0" "accelerate==0.33.0"

# 2. Lancement du serveur sur 2 GPU (tensor‑parallel=2)
python -m vllm.entrypoints.openai.api_server \
    --model deepseek/open-7b \
    --dtype bfloat16 \
    --tensor-parallel-size 2 \
    --max-num-batched-tokens 4096 \
    --port 8000
```

#### 4.2.1 Appel client (Python)
```python
import openai

client = openai.OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

resp = client.chat.completions.create(
    model="deepseek/open-7b",
    messages=[{"role": "user", "content": "Explique la différence entre LoRA et QLoRA."}],
    temperature=0.7,
    max_tokens=256,
    stream=False,
)

print(resp.choices[0].message.content)
```
*Commentaires*  
- `dtype bfloat16` exploite le support matériel des RTX 4090 (Tensor Core BF16) et réduit la consommation de VRAM d’environ 30 % vs FP16.  
- `max-num-batched-tokens` limite la taille du *prefill* batch afin d’éviter le débordement de la mémoire de travail (`kv_cache`).  
- Le serveur expose l’endpoint `/v1/chat/completions` compatible avec les SDK OpenAI, ce qui simplifie l’intégration dans les pipelines existants.

### 4.3 Optimisations complémentaires
| Technique | Commande / Flag | Impact mesurable |
|-----------|----------------|------------------|
| **Flash‑Attention 2** | `--attention-type flash` (vLLM) | ↓ latence de 15 % sur tokens ≥ 1024 |
| **Quantisation INT8** (bitsandbytes) | `--quantization int8` (DeepSpeed) | ↓ VRAM de 3 Go, débit ≈ 0.9× du FP16 |
| **Chunked KV‑Cache** | `--max-num-batched-tokens 2048` + `--max-num-seqs 32` | ↑ taux de remplissage GPU de 20 % sous charge mixte |
| **CUDA Graphs** | `--use-cuda-graph` (DeepSpeed) | ↓ overhead de lancement de kernels de 5 µs → gain de 2 % en TPS |

> **Piège** : la combinaison `bfloat16 + flash-attention` n’est pas supportée sur les drivers < 560.31 ; le serveur échoue avec `RuntimeError: FlashAttention not compiled for BF16`. Solution : mettre à jour le driver NVIDIA ou revenir à `fp16`.

### 4.4 Monitoring et observabilité
| Métrique | Outil | Collecte |
|----------|-------|-----------|
| **GPU utilisation / mémoire** | `nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv -l 1` | Exporter vers Prometheus via `node_exporter` |
| **TPS (tokens per second)** | vLLM expose `/metrics` (Prometheus) | `rate(vllm_request_tokens_total[30s])` |
| **Latence 95e percentile** | Grafana dashboard (Prometheus) | `histogram_quantile(0.95, sum(rate(vllm_request_latency_seconds_bucket[30s])) by (le))` |
| **Erreur d’inférence** | Sentry (trace) | Capture des exceptions (`torch.cuda.OutOfMemoryError`) |

#### 4.4.1 Exemple de script d’alerte Prometheus
```yaml
groups:
- name: deepseek_alerts
  rules:
  - alert: GPUOutOfMemory

---

## Module 5 — contenu

## Module 5 – Mise en production : orchestration, scalabilité et observabilité  

### 5.1. Conteneurisation du modèle DeepSeek‑Open 7B  

| Étape | Action | Commande / Fichier |
|------|--------|--------------------|
| 5.1.1 | Base image : `nvidia/cuda:12.2.2-runtime-ubuntu22.04` (CUDA 12.2, cuDNN 8.9) | `FROM nvidia/cuda:12.2.2-runtime-ubuntu22.04` |
| 5.1.2 | Installation de Python 3.11 et dépendances système | `RUN apt-get update && apt-get install -y python3.11 python3.11-venv git && rm -rf /var/lib/apt/lists/*` |
| 5.1.3 | Création d’un environnement virtuel, installation du wheel `deepseek-open` (commit `v0.3.2`) et de `fastapi`, `uvicorn[standard]`, `bitsandbytes` | ```Dockerfile\nRUN python3.11 -m venv /opt/venv && \\\n    /opt/venv/bin/pip install --upgrade pip && \\\n    /opt/venv/bin/pip install torch==2.3.0+cu122 -f https://download.pytorch.org/whl/torch_stable.html && \\\n    /opt/venv/bin/pip install deepseek-open==0.3.2 && \\\n    /opt/venv/bin/pip install fastapi uvicorn[standard] bitsandbytes\n``` |
| 5.1.4 | Copie du code serveur (voir 5.2) et du script de warm‑up | `COPY app/ /app/` |
| 5.1.5 | Variable d’environnement pour limiter la visibilité GPU (ex. `CUDA_VISIBLE_DEVICES=0`) | `ENV CUDA_VISIBLE_DEVICES=0` |
| 5.1.6 | Point d’entrée : `uvicorn app.main:app --host 0.0.0.0 --port 8080` | `CMD ["/opt/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]` |

**Dockerfile complet**  

```Dockerfile
# 5.1.1 – Image de base CUDA 12.2
FROM nvidia/cuda:12.2.2-runtime-ubuntu22.04

# 5.1.2 – Python 3.11 + outils système
RUN apt-get update && \
    apt-get install -y python3.11 python3.11-venv git && \
    rm -rf /var/lib/apt/lists/*

# 5.1.3 – Environnement virtuel et dépendances
RUN python3.11 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install torch==2.3.0+cu122 -f https://download.pytorch.org/whl/torch_stable.html && \
    /opt/venv/bin/pip install deepseek-open==0.3.2 && \
    /opt/venv/bin/pip install fastapi uvicorn[standard] bitsandbytes

# 5.1.4 – Code serveur
COPY app/ /app/
WORKDIR /app

# 5.1.5 – Limitation GPU (modifiable à l’exécution)
ENV CUDA_VISIBLE_DEVICES=0

# 5.1.6 – Entrypoint
CMD ["/opt/venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 5.2. API FastAPI avec streaming et warm‑up  

```python
# app/main.py
import os
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from deepseek_open import DeepSeekModel, DeepSeekTokenizer

# 5.2.1 – Chargement unique du modèle (singleton)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_ID = "deepseek/open-7b"

# Vérification du checksum du wheel (déjà fait lors du build Docker)
tokenizer = DeepSeekTokenizer.from_pretrained(MODEL_ID)
model = DeepSeekModel.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,          # INT8 via bitsandbytes sera appliqué à la volée
    device_map="auto",                  # répartit les sous‑modules sur les GPUs disponibles
)
model.eval()
model = torch.compile(model, mode="max-autotune")   # 5.2.2 – torch.compile pour inference

app = FastAPI(title="DeepSeek‑Open 7B Inference API")

# 5.2.3 – Warm‑up (exécuté au démarrage du container)
@app.on_event("startup")
def warm_up():
    dummy = tokenizer.encode("Bonjour", return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        _ = model.generate(dummy, max_new_tokens