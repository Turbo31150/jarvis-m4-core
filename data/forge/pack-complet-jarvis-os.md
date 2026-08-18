# Pack Intégral — 62 Formations

> Référence `pack-complet-jarvis-os` · 399 €

## Plan

## Module 1 – Fondamentaux de l’IA générative avec Jarvis‑OS  
**Objectif mesurable** : Être capable de créer, entraîner et évaluer un modèle de texte génératif basique sous Jarvis‑OS en moins de 4 h de travail.  

- Architecture de transformeurs (self‑attention, couches d’encodage/décodage)  
- Installation et configuration de l’environnement Jarvis‑OS (Docker, Python 3.11, GPU CUDA)  
- Pipeline de pré‑traitement des corpus (tokenisation, normalisation, gestion des séquences)  
- Entraînement d’un modèle de type GPT‑2‑small avec les API Jarvis‑OS (hyper‑paramètres, early‑stopping)  
- Métriques d’évaluation (perplexité, BLEU, ROUGE) et interprétation des résultats  

## Module 2 – Développement d’assistants conversationnels spécialisés  
**Objectif mesurable** : Concevoir un chatbot capable de répondre à des requêtes métier avec une précision ≥ 85 % sur un jeu de test de 500 questions.  

- Conception de prompts conditionnels et utilisation de la fonction “system‑message” de Jarvis‑OS  
- Gestion du contexte multi‑tour (state tracking, slot‑filling)  
- Intégration de bases de connaissances externes via Retrieval‑Augmented Generation (RAG)  
- Implémentation de filtres de sécurité (détection de toxicité, filtrage PII) avec les modèles de modération Jarvis‑OS  
- Déploiement d’une API RESTful (FastAPI) et tests de charge (Locust)  

## Module 3 – IA multimodale : texte‑image et vision‑langage  
**Objectif mesurable** : Générer des images à partir de descriptions textuelles et extraire du texte d’images avec un taux de réussite ≥ 90 % sur un jeu de validation de 200 paires.  

- Modèles diffusion (Stable Diffusion v2.1) intégrés à Jarvis‑OS : architecture, conditionnement latents  
- Fine‑tuning de modèles diffusion sur un dataset propriétaire (LoRA, DreamBooth)  
- OCR avancé avec les modèles de vision‑langage (TrOCR, LayoutLM) et post‑traitement (spell‑checking)  
- Fusion texte‑image via CLIP pour la validation de la correspondance sémantique  
- Construction d’un pipeline end‑to‑end (FastAPI + Celery) pour la génération et la reconnaissance  

## Module 4 – Optimisation et mise à l’échelle des modèles IA  
**Objectif mesurable** : Réduire le temps d’inférence d’un modèle de 2 GB à ≤ 50 ms par requête sur un serveur GPU A100 tout en conservant une perte de précision ≤ 2 %.  

- Quantisation (INT8, FP16) et prunage de poids avec les outils Jarvis‑OS Quantizer  
- Compilation avec TensorRT et ONNX Runtime (optimisation du graphe, fusion d’opérations)  
- Mise en place de serveurs de modèles (Triton Inference Server) et gestion du batching dynamique  
- Monitoring de la latence

---

## Module 1 — contenu

## 1. Architecture des transformeurs  

| Élément | Fonction | Référence |
|--------|----------|-----------|
| **Self‑attention** | Chaque token échange des informations avec tous les autres tokens du même séquence via des requêtes (Q), clés (K) et valeurs (V). La sortie est `softmax(QKᵀ/√d_k)·V`. | Vaswani et al., *Attention is All You Need*, 2017 |
| **Couches d’encodage / décodage** | Un bloc d’encodage = **MHA** + **Add‑Norm** + **FFN** + **Add‑Norm**. Le décodage ajoute une **masquage causal** et une couche d’**attention cross‑encoder** vers les sorties de l’encodeur. | idem |
| **Positionnal Encoding** | Ajoute des informations de position (sinusoidales ou apprises) à chaque embedding. | idem |
| **Layer‑norm** | Stabilise les gradients en normalisant sur la dimension des caractéristiques. | Ba et al., 2016 |

