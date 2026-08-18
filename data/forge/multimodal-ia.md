# IA Multimodale — Image, Audio, Vidéo

> Référence `multimodal-ia` · 79 €

## Plan

## Module 1 – Architectures fondamentales du multimodal : image, audio, vidéo  
**Objectif** : Concevoir et coder une architecture de base capable de traiter simultanément des entrées image, audio et vidéo, et de produire une sortie classifiée avec une précision ≥ 75 % sur un jeu de données de référence (ex. AVMNIST).  

**Notions couvertes**  
1. CNN 2D (ResNet‑50) pour l’extraction de caractéristiques d’images – implémentation PyTorch et poids pré‑entraînés ImageNet.  
2. Réseaux spectrogrammes 1D/2D (Mel‑spectrogram, MFCC) et CNN 1D (TCN) pour l’audio – génération avec `librosa`, normalisation et encodage.  
3. 3D‑CNN (I3D) et flux optique (Farneback) pour la vidéo – pré‑traitement avec `opencv`, agrégation temporelle.  
4. Fusion « early » (concaténation de tenseurs) vs « late » (moyenne pondérée des logits) – implémentation d’un module `MultimodalFusion`.  
5. Fonction de perte multi‑tâche (cross‑entropy combinée) et optimisation AdamW (lr = 1e‑4).  

---

## Module 2 – Pré‑traitement et augmentation des données multimodales  
**Objectif** : Mettre en place un pipeline d’augmentation qui augmente le nombre d’échantillons effectifs d’au moins 30 % sans dégrader la performance du modèle de base.  

**Notions couvertes**  
1. Augmentations image (random crop, horizontal flip, color jitter) via `torchvision.transforms`.  
2. Augmentations audio (time‑stretch, pitch‑shift, ajout de bruit blanc) via `torchaudio.transforms`.  
3. Aug

---

## Module 1 — contenu

## 1.1 Extraction de caractéristiques d’image – ResNet‑50 2D  

| Étape | Action | Code clé |
|------|--------|----------|
| 1. Charger le modèle pré‑entraîné | `torchvision.models.resnet50(pretrained=True)` | `resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)` |
| 2. Supprimer la couche de classification | `nn.Sequential(*list(resnet.children())[:-1])` | `img_encoder = nn.Sequential(*list(resnet.children())[:-1])` |
| 3. Geler les poids (optionnel) | `param.requires_grad = False` | `for p in img_encoder.parameters(): p.requires_grad = False` |
| 4. Normaliser les entrées | `transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)` | `normalize = transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])` |

**Remarque** : la sortie de `img_encoder` est de forme `(B, 2048, 1, 1)`. On a besoin de la convertir en vecteur plat : `x = x.view(x.size(0), -1)` → `(B, 2048)`.

---

## 1.2 Extraction de caractéristiques audio – spectrogrammes + TCN  

### 1.2.1 Génération du Mel‑spectrogramme  

```python
import librosa, torch, torchaudio
def mel_spec(wav_path, sr=16000, n_mels=64, hop_length=160, n_fft=400):
    y, _ = librosa.load(wav_path, sr=sr)                # resampling
    mel = librosa.feature.melspectrogram(
        y, sr=sr, n_fft=n_fft, hop_length=hop_length,
        n_mels=n_mels, power=1.0)                        # power=1 → amplitude
    mel_db = librosa.power_to_db(mel, ref=np.max)      # dB scaling
    mel_db = (mel_db - mel_db.mean()) / mel_db.std()   # normalisation Z‑score
    return torch.tensor(mel_db, dtype=torch.float32)  # (n_mels, T)
```

*Le spectrogramme est traité comme une séquence 2‑D (canaux = 1, hauteur = n_mels, longueur = T).*

### 1.2.2 Temporal Convolutional Network (TCN)  

