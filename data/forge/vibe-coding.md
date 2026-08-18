# Vibe Coding 2026

> Référence `vibe-coding` · 39 €

## Plan

## Module 1 : Prompt Engineering avancé  
**Objectif mesurable** : À l’issue de ce module, le participant sera capable de concevoir, tester et itérer des prompts capables de générer des réponses avec une précision sémantique ≥ 90 % sur un jeu de validation de 100 requêtes.  

**Notions couvertes**  
1. Structure syntaxique des prompts (système, utilisateur, assistant) et impact sur le modèle.  
2. Techniques de few‑shot et chain‑of‑thought pour guider le raisonnement.  
3. Méthodes de contrôle de la température, top‑p et présence‑penalty pour la diversité et la cohérence.  
4. Analyse de la sortie : métriques BLEU, ROUGE, et évaluation humaine calibrée.  
5. Boucles d’optimisation automatisées (prompt‑tuning via API).

---

## Module 2 : Modélisation de données pour LLMs  
**Objectif mesurable** : Le participant pourra préparer un corpus de 10 Mo, le nettoyer, le tokeniser et le charger dans un pipeline d’entraînement, en respectant un taux d’erreur de pré‑traitement ≤ 1 %.  

**Notions couvertes**  
1. Nettoyage de texte (déduplication, normalisation Unicode, filtrage de toxicité).  
2. Tokenisation byte‑pair encoding (BPE) et comparaison avec WordPiece.  
3. Construction de jeux d’entraînement/validation/test équilibrés.  
4. Gestion des biais de distribution (stratification, rééchantillonnage).  
5. Utilisation de `datasets` de Hugging Face et de `DataCollator`.

---

## Module 3 : Fine‑tuning et adaptation de modèles pré‑entraînés  
**Objectif mesurable** : Le participant sera capable de fine‑tuner un modèle de 1,3 B paramètres sur un domaine spécifique en moins de 4 heures GPU, avec une perte de validation ≤ 0,45.  

**Notions couvertes**  
1. Sélection de l’architecture (GPT‑Neo, LLaMA, Falcon) et du checkpoint.  
2. Paramètres d’entraînement (learning‑rate, batch size, gradient accumulation).  
3. Techniques de LoRA (Low‑Rank Adaptation) et QLoRA pour réduire la consommation mémoire.  
4. Gestion des checkpoints et reprise d’entraînement (DeepSpeed, ZeRO‑3).  
5. Évaluation post‑entraînement (perplexité, exact‑match, métriques de tâche).

---

## Module 4 : Intégration d’IA générative dans des applications backend  
**Objectif mesurable** : Le participant pourra exposer une API REST sécurisée qui interroge un LLM fine‑tuned, avec un temps de latence moyen ≤ 200 ms pour 128 tokens, et implémenter une politique de quota.  

**Notions couvertes**  
1. Déploiement de modèles via `transformers` + `FastAPI` ou `Flask`.  
2. Optimisation d’inférence (ONNX, TensorRT, quantisation int8).  
3. Authentification OAuth2, gestion de tokens d’accès et limites de requêtes.  
4. Mise en cache des réponses (Redis) et stratégies de rafraîchissement.  
5. Monitoring (Prometheus, Grafana) et logs

---

## Module 1 — contenu

## Module 1 – Prompt Engineering avancé  

### 1. Structure syntaxique des messages  

| Niveau | Rôle | Exemple de champ | Influence sur le modèle |
|--------|------|------------------|--------------------------|
| Système | `system` | `"You are a helpful assistant that always returns JSON."` | Définit le comportement global, la tonalité et les contraintes de format. |
| Utilisateur | `user` | `"Explique la différence entre BPE et WordPiece en 2 phrases."` | Pose la question ou la tâche. Le modèle se base sur le contexte fourni. |
| Assistant | `assistant` | `"Sure, here is the answer …"` | Utilisé pour le few‑shot (exemples de réponses attendues). |

**Bonnes pratiques**  
- Le message `system` doit être concis : ≤ 150 tokens pour éviter de consommer le budget de contexte.  
- Chaque exemple `user`/`assistant` doit être complet : ne laissez pas de champs vides, sinon le modèle peut générer des réponses hors‑format.  
- Placez les contraintes de format (ex. `JSON`, `XML`) dans le `system` ou le premier `user` pour que le modèle les mémorise dès le départ.  

### 2. Few‑shot & Chain‑of‑thought (CoT)  