> **Note** : GPT‑2‑small possède 12 blocs d’auto‑attention, 768 dimensions d’embedding et 12 M paramètres.  

---

## 2. Installation et configuration de l’environnement Jarvis‑OS  

### 2.1 Prérequis système  

| Élément | Version minimale |
|--------|------------------|
| Docker | 20.10+ |
| NVIDIA driver | 525.60.11 (ou plus) |
| CUDA Toolkit | 12.1 |
| Python | 3.11 |
| GPU | ≥ 8 GB VRAM (ex. RTX 3090, A100) |

### 2.2 Pull de l’image Docker officielle  

```bash
docker pull jarvisos/ai-base:latest
```

### 2.3 Lancement du conteneur avec GPU  

```bash
docker run -it --gpus all \
  -v $(pwd)/workspace:/workspace \
  -e JARVIS_OS_HOME=/workspace \
  jarvisos/ai-base:latest /bin/bash
```

- `-v` monte le répertoire local `workspace` dans le conteneur pour persister les données.  
- `JARVIS_OS_HOME` indique à Jarvis‑OS où placer les modèles, caches et logs.  

### 2.4 Vérification du GPU dans le conteneur  

```bash
python -c "import torch; print(torch.cuda.is_available())"
# → True
```

---

## 3. Pipeline de pré‑traitement des corpus  

### 3.1 Structure attendue du jeu de données  

| Fichier | Format | Exemple |
|---------|--------|---------|
| `train.txt` | texte brut, une phrase par ligne | `Le chat dort sur le canapé.` |
| `valid.txt` | idem | `Le soleil se couche à l’horizon.` |

### 3.2 Tokenisation avec le tokenizer Jarvis‑OS (compatible HuggingFace)  

```python
from jarvisos.tokenizer import JarvisTokenizer

# Le tokenizer utilise le vocabulaire de GPT‑2‑small
tokenizer = JarvisTokenizer.from_pretrained("gpt2-small")

def encode_file(path: str, max_len: int = 512):
    """Lit un fichier texte ligne par ligne, tokenise et tronque à max_len."""
    token_ids = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            ids = tokenizer.encode(line.strip())
            # Ajout du token EOS (50256) si absent
            if ids[-1] != tokenizer.eos_token_id:
                ids.append(tokenizer.eos_token_id)
            # Troncature / padding
            ids = ids[:max_len]
            token_ids.append(ids)
    return token_ids
```

### 3.3 Création d’un `DataLoader` Jarvis‑OS  

```python
from torch.utils.data import Dataset, DataLoader
import torch

class TextDataset(Dataset):
    def __init__(self, tokenized_corpus):
        self.corpus = tokenized_corpus

    def __len__(self):
        return len(self.corpus)

    def __getitem__(self, idx):
        ids = torch.tensor(self.corpus[idx], dtype=torch.long)
        # Le modèle attend (input_ids, labels) où labels = input_ids décalés
        return {"input_ids": ids, "labels": ids}

def collate_fn(batch, pad_token_id=tokenizer.pad_token_id):
    # Pad dynamique au plus long de la batch
    max_len = max(len(item["input_ids"]) for item in batch)
    input_ids = []
    labels = []
    for item in batch:
        ids = item["input_ids"]
        pad_len = max_len - len(ids)
        input_ids.append(torch.cat([ids, torch.full((pad_len,), pad_token_id)]))
        labels.append(torch.cat([ids, torch.full((pad_len,), -100)]))  # -100 = ignore_index
    return {"input_ids": torch.stack(input_ids),
            "labels": torch.stack(labels)}
```

```python
train_corpus = encode_file("train.txt")
valid_corpus = encode_file("valid.txt")

train_loader = DataLoader(
    TextDataset(train_corpus),
    batch_size=8,
    shuffle=True,
    collate_fn=collate_fn,
    num_workers=2,
)

valid_loader = DataLoader(
    TextDataset(valid_corpus),
    batch_size=8,
    shuffle=False,
    collate_fn=collate_fn,
    num_workers=2,
)
```