```python
class Chomp1d(nn.Module):
    def __init__(self, chomp_size):
        super().__init__()
        self.chomp_size = chomp_size
    def forward(self, x):
        return x[:, :, :-self.chomp_size]

class TemporalBlock(nn.Module):
    def __init__(self, n_inputs, n_outputs, kernel_size, stride, dilation, padding, dropout=0.2):
        super().__init__()
        self.conv1 = nn.Conv1d(n_inputs, n_outputs, kernel_size,
                               stride=stride, padding=padding, dilation=dilation)
        self.chomp1 = Chomp1d(padding)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(dropout)

        self.conv2 = nn.Conv1d(n_outputs, n_outputs, kernel_size,
                               stride=stride, padding=padding, dilation=dilation)
        self.chomp2 = Chomp1d(padding)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(dropout)

        self.net = nn.Sequential(self.conv1, self.chomp1, self.relu1, self.dropout1,
                                 self.conv2, self.chomp2, self.relu2, self.dropout2)
        self.downsample = nn.Conv1d(n_inputs, n_outputs, 1) if n_inputs != n_outputs else None
        self.relu = nn.ReLU()
        self.init_weights()

    def init_weights(self):
        nn.init.kaiming_normal_(self.conv1.weight)
        nn.init.kaiming_normal_(self.conv2.weight)
        if self.downsample is not None:
            nn.init.kaiming_normal_(self.downsample.weight)

    def forward(self, x):
        out = self.net(x)
        res = x if self.downsample is None else self.downsample(x)
        return self.relu(out + res)

class TCN(nn.Module):
    def __init__(self, input_size, num_channels, kernel_size=3, dropout=0.2):
        super().__init__()
        layers = []
        num_levels = len(num_channels)
        for i in range(num_levels):
            dilation = 2 ** i
            in_ch = input_size if i == 0 else num_channels[i-1]
            out_ch = num_channels[i]
            padding = (kernel_size - 1) * dilation
            layers += [TemporalBlock(in_ch, out_ch, kernel_size, stride=1,
                                     dilation=dilation, padding=padding, dropout=dropout)]
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        # x : (B, C, T)  – C = n_mels
        return self.network(x)[:, :, -1]          # garder le dernier pas temporel
```

*Utilisation* :

```python
mel = mel_spec('sample.wav')                # (64, T)
mel = mel.unsqueeze(0)                        # (1, 64, T) → canal = 64
audio_encoder = TCN(input_size=64, num_channels=[128, 256, 512])
audio_feat = audio_encoder(mel)              # (1, 512)
```

---

## 1.3 Extraction de caractéristiques vidéo – I3D (3D

---

## Module 2 — contenu

## 2.1 Principe général de l’augmentation multimodale  

| Modalité | Pourquoi augmenter ? | Risque principal |
|----------|----------------------|------------------|
| Image    | Diversifier les variations d’échelle, d’orientation, de couleur – le modèle ne doit pas dépendre d’un cadrage fixe. | Décalage entre image et ses métadonnées (ex. : boîte englobante non mise à jour). |
| Audio    | Simuler différentes conditions d’enregistrement (vitesse, tonalité, bruit). | Modification du timing qui désynchronise audio/vidéo. |
| Vidéo    | Varier la dynamique temporelle (frame‑rate, direction) et l’apparence (couleur, flou). | Incohérence entre flux vidéo et spectrogramme audio si les deux ne sont pas transformés de façon identique. |

L’objectif est d’appliquer **les mêmes transformations temporelles** (ex. : découpage temporel, retournement) à la fois aux séquences vidéo et aux signaux audio, afin de garder la correspondance frame‑à‑frame.

---

## 2.2 Pipeline d’augmentation d’images  

```python
import torch
import torchvision.transforms as T

# 1️⃣ Transformations de base (appliquées à chaque image)
image_transform = T.Compose([
    T.RandomResizedCrop(size=224, scale=(0.8, 1.0)),   # recadrage aléatoire + redimensionnement
    T.RandomHorizontalFlip(p=0.5),                  # symétrie horizontale
    T.ColorJitter(brightness=0.2, contrast=0.2,
                  saturation=0.2, hue=0.1),        # variations de couleur
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],          # valeurs ImageNet
                std =[0.229, 0.224, 0.225])
])
```