#### 2.1 Few‑shot  
```python
messages = [
    {"role": "system", "content": "You are a French tutor. Answer in French only."},
    {"role": "user",   "content": "Comment dit‑on 'apple' en français ?"},
    {"role": "assistant", "content": "Pomme"},
    {"role": "user",   "content": "Comment dit‑on 'computer' en français ?"},
    {"role": "assistant", "content": "Ordinateur"},
    # Prompt réel
    {"role": "user",   "content": "Comment dit‑on 'library' en français ?"}
]
```
- **Pourquoi ça marche** : le modèle infère le schéma *question → réponse courte* à partir des deux exemples.  
- **Limite** : chaque exemple consomme du contexte ; pour des modèles avec 8 k tokens, on ne peut pas dépasser ≈ 30 exemples avant d’impacter la longueur de la requête.

#### 2.2 Chain‑of‑thought  
```python
prompt = """Résous le problème suivant en détaillant chaque étape :

Quel est le résultat de (23 × 7) + (15 ÷ 3) ?

Réponse :"""
```
- **Effet** : le modèle génère un raisonnement explicite, ce qui augmente la précision sur les tâches de calcul ou de logique (voir *Wei et al., 2022*).  
- **Paramètre clé** : `temperature` doit être inférieur à 0.7 pour éviter des digressions inutiles.

### 3. Contrôle de la génération  

| Paramètre | Valeur typique | Impact |
|----------|----------------|--------|
| `temperature` | 0.0 – 0.7 | Plus bas → sortie déterministe, plus haut → diversité. |
| `top_p` (nucleus) | 0.9 – 1.0 | Couper la distribution à la probabilité cumulée `p`. |
| `presence_penalty` | 0.0 – 0.6 | Décourage la répétition de tokens déjà vus dans le contexte. |
| `frequency_penalty` | 0.0 – 0.6 | Décourage la sur‑utilisation d’un même token. |

**Exemple d’appel API (OpenAI)**  
```python
import openai

response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=messages,
    temperature=0.3,
    top_p=0.95,
    presence_penalty=0.2,
    frequency_penalty=0.0,
    max_tokens=150,
)
print(response["choices"][0]["message"]["content"])
```
- `max_tokens` doit être fixé en fonction du budget de latence : 150 tokens ≈ 0.12 s sur GPU A100.

### 4. Analyse de la sortie  

#### 4.1 Métriques automatiques  
- **BLEU** : compare n‑grammes de la réponse générée à une ou plusieurs références.  
- **ROUGE‑L** : mesure la longueur de la plus longue sous‑séquence commune.  
- **Exact‑match (EM)** : 1 si la réponse est identique à la référence, 0 sinon.  

```python
from nltk.translate.bleu_score import sentence_bleu
from rouge_score import rouge_scorer

ref = ["Pomme"]
hyp = ["pomme"]  # case‑insensitive

bleu = sentence_bleu([ref], hyp, weights=(1, 0, 0, 0))
scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
rouge = scorer.score(' '.join(ref), ' '.join(hyp))['rougeL'].fmeasure

print(f"BLEU={bleu:.3f}  ROUGE‑L={rouge:.3f}")
```
- **Limite** : ces scores ne capturent pas toujours la pertinence sémantique (ex. synonymes).  

#### 4.2 Évaluation humaine calibrée  
1. **Échelle 0‑5** : 0 = hors‑sujet, 5 = parfaitement conforme.  
2. **Guidelines** : préciser la prise en compte du format (JSON valide, respect du ton, etc.).  
3. **Inter‑annotateur** : calculer le coefficient de corrélation de Krippendorff (`α ≥ 0.8` requis).  

### 5. Boucles d’optimisation automatisées

---

## Module 2 — contenu

## Module 2 : Modélisation de données pour LLMs  

### 2.1 Nettoyage de texte  

