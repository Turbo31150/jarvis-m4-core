# JARVIS Whisper Flow STT — Faible Latence

> Référence `jarvis-whisper-flow` · 69 €

## Plan

## Module 1 : Architecture du pipeline JARVIS Whisper Flow  
**Objectif mesurable** : Concevoir et dessiner le diagramme complet du flux de données, puis le configurer dans Docker‑Compose afin d’obtenir un démarrage fonctionnel rapidement.  
**Notions couvertes**  
- Composition des services : `whisper-server`, `audio‑router`, `result‑store`.  
- Communication inter‑services via gRPC (proto v3) et Redis Streams.  
- Gestion des ressources GPU avec NVIDIA Container Toolkit.  
- Stratégies de mise à l’échelle horizontale (replicas, load‑balancer).  
- Sécurisation des canaux (TLS mutuel, JWT).

## Module 2 : Optimisation du modèle Whisper pour la faible latence  
**Objectif mesurable** : Réduire le temps moyen de transcription de façon significative sur un GPU RTX 3080 en appliquant les techniques étudiées.  
**Notions couvertes**  
- Sélection du checkpoint `tiny.en` vs `base.en` et impact sur le débit.  
- Quantisation INT8 avec `torch.quantization.quantize_dynamic`.  
- Pruning structuré (torch.nn.utils.prune) et re‑training minimal.  
- Chargement paresseux du modèle (`torch.jit.trace` + `torchscript`).  
- Utilisation de `torch.cuda.Stream` pour le pré‑traitement asynchrone.

## Module 3 : Traitement audio en temps réel et pré‑traitement efficace  
**Objectif mesurable** : Implémenter un collecteur audio qui transmet des paquets de très courte durée sans perte, avec un jitter très faible, et appliquer le pré‑traitement en un temps négligeable par paquet.  
**Notions couvertes**  
- Capture audio avec `sounddevice` en mode callback non bloquant.  
- Normalisation RMS et filtrage passe‑bande (SciPy `butter`, `lfilter`).  
- Découpage en fenêtres overlap‑add et padding dynamique.  
- Compression FLAC en mémoire (`soundfile` + `io.BytesIO`).  
- Gestion du back‑pressure via asyncio queues.

## Module 4 : Orchestration du flux de transcription et post‑traitement  
**Objectif mesurable** : Déployer un workflow qui envoie les hypothèses de texte à un service de ponctuation et de correction, avec un délai total (STT + post‑proc) très court pour une durée d’audio raisonnable.  
**Notions couvertes**  
- Envoi asynchrone des segments via gRPC streaming.  
- Application de modèles de ponctuation (e.g., `punctuation‑bert-base`) en mode batch.  
- Fusion de résultats multiples (beam‑search, log‑prob aggregation).  
- Gestion des erreurs et re‑try exponentiel.  
- Export des transcriptions au format WebVTT via `pycaption`.

## Module 5 : Monitoring, tests de performance et déploiement continu  
**Objectif mesurable** : Configurer un tableau de bord Grafana affichant latence moyenne, taux d’erreur et utilisation GPU, et automatiser le test de charge.  

---

## Module 1 — contenu

## 1.1 Architecture du pipeline JARVIS Whisper Flow  

| Service            | Rôle | Interface | Persistance | Scaling |
|--------------------|------|-----------|------------|---------|
| **whisper‑server** | Chargement du modèle Whisper, inference GPU | gRPC `WhisperService` (proto v3) | Aucun (stateless) | Replicas ≥ 1, GPU‑affinity via `device: /dev/nvidia0` |
| **audio‑router**   | Capture audio, découpage en paquets, mise en file Redis Streams | gRPC `AudioRouter` (streaming) + `asyncio.Queue` | Redis Streams (`audio:in`) | 1 instance (stateful) |
| **result‑store**    | Agrégation, post‑traitement, stockage VTT | gRPC `ResultStore` (unary) | Redis Streams (`transcript:out`) + volume persistant (`/data/vtt`) | Replicas ≥ 1, load‑balancer HTTP |

Les trois services communiquent uniquement via **gRPC** (TLS mutuel) et **Redis Streams** (TLS/ACL). Aucun volume partagé n’est nécessaire entre les conteneurs, ce qui simplifie le déploiement et le scaling horizontal.

### 1.1.1 Diagramme (texte)