* **RandomResizedCrop** garantit que chaque image conserve la même taille d’entrée (224 × 224) attendue par ResNet‑50.  
* **ColorJitter** doit rester dans des intervalles modestes ; des valeurs trop extrêmes créent des images hors distribution et dégradent la précision.  

---

## 2.3 Pipeline d’augmentation audio  

```python
import torchaudio
import random

class AudioAugment:
    """Applique une suite d'augmentations audio compatibles avec la synchronisation vidéo."""
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.time_stretch = torchaudio.transforms.TimeStretch(
            hop_length=256, n_freq=201, fixed_rate=None)   # rate choisi aléatoirement
        self.pitch_shift = torchaudio.transforms.PitchShift(
            sample_rate=self.sample_rate, n_steps=2)        # +‑2 demi‑tons max
        self.add_noise = lambda x: x + 0.005*torch.randn_like(x)

    def __call__(self, waveform):
        # 1️⃣ Time‑stretch (0.8‑1.25x) – conserve la longueur en ré‑échantillonnant
        rate = random.uniform(0.8, 1.25)
        stretched = torchaudio.functional.phase_vocoder(
            waveform, rate=rate, phase_advance=torch.linspace(0, torch.pi * rate, waveform.shape[0]))
        # 2️⃣ Pitch‑shift (±2 demi‑tons)
        n_steps = random.choice([-2, -1, 0, 1, 2])
        shifted = torchaudio.functional.pitch_shift(
            stretched, self.sample_rate, n_steps=n_steps)
        # 3️⃣ Ajout de bruit blanc
        noisy = self.add_noise(shifted)
        return noisy
```

* **Phase‑vocoder** (dans `torchaudio.functional.phase_vocoder`) permet de changer la vitesse sans altérer la hauteur.  
* Après le time‑stretch, la durée du signal change ; on **re‑échantillonne** à la longueur originale (`torch.nn.functional.interpolate`) ou on **pad/truncate** pour garder la synchronisation avec la vidéo.  
* Le bruit blanc doit rester inférieur à ‑30 dBFS pour ne pas masquer le contenu sémantique.

---

## 2.4 Pipeline d’augmentation vidéo  

```python
import cv2
import numpy as np
import random
import torch

def video_augment(frames: torch.Tensor, fps: int = 30):
    """
    frames : Tensor (T, C, H, W)  – T = nombre de frames, C=3, H=W=224
    Retourne les frames augmentées et le nouveau taux de fps (si décimation).
    """
    T, C, H, W = frames.shape

    # 1️⃣ Découpage temporel aléatoire (keep 70‑100% des frames)
    keep_ratio = random.uniform(0.7, 1.0)
    keep_len   = max(1, int(T * keep_ratio))
    start_idx  = random.randint(0, T - keep_len)
    frames = frames[start_idx:start_idx + keep_len]

    # 2️⃣ Retour horizontal (identique à l'image)
    if random.random() < 0.5:
        frames = torch.flip(frames, dims=[3])   # flip width

    # 3️⃣ Color jitter (similaire à torchvision mais appliqué frame‑par‑frame)
    brightness = random.uniform(0.8, 1.2)
    contrast   = random.uniform(0.8, 1.2)

---

## Module 3 — contenu

## Module 3 – Entraînement avancé, réglage d’hyper‑paramètres et interprétabilité des modèles multimodaux  

### 3.1. Gestion de la mémoire et accélération (AMP, gradient accumulation)  

| Technique | Pourquoi c’est utile | Implémentation PyTorch (extrait) |
|-----------|----------------------|----------------------------------|
| **Mixed‑precision (AMP)** | Réduit la consommation GPU de ~2× tout en conservant la précision numérique grâce à la mise à l’échelle dynamique des gradients. | ```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()
for epoch in range(num_epochs):
    for batch in train_loader:
        optimizer.zero_grad()
        with autocast():                     # ← calcul en FP16
            logits = model(batch)            # sortie multimodale
            loss = criterion(logits, batch['label'])
        scaler.scale(loss).backward()       # ← mise à l’échelle du gradient
        scaler.step(optimizer)
        scaler.update()