| Étape | Action | Outils / Méthodes | Vérifiabilité |
|------|--------|-------------------|----------------|
| Déduplication | Suppression de lignes ou documents identiques (hash MD5 ou SHA‑256) | `pandas.DataFrame.drop_duplicates`, `set` Python | Le nombre d’entrées avant/après doit diminuer ou rester identique |
| Normalisation Unicode | Convertir toutes les chaînes en forme NFC (canonical composition) | `unicodedata.normalize('NFC', txt)` | `unicodedata.is_normalized('NFC', txt)` renvoie `True` |
| Nettoyage de ponctuation & espaces | Supprimer espaces multiples, normaliser les apostrophes, remplacer les tirets typographiques | Regex `re.sub(r'\s+', ' ', txt)`, `re.sub(r'[‘’´`]', "'", txt)` | Comparaison avant/après montre le nombre de caractères remplacés |
| Filtrage de toxicité | Éliminer les phrases contenant des mots de la liste de toxicité (ex. `detoxify` ou `Perspective API`) | `detoxify.Detoxify(model="original")` → `score['toxicity'] > 0.7` | Le taux de détection doit être mesurable sur un sous‑ensemble annoté |
| Normalisation des URLs & emails | Remplacer par des tokens `<URL>` / `<EMAIL>` | Regex `re.sub(r'https?://\S+', '<URL>', txt)` | Le nombre de remplacements doit correspondre au nombre d’occurrences détectées |

#### Exemple de pipeline de nettoyage (Python 3.10)

```python
import re
import hashlib
import unicodedata
from pathlib import Path
import pandas as pd
from detoxify import Detoxify

# 1️⃣ Chargement du corpus brut (un fichier texte par ligne)
raw_path = Path("data/raw_corpus.txt")
df = pd.read_csv(raw_path, sep="\n", header=None, names=["text"])

# 2️⃣ Déduplication (hash MD5)
df["hash"] = df["text"].apply(lambda x: hashlib.md5(x.encode("utf-8")).hexdigest())
df = df.drop_duplicates(subset="hash").drop(columns="hash")

# 3️⃣ Normalisation Unicode (NFC)
df["text"] = df["text"].apply(lambda x: unicodedata.normalize("NFC", x))

# 4️⃣ Nettoyage de ponctuation & espaces
def clean_spaces(txt: str) -> str:
    txt = re.sub(r"[‘’´`]", "'", txt)          # apostrophes typographiques
    txt = re.sub(r"[“”«»]", '"', txt)         # guillemets typographiques
    txt = re.sub(r"\s+", " ", txt)            # espaces multiples
    return txt.strip()
df["text"] = df["text"].apply(clean_spaces)

# 5️⃣ Filtrage de toxicité (seuil 0.7)
detox = Detoxify(model="original")
def is_toxic(txt: str) -> bool:
    scores = detox.predict(txt)
    return scores["toxicity"] > 0.7
df = df[~df["text"].apply(is_toxic)]

# 6️⃣ Masquage URLs et emails
url_pat = re.compile(r"https?://\S+|www\.\S+")
email_pat = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w{2,}\b")
df["text"] = df["text"].apply(lambda x: url_pat.sub("<URL>", x))
df["text"] = df["text"].apply(lambda x: email_pat.sub("<EMAIL>", x))

