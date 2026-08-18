# Phanesis — Transcription Multilingue

> Référence `lumen-multilang` · 59 €

## Plan

## Module 1 : Architecture et principes de la transcription multilingue  
**Objectif mesurable** : L’apprenant implémente, à partir de zéro, un pipeline d’inférence capable de transcrire du texte en français, anglais et espagnol avec un taux d’erreur de mots (WER) ≤ 15 % sur le jeu de validation Common Voice.  

- Modèles de base : Whisper tiny, wav2vec 2.0, Conformer.  
- Encodage acoustique vs décodage linguistique.  
- Gestion du vocabulaire multilingue (Byte‑Pair Encoding, SentencePiece).  
- Alignement temporel des sorties (CTC vs seq2seq).  
- Métriques d’évaluation : WER, CER, BLEU pour la traduction simultanée.

## Module 2 : Pré‑traitement et enrichissement des données audio  
**Objectif mesurable** : L’apprenant prépare un corpus multilingue de ≥ 200 h d’audio, applique des augmentations contrôlées et génère des alignements phonétiques avec une précision ≥ 90 % sur un sous‑ensemble annoté.  

- Normalisation du signal (16 kHz, 16 bits, RMS).  
- Augmentations : bruit de fond (MUSAN), vitesse, pitch shifting, SpecAugment.  
- Extraction de caractéristiques : MFCC, log‑Mel spectrogram, HuBERT embeddings.  
- Alignement forcé avec Montreal Forced Aligner.  
- Construction de manifestes JSON compatibles avec ESPnet/NeMo.

## Module 3 : Fine‑tuning d’un modèle pré‑entraîné sur un domaine ciblé  
**Objectif mesurable** : L’apprenant réalise un fine‑tuning sur un jeu de données sectoriel (ex. télé‑consultation médicale) et améliore le WER de 12 % par rapport au modèle de base.  

- Stratégies de gel de couches et d’apprentissage différentiel.  
- Optimiseurs et planificateurs de taux d’apprentissage (AdamW, cosine annealing).  
- Gestion du déséquilibre linguistique (sampling, loss weighting).  
- Validation croisée temporelle et early stopping.  
- Utilisation de PyTorch Lightning pour le suivi des expériences.

## Module 4 : Déploiement efficace et scalabilité  
**Objectif mesurable** : L’apprenant déploie le modèle sur un serveur Docker avec un temps de latence moyen ≤ 200 ms par seconde d’audio et consomme ≤ 2 W GPU (NVIDIA T4).  

- Export ONNX et quantisation dynamique/int8.  
- Serveur d’inférence Triton vs FastAPI + TorchServe.  
- Batching dynamique et gestion de la mémoire GPU.  
- Monitoring (Prometheus, Grafana) et métriques de SLA.  
- Sécurisation des flux audio (TLS, token JWT).

## Module 5 : Évaluation continue, adaptation et conformité juridique  
**Objectif mesurable** : L’apprenant met en place un pipeline d’évaluation automatisé qui détecte les dérives de performance ≥ 5 % et déclenche un ré‑entraînement mensuel, tout en assurant la conformité RGPD.  