---

## 4. Entraînement d’un modèle GPT‑2‑small avec les API Jarvis‑OS  

### 4.1 Chargement du modèle de base  

```python

---

## Module 2 — contenu

## Module 2 – Développement d’assistants conversationnels spécialisés  

### 1. Conception de prompts conditionnels et fonction `system‑message`

Jarvis‑OS expose l’API `ChatCompletion.create` similaire à OpenAI. Le champ `system` fixe le comportement général du modèle ; les champs `user` et `assistant` sont les tours de dialogue.

```python
from jarvis_os import ChatCompletion

# Prompt de base : le système indique le rôle
system_prompt = {
    "role": "system",
    "content": (
        "Tu es un assistant juridique spécialisé dans le droit du travail français. "
        "Réponds de façon concise, cite les articles du Code du travail quand c’est "
        "pertinent, et indique toujours la source légale."
    )
}

def ask_question(question: str) -> str:
    """Envoie une requête à Jarvis‑OS et retourne la réponse brute."""
    response = ChatCompletion.create(
        model="jarvis-gpt-2.7b",
        messages=[
            system_prompt,
            {"role": "user", "content": question}
        ],
        temperature=0.2,          # faible créativité pour la précision juridique
        max_tokens=512,
        stop=None
    )
    return response["choices"][0]["message"]["content"]

# Exemple d’utilisation
print(ask_question("Quelle est la durée légale du travail à temps plein en France ?"))
```

*Commentaires*  
- `temperature` ≤ 0.3 limite les hallucinations.  
- `max_tokens` doit couvrir la réponse complète + la référence légale.  
- Le champ `system` est persistant tant que la même session de conversation est maintenue ; si vous créez une nouvelle session, il faut le renvoyer.

### 2. Gestion du contexte multi‑tour (state tracking, slot‑filling)

Jarvis‑OS ne conserve pas automatiquement le contexte ; il faut le gérer côté client. La structure typique :

```python
class Conversation:
    def __init__(self, system_prompt: dict):
        self.history = [system_prompt]          # liste de dicts
        self.slots = {}                         # dictionnaire de slots remplis

    def add_user(self, text: str):
        self.history.append({"role": "user", "content": text})

    def add_assistant(self, text: str):
        self.history.append({"role": "assistant", "content": text})

    def fill_slot(self, name: str, value):
        self.slots[name] = value

    def get_prompt(self):
        """Retourne l’historique complet, tronqué à 4096 tokens si besoin."""
        # Utiliser le tokenizer de Jarvis‑OS pour compter les tokens
        from jarvis_os import tokenizer
        tokens = tokenizer.encode_chat(self.history)
        while len(tokens) > 4096:
            # Retirer le plus ancien tour utilisateur‑assistant
            self.history.pop(1)   # supprime le premier user (index 1)
            self.history.pop(1)   # supprime l’assistant qui suit
            tokens = tokenizer.encode_chat(self.history)
        return self.history
```

**Slot‑filling** (exemple : collecte du nom du salarié) :

```python
def extract_name(response: str) -> str | None:
    """Simple extraction par regex, à remplacer par un NER si besoin."""
    import re
    m = re.search(r"nom\s*[:\-]?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)", response)
    return m.group(1) if m else None

conv = Conversation(system_prompt)

# Tour 1 – question ouverte
conv.add_user("Je veux connaître mes droits en cas de licenciement économique.")
assistant_reply = ChatCompletion.create(
    model="jarvis-gpt-2.7b",
    messages=conv.get_prompt(),
    temperature=0.2,
    max_tokens=512
)["choices"][0]["message"]["content"]
conv.add_assistant(assistant_reply)

# Le modèle demande le nom du salarié
conv.add_user("Mon nom est Dupont Marie.")
assistant_reply = ChatCompletion.create(
    model="jarvis-gpt-2.7b",
    messages=conv.get_prompt(),
    temperature=0.2,
    max_tokens=512
)["choices"][0]["message"]["content"]
conv.add_assistant(assistant_reply)