# 7️⃣ Export du corpus nettoyé
clean_path = Path("data/clean_corpus.txt")
df["text"].to_csv(clean_path, index=False, header=False)
print(f"Nettoyé : {len(df)} lignes conservées")
```

*Commentaires*  
- Chaque transformation est **déterministe** : exécuter deux fois le script sur le même fichier produit exactement le même résultat.  
- Le modèle `Detoxify` (v0.5.1) a une précision de 0.84 sur le benchmark CivilComments (source : GitHub detoxify).  
- Le pipeline respecte la contrainte d’erreur de pré‑traitement ≤ 1 % : le nombre de lignes supprimées doit être inférieur à 1 % du total, sinon ré‑évaluer le seuil de toxicité ou la logique de déduplication.

---

### 2.2 Tokenisation byte‑pair encoding (BPE) vs WordPiece  

| Critère | BPE (ex. GPT‑Neo) | WordPiece (ex. BERT) |
|--------|-------------------|----------------------|
| Algorithme de base | Fusion itérative des paires de caractères les plus fréquentes (Sennrich et al., 2016) | Construction d’un vocabulaire à partir de sous‑mots basés sur la fréquence maximale (Wu et al., 2016) |
| Taille typique du vocabulaire | 50 k – 250 k tokens | 30 k – 100 k tokens |
| Gestion des OOV | Aucun OOV : chaque chaîne est décomposée en sous‑tokens | OOV limité à `<unk>` si la chaîne ne peut pas être segmentée |
| Performance sur langues à forte agglutination | Supérieure (ex. turc, finnois) | Légèrement inférieure, mais plus stable pour les langues à alphabet latin simple |
| Implémentation Hugging Face

---

## Module 3 — contenu

## Module 3 : Fine‑tuning et adaptation de modèles pré‑entraînés  

### 3.1 Sélection de l’architecture et du checkpoint  

| Architecture | Paramètres (≈) | Licence | Points forts | Points faibles |
|--------------|----------------|---------|--------------|---------------|
| **GPT‑Neo 1.3B** | 1,3 B | MIT | Large communauté, support HF complet | Pas d’instructions fine‑tuned, performances inférieures à LLaMA‑2 7B |
| **LLaMA‑2 7B** | 7 B | Meta (requiert accord) | Meilleure perplexité, instruction‑tuned disponible | Mémoire GPU > 16 GB (sans DeepSpeed) |
| **Falcon‑7B‑Instruct** | 7 B | Apache 2.0 | Fine‑tuned sur instructions, poids disponibles sur HF | Pas de support officiel DeepSpeed (mais possible) |

**Choix recommandé pour l’objectif** : GPT‑Neo 1.3B (compatible GPU 8 GB + DeepSpeed ZeRO‑2).  

### 3.2 Paramètres d’entraînement  

| Hyper‑paramètre | Valeur typique (GPT‑Neo 1.3B) | Impact |
|-----------------|------------------------------|--------|
| `learning_rate` | 2 e‑5 → 5 e‑5 | Trop haut → divergence, trop bas → convergence lente |
| `batch_size` (per device) | 4–8 (FP16) | Influence mémoire ; augmenter avec gradient accumulation |
| `gradient_accumulation_steps` | 8–16 | Simule batch = batch_size × accum_steps |
| `max_steps` | 1500–2500 (≈ 4 h GPU A100 40 GB) | Ajuster selon taille du jeu |
| `weight_decay` | 0.01 | Régularisation L2 |
| `lr_scheduler_type` | `cosine` ou `linear` | Décroît le LR pendant l’entraînement |
| `warmup_steps` | 0.1 % du total | Stabilise les premiers updates |

**Rappel** : le nombre total d’updates = `len(train_dataset) // (batch_size * gradient_accumulation_steps)`.

### 3.3 Techniques de LoRA et QLoRA  

#### 3.3.1 Principes  

- **LoRA** (Low‑Rank Adaptation) ajoute deux matrices \(A \in \mathbb{R}^{d \times r}\) et \(B \in \mathbb{R}^{r \times d}\) (r ≈ 8–64) à chaque poids linéaire \(W\). Le poids effectif devient \(W + \Delta W\) avec \(\Delta W = \frac{\alpha}{r}AB\).  
- **QLoRA** quantise les poids du modèle en **int4** (ou int8) **avant** d’appliquer LoRA, ce qui réduit la RAM GPU de ~ 4× tout en conservant la précision du fine‑tuning grâce à la mise à jour des matrices LoRA en FP16.  

#### 3.3.2 Avantages mesurables  

| Métrique | Full‑fine‑tuning | LoRA (r = 16) | QLoRA (int4) |
|----------|------------------|---------------|--------------|
| GPU RAM (GPT‑Neo 1.3B) | ~ 12 GB | ~ 6 GB | ~ 3 GB |
| Temps d’entraînement (h) | 4.0 | 2.5 | 2.2 |
| Perplexité validation (exemple) | 7.8 | 8.1 | 8.2 |

#### 3.3.3 Implémentation avec `peft`  

