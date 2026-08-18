# DeepSeek & Open Source 2026

> Référence `deepseek-open` ·  

## Plan

## Module 1 – Installation et configuration de l’écosystème DeepSeek‑Open  
**Objectif mesurable** : Installer et valider un environnement de développement complet (Python 3.11, PyTorch 2.3, CUDA 12.2) capable d’exécuter le modèle DeepSeek‑Open 7B avec une utilisation de VRAM raisonnable.  
**Notions couvertes**  
1. Gestion d’environnements virtuels avec `venv` et `conda` – vérification via `python -c "import torch; print(torch.cuda.is_available())"`  
2. Installation du package `deepseek-open` depuis le dépôt GitHub officiel (commit `v0.3.2`) – validation du checksum SHA‑256 du wheel  
3. Configuration du backend GPU : driver NVIDIA 560.xx, cuDNN 8.9, variables d’environnement `CUDA_VISIBLE_DEVICES`  
4. Test de chargement du modèle `deepseek/open-7b` via `torch.load` – temps de warm‑up très court  
5. Mise en place de l’interface CLI `deepseek-cli` et du serveur HTTP `uvicorn` pour les requêtes REST  

## Module 2 – Utilisation de l’API DeepSeek‑Open pour l’inférence  
**Objectif mesurable** : Générer des réponses cohérentes avec un score BLEU élevé sur le benchmark `OpenAI‑Evals` avec une latence d’inférence très faible par token sur une RTX 4090.  
**Notions couvertes**  
1. Structure du modèle Transformer : couches d’attention, normalisation RMS, positionnement rotatif (RoPE)  
2. Paramétrage de `generation_config` (temperature, top‑p, max_new_tokens) – impact mesurable sur perplexité  
3. Gestion du tokenisation avec `tiktoken` – comparaison des tailles de vocabulaire (vocab‑size)  
4. Optimisations inference : `torch.compile`, `torch.autocast`, quantisation INT8 via `bitsandbytes`  
5. Déploiement d’une API FastAPI avec streaming de tokens – validation du débit (`tokens/s`)  

## Module 3 – Fine‑tuning supervisé du modèle DeepSeek‑Open 7B  
**Objectif mesurable** : Produire un modèle fine‑tuné qui atteint une perte moyenne faible sur le dataset `Alpaca‑GPT4‑Data` avec un temps d’entraînement raisonnable sur un cluster de GPU haut de gamme.  
**Notions couvertes**  
1. Pré‑traitement des paires instruction/réponse – format `ChatML` et balises `<|assistant|>`  
2. Script `deepseek-train` : options `--lora-rank`, `--lora-alpha`, `--gradient-checkpointing` – calcul du nombre de paramètres entraînables représentant une petite fraction du total  
3. Stratégies d’apprentissage : LoRA, QLoRA, PEFT – comparaison des exigences en VRAM (utilisation modérée)  
4. Scheduler d’apprentissage `cosine` avec warm‑up très limité – suivi du
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
```


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
    top_p=0.9,               # nucleus sampling, cumule jusqu'à un seuil de probabilité
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

| Paramètre | Impact observé | Valeur typique |
|-----------|----------------|----------------|
| `temperature` | Influence la perplexité du texte généré | valeur courante |
| `top_p` | Modifie la charge de calcul lors de la génération | valeur courante |
| `max_new_tokens` | Le temps total de génération dépend du nombre de tokens produits | valeur courante |
| `repetition_penalty` | Affecte la propension du modèle à répéter des séquences | valeur courante |

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

| Technique | Commande d’activation | Mémoire |
|-----------|----------------------|---------|
| **`torch.compile`** | `model = torch.compile(model, mode="max-autotune")` | approximative |
| **Quantisation INT8** | `model = quantize_int8(model)` | approximative |
| **Fusion de couches** | `model = fuse_layers(model)` | approximative |
| **Cache KV** | `model.enable_kv_cache()` | approximative |

---