# Extraction du slot
name = extract_name(conv.history[-2]["content"])   # texte du dernier user
if name:
    conv.fill_slot("employee_name", name)
```

#### Points à retenir
| Situation | Action recommandée |
|-----------|--------------------|
| Historique > 4096 tokens | Troncature du plus ancien tour (toujours garder le `system`). |
| Slots non remplis après 2 tours | Ajouter un prompt explicite : « Peux‑tu préciser ? ». |
| Ambiguïté sur le type de donnée (date, montant) | Utiliser un petit modèle NER (spaCy) en pré‑traitement. |

### 3. Intégration de bases de connaissances externes via Retrieval‑Augmented Generation (RAG)

#### 3.1 Architecture RAG sous Jarvis‑OS

1. **Indexation** : créer un vecteur d’embeddings pour chaque document (ex. articles de loi) avec `JarvisEmbedding.encode`.  
2. **Recherche** : au moment du dialogue, interroger l’index avec la requête de l’utilisateur.  
3. **Fusion** : injecter les passages récupérés dans le prompt via le champ `context`.

```python
from jarvis_os import Embedding, VectorStore

# 1. Indexation (exécutée hors ligne)
documents = [
    {"id": "L1234-1", "text": "Article L1234‑1 du Code du travail : ..."},
    {"id": "L1234-2", "text": "Article L1234‑2 du Code du travail : ..."},
    # …
]
embeddings = Embedding.encode([doc["text"] for doc in documents])
vector_store = VectorStore(embeddings, [doc["id

---

## Module 3 — contenu

## 3.1 Modèles de diffusion intégrés à Jarvis‑OS  

### 3.1.1 Architecture de Stable Diffusion v2.1  

| Composant | Rôle | Référence |
|-----------|------|------------|
| **UNet** | Décodage latents → image | Rombach *et al.*, 2022 |
| **Variational Auto‑Encoder (VAE)** | Encodage/ décodage d’images ↔ latents | Kingma & Welling, 2014 |
| **Text Encoder (CLIP‑ViT‑L/14)** | Convertit le prompt en embedding 768‑d | Radford *et al.*, 2021 |
| **Scheduler (DPM‑Solver++)** | Intègre le processus de diffusion inverse | Liu *et al.*, 2022 |

- **Latent space** : 4× down‑sampling (64×64 → 16×16) pour les images 512×512.  
- **Conditionnement** : le texte est injecté dans chaque bloc UNet via le *cross‑attention*.

### 3.1.2 Utilisation de l’API Jarvis‑OS  

```python
# file: generate_image.py
import os
import json
from jarvis_os import DiffusionClient  # SDK officiel

# 1️⃣ Chargement du client (GPU A100, torch‑cuda 12.1)
client = DiffusionClient(
    model_name="stable-diffusion-v2.1",
    device="cuda",               # ou "cpu" pour test rapide
    precision="fp16"            # économise la VRAM
)

# 2️⃣ Prompt et paramètres
prompt = "un chat siamois assis sur un rebord de fenêtre, style hyper‑réaliste, lumière du soir"
negative_prompt = "déformation, artefact, low‑res"
steps = 30                     # DPM‑Solver++ converge en < 30 steps
guidance_scale = 7.5           # poids du texte vs bruit

# 3️⃣ Appel de génération
result = client.txt2img(
    prompt=prompt,
    negative_prompt=negative_prompt,
    num_inference_steps=steps,
    guidance_scale=guidance_scale,
    seed=42                     # reproductibilité
)

# 4️⃣ Sauvegarde
output_path = os.path.join("outputs", "chat_siamois.png")
result.image.save(output_path)
print(f"Image sauvée → {output_path}")
```

- `DiffusionClient` charge automatiquement le VAE et le Text Encoder.  
- `precision="fp16"` nécessite CUDA ≥ 11.0 et un GPU supportant le *half‑precision* (ex. A100, RTX 3090).  
- Le paramètre `seed` garantit la même image à chaque exécution, utile pour le debugging.

### 3.1.3 Pièges courants  

| Situation | Symptom | Cause | Remède |
|-----------|---------|-------|--------|
| OOM (out‑of‑memory) dès le premier batch | Crash du processus Docker | Batch size > 1 sur 24 GB VRAM | Fixer `batch_size=1` ou activer `torch.cuda.empty_cache()` entre les appels |
| Image floue ou bruitée malgré 50 steps | Scheduler mal configuré | Utilisation du *Euler‑a* scheduler avec `steps<20` | Passer à `scheduler="dpm_solver++"` et `steps≥30` |
| Texte du prompt ignoré | `guidance_scale` trop bas | Valeur < 3 ne force pas le conditionnement | Utiliser `guidance_scale` entre 7‑9 pour la plupart des prompts |
| Artefacts de bordure (bandes noires) | VAE mal initialisé | Chargement du VAE en mode `float32` alors que le UNet est en `fp16` | Uniformiser la précision (`precision="fp16"` pour les deux) |

---

## 3.2 Fine‑tuning de diffusion (LoRA & DreamBooth)  

### 3.2.1 LoRA (Low‑Rank Adaptation)  

- **Principe** : Ajoute deux matrices `A (rank r)` et `B (rank r)` à chaque poids `W` du UNet : `W' = W + α·A·B`.  
- **Avantages** : Mémoire GPU réduite (r≈4), entraînement en < 2 h sur 1 A100 pour un dataset de 100 images.  

#### Code de fine‑tuning LoRA avec Jarvis‑OS  

```python
# file: lora_finetune.py
import torch
from jarvis_os import DiffusionTrainer, LoRAConfig

# 1️⃣ Dataset local (images + captions)
train_dataset = "data/petites_fleurs/"          # structure: img/*.jpg + captions.txt

# 2️⃣ Configuration LoRA
lora_cfg = LoRAConfig(
    rank=4,
    alpha=16,
    target_modules=["attn1", "attn2"],   # modules de cross‑attention uniquement
    dropout=0.1
)

# 3️⃣ Trainer
trainer = DiffusionTrainer(
    base_model="stable-diffusion-v2.1",
    lora_config=lora_cfg,
    train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=5e-5,
    num_train_epochs=3,
    mixed_precision="fp16",
    device="cuda"
)

# 4️⃣ Lancement
trainer.run(train_dataset)
# 5️⃣ Sauvegarde du checkpoint LoRA (≈ 1 Mo)
trainer.save_checkpoint("checkpoints/lora_fleurs")
```

- Le checkpoint LoRA ne contient que

---

## Module 4 — contenu

## 4.1 Quantisation et élagage de poids  

| Technique | Bibliothèque Jarvis‑OS | Format cible | Impact typique |
|-----------|------------------------|--------------|----------------|
| **Quantisation post‑training (PTQ)** | `jarvis.quantizer` | INT8, FP16 | -30 % à -60 % de latence, perte de précision ≤ 1 % si calibration correcte |
| **Quantisation aware training (QAT)** | `jarvis.quantizer.qat` | INT8 | +10 % de précision vs PTQ, nécessite 1‑2 époques de ré‑entraînement |
| **Élagage (pruning)** | `jarvis.pruner` | FP32/FP16 | Réduction du nombre de paramètres de 30‑80 %, gain de bande passante mémoire, perte de précision dépend du taux d’élagage |

### 4.1.1 Pipeline PTQ (INT8)  

```python
# fichier : quantize_int8.py
import torch
from jarvis.quantizer import PTQQuantizer
from jarvis.model import load_model, export_onnx

# 1️⃣ Charger le modèle pré‑entraîné (ex. GPT‑2‑small, 124 M paramètres)
model = load_model("gpt2_small", device="cpu")   # PTQ s’effectue sur CPU

# 2️⃣ Définir le calibrateur : on utilise 500 batches d’un jeu de calibration
def calibration_data_loader(batch_size=32, nb_batches=500):
    for _ in range(nb_batches):
        # `input_ids` : torch.LongTensor [batch, seq_len]
        # ici on génère des séquences aléatoires de longueur 128
        input_ids = torch.randint(0, model.config.vocab_size,
                                  (batch_size, 128), dtype=torch.long)
        yield {"input_ids": input_ids}

# 3️⃣ Instancier le quantiseur
quantizer = PTQQuantizer(
    model=model,
    calibrator=calibration_data_loader,
    dtype=torch.int8,               # cible INT8
    per_channel=True,              # meilleure précision sur les poids
    symmetric=True,                # plus simple à exporter vers TensorRT
)

# 4️⃣ Exécuter la calibration + quantisation
quantized_model = quantizer.quantize()

# 5️⃣ Exporter le modèle quantisé au format ONNX (compatible TensorRT)
export_onnx(
    model=quantized_model,
    path="gpt2_int8.onnx",
    input_names=["input_ids"],
    output_names=["logits"],
    dynamic_axes={"input_ids": {0: "batch", 1: "seq_len"},
                  "logits":    {0: "batch", 1: "seq_len"}},
)
print("Export ONNX complet : gpt2_int8.onnx")
```

*Points de vigilance*  
- **Calibration** : le jeu de calibration doit couvrir la même distribution que la charge de production (longueur de séquence, vocabulaire). Un jeu trop petit entraîne un **scale** inadapté → sous‑ou sur‑estimation des valeurs, perte de précision > 2 %.  
- **Per‑channel vs per‑tensor** : le premier conserve plus de précision mais augmente la taille du tableau de `scale`/`zero_point`. Certains back‑ends (ex. TensorRT < 8.2) ne le supportent pas.  
- **Symétrique** : requis pour TensorRT INT8, sinon le convertisseur insère des opérations de conversion qui augmentent la latence.  

### 4.1.2 Élagage global à 40 %  

```python
# fichier : prune_global.py
import torch
from jarvis.pruner import GlobalMagnitudePruner
from jarvis.model import load_model, save_model

model = load_model("gpt2_small", device="cpu")

pruner = GlobalMagnitudePruner(
    model=model,
    target_sparsity=0.40,          # 40 % des poids seront mis à zéro
    prune_type="unstructured",    # pruning fine‑grained
)

pruned_model = pruner.prune()
# Optionnel : fine‑tuning de 1 epoch pour récupérer la précision
pruned_model.train()
optimizer = torch.optim.AdamW(pruned_model.parameters(), lr=5e-5)
for batch in calibration_data_loader(batch_size=32, nb_batches=100):
    optimizer.zero_grad()
    logits = pruned_model(**batch)
    loss = torch.nn.functional.cross_entropy(
        logits.view(-1, logits.size(-1)),
        batch["input_ids"].view(-1)
    )
    loss.backward()
    optimizer.step()

save_model(pruned_model, "gpt2_pruned_40.pt")
print("Modèle élagué sauvegardé.")
```

*Pièges*  
- **Élagage non‑structuré** : les GPU modernes (A100) ne profitent que partiellement du sparsity non‑structuré ; la latence ne diminue pas proportionnellement au taux d’élagage.  
- **Fine‑tuning insuffisant** : un seul epoch peut ne pas suffire pour récupérer la perte de précision. En pratique, 2‑3 epochs avec un LR réduit sont recommandés.  

---

## 4.2 Compilation avec TensorRT et ONNX Runtime  

### 4.2.1 Conversion ONNX → TensorRT Engine (INT8)  

```bash
# script bash : build_trt_engine.sh
#!/usr/bin/env bash
set -euo pipefail

ONNX_MODEL="gpt2_int8.onnx"
ENGINE_OUT="gpt2_int8.trt"

# 1. Créer un fichier de calibration si le modèle n’est pas déjà quantisé
#

---

## Module 5 — contenu

## Module 5 – Gouvernance, conformité et auditabilité des IA génératives

### Objectif mesurable
Mettre en place un cadre de gouvernance permettant de tracer, auditer et garantir la conformité RGPD et les exigences de transparence sur un assistant conversationnel Jarvis‑OS. Le livrable doit être capable de **produire un journal d’interaction complet** (prompt, réponse, métadonnées) où toutes les données à caractère personnel sont **pseudonymisées** et **stockées** dans une base de données audit‑ready en moins de 30 min de configuration.

---

## 5.1 Principes de gouvernance appliqués à Jarvis‑OS  

| Domaine | Exigence légale / norme | Implémentation concrète dans Jarvis‑OS |
|--------|--------------------------|----------------------------------------|
| **Traçabilité** | RGPD Art. 30 – registre des activités de traitement | Logger chaque appel d’API (`prompt`, `response`, `user_id`, `timestamp`, `model_version`). |
| **Minimisation** | RGPD Art. 5(1c) – ne collecter que le strict nécessaire | Supprimer les champs `raw_text` contenant des PII avant persistance. |
| **Transparence** | ISO 27001 A.12.7 – communication des politiques de sécurité | Générer automatiquement un **Data‑Processing‑Statement** (DPS) à partir du manifeste de modèle (fichier `manifest.yaml`). |
| **Responsabilité** | EU AI Act – exigences de suivi des performances | Stocker les métriques d’évaluation (`perplexity`, `toxicity_score`) associées à chaque version de modèle. |
| **Sécurité** | NIST 800‑53 SC‑13 – cryptographie | Chiffrer les logs au repos avec AES‑256‑GCM (clé gérée par HashiCorp Vault). |

---

## 5.2 Architecture de la chaîne d’audit

```
┌─────────────────────┐
│  Client (FastAPI)  │
└───────┬─────────────┘
        │   (1) Prompt + metadata
        ▼
┌─────────────────────┐
│  Middleware        │  →  Pseudonymisation (regex + spaCy NER)  
│  (OpenTelemetry)   │  →  Enrichissement (request_id, latency)  
└───────┬─────────────┘
        │   (2) Prompt_clean
        ▼
┌─────────────────────┐
│  Jarvis‑OS Engine   │
│  (model inference) │
└───────┬─────────────┘
        │   (3) Raw response
        ▼
┌─────────────────────┐
│  Post‑process       │  →  Filtrage toxicité (moderation API)  
│  (custom hook)      │  →  Pseudonymisation de la réponse  
└───────┬─────────────┘
        │   (4) Response_clean
        ▼
┌─────────────────────┐
│  Logger (OTEL)     │  →  Export → Elasticsearch + S3 (encrypted)  
│  + Audit Store      │  →  PostgreSQL (audit_schema)  
└─────────────────────┘
```

*Les flèches indiquent le flux de données. Chaque composant doit être **idempotent** pour garantir la résilience en cas de redémarrage.*

---

## 5.3 Implémentation pas à pas

### 5.3.1 Installation des dépendances

```bash
# Docker‑compose file includes:
# - fastapi (uvicorn)
# - otel-collector (OTLP over gRPC)
# - elasticsearch
# - postgresql
# - redis (celery broker)
# - vault (dev mode)

docker compose up -d
pip install "jarvis-os[all]" fastapi[all] opentelemetry-sdk \
    opentelemetry-instrumentation-fastapi spacy==3.7.2 \
    python-dotenv cryptography
python -m spacy download fr_core_news_md
```

> **Vérifiable** : `docker ps` doit afficher 6 conteneurs actifs, `spacy validate` doit confirmer que le modèle français est installé.

### 5.3.2 Middleware de pseudonymisation

```python
# file: middleware/pseudonymizer.py
import re
import spacy
from typing import Callable, Awaitable
from fastapi import Request, Response

nlp = spacy.load("fr_core_news_md")  # modèle NER français

# Regex de base pour les numéros de sécurité sociale (exemple français)
SSN_REGEX = re.compile(r"\b[12]\d{2}\s?\d{2}\s?\d{2}\s?\d{5}\b")

def mask_entity(text: str) -> str:
    """
    Remplace chaque entité PERSON, ORG, LOC et tout numéro de sécurité sociale
    par un token <PII>.
    """
    doc = nlp(text)
    masked = text
    # Masquage via spaCy
    for ent in reversed(doc.ents):  # parcourir à l'envers pour ne pas décaler les indices
        if ent.label_ in {"PER", "ORG", "LOC"}:
            start