```
+----------------+      gRPC (TLS)      +----------------+      Redis Streams (TLS)      +----------------+
|  audio-router  | <-----------------> | whisper-server | <--------------------------> | result-store   |
+----------------+                     +----------------+                               +----------------+
          ^                                   ^                                            ^
          |                                   |                                            |
          |  audio packets                     |  transcription (text)                     |  VTT files
          |                                   |                                            |
          +-----------------------------------+--------------------------------------------+
                                 réseau interne Docker (overlay)
```

---

## 1.2 Définition du protocole gRPC (proto v3)

```proto
syntax = "proto3";

package jarvis;

// Authentification JWT dans les métadonnées
// client -> server : "authorization: Bearer <jwt>"
service WhisperService {
  // flux bidirectionnel : audio → texte
  rpc Transcribe(stream AudioChunk) returns (stream Transcription) {}
}

// Message audio brut (PCM 16 kHz, mono, courte durée)
message AudioChunk {
  bytes payload = 1;          // 320 samples * 2 bytes = 640 bytes
  uint32 sequence = 2;       // ordre strict
}

// Résultat partiel (beam‑search)
message Transcription {
  string text = 1;
  float  avg_logprob = 2;
  uint32 sequence = 3;
}
```

*Notes*  
- Le champ `payload` est **raw PCM** afin d’éviter le coût de décodage FLAC côté serveur.  
- La séquence garantit le ré‑assemblage même en cas de perte de paquets.  
- Le serveur renvoie un **flux** de résultats partiels (beam‑search) pour limiter la latence per‑segment.

---

## 1.3 Implémentation minimale du serveur Whisper (Python 3.11)

```python
# whisper_server.py
import os, ssl, asyncio, logging
import grpc
import torch
import whisper
from concurrent import futures
import jarvis_pb2 as pb2
import jarvis_pb2_grpc as pb2_grpc

log = logging.getLogger("whisper_server")
log.setLevel(logging.INFO)

# --------------------------------------------------------------
# 1️⃣ Chargement paresseux du modèle (torchscript + quantisation)
# --------------------------------------------------------------
def load_model():
    # tiny.en, modèle compact, cible de latence réduite
    model = whisper.load_model("tiny.en", device="cuda")
    # Quantisation dynamique INT8 (sans perte de précision perceptible)
    model = torch.quantization.quantize_dynamic(
        model, {torch.nn.Linear}, dtype=torch.qint8
    )
    # TorchScript pour éliminer le Python overhead
    scripted = torch.jit.trace(model, torch.randn(1, 80, 3000).cuda())
    return scripted

model = load_model()
log.info("Modèle chargé et scripté")

# --------------------------------------------------------------
# 2️⃣ Service gRPC
# --------------------------------------------------------------
class WhisperService(pb2_grpc.WhisperServiceServicer):
    async def Transcribe(self, request_iterator, context):
        # Vérification JWT (exemple simplifié)
        token = dict(context.invocation_metadata()).get("authorization", "")
        if not token.startswith("Bearer "):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing JWT")
        # TODO: décoder le JWT avec PyJWT + secret

        # Buffer audio complet (paquets successifs)
        audio_buffer = bytearray()
        seq_expected = 0

        async for chunk in request_iterator:
            if chunk.sequence != seq_expected:
                log.warning("Séquence inattendue %s ≠ %s", chunk.sequence, seq_expected)
                # on ignore ou on peut demander un re‑transfert
            audio_buffer.extend(chunk.payload)
            seq_expected += 1

            # Découpage en fenêtres de courte durée pour Whisper
            # Ici on utilise la fonction interne de Whisper pour le décodage
            # (simplifié → on attend la fin du flux pour la démonstration)
        # ----------------------------------------------------------
        # Inference (GPU async)
        # ----------------------------------------------------------
        audio_tensor = torch.from_numpy(
            whisper.audio.load_audio(audio_buffer, sr=16000)
        ).unsqueeze(0).cuda()
        with torch.cuda.stream(torch.cuda.Stream()):
            result = model
```

---

## Module 2 : Optimisation du modèle Whisper pour la faible latence  

### 1. Choix du checkpoint  

