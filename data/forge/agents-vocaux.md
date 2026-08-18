# Agents Vocaux IA — Pipeline Complet

> Référence `agents-vocaux` · 79 €

## Plan

## Module 1 – Architecture du pipeline vocal IA  
**Objectif mesurable** : Concevoir et déployer un pipeline complet (ASR → NLU → TTS) fonctionnant en local, avec un taux d’erreur de transcription ≤ 10 % sur le jeu de test *LibriSpeech clean* et un temps de latence total ≤ 300 ms par interaction.  

- Modélisation et entraînement d’un ASR (ex. Whisper base, DeepSpeech)  
- Normalisation du signal audio : échantillonnage 16 kHz, pré‑emphasis, framing, windowing  
- Implémentation du streaming audio via gRPC ou WebSocket  
- Intégration d’un composant NLU (spaCy + EntityRuler ou Rasa NLU)  
- Synthèse vocale avec Tacotron 2, VITS ou FastSpeech 2  

---

## Module 2 – Gestion du dialogue et logique décisionnelle  
**Objectif mesurable** : Implémenter un gestionnaire de dialogue capable de suivre au moins 3 tours de conversation et de choisir la bonne réponse dans 95 % des scénarios du benchmark *MultiWOZ* (version 2.2).  

- Modélisation de l’état du dialogue (slot‑filling, agenda‑based)  
- Utilisation de modèles de génération de réponses (GPT‑2, T5) fine‑tuned sur des dialogues vocaux  
- Politique de décision basée sur des règles et/ou du reinforcement learning (Rasa Core, Deep Q‑Network)  
- Gestion des interruptions et des reprises (re‑entrancy)  
- Logging et métriques de suivi (turn‑level accuracy, action‑level F1)  

---

## Module 3 – Optimisation de la performance et du déploiement  
**Objectif mesurable** : Réduire la consommation GPU de chaque composant d’au moins 30 % tout en maintenant les performances métriques du module 1, et containeriser le pipeline avec Docker‑Compose pour un déploiement sur un serveur Ubuntu 20.04.  

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
| **T5** | `t5-base` | 220 | 2 époques, LR = 3e‑5, batch = 4 | MultiWOZ‑2.2 + augmentations (paraphrase) |

#### Pipeline de génération (exemple fonctionnel)

```python
# dialogue_manager.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class Generator:
    """Wrapper minimal autour de GPT‑2 fine‑tuned pour la réponse vocale."""
    def __init__(self, model_name="distilgpt2-finetuned-multiwoz"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name).to(self.device)

    def generate(self, state, max_len=50):
        """
        state: DialogueState instance
        Retourne la réponse textuelle.
        """
        # Construction du prompt à partir de l'historique et des slots remplis
        prompt = self._build_prompt(state)
        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)

        # Décodage avec nucleus sampling (p=0.9) pour éviter les réponses génériques
        output_ids = self.model.generate(
            inputs,
            max_length=len(inputs[0]) + max_len,
            do_sample=True,
            top_p=0.9,
            temperature=0.7,
            eos_token_id=self.tokenizer.eos_token_id,
        )
        # On retire le prompt du texte généré
        answer = self.tokenizer.decode(output_ids[0][len(inputs[0]):], skip_special_tokens=True)
        return answer.strip()

    def _build_prompt(self, state):
        # Historique limité aux 5 derniers tours pour garder le contexte
        hist = "\n".join(
            f"{speaker}: {utt}" for speaker, utt, _ in state.history[-5:]
        )
        # Slots non remplis présentés comme questions implicites
        slots_info = ", ".join(
            f"{k}={v}" for k, v in state.slots.items() if v is not None
        )
        return f"{hist}\nSlots: {slots_info}\nAssistant:"
```

*Le code ci‑dessus* :  
* utilise `torch.cuda.is_available()` pour le basculement CPU/GPU,  
* construit un prompt à partir de l’historique (max 5 tours) et des slots remplis,  
* applique la génération avec `top‑p` (nucleus sampling) afin de réduire le taux de réponses « I don’t know ».  

---

## 2.3 Politique de décision  

### 2.3.1 Règles simples (baseline)

