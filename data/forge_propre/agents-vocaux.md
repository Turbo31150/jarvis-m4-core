# Agents Vocaux IA — Pipeline Complet

> Référence `agents-vocaux` · 79 €

## Plan

## Module 1 – Architecture du pipeline vocal IA  
**Objectif mesurable** : Concevoir et déployer un pipeline complet (ASR → NLU → TTS) fonctionnant en local, avec un taux d’erreur de transcription faible sur le jeu de test *LibriSpeech clean* et un temps de latence total réduit par interaction.  

- Modélisation et entraînement d’un ASR (ex. Whisper base, DeepSpeech)  
- Normalisation du signal audio : échantillonnage 16 kHz, pré‑emphasis, framing, windowing  
- Implémentation du streaming audio via gRPC ou WebSocket  
- Intégration d’un composant NLU (spaCy + EntityRuler ou Rasa NLU)  
- Synthèse vocale avec Tacotron 2, VITS ou FastSpeech 2  

---

## Module 2 – Gestion du dialogue et logique décisionnelle  
**Objectif mesurable** : Implémenter un gestionnaire de dialogue capable de suivre au moins trois tours de conversation et de choisir la bonne réponse dans la plupart des scénarios du benchmark *MultiWOZ* (version 2.2).  

- Modélisation de l’état du dialogue (slot‑filling, agenda‑based)  
- Utilisation de modèles de génération de réponses (GPT‑2, T5) fine‑tuned sur des dialogues vocaux  
- Politique de décision basée sur des règles et/ou du reinforcement learning (Rasa Core, Deep Q‑Network)  
- Gestion des interruptions et des reprises (re‑entrancy)  
- Logging et métriques de suivi (turn‑level accuracy, action‑level F1)  

---

## Module 3 – Optimisation de la performance et du déploiement  
**Objectif mesurable** : Réduire la consommation GPU de chaque composant tout en maintenant les performances métriques du module 1, et containeriser le pipeline avec Docker‑Compose pour un déploiement sur un serveur Ubuntu 20.04.  

- Quantification post‑training (int8, float16) avec ONNX Runtime ou TensorRT  
- Pruning des réseaux de neur

---

## Module 1 — contenu

## 1.1 Pré‑traitement du signal audio  

| Étape | Description | Implémentation (Python + NumPy + SciPy) |
|------|-------------|----------------------------------------|
| **Resampling** | Convertir tout le flux en 16 kHz, mono, 16‑bit PCM. | ```python\nimport librosa, soundfile as sf\n\ndef resample_wav(path, target_sr=16000):\n    y, sr = sf.read(path)\n    if sr != target_sr:\n        y = librosa.resample(y.astype(float), orig_sr=sr, target_sr=target_sr)\n    if y.ndim > 1:            # for stereo → mono\n        y = y.mean(axis=1)\n    return y.astype('float32')\n``` |
| **Pre‑emphasis** | Accentue les hautes fréquences (coeff = 0.97) pour améliorer la convergence du modèle. | ```python\ndef pre_emphasis(sig, coeff=0.97):\n    return np.append(sig[0], sig[1:] - coeff * sig[:-1])\n``` |
| **Framing & Windowing** | Découpage en trames de 25 ms (400 samples) avec un pas de 10 ms (160 samples). Fenêtre de Hann. | ```python\ndef frame_signal(sig, frame_len=400, frame_step=160):\n    shape = ((len(sig) - frame_len) // frame_step + 1, frame_len)\n    strides = (sig.strides[0] * frame_step, sig.strides[0])\n    frames = np.lib.stride_tricks.as_strided(sig, shape=shape, strides=strides)\n    return frames * np.hanning(frame_len)\n``` |

> **Vérifiable** : `librosa.resample` reproduit exactement la même courbe de fréquence que le script de référence de l’OpenSLR LibriSpeech preprocessing (voir `scripts/prepare_data.sh` du dépôt `mozilla/DeepSpeech`).

---

## 1.2 Modèle ASR (Whisper base) – entraînement & inference locale  

### 1.2.1 Installation des dépendances  

```bash
pip install torch==2.2.0 torchaudio==2.2.0 transformers==4.40.0 librosa soundfile
```

> **Note** : `torch` doit être compilé avec le support CUDA 12.x si un GPU RTX 3080 ou supérieur est disponible; sinon, `--extra-index-url https://download.pytorch.org/whl/cpu` pour CPU‑only.