``` |
| **Gradient accumulation** | Permet d’utiliser un « effective batch size » plus grand que la capacité mémoire du GPU. | ```python
accum_steps = 4          # 4 mini‑batches → 1 mise à jour du poids
optimizer.zero_grad()
for i, batch in enumerate(train_loader, 1):
    loss = model(batch).loss() / accum_steps
    loss.backward()
    if i % accum_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
``` |

**Pièges concrets**  
* Oublier de désactiver `torch.backends.cudnn.benchmark` lorsqu’on utilise des tailles d’entrée variables (ex. vidéos de durée différente) → ralentissements imprévisibles.  
* Mélanger AMP avec des opérations non‑supportées (ex. `torch.nn.functional.grid_sample` en FP16) génère des NaN. Utiliser `with autocast(enabled=False):` autour de ces blocs.  

---

### 3.2. Planification du taux d’apprentissage (LR‑scheduler)  

| Scheduler | Forme de décroissance | Code minimal |
|-----------|----------------------|--------------|
| **CosineAnnealingLR** | Décroît suivant un cosinus, bon pour les entraînements courts. | ```python
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,
                                                        T_max=30,
                                                        eta_min=1e-6)
``` |
| **ReduceLROnPlateau** | Réduit le LR quand la métrique de validation ne progresse plus. | ```python
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer,
                                                       mode='max',
                                                       factor=0.5,
                                                       patience=3,
                                                       min_lr=1e-6)
``` |
| **OneCycleLR** | Augmente puis diminue le LR en un cycle, souvent le plus performant sur des datasets de taille moyenne. | ```python
scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer,
                                                max_lr=5e-4,
                                                total_steps=len(train_loader)*num_epochs,
                                                pct_start=0.3,
                                                anneal_strategy='cos')
``` |

**Pièges concrets**  
* Appliquer `scheduler.step()` **après** l’optimisation (pour `OneCycleLR` et `CosineAnnealingLR`) mais **avant** la perte de validation (pour `ReduceLROnPlateau`). Inverser l’ordre entraîne un LR incohérent.  
* Ne pas réinitialiser le scheduler lors d’un *restart* d’entraînement (checkpoint) conduit à des sauts de LR inattendus.  

---

### 3.3. Recherche d’hyper‑paramètres (Optuna)  

```python
import optuna
import torch.nn.functional as F

def objective(trial):
    # Hyper‑paramètres à explorer
    lr = trial.suggest_loguniform('lr', 1e-5, 1e-3)
    wd = trial.suggest_loguniform('weight_decay', 1e-6, 1e-2)
    dropout = trial.suggest_uniform('dropout', 0.0, 0.5)

    # Modèle avec dropout configurable
    model = MultimodalNet(dropout=dropout).to(device)
    optimizer = torch.optim.AdamW(model.parameters(),
                                  lr=lr,
                                  weight_decay=wd)

    # Entraînement très court pour l’évaluation (3 epochs)
    for epoch in range(3):
        train_one_epoch(model, train_loader, optimizer)

    # Validation
    acc = evaluate(model, val_loader)          # retourne l’accuracy
    return acc

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=30, timeout=3600)

