# Phanesis — Transcription Multilingue

> Référence `lumen-multilang` · 59 €

## Plan

## Module 1 : Architecture et principes de la transcription multilingue  
**Objectif mesurable** : L’apprenant implémente, à partir de zéro, un pipeline d’inférence capable de transcrire du texte en français, anglais et espagnol avec un taux d’erreur de mots (WER) inférieur à un seuil raisonnable sur le jeu de validation Common Voice.  

- Modèles de base : Whisper tiny, wav2vec 2.0, Conformer.  
- Encodage acoustique vs décodage linguistique.  
- Gestion du vocabulaire multilingue (Byte‑Pair Encoding, SentencePiece).  
- Alignement temporel des sorties (CTC vs seq2seq).  
- Métriques d’évaluation : WER, CER, BLEU pour la traduction simultanée.

## Module 2 : Pré‑traitement et enrichissement des données audio  
**Objectif mesurable** : L’apprenant prépare un corpus multilingue conséquent d’audio, applique des augmentations contrôlées et génère des alignements phonétiques avec une précision élevée sur un sous‑ensemble annoté.  

- Normalisation du signal (16 kHz, 16 bits, RMS).  
- Augmentations : bruit de fond (MUSAN), vitesse, pitch shifting, SpecAugment.  
- Extraction de caractéristiques : MFCC, log‑Mel spectrogram, HuBERT embeddings.  
- Alignement forcé avec Montreal Forced Aligner.  
- Construction de manifestes JSON compatibles avec ESPnet/NeMo.

## Module 3 : Fine‑tuning d’un modèle pré‑entraîné sur un domaine ciblé  
**Objectif mesurable** : L’apprenant réalise un fine‑tuning sur un jeu de données sectoriel (ex. télé‑consultation médicale) et améliore le WER de façon notable par rapport au modèle de base.  

- Stratégies de gel de couches et d’apprentissage différentiel.  
- Optimiseurs et planificateurs de taux d’apprentissage (AdamW, cosine annealing).  
- Gestion du déséquilibre linguistique (sampling, loss weighting).  
- Validation croisée temporelle et early stopping.  
- Utilisation de PyTorch Lightning pour le suivi des expériences.

## Module 4 : Déploiement efficace et scalabilité  
**Objectif mesurable** : L’apprenant déploie le modèle sur un serveur Docker avec un temps de latence moyen raisonnable et une consommation énergétique faible.  

- Export ONNX et quantisation dynamique/int8.  
- Serveur d’inférence Triton vs FastAPI + TorchServe.  
- Batching dynamique et gestion de la mémoire GPU.  
- Monitoring (Prometheus, Grafana) et métriques de SLA.  
- Sécurisation des flux audio (TLS, token JWT).

## Module 5 : Évaluation continue, adaptation et conformité juridique  
**Objectif mesurable** : L’apprenant met en place un pipeline d’évaluation automatisé qui détecte les dérives de performance significatives et déclenche un ré‑entraînement mensuel, tout en assurant la conformité RGPD.  

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
| **Whisper‑tiny** | 39 M paramètres | Transformer encoder‑decoder, pré‑entraînement multitâche (ASR + traduction) | pratiquement toutes les langues du Common Voice | MIT |
| **wav2vec 2.0‑base** | 95 M | CNN + Transformer, pré‑entraînement self‑supervised (contrastive) | plusieurs dizaines de langues (pré‑entraînement multilingual) | Apache‑2.0 |
| **Conformer‑small** | 30 M | Convolution‑augmented Transformer (CNN + MHSA) | plusieurs langues dont anglais, français, espagnol | Apache‑2.0 |

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

1. **Byte‑Pair Encoding (BPE)** – découpé en sous‑mots, permet de couvrir plusieurs langues avec un vocabulaire partagé (ex. plusieurs dizaines de milliers de tokens).  
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
| **Normalisation RMS** | Appliquer un gain pour que le RMS corresponde à un niveau de référence. | ```python\nimport torch\nrms = torch.sqrt(torch.mean(wave**2))\nwave = wave * (0.1 / rms)\n``` | `torch.isclose(torch.sqrt(torch.mean(wave**2)), torch.tensor(0.1), atol=1e‑3)` |

> **Piège** : le resampling doit être effectué **avant** la normalisation RMS, sinon le gain appliqué sera faussé par la modification de la densité spectrale.

---

## 2.2 Augmentations contrôlées  

Les augmentations sont appliquées *on‑the‑fly* pendant le chargement du dataset afin de ne pas gonfler le stockage.  

| Type | Bibliothèque | Exemple (pipeline `torch.utils.data.Dataset`) |
|------|--------------|----------------------------------------------|
| Bruit de fond (MUSAN) | `torchaudio.sox_effects` + `torch` | ```python\nimport random, torch, torchaudio\nclass AugmentedDataset(torch.utils.data.Dataset):\n    def __init__(self, manifest, musan_dir, prob_noise=0.3):\n        self.manifest = manifest\n        self.musan_files = list(Path(musan_dir).rglob('*.wav'))\n        self.prob_noise = prob_noise\n    def __len__(self):\n        return len(self.manifest)\n    def __getitem__(self, idx):\n        entry = self.manifest[idx]\n        wav, sr = torchaudio.load(entry['audio_filepath'])\n        # resample / normalize déjà fait dans le manifest\n        if random.random() < self.prob_noise:\n            noise_path = random.choice(self.musan_files)\n            noise, _ = torchaudio.load(noise_path)\n            # tronquer ou répéter le bruit à la même durée\n            if noise.shape[1] < wav.shape[1]:\n                repeats = wav.shape[1] // noise.shape[1] + 1\n                noise = noise.repeat(1, repeats)[:, :wav.shape[1]]\n            else:\n                noise = noise[:, :wav.shape[1]]\n            # SNR entre 0 et 20 dB\n            snr_db = random.uniform(0, 20)\n            wav_power = wav.norm(p=2)\n            noise_power = noise.norm(p=2)\n            scale = wav_power / (10**(snr_db/20) * noise_power)\n            wav = wav + scale * noise\n        return wav.squeeze(0), entry['transcript']\n``` |
| Speed‑perturbation | `torchaudio.functional.time_stretch` (via SoX) | ```python\nif random.random() < 0.2:\n    factor = random.choice([0.9, 1.0, 1.1])\n    wav, _ = torchaudio.sox_effects.apply_effects_tensor(wav, sr, [['speed', str(factor)], ['rate', str(sr)]])\n``` |
| Pitch‑shifting | `torchaudio.sox_effect