### 1.2.2 Chargement du modèle  

```python
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
processor = WhisperProcessor.from_pretrained("openai/whisper-base")
asr_model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base").to(device)
asr_model.eval()
```

### 1.2.3 Inference en streaming (gRPC)  

#### Proto (`asr.proto`)

```proto
syntax = "proto3";

service ASRService {
  rpc StreamTranscribe (stream AudioChunk) returns (stream Transcription);
}

message AudioChunk {
  bytes data = 1;               // PCM 16‑bit, 16 kHz, mono
  bool   last = 2;              // true → fin du flux
}

message Transcription {
  string text = 1;
  bool   final = 2;            // true → résultat final, sinon partiel
}
```

#### Serveur (Python)

```python
import grpc
import asr_pb2, asr_pb2_grpc
import numpy as np

class ASRServicer(asr_pb2_grpc.ASRServiceServicer):
    def __init__(self, model, processor, device):
        self.model = model
        self.processor = processor
        self.device = device
        self.buffer = bytearray()

    def StreamTranscribe(self, request_iterator, context):
        for chunk in request_iterator:
            self.buffer.extend(chunk.data)
            if len(self.buffer) < 32000:          # 2 s de données (16 kHz×2 s×2 bytes)
                continue

            # décodage PCM → float32 tensor
            audio = np.frombuffer(self.buffer, dtype=np.int16).astype(np.float32) / 32768.0
            self.buffer.clear()

            # pré‑emphasis & framing ne sont pas nécessaires : Whisper attend le signal brut.
            inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt").to(self.device)

            # génération incrémentale (no‑beam, max_new_tokens=1) pour obtenir un texte partiel
            with torch.no_grad():
                logits = self.model(**inputs).logits
                pred_ids = torch.argmax(logits, dim=-1)
                text = self.processor.batch_decode(pred_ids, skip_special_tokens=True)[0]

            yield asr_pb2.Transcription(text=text, final=False)

        # fin du flux → décodage final
        if self.buffer:
            audio = np.frombuffer(self.buffer, dtype=np.int16).astype(np.float32) / 32768.0
            inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt").to(self.device)
            with torch.no_grad():
                generated_ids = self.model.generate(**inputs, max_new_tokens=100)
                final_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            yield asr_pb2.Transcription(text=final_text, final=True)

def serve():
    server = grpc.server(grpc.thread_pool_executor(max_workers=4))

---

## Module 2 — contenu

## 2.1 Modélisation de l’état du dialogue  

| Élément | Description | Implémentation concrète |
|--------|-------------|------------------------|
| **Slot‑filling** | Table de valeurs (slot) remplie au fil des tours. Chaque slot possède un type (`categorical`, `text`, `float`) et une valeur `None` tant qu’elle n’est pas renseignée. | ```python\nclass DialogueState:\n    def __init__(self, slots):\n        self.slots = {name: None for name in slots}\n    def update(self, name, value):\n        if name in self.slots:\n            self.slots[name] = value\n    def is_filled(self):\n        return all(v is not None for v in self.slots.values())\n``` |
| **Agenda‑based** | File d’actions à exécuter (ex. `ask_location`, `confirm_booking`). L’agenda est manipulé par la politique de décision. | ```python\nfrom collections import deque\nclass Agenda:\n    def __init__(self):\n        self.q = deque()\n    def push(self, act):\n        self.q.append(act)\n    def pop(self):\n        return self.q.popleft() if self.q else None\n``` |
| **Historique** | Liste de tuples `(speaker, utterance, timestamp)`. Utilisée par les modèles de génération et les métriques. | ```python\nself.history.append(('user', user_utt, time.time()))\n``` |

### Points de vérification  
* Chaque tour doit mettre à jour **exactement** les slots mentionnés dans l’UTT.  
* L’agenda doit être vidé à la fin du dialogue, sinon les réponses « fantômes » apparaissent.  

---

## 2.2 Modèles de génération de réponses  

| Modèle | Version | Taille (M) | Fine‑tuning recommandé | Données d’entraînement |
|-------|---------|-----------|-----------------------|-----------------------|
| **GPT‑2** | `distilgpt2` | 82 | 3 époques, LR = 5e‑5, batch = 8 | MultiWOZ‑2.2 (texte) + TTS‑aligned transcripts |
| **T5** | `t5-base` | 220 | 2 époques, LR = 3e‑5, batch = 4 |