```python
# fine_tune_lora.py
# -------------------------------------------------
# Fonctionnel avec HuggingFace Transformers >=4.35,
# PEFT >=0.5.0 et Accelerate >=0.23.0
# -------------------------------------------------
import os
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, prepare_model_for_int8_training
from accelerate import Accelerator

# 1. Initialisation
accelerator = Accelerator()
model_name = "EleutherAI/gpt-neo-1.3B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token  # GPT‑Neo n’a pas de PAD

# 2. Chargement du checkpoint en int8 (QLoRA)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    load_in_8bit=True,          # quantisation int8
    torch_dtype="auto"
)
model = prepare_model_for_int8_training(model)

# 3. Configuration LoRA (r=16, alpha=32)
lora_cfg = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "out_proj"],  # attention linéaires
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_cfg)

# 4. Jeu de données (exemple : wikitext‑2‑raw‑v1)
raw_dset = load_dataset("wikitext", "wikitext-2-raw-v1")
def tokenize_fn(ex):
    return tokenizer(
        ex["text"],
        truncation=True,
        max_length=512,
        padding="max_length",

---

## Module 4 — contenu

## 4.1 Architecture de service REST pour un LLM fine‑tuned  

| Composant | Rôle | Bibliothèque / Outil recommandé |
|----------|------|----------------------------------|
| **API** | Point d’entrée HTTP, sérialisation JSON, validation des requêtes | `FastAPI` (pydantic) |
| **Modèle** | Chargement en mémoire, inférence | `transformers` + `torch` (ou `accelerate`), éventuellement `optimum` pour ONNX/Quant |
| **Cache** | Mémoire clé‑valeur pour réponses déjà générées | `redis-py` (Redis) |
| **Auth / Quota** | Vérification d’un token OAuth2, comptage d’appels par client | `fastapi.security.OAuth2PasswordBearer`, `redis` (counters) |
| **Monitoring** | Métriques d’inférence, latence, erreurs | `prometheus_client` + `Grafana` (exporter) |
| **Serveur** | Gestion du processus, logs, redémarrage | `uvicorn` (workers = 4), `systemd` ou `Docker` |

### 4.1.1 Schéma de flux  

```
Client → (HTTPS) → FastAPI endpoint /generate
   │
   ├─► Authentifie le token (OAuth2)
   │
   ├─► Vérifie le quota (Redis incr)
   │
   ├─► Recherche dans le cache (hash du prompt)
   │    ├─► Hit → renvoie réponse cachée
   │    └─► Miss → passe au modèle
   │
   ├─► Modèle (GPU) → génère texte
   │
   ├─► Stocke la réponse dans le cache (TTL configurable)
   │
   └─► Retour HTTP 200 + métriques Prometheus
```

---

## 4.2 Déploiement du modèle  

### 4.2.1 Chargement avec `transformers` + `accelerate`

```python
# model_loader.py
from transformers import AutoModelForCausalLM, AutoTokenizer
from accelerate import init_empty_weights, infer_auto_device_map
import torch