print('Meilleur jeu d’hyper‑paramètres :', study.best_params)
```

**Points de vigilance**  
* Fixer le même *seed* (`torch.manual_seed`, `np.random.seed`, `random.seed`) à chaque trial pour éviter que la variance aléatoire ne masque l’effet des

---

## Module 4 — contenu

## Module 4 – Modélisation avancée : Transformers multimodaux et attention croisée  

### 4.1 Principes théoriques  

| Concept | Définition vérifiable | Référence |
|--------|----------------------|-----------|
| **Self‑attention** | Chaque token (image patch, frame audio, ou token vidéo) calcule une pondération sur tous les autres tokens du même modality via les matrices Q, K, V. | Vaswani et al., *Attention Is All You Need* (2017) |
| **Cross‑modal attention** | Q provient d’une modalité, K et V d’une autre. Permet à l’audio d’informer la représentation visuelle (et inversement). | Lu et al., *ViLBERT* (2019) |
| **Positional encoding** | Ajout de vecteurs sinusoidaux ou appris pour injecter l’ordre temporel/spatial. Nécessaire pour les séquences vidéo/audio. | Same as above |
| **Multimodal Transformer (MMT)** | Empile plusieurs blocs de self‑attention séparés par des blocs de cross‑attention. Le nombre de blocs = profondeur du modèle. | Li et al., *MMF* (2020) |
| **CLS token** | Token spécial ajouté au début de chaque séquence; sa sortie sert de représentation agrégée pour la classification. | BERT (Devlin et al., 2018) |

#### Formules clés  

- **Score d’attention** :  
  \[
  \text{Attention}(Q,K,V)=\text{softmax}\!\left(\frac{QK^{\top}}{\sqrt{d_k}}\right)V
  \]  

- **Cross‑attention (audio → image)** :  
  \[
  Q_a = X_aW_Q,\; K_i = X_iW_K,\; V_i = X_iW_V
  \]  

- **Fusion** (concatenation + projection) :  
  \[
  Z = \text{LayerNorm}\big([X_i;X_a]W_{proj}+b_{proj}\big)
  \]  

### 4.2 Implémentation d’un **Multimodal Transformer** simple (PyTorch)  

```python
# -*- coding: utf-8 -*-
import torch
import torch.nn as nn
import torch.nn.functional as F

# -------------------------------------------------
# 1. Encoders de base (pré‑entraînés)  
# -------------------------------------------------
class ImageEncoder(nn.Module):
    """ResNet‑50 tronqué → vecteurs de patch 1D."""
    def __init__(self, embed_dim=768):
        super().__init__()
        backbone = torch.hub.load('pytorch/vision:v0.10.0', 'resnet50', pretrained=True)
        self.features = nn.Sequential(*list(backbone.children())[:-2])  # sortie (B,2048,H/32,W/32)
        self.proj = nn.Linear(2048, embed_dim)

    def forward(self, x):
        B = x.size(0)
        feats = self.features(x)                     # (B,2048,H',W')
        feats = feats.flatten(2).transpose(1, 2)      # (B,N_patches,2048)
        return self.proj(feats)                     # (B,N_patches,embed_dim)

class AudioEncoder(nn.Module):
    """1‑D CNN (TCN) → séquence de vecteurs."""
    def __init__(self, embed_dim=768):
        super().__init__()
        self.tcn = nn.Sequential(
            nn.Conv1d(1, 64, kernel_size=5, stride=2, padding=2),
            nn.ReLU(),
            nn.Conv1d(64, 128, kernel_size=5, stride=2, padding=2),
            nn.ReLU(),
            nn.Conv1d(128, embed_dim, kernel_size=3, stride=2, padding=1),
        )

    def forward(self, wav):
        # wav : (B, 1, T)
        out = self.tcn(wav)                         # (B, embed_dim, T')
        out = out.transpose(1, 2)                   # (B, T', embed_dim)
        return out

class VideoEncoder(nn.Module):
    """I3D (3‑D CNN) tronqué → séquence temporelle."""
    def __init__(self, embed_dim=768):
        super().__init__()
        i3d = torch.hub.load('deepmind/i3d', 'i3d_r50', pretrained=True)
        self.features = nn.Sequential(*list(i3d.children())[:-1])  # drop logits
        self.proj = nn.Linear(1024, embed_dim)

    def forward(self, clip):
        # clip : (B, 3, T, H, W)
        feats = self.features(clip)                  # (B,1024,T',1,1)
        feats = feats.squeeze(-1).squeeze(-1)       # (B,1024,T')
        feats = feats.transpose(1, 2)                # (B,T',1024)
        return self.proj(feats)                      # (B,T',embed_dim)