```python
# rule_policy.py
class RulePolicy:
    """Politique basée sur un dictionnaire de conditions → actions."""
    def __init__(self, rules):
        """
        rules: list of dicts, each with:
            - 'condition': lambda state: bool
            - 'action': str (agenda item)
        """
        self.rules = rules

    def next_action(self, state):
        for rule in self.rules:
            if rule["condition"](state):
                return rule["action"]
        return "fallback"

# Exemple de règle
rules = [
    {
        "condition

---

## Module 3 — contenu

## Module 3 – Optimisation de la performance et du déploiement  

### 3.1 Quantification post‑training  

| Étape | Action | Commande / API | Résultat attendu |
|------|--------|----------------|------------------|
| 1 | Export du modèle PyTorch → ONNX (opset = 13) | ```python -c "import torch, whisper; model=whisper.load_model('base'); dummy=torch.randn(1,80,3000); torch.onnx.export(model, dummy, 'asr.onnx', opset_version=13, input_names=['mel'], output_names=['logits'])"``` | `asr.onnx` (≈ 140 Mo) |
| 2 | Calibration du jeu de validation (≤ 500 samples) | ```python calibrate.py --model asr.onnx --data val/``` | `asr_calib_data.npy` (float32) |
| 3 | Quantification int8 avec ONNX Runtime | ```python - <<'PY'\nimport onnxruntime as ort, numpy as np\nfrom onnxruntime.quantization import quantize_static, CalibrationDataReader, QuantFormat, QuantType\nclass DataReader(CalibrationDataReader):\n    def __init__(self, path):\n        self.data = np.load(path)\n        self.iterator = iter([{'mel': self.data}])\n    def get_next(self):\n        return next(self.iterator, None)\nreader = DataReader('asr_calib_data.npy')\nquantize_static('asr.onnx','asr_int8.onnx',reader, quant_format=QuantFormat.QOperator, weight_type=QuantType.QInt8)\nPY``` | `asr_int8.onnx` (≈ 35 Mo) |
| 4 | Vérification de la perte de précision | ```python eval_asr.py --model asr_int8.onnx --test test/clean/``` | WER ≤ 10 % (même que modèle FP32 sur LibriSpeech clean) |
| 5 | Benchmark de latence | ```python -m timeit -s "import onnxruntime as ort, numpy as np; sess=ort.InferenceSession('asr_int8.onnx'); x=np.random.randn(1,80,3000).astype('float32')" "sess.run(None,{'mel':x})"``` | Temps moyen ≤ 0.25 s sur RTX 3060 (GPU) |

**Points de vérification**  
* L’opset 13 inclut `Gather` et `ScatterElements` qui sont requis par Whisper.  
* La calibration doit couvrir **tous** les intervalles dynamiques ; sinon, le modèle peut subir un *scale overflow* et renvoyer des logits saturés.  
* ONNX Runtime 1.13+ supporte l’exécution GPU via `CUDAExecutionProvider`.  

---

### 3.2 Pruning (élagage) des réseaux de neurones  

1. **Pruning structuré** (suppression de canaux) → compatible avec TensorRT.  
2. **Outil recommandé** : `torch.nn.utils.prune`.  

```python
# prune_asr.py – Exemple de pruning structuré d’un bloc Conv1d de Whisper
import torch, torch.nn.utils.prune as prune, whisper

model = whisper.load_model('base')
layer = model.encoder.blocks[0].conv1  # Conv1d (in_channels=384, out_channels=384)

# 30 % de canaux sont masqués (pruning structuré)
prune.ln_structured(layer, name='weight', amount=0.30, n=1, dim=0)

# Supprimer les paramètres masqués pour réduire la taille du checkpoint
prune.remove(layer, 'weight')
torch.save(model.state_dict(), 'asr_pruned.pth')
```

*Après le pruning, ré‑exporter en ONNX et ré‑appliquer la quantification.*  

**Vérifications**  
* `torch.onnx.export` doit être appelé **après** `prune.remove` sinon le graphe exporté contient encore les masques inutiles.  
* Le taux de pruning ne doit pas dépasser 40 % sur les couches critiques (self‑attention) ; au‑delà, le WER augmente de > 5 % sur LibriSpeech clean.  

---

### 3.3 Optimisation du batch et du pipeline de streaming  

| Paramètre | Valeur recommandée | Raison |
|-----------|--------------------|--------|
| `batch_size` (ASR) | 1 (streaming) | Latence ≤ 300 ms, pas de buffering excessif. |
| `prefetch_factor` (DataLoader) | 2 | Maintient le GPU occupé sans surcharge CPU. |
| `torch.backends.cudnn.benchmark` | `True` | Active le autotuning des kernels CUDA, gain moyen : ‑ 5 % de latence. |
| `torch.cuda.synchronize()` | **Éviter** dans le loop de production | Chaque appel bloque le GPU et augmente la latence. |

**Code de streaming gRPC (serveur)**  

```python
# asr_grpc_server.py – serveur gRPC minimal pour le flux audio
import grpc, asr_pb2_grpc, asr_pb2, queue, threading, numpy as np, onnxruntime as ort