def load_model(model_name: str, device: str = "cuda"):
    """
    Charge le modèle en mode quantisé int8 si possible.
    Retourne (model, tokenizer).
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

    # 1️⃣ Charger les poids en mode "empty" pour appliquer le device map
    with init_empty_weights():
        model = AutoModelForCausalLM.from_pretrained(model_name)

    # 2️⃣ Déterminer le device map optimal (ZeRO‑3, offload)
    device_map = infer_auto_device_map(
        model,
        max_memory={0: "12GiB", "cpu": "2GiB"},  # ajuster selon le GPU disponible
        dtype=torch.float16,
    )

    # 3️⃣ Re‑charger les poids sur les devices définis
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map=device_map,
        torch_dtype=torch.float16,
    )

    # 4️⃣ (Optionnel) quantisation int8 via Optimum
    try:
        from optimum.intel import INCModelForCausalLM
        model = INCModelForCausalLM.from_pretrained(model, export=True)
    except Exception:
        pass  # pas d’Intel extension, on garde le modèle FP16

    model.eval()
    return model, tokenizer
```

*Points de vérification*  

- `torch.cuda.is_available()` doit être **True** sur le nœud de production.  
- Le `device_map` doit couvrir **tous** les sous‑modules ; sinon `RuntimeError: some layers not on device`.  
- La quantisation int8 ne fonctionne que sur des modèles supportés par `optimum`; sinon, ignorer le bloc `try/except`.

### 4.2.2 Optimisation d’inférence  

| Technique | Quand l’utiliser | Implémentation |
|-----------|------------------|----------------|
| **ONNX export + TensorRT** | Latence < 100 ms, batch = 1, GPU RTX 3080+ | `optimum.onnxruntime` → `ORTModelForCausalLM` + `torch.compile` |
| **Quantisation int8** | Mémoire < 8 GB, perte de perplexité < 0.2 | `optimum.intel` ou `bitsandbytes` (`bnb.nn.Linear8bitLt`) |
| **Batching dynamique** | Plusieurs requêtes simultanées | `FastAPI` + `asyncio.gather` + `torch.cuda.synchronize()` |

Exemple d’export ONNX :

```python
# export_onnx.py
from optimum.onnxruntime import ORTModelForCausalLM
from transformers import AutoTokenizer

model_name = "bigscience/bloom-560m"
tokenizer = AutoTokenizer.from_pretrained(model_name)

ort_model = ORTModelForCausalLM.from_pretrained(
    model_name,
    from_transformers=True,          # conversion automatique
    export=True,                    # crée le fichier .onnx
    provider="CUDAExecutionProvider"
)

ort_model.save_pretrained("./bloom_560m_onnx")
```

---

## 4.3 API FastAPI sécurisée  

### 4.3.1 Définition du schéma de requête

```python
# schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

class GenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1024)
    max_new_tokens: int = Field(128, ge=1, le=512)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    stop: Optional[List

---

## Module 5 — contenu

## Module 5 : MLOps et gestion du cycle de vie des LLMs  

### 5.1 Gestion des versions de modèles  

| Concept | Description | Référence |
|--------|-------------|-----------|
| **Model Registry** | Un catalogue centralisé qui stocke le poids, les métadonnées (hash SHA‑256, hyper‑paramètres, jeu de validation) et le statut (Staging, Production, Archived). | MLflow Model Registry, Hugging Face Hub |
| **Semantic versioning** | `MAJOR.MINOR.PATCH` où : <br>• MAJOR : rupture d’API (ex. changement de tokenisation) <br>• MINOR : ajout de capacités sans rupture (ex. nouveau prompt‑template) <br>• PATCH : correction de bug ou ré‑entrainement mineur | https://semver.org/ |
| **Hash de contrôle** | Calculer `sha256` du fichier `pytorch_model.bin` (ou `ggml‑model‑q4_0.bin` pour GGML) et le stocker dans le registre. Permet de détecter toute altération accidentelle. | `hashlib.sha256(open(path, "rb").read()).hexdigest()` |

#### Exemple : Enregistrement d’un modèle fine‑tuned avec MLflow  

```python
# file: register_model.py
import mlflow
import hashlib
import json
from pathlib import Path
import torch

# 1️⃣ Chemin du checkpoint fine‑tuned
ckpt_path = Path("./outputs/checkpoint-epoch3/pytorch_model.bin")

# 2️⃣ Calcul du hash SHA‑256 (vérifiable)
hash_sha256 = hashlib.sha256(ckpt_path.read_bytes()).hexdigest()

# 3️⃣ Méta‑données du modèle
metadata = {
    "model_name": "falcon-7b-loRA",
    "framework": "pytorch",
    "training_dataset": "legal_fr_v1",
    "validation_perplexity": 12.3,
    "hash_sha256": hash_sha256,
    "git_commit": "a1b2c3d",          # version du code source
    "training_args": {
        "learning_rate": 2e-4,
        "batch_size": 8,
        "epochs": 3
    }
}

# 4️⃣ Démarrage d’un run MLflow
with mlflow.start_run(run_name="falcon-7b-loRA-epoch3") as run:
    # Log du fichier binaire
    mlflow.log_artifact(str(ckpt_path), artifact_path="model")
    # Log des métadonnées (format JSON)
    mlflow.log_text(json.dumps(metadata, indent=2), "metadata.json")
    # Enregistrement dans le registre
    model_uri = f"runs:/{run.info.run_id}/model"
    mlflow.register_model(model_uri, "falcon-7b-loRA")
```

*Le script est autonome : il ne dépend que de `mlflow`, `torch` et de la bibliothèque standard.*  

---

### 5.2 CI/CD pour LLMs  

1. **Pipeline de tests unitaires** (ex. vérifier que le tokenizer ne génère pas d’`<unk>` sur un sous‑ensemble de validation).  
2. **Pipeline d’intégration** : entraînement rapide (≤ 5 min) sur un sous‑jeu, calcul du `validation_perplexity` et comparaison avec le seuil fixé (`< 0.5` d’écart).  
3. **Déploiement automatisé** : si le job de validation passe, le modèle est promu de *Staging* à *Production* dans le registre et le service FastAPI est redéployé via Docker‑Compose ou Kubernetes.  

#### Exemple : Workflow GitHub Actions (`.github/workflows/ci.yml`)  

```yaml
name: CI/CD LLM

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install mlflow pytest
      - name: Run unit tests
        run: pytest tests/unit
      - name: Quick finetune (5‑min)
        run: |
          python scripts/quick_finetune.py \
            --max_steps 100 \
            --output_dir ./tmp/model
      - name: Compute perplexity
        id: perplexity
        run: |
          python scripts/eval_perplexity.py \
            --model_dir ./tmp/model \
            --split validation > perplexity.txt
          cat perplexity.txt
      - name: Check threshold
        if: success()
        run: |
          PERP=$(cat perplexity.txt | grep -oP '\d+\.\d+')
          echo "Perplexity=$PERP"
          if (( $(echo "$PERP > 13.0" | bc -l) )); then
            echo "❌ Perplexity too high"
            exit 1
          fi

  deploy:
    needs: test
    runs-on: ubuntu-latest