# -------------------------------------------------
# 2. Bloc d’attention croisée  
# -------------------------------------------------
class CrossAttentionBlock(nn.Module):
    """

---

## Module 5 — contenu

## Module 5 – Déploiement, optimisation et inference des modèles multimodaux  

### 5.1 Objectif pédagogique  
- Exporter un modèle multimodal (image + audio + vidéo) entraîné avec PyTorch vers un format d’inférence (TorchScript / ONNX).  
- Appliquer les techniques de quantification (dynamic, static, quant‑aware) pour réduire la latence et la consommation mémoire tout en conservant une perte de précision ≤ 2 %.  
- Mettre en place un serveur d’inférence léger (TorchServe) et mesurer les métriques (throughput, latency, utilisation GPU/CPU).  

---

### 5.2 Concepts clés  

| Concept | Description technique | Référence |
|---|---|---|
| **TorchScript** | Tracing ou scripting du modèle PyTorch pour obtenir un graphe statique exécutable en C++/Python sans dépendance au runtime Python. | <https://pytorch.org/docs/stable/jit.html> |
| **ONNX** | Open Neural Network Exchange, format inter‑opérable. Exportation via `torch.onnx.export`. | <https://onnx.ai/> |
| **Quantification dynamique** | Conversion des poids en int8 après entraînement, les activations sont quantifiées à la volée. | <https://pytorch.org/docs/stable/quantization.html#dynamic-quantization> |
| **Quantification statique** | Calibration du jeu de données d’entraînement pour déterminer les plages d’activations, puis conversion en int8. | idem |
| **Quant‑aware training (QAT)** | Simule la quantification pendant l’entraînement, améliore la précision post‑quantification. | idem |
| **TorchServe** | Serveur d’inférence PyTorch, support du batching, du scaling et du monitoring via Prometheus. | <https://pytorch.org/serve/> |
| **Benchmarking** | Mesure du temps d’inférence (`torch.utils.benchmark.Timer`) ou de la latence HTTP (`wrk`, `hey`). | idem |

---

### 5.3 Implémentation – Exemple complet  

> **Contexte** : le modèle `MultimodalNet` a été entraîné dans le module 1 et sauvegardé sous `multimodal_best.pth`.  
> **Cible** : exporter en TorchScript, appliquer la quantification dynamique, créer un handler TorchServe et lancer un benchmark CPU.

```python
# -*- coding: utf-8 -*-
# file: deploy_multimodal.py
import torch
import torch.nn as nn
import torch.quantization as quant
from pathlib import Path

# ----------------------------------------------------------------------
# 1. Chargement du modèle entraîné
# ----------------------------------------------------------------------
class MultimodalNet(nn.Module):
    """Architecture simplifiée utilisée dans le module 1.
    - image_encoder : ResNet‑50 (pré‑entraîné ImageNet, sortie 2048)
    - audio_encoder : 1‑D CNN (TCN) → 256
    - video_encoder : I3D (pré‑entraîné Kinetics) → 1024
    - fusion : concat → FC → logits (10 classes)
    """
    def __init__(self, n_classes=10):
        super().__init__()
        # image branch
        self.image_encoder = torch.hub.load('pytorch/vision:v0.15.2', 'resnet50', pretrained=True)
        self.image_encoder.fc = nn.Identity()          # 2048‑dim

        # audio branch (TCN simplifié)
        self.audio_encoder = nn.Sequential(
            nn.Conv1d(1, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv1d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
        )  # 128‑dim

        # video branch (I3D simplifié)
        self.video_encoder = torch.hub.load('deepmind/kinetics-i3d', 'i3d', pretrained=True)
        self.video_encoder.fc = nn.Identity()          # 1024‑dim

        # fusion + classifier
        self.classifier = nn.Sequential(
            nn.Linear(2048 + 128 + 1024, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, n_classes),
        )

    def forward(self, img, audio, video):
        # img : (B, 3, H, W)      –‑> (B, 2048)
        # audio : (B, 1, T)       –‑> (B, 128)
        # video : (B, 3, T, H, W) –‑> (B, 1024)
        img_f = self.image_encoder(img)
        aud_f = self.audio_encoder(audio)
        vid_f = self.video_encoder(video)
        fused = torch.cat([img_f, aud_f, vid_f], dim=1)
        return self.classifier(fused)

# ----------------------------------------------------------------------
# 2. Instanciation et chargement du checkpoint
# ----------------------------------------------------------------------
device = torch.device('cpu')
model = MultimodalNet()
ckpt_path = Path