- Tests A/B en production et analyse statistique (boot

---

## Module 1 — contenu

## 1.1 Architecture générale d’un système de transcription multilingue  

| Bloc | Fonction | Implémentation typique |
|------|----------|------------------------|
| **Pre‑processing** | Normalisation du signal, extraction de spectrogrammes | `torchaudio.transforms.Resample`, `LogMelSpectrogram` |
| **Encodeur acoustique** | Convertit le signal en une séquence de vecteurs latents | Whisper‑tiny (transformer), wav2vec 2.0 (CNN‑Transformer), Conformer (CNN + self‑attention) |
| **Décodeur linguistique** | Génère la séquence de tokens à partir des latents | Decoder seq2seq (Whisper), CTC greedy/beam‑search (wav2vec 2.0, Conformer) |
| **Post‑processing** | Décodage du vocabulaire, ponctuation, normalisation de texte | SentencePiece‑BPE, `tokenizer.decode`, `postprocess_text` |
| **Évaluation** | Calcul du WER / CER / BLEU | `jiwer.wer`, `torchmetrics.CharErrorRate`, `sacrebleu` |

Le pipeline doit être **modulaire** : chaque bloc peut être remplacé sans toucher aux autres. En pratique, on utilise souvent les API de `transformers` (Hugging Face) ou `espnet` qui exposent déjà ces blocs sous forme de classes Python.

---

## 1.2 Modèles de base  

| Modèle | Taille | Architecture | Langues supportées (exemple) | Licence |
|--------|--------|--------------|-----------------------------|---------|
| **Whisper‑tiny** | 39 M paramètres | Transformer encoder‑decoder, pré‑entraînement multitâche (ASR + traduction) | 99 % des langues du Common Voice (≈ 96 % du corpus) | MIT |
| **wav2vec 2.0‑base** | 95 M | CNN + Transformer, pré‑entraînement self‑supervised (contrastive) | 53 langues (pré‑entraînement multilingual) | Apache‑2.0 |
| **Conformer‑small** | 30 M | Convolution‑augmented Transformer (CNN + MHSA) | 15 langues (anglais, français, espagnol, …) | Apache‑2.0 |

> **Vérifiable** : les tailles et architectures sont indiquées dans les fiches GitHub respectives (`openai/whisper`, `facebook/wav2vec2-base`, `espnet/Conformer`).

---

## 1.3 Encodage acoustique vs décodage linguistique  

* **Encodage acoustique** produit une représentation temporelle `T × D` (T = nombre de frames, D = dimension du vecteur latent).  
* **Décodage linguistique** transforme cette séquence en tokens. Deux paradigmes :  

| Paradigme | Principe | Avantages | Inconvénients |
|----------|----------|-----------|----------------|
| **CTC (Connectionist Temporal Classification)** | Décodage greedy ou beam‑search sur la distribution `softmax` à chaque frame, avec token *blank* | Simple, pas besoin d’alignement explicite, bonne vitesse | Pas de modèle de langue intégré, difficulté à gérer la ponctuation |
| **Seq2Seq (Encoder‑Decoder avec attention)** | Le décodeur génère un token à la fois, conditionné sur le contexte complet via attention | Modèle de langue intégré, meilleure ponctuation, support traduction simultanée | Coût mémoire + latence plus élevés, nécessite un jeu d’entraînement aligné (teacher‑forcing) |

Whisper utilise le second (seq2seq) ; wav2vec 2.0 et Conformer sont généralement exploités en CTC, mais on peut les coupler à un **LM shallow fusion** (ex. KenLM) pour compenser l’absence de modèle de langue.

---

## 1.4 Gestion du vocabulaire multilingue  

1. **Byte‑Pair Encoding (BPE)** – découpé en sous‑mots, permet de couvrir plusieurs langues avec un vocabulaire partagé (ex. 32 k tokens).  
2. **SentencePiece (unigram ou BPE)** – même principe, mais le modèle est entraîné directement sur le texte multilingue, ce qui garantit que les caractères rares (ñ, ç, …) sont présents.  

### Exemple d’entraînement SentencePiece  

```python
# train_sentencepiece.py
import sentencepiece as spm
import pathlib

# 1. Rassembler les transcriptions multilingues dans un seul fichier texte
corpus_path = pathlib.Path("data/corpus.txt")   # chaque ligne = une phrase (FR/EN/ES)

# 2. Lancer l'entraînement
spm.SentencePieceTrainer.train(
    input=str(corpus_path),
    model_prefix="spm_multilingual",
    vocab_size=32000,
    character_coverage=1.0,          # couvre tous les caractères Unicode présents
    model_type="bpe",                # ou "unigram"
    user_defined_symbols="[CLS],[SEP]"  # optionnel, pour des tokens spéciaux
)

print("Modèle entraîné → spm_multilingual.model + .vocab")
```

*Le fichier `spm_multilingual.model` sera chargé par le décodeur du modèle ASR (ex. Whisper) pour convertir les IDs en texte.*  

**Piège** : si le corpus d’entraînement ne contient pas assez d’exemples d’une langue rare, le tokenizer peut fragmenter ces mots en trop petits sous‑tokens, augmentant le WER. La solution consiste à **sur‑échantillonner** les phrases de ces langues ou à **ajouter des tokens spéciaux** (`

---

## Module 2 — contenu

## 2.1 Normalisation du signal  

| Étape | Action | Commande / Code | Vérification |
|------|--------|----------------|--------------|
| **Resampling** | Convertir tout le corpus en 16 kHz (ou 8 kHz pour modèles ultra‑légers). | ```python\nimport torchaudio\nwave, sr = torchaudio.load(path)\nwave = torchaudio.functional.resample(wave, sr, 16000)\n``` | `wave.shape[0] == 1` (mono) et `sr == 16000` |
| **Quantisation** | 16 bits PCM (int16) → float32 dans `[-1, 1]`. | ```python\nwave = wave.float() / 32768.0  # si wave était int16\n``` | `wave.max() <= 1.0` et `wave.min() >= -1.0` |
| **Normalisation RMS** | Appliquer un gain pour que le RMS ≈ -20 dBFS (0.1). | ```python\nimport torch\nrms = torch.sqrt(torch.mean(wave**2))\nwave = wave * (0.1 / rms)\n``` | `torch.isclose(torch.sqrt(torch.mean(wave**2)), torch.tensor(0.1), atol=1e‑3)` |

> **Piège** : le resampling doit être effectué **avant** la normalisation RMS, sinon le gain appliqué sera faussé par la modification de la densité spectrale.

---

## 2.2 Augmentations contrôlées  

Les augmentations sont appliquées *on‑the‑fly* pendant le chargement du dataset afin de ne pas gonfler le stockage.  

| Type | Bibliothèque | Exemple (pipeline `torch.utils.data.Dataset`) |
|------|--------------|----------------------------------------------|
| Bruit de fond (MUSAN) | `torchaudio.sox_effects` + `torch` | ```python\nimport random, torch, torchaudio\nclass AugmentedDataset(torch.utils.data.Dataset):\n    def __init__(self, manifest, musan_dir, prob_noise=0.3):\n        self.manifest = manifest\n        self.musan_files = list(Path(musan_dir).rglob('*.wav'))\n        self.prob_noise = prob_noise\n    def __len__(self):\n        return len(self.manifest)\n    def __getitem__(self, idx):\n        entry = self.manifest[idx]\n        wav, sr = torchaudio.load(entry['audio_filepath'])\n        # resample / normalize déjà fait dans le manifest\n        if random.random() < self.prob_noise:\n            noise_path = random.choice(self.musan_files)\n            noise, _ = torchaudio.load(noise_path)\n            # tronquer ou répéter le bruit à la même durée\n            if noise.shape[1] < wav.shape[1]:\n                repeats = wav.shape[1] // noise.shape[1] + 1\n                noise = noise.repeat(1, repeats)[:, :wav.shape[1]]\n            else:\n                noise = noise[:, :wav.shape[1]]\n            # SNR entre 0 et 20 dB\n            snr_db = random.uniform(0, 20)\n            wav_power = wav.norm(p=2)\n            noise_power = noise.norm(p=2)\n            scale = wav_power / (10**(snr_db/20) * noise_power)\n            wav = wav + scale * noise\n        return wav.squeeze(0), entry['transcript']\n``` |
| Speed‑perturbation | `torchaudio.functional.time_stretch` (via SoX) | ```python\nif random.random() < 0.2:\n    factor = random.choice([0.9, 1.0, 1.1])\n    wav, _ = torchaudio.sox_effects.apply_effects_tensor(wav, sr, [['speed', str(factor)], ['rate', str(sr)]])\n``` |
| Pitch‑shifting | `torchaudio.sox_effects` | ```python\nif random.random() < 0.2:\n    n_steps = random.randint(-2, 2)  # semitones\n    wav, _ = torchaudio.sox_effects.apply_effects_tensor(wav, sr, [['pitch', str(n_steps*100)], ['rate', str(sr)]])\n``` |
| SpecAugment (spectrogram) | `torch.nn.functional` | ```python\nspec = torchaudio.transforms.MelSpectrogram(sample_rate=sr)(wav)\n# time mask\ntime_mask = torchaudio.transforms.TimeMasking(time_mask_param=30)\nspec = time_mask(spec)\n# freq mask\nfreq_mask = torchaudio.transforms.FrequencyMasking(freq_mask_param=15)\nspec = freq_mask(spec)\n``` |

> **Piège** : appliquer `speed` ou `pitch` sans ré‑ajuster le taux d’échantillonnage (`rate`) entraîne un *aliasing* audible et dégrade le WER. Toujours finir la chaîne d’effets par `['rate', str(sr)]`.

---

## 2.3 Extraction de caractéristiques  

| Métrique | Implémentation | Paramètres recommandés (Common Voice) |
|----------|----------------|----------------------------------------|
| **MFCC** | `torchaudio.compliance.kaldi.mfcc` | `num_mfcc=13, frame_length=25e-3, frame_shift=10e-3, sample_frequency=16000` |
| **Log‑Mel Spectrogram** | `torchaudio.transforms.MelSpectrogram` + `torch.log1p` | `n_mels=

---

## Module 3 — contenu

## Module 3 : Fine‑tuning d’un modèle pré‑entraîné sur un domaine ciblé  

### 3.1. Principes de base du fine‑tuning  

| Concept | Description technique | Référence |
|--------|-----------------------|-----------|
| **Gel de couches** | Empêche la mise à jour des poids d’une sous‑partie du réseau (ex. encodeur : `requires_grad=False`). | HuggingFace transformers doc [Freezing layers] |
| **Apprentissage différentiel** | Applique un taux d’apprentissage (LR) plus élevé aux couches nouvellement ajoutées (ex. tête de décodage) et plus faible aux couches pré‑entraînées. | Howard & Ruder 2018 “ULMFiT” |
| **Loss weighting** | Multiplie la loss par un facteur > 1 pour les langues sous‑représentées afin de compenser le déséquilibre. | Kumar et al. 2020 “Balanced Cross‑Entropy” |
| **Early stopping** | Arrête l’entraînement si la perte de validation ne s’améliore pas pendant *p* époques (p ≈ 5). | Goodfellow et al. 2016 |
| **Cross‑validation temporelle** | Découpe le corpus en blocs chronologiques (ex. jan‑mar, apr‑jun…) afin d’éviter la fuite d’informations entre train/val. | Bergstra et al. 2012 |

---

### 3.2. Architecture du pipeline de fine‑tuning  

```
┌─────────────────────┐
│  Dataset (audio+txt)│
└───────┬─────────────┘
        │
        ▼
┌─────────────────────┐   ┌─────────────────────┐
│  DataModule (PL)    │──►│  CollateFn (pad)    │
└───────┬─────────────┘   └───────┬─────────────┘
        │                         │
        ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐
│  Model (Whisper‑tiny)│   │  Tokenizer (BPE)    │
└───────┬─────────────┘   └───────┬─────────────┘
        │                         │
        ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐
│  LightningModule    │──►│  Optimizer + Scheduler│
└───────┬─────────────┘   └─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  Trainer (PL)       │
└─────────────────────┘
```

---

### 3.3. Implémentation concrète (PyTorch Lightning + 🤗 Transformers)

> **Contexte** : fine‑tuning de `openai/whisper-tiny` sur un jeu de données médical (≈ 30 h d’audio, 3 langues : fr, en, es).  
> **Objectif** : réduire le WER de 12 % par rapport au modèle de base (ex. WER = 18 % → ≈ 15,8 %).  

#### 3.3.1. Pré‑requis (versions exactes)

```bash
python==3.10
torch==2.2.0
pytorch-lightning==2.2.2
transformers==4.40.0
datasets==2.18.0
torchaudio==2.2.0
jiwer==3.0.3
```

#### 3.3.2. `MedicalASRDataModule`

```python
# file: datamodule.py
import os
import json
import torch
import torchaudio
from torch.utils.data import Dataset, DataLoader
from transformers import WhisperProcessor
from pathlib import Path

class MedicalASRDataset(Dataset):
    """Dataset compatible avec WhisperProcessor.
    Chaque entrée du manifest JSON doit contenir:
        {"audio_path": "...", "text": "...", "language": "fr"}
    """
    def __init__(self, manifest_path: str, processor: WhisperProcessor):
        self.manifest = json.load(open(manifest_path, "r", encoding="utf-8"))
        self.processor = processor

    def __len__(self):
        return len(self.manifest)

    def __getitem__(self, idx):
        entry = self.manifest[idx]
        wav, sr = torchaudio.load(entry["audio_path"])
        # Resample si nécessaire (Whisper attend 16 kHz)
        if sr != 16000:
            wav = torchaudio.functional.resample(wav, sr, 16000)
        # Normalisation RMS (optionnel, déjà faite en pré‑traitement)
        wav = wav / wav.abs().max()
        # Tokenisation
        input_features = self.processor(
            wav.squeeze().numpy(),
            sampling_rate=16000,
            return_tensors="pt"
        ).input_features.squeeze(0)          # (1, seq_len, feat_dim) → (seq_len, feat_dim)

        # Whisper attend un token de langue en préfixe
        language_token = self.processor.tokenizer.get_lang_id(entry["language"])
        target_ids = self.processor.tokenizer(
            entry["text"],
            add_special_tokens=False
        ).input_ids
        #

---

## Module 4 — contenu

## 4.1 Export du modèle vers ONNX  

| Étape | Commande / Code | Explication vérifiable |
|------|----------------|------------------------|
| 1️⃣ Charger le modèle PyTorch (Whisper‑tiny) | ```python\nimport torch, whisper\nmodel = whisper.load_model("tiny")\n``` | `whisper` v2023.06.07 expose `load_model` qui renvoie un `nn.Module` déjà en mode eval. |
| 2️⃣ Définir un *dummy* d’entrée (log‑Mel spectrogram) | ```python\nsample_rate = 16000\nn_mels = 80\nseq_len = 3000   # ≈ 30 s à 100 Hz\ndummy = torch.randn(1, n_mels, seq_len)   # (B, C, T)\n``` | Le pré‑processeur Whisper attend un spectrogramme de forme `(batch, n_mels, time)`. |
| 3️⃣ Tracer le graphe avec `torch.onnx.export` | ```python\ntorch.onnx.export(\n    model,\n    dummy,\n    \"whisper_tiny.onnx\",\n    export_params=True,\n    opset_version=17,\n    do_constant_folding=True,\n    input_names=[\"spectrogram\"],\n    output_names=[\"logits\"],\n    dynamic_axes={\n        \"spectrogram\": {2: \"time\"},   # axe temporel variable\n        \"logits\": {1: \"seq\"}\n    },\n)\nprint(\"Export OK\")\n```<br>**Vérification** : le fichier `whisper_tiny.onnx` doit contenir les nœuds `Conv`, `LayerNorm`, `GELU`, `Linear` et le `CTC/Seq2Seq` head selon le code source de Whisper. |
| 4️⃣ Vérifier l’intégrité avec `onnxruntime` | ```python\nimport onnxruntime as ort\nsess = ort.InferenceSession(\"whisper_tiny.onnx\")\nlogits = sess.run(None, {\"spectrogram\": dummy.numpy()})\nprint(logits[0].shape)\n``` | La forme retournée doit être `(1, seq_len, vocab_size)` où `vocab_size = 51864` pour Whisper. |

### Pièges fréquents  

| Situation | Pourquoi c’est un problème | Solution |
|-----------|----------------------------|----------|
| **Opset trop bas** (`opset_version < 13`) | Certains opérateurs de `torch.nn.functional.gelu` ne sont pas supportés. | Utiliser `opset_version >= 16` (ex. 17). |
| **Axes dynamiques non déclarés** | ONNX ne peut pas accepter des séquences de longueur variable → erreur `RuntimeError: shape inference failed`. | Ajouter `dynamic_axes` pour les dimensions temporelles. |
| **Conversion du `torch.float16` en `float32`** | `onnxruntime` sur CPU ne supporte pas `float16` en entrée. | Exporter en `float32` puis quantiser séparément (section 4.2). |
| **Modèle Whisper utilise `torch.jit.script` interne** | Certaines fonctions (ex. `torch.nn.functional.unfold`) ne sont pas exportables. | Remplacer le bloc concerné par une implémentation pure PyTorch ou désactiver le `torch.jit` du modèle avant export. |

---

## 4.2 Quantisation dynamique et int8  

```bash
# 1️⃣ Installation des outils
pip install onnx onnxruntime onnxruntime-gpu onnxruntime-tools
```

```python
# 2️⃣ Quantisation dynamique (float32 → int8) – compatible CPU & GPU
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType

model_fp32 = "whisper_tiny.onnx"
model_int8 = "whisper_tiny_int8.onnx"

quantize_dynamic(
    model_input=model_fp32,
    model_output=model_int8,
    weight_type=QuantType.QInt8,   # int8 poids, activations restent float32
    per_channel=True,
    reduce_range=False,
)

print("Quantisation dynamique terminée")
```

### Quantisation statique (int8 activations) – nécessite un jeu de calibration  

```python
from onnxruntime.quantization import quantize_static, CalibrationDataReader, QuantFormat, CalibrationMethod

class WhisperCalibReader(CalibrationDataReader):
    def __init__(self, data_path, batch_size=8):
        self.batch_size = batch_size
        self.files = [os.path.join(data_path, f) for f in os.listdir(data_path) if f.endswith(".pt")]
        self.iterator = iter(self.files)

    def get_next(self):
        try:
            batch = []
            for _ in range(self.batch_size):
                path = next(self.iterator)
                batch.append(torch.load(path).numpy())
            return {"spectrogram": np.concatenate(batch, axis=0)}
        except StopIteration:
            return None

calib_reader = WhisperCalibReader("./calib_data")
quantize_static(
    model_input=model_fp32,
    model_output="whisper_tiny_int8_static.onnx",
    calibration_data_reader=calib_reader,
    quant_format=QuantFormat.QOperator,
    activation_type=QuantType.QInt8,
    weight_type=QuantType.QInt8,
    calibrate_method=CalibrationMethod.MinMax,
)

print("Quantisation statique terminée")
```

**Vérification** : mesurer le WER avant/après quantisation sur le même sous‑jeu de validation. La perte de précision doit être < 0.5 % WER

---

## Module 5 — contenu

## 5.1 Détection de dérive de performance  

| Étape | Action | Outils / Bibliothèques | Détails techniques |
|------|--------|------------------------|--------------------|
| 5.1.1 | Collecte de métriques en temps réel | **Prometheus** (exporter custom), **Grafana** (dashboards) | Exporter `wer`, `cer`, latence et taux d’erreur de transcription via un endpoint `/metrics` (format texte Prometheus). |
| 5.1.2 | Stockage historique | **TimescaleDB** (extension PostgreSQL) | Partitionner par jour, indexer sur `model_version` et `language`. |
| 5.1.3 | Calcul de la dérive | Script Python (pandas, scipy) exécuté chaque heure | *Window* : dernières 24 h vs fenêtre de référence (7 j). Utiliser le test de **Mann‑Whitney U** (p < 0.01) pour détecter une hausse statistiquement significative du WER. |
| 5.1.4 | Seuil de déclenchement | 5 % d’augmentation du WER moyen ou p‑value < 0.01 | Le seuil doit être paramétrable (`config.yaml`). |
| 5.1.5 | Alerting | **Alertmanager** (Prometheus) → **Slack** / **PagerDuty** | Message contenant `model_version`, `language`, `WER_current`, `WER_reference`. |

### Exemple d’exporter Prometheus (FastAPI)

```python
# file: metrics_exporter.py
from fastapi import FastAPI, Request
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time

app = FastAPI()

# Compteurs globaux
REQ_TOTAL = Counter(
    "asr_requests_total",
    "Nombre total de requêtes ASR",
    ["model_version", "language"]
)

# Gauges pour les métriques d’erreur
WER_GAUGE = Gauge(
    "asr_wer",
    "Word Error Rate moyen (sur la fenêtre glissante)",
    ["model_version", "language"]
)

# Simuler l’injection de métriques depuis la base de données
def update_metrics():
    # Exemple de données récupérées (à remplacer par une vraie requête)
    stats = [
        {"model_version": "v1.2", "language": "fr", "wer": 0.132},
        {"model_version": "v1.2", "language": "en", "wer": 0.108},
        {"model_version": "v1.2", "language": "es", "wer": 0.145},
    ]
    for s in stats:
        WER_GAUGE.labels(s["model_version"], s["language"]).set(s["wer"])

# Cron interne (simplifié) – à remplacer par APScheduler ou Kubernetes CronJob
@app.on_event("startup")
def schedule_updater():
    import threading

    def loop():
        while True:
            update_metrics()
            time.sleep(300)  # toutes les 5 min

    threading.Thread(target=loop, daemon=True).start()


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

*Points critiques*  
- **Synchronisation** : le job qui met à jour les métriques doit être idempotent ; sinon le même enregistrement peut être compté plusieurs fois.  
- **Granularité** : ne pas exporter le WER par requête individuelle (confidentialité) – agréger sur une fenêtre (ex. 5 min).  
- **Sécurité** : l’endpoint `/metrics` doit être protégé par TLS et, idéalement, par authentification mutuelle (client cert).  

---

## 5.2 Pipeline de ré‑entraînement automatisé  

### Architecture générale  

```
+-------------------+      +-------------------+      +-------------------+
|  Ingestion audio  | ---> |  Feature store    | ---> |  Drift detector   |
+-------------------+      +-------------------+      +-------------------+
                                            |
                                            v
                                   +-------------------+
                                   |  Scheduler (cron) |
                                   +-------------------+
                                            |
                                            v
                                   +-------------------+
                                   |  Retraining job   |
                                   +-------------------+
                                            |
                                            v
                                   +-------------------+
                                   |  Model registry   |
                                   +-------------------+
```

### Étape 5.2.1 Pré‑sélection des données  

1. **Filtrage par langue** : `language IN ('fr','en','es')`.  
2. **Pondération temporelle** : poids = `exp(-Δt/30d)` pour favoriser les enregistrements récents.  
3. **Échantillonnage équilibré** : sous‑échantillonner les langues sur‑représentées jusqu’à `N = 100 000` segments.  

```python
# file: data_selector.py
import pandas as pd
import numpy as np

def select_training_set(manifest_path: str, target_size: int = 100_000):
    df = pd.read_json(manifest_path, lines=True)

    # 1. garder les langues cibles
    df = df[df["language"].isin(["fr", "en", "es"])]

    # 2. poids temporel
    now = pd.Timestamp.utcnow()
    df["age_days"] = (now - pd.to_datetime(df["recording_date"])).dt.days
    df["weight"] = np.exp(-df["age_days"] / 30.0)

    # 3. tirage probabiliste pondéré
    chosen = df.sample(
        n=target_size,
        replace=False,
        weights=df["weight"],
        random_state=42,
    )
    return chosen
```

### Étape 5.2.2 Fine