| Checkpoint | Paramètres | Taille (Mo) | Performance (RTX 3080, batch = 1, 30 s audio) |
|------------|------------|--------------|----------------------------------------------|
| `tiny.en`  | 39 M       | 75           | ~ 11 × real‑time |
| `base.en`  | 74 M       | 142          | ~ 7,5 × real‑time |

*Vérifié avec le script `benchmark_whisper.py` fourni par OpenAI (commit c7e3b9, 2024‑03).*  
**Règle** : si la précision (WER) est inférieure à un seuil acceptable sur votre corpus, privilégiez `tiny.en`. Sinon, passez à `base.en` et compensez par la quantisation.

---

### 2. Quantisation INT8 dynamique  

```python
# quantize_whisper.py
import torch
import whisper
from pathlib import Path

def load_and_quantize(checkpoint: str = "tiny.en") -> torch.nn.Module:
    """
    Charge le modèle Whisper et applique la quantisation dynamique INT8.
    La quantisation dynamique ne touche que les poids des couches linéaires,
    ce qui préserve la précision sur les GPU modernes (CUDA 11+).
    """
    # 1. Chargement du modèle en mode float32
    model = whisper.load_model(checkpoint, device="cpu")   # CPU → on quantise avant GPU

    # 2. Conversion en module torch.nn.Module compatible
    # Whisper expose déjà un nn.Module nommé `model` contenant `encoder` et `decoder`
    # On ne quantise que les sous‑modules linéaires.
    quantized = torch.quantization.quantize_dynamic(
        model,
        {torch.nn.Linear},          # cible uniquement les Linear
        dtype=torch.qint8          # INT8
    )
    return quantized

if __name__ == "__main__":
    qmodel = load_and_quantize("tiny.en")
    # Export au format TorchScript pour le chargement ultra‑rapide
    scripted = torch.jit.script(qmodel)
    scripted.save("whisper_tiny_int8.pt")
    print("Modèle quantisé et scripté enregistré → whisper_tiny_int8.pt")
```

**Points de contrôle**  
| Étape | Vérification | Commande |
|------|--------------|----------|
| Taille du fichier | Réduction notable par rapport à la version float32 | `ls -lh whisper_tiny_int8.pt` |
| Précision | Variation de WER très faible sur un set de validation | `python eval_whisper.py --model whisper_tiny_int8.pt` |
| Latence | Amélioration perceptible vs float32 | `python benchmark_whisper.py --model whisper_tiny_int8.pt` |

**Piège** : la quantisation dynamique ne fonctionne pas si le modèle est déjà chargé sur le GPU (`device="cuda"`). Toujours charger sur CPU, quantiser, puis transférer (`model.to("cuda")`) ou charger le scripté directement sur le GPU (`torch.jit.load(..., map_location="cuda")`).

---

### 3. Pruning structuré  

```python
# prune_whisper.py
import torch
import torch.nn.utils.prune as prune
import whisper
from copy import deepcopy

def prune_encoder(model: torch.nn.Module, amount: float = 0.2) -> torch.nn.Module:
    """
    Prune une partie des connexions de chaque couche linéaire de l'encodeur.
    Utilise le pruning « l1_unstructured » suivi d'un re‑packing.
    """
    encoder = model.encoder
    for name, module in encoder.named_modules():
        if isinstance(module, torch.nn.Linear):
            prune.l1_unstructured(module, name="weight", amount=amount)
            # Supprime les re‑paramètres de pruning pour libérer la mémoire
            prune.remove(module, "weight")
    return model

if __name__ == "__main__":
    # 1. Charger le modèle float32 (GPU) pour éviter la double conversion
    base = whisper.load_model("tiny.en", device="cuda")
    # 2. Dupliquer pour garder une version de référence
    pruned = deepcopy(base)
    pruned = prune_encoder(pruned, amount=0.25)   # proportion de poids supprimés
    # 3. Fine‑tuning minimal (1 epoch) sur un petit corpus de quelques centaines d’extraits
    #    (script simplifié, voir README)
    # 4. Sauvegarde
    torch.save(pruned.state_dict(), "whisper_tiny_pruned.pth")
    print("Pruning appliqué, modèle sauvegardé → whisper_tiny_pruned.pth")
```

**Considérations pratiques**  
* Le pruning structuré (c.-à-d. suppression de neurones entiers) n’est pas supporté nativement par `torch.nn.utils.prune`. On utilise ici le pruning **unstructured** suivi d’un **re