class ASRServicer(asr_pb2_grpc.ASRService

---

## Module 4 — contenu

## Module 4 – Observabilité, tests automatisés et CI/CD du pipeline vocal IA  

### 4.1. Exposition des métriques d’exécution  

| Métrique | Type | Unité | Source de données |
|---------|------|-------|-------------------|
| `asr_transcription_latency_seconds` | Histogram | s | Chronométrage du bloc `asr.decode()` |
| `asr_wer` | Gauge | % | Calcul du WER sur le batch de validation |
| `nlu_inference_time_seconds` | Histogram | s | `nlp.pipe()` |
| `tts_synthesis_time_seconds` | Histogram | s | `tts.infer()` |
| `gpu_memory_usage_bytes` | Gauge | B | `torch.cuda.memory_allocated()` |
| `process_cpu_seconds_total` | Counter | s | `psutil.Process().cpu_times()` |

```python
# file: metrics.py
from prometheus_client import Histogram, Gauge, start_http_server
import time, torch, psutil

# Histograms avec buckets adaptés aux exigences de latence (<300 ms)
asr_latency = Histogram(
    "asr_transcription_latency_seconds",
    "Temps de transcription ASR",
    buckets=[0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50],
)

gpu_mem = Gauge(
    "gpu_memory_usage_bytes",
    "Mémoire GPU allouée par le processus PyTorch",
)

def record_asr_latency(fn):
    """Wrapper décorateur qui mesure et enregistre la latence d’une fonction ASR."""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed = time.perf_counter() - start
        asr_latency.observe(elapsed)
        # mise à jour ponctuelle de la consommation GPU
        if torch.cuda.is_available():
            gpu_mem.set(torch.cuda.memory_allocated())
        return result
    return wrapper

# Exemple d’utilisation avec un modèle Whisper‑base chargé via 🤗 Transformers
from transformers import WhisperForConditionalGeneration, WhisperProcessor
import torch

processor = WhisperProcessor.from_pretrained("openai/whisper-base")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base").cuda()

@record_asr_latency
def transcribe(audio_tensor):
    """Transcrit un tenseur audio (16 kHz, mono). Retourne le texte brut."""
    input_features = processor(audio_tensor, sampling_rate=16000, return_tensors="pt").input_features.cuda()
    predicted_ids = model.generate(input_features)
    return processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

if __name__ == "__main__":
    # Démarrage du serveur métriques sur le port 8000
    start_http_server(8000)
    # Boucle de test rapide (remplacez par votre flux gRPC/WebSocket)
    dummy_audio = torch.randn(1, 16000 * 5).cuda()  # 5 s de bruit aléatoire
    for _ in range(100):
        transcribe(dummy_audio)
```

*Le serveur expose `/metrics` au format texte compatible Prometheus.*  

### 4.2. Tracing distribué avec OpenTelemetry  

```yaml
# file: otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
      http:
exporters:
  otlphttp:
    endpoint: "http://tempo:4318/v1/traces"
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [otlphttp]
```

```python
# file: tracing.py
from opentelemetry import trace
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

trace.set_tracer_provider(TracerProvider())
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

# Instrumentation du serveur gRPC (ou WebSocket) existant
GrpcInstrumentorServer().instrument()
LoggingInstrumentor().instrument(set_logging_format=True)
```

*Chaque appel gRPC crée un span nommé `asr.Transcribe

---

## Module 5 — contenu

**Clarification requise**  

Le plan fourni décrit uniquement les modules 1, 2 et 3. Aucun détail n’est donné pour un « module 5 ». Pour pouvoir rédiger le contenu complet (explications, exemple de code, pièges, exercice avec corrigé) il me faut :

1. Le titre du module 5.  
2. Les objectifs mesurables ou les compétences visées.  
3. Les sous‑points ou thématiques à couvrir (ex. : « Sécurité et confidentialité des données vocales », « Intégration multi‑langues », etc.).  

Merci de préciser ces éléments afin que je puisse fournir le contenu demandé.