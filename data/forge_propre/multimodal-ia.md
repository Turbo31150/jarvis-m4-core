# IA Multimodale — Image, Audio, Vidéo

> Référence `multimodal-ia` · 79 €

## Plan

## Module 1 – Architectures fondamentales du multimodal : image, audio, vidéo  
**Objectif** : Concevoir et coder une architecture de base capable de traiter simultanément des entrées image, audio et vidéo, et de produire une sortie classifiée avec une précision sur un jeu de données de référence (ex. AVMNIST).  

**Notions couvertes**  
1. CNN 2D (ResNet‑50) pour l’extraction de caractéristiques d’images – implémentation PyTorch et poids pré‑entraînés ImageNet.  
2. Réseaux spectrogrammes 1D/2D (Mel‑spectrogram, MFCC) et CNN 1D (TCN) pour l’audio – génération avec `librosa`, normalisation et encodage.  
3. 3D‑CNN (I3D) et flux optique (Farneback) pour la vidéo – pré‑traitement avec `opencv`, agrégation temporelle.  
4. Fusion « early » (concaténation de tenseurs) vs « late » (moyenne pondérée des logits) – implémentation d’un module `MultimodalFusion`.  
5. Fonction de perte multi‑tâche (cross‑entropy combinée) et optimisation AdamW (lr = 1e‑4).  

---

## Module 2 – Pré‑traitement et augmentation des données multimodales  
**Objectif** : Mettre en place un pipeline d’augmentation qui augmente le nombre d’échantillons effectifs sans dégrader la performance du modèle de base.  

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
    T.RandomResizedCrop(size=IMG_SIZE),          # recadrage aléatoire + redimensionnement
    T.RandomHorizontalFlip(),                    # symétrie horizontale
    T.ColorJitter(),                             # variations de couleur modestes
    T.ToTensor(),
    T.Normalize(mean=MEAN, std=STD)               # valeurs normalisées (ex. ImageNet)
])
```

* **RandomResizedCrop** garantit que chaque image conserve la même taille d’entrée attendue par le réseau.  
* **ColorJitter** doit rester dans des intervalles modestes ; des valeurs trop extrêmes créent des images hors distribution et dégradent la précision.  

---

## 2.3 Pipeline d’augmentation audio  

```python
import torchaudio
import random
import torch

class AudioAugment:
    """Applique une suite d'augmentations audio compatibles avec la synchronisation vidéo."""
    def __init__(self, sample_rate=SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.time_stretch = torchaudio.transforms.TimeStretch()   # taux choisi aléatoirement
        self.pitch_shift = torchaudio.transforms.PitchShift(
            sample_rate=self.sample_rate)                        # décalage de hauteur limité
        self.add_noise = lambda x: x + torch.randn_like(x) * NOISE_FACTOR

    def __call__(self, waveform):
        # 1️⃣ Time‑stretch – conserve la hauteur
        rate = random.random()                               # facteur de vitesse aléatoire
        stretched = torchaudio.functional.phase_vocoder(
            waveform, rate=rate, phase_advance=None)

        # 2️⃣ Pitch‑shift – léger décalage de hauteur
        shifted = torchaudio.functional.pitch_shift(
            stretched, self.sample_rate, n_steps=None)

        # 3️⃣ Ajout de bruit blanc
        noisy = self.add_noise(shifted)
        return noisy
```

* **Phase‑vocoder** (dans `torchaudio.functional.phase_vocoder`) permet de changer la vitesse sans altérer la hauteur.  
* Après le time‑stretch, la durée du signal change ; on **re‑échantillonne** à la longueur originale ou on **pad/truncate** pour garder la synchronisation avec la vidéo.  
* Le bruit blanc doit rester suffisamment faible pour ne pas masquer le contenu sémantique.

---

## 2.4 Pipeline d’augmentation vidéo  

```python
import cv2
import numpy as np
import random
import torch

def video_augment(frames: torch.Tensor, fps=None):
    """
    frames : Tensor (T, C, H, W)  – T = nombre de frames, C=3, H=W=IMG_SIZE
    Retourne les frames augmentées et le nouveau taux de fps (si décimation).
    """
    T, C, H, W = frames.shape

    # 1️⃣ Découpage temporel aléatoire (conserver une partie des frames)
    keep_ratio = random.random()                     # proportion de frames à garder
    keep_len   = max(1, int(T * keep_ratio))
    start_idx  = random.randint(0, T - keep_len)
    frames = frames[start_idx:start_idx + keep_len]

    # 2️⃣ Retour horizontal (identique à l'image)
    if random.random() < 0.5:
        frames = torch.flip(frames, dims=[3])   # flip width

    # 3️⃣ Color jitter (similaire à torchvision mais appliqué frame‑par‑frame)
    brightness = random.random()
    contrast   = random.random()
    # Application du jitter sur chaque frame (exemple simplifié)
    for i in range(frames.shape[0]):
        frames[i] = T.functional.adjust_brightness(frames[i], brightness)
        frames[i] = T.functional.adjust_contrast(frames[i], contrast)

    return frames, fps
```

* Le découpage temporel conserve la cohérence entre les flux vidéo et audio en appliquant les mêmes indices de début et de fin.  
* Le retournement horizontal préserve la correspondance spatiale entre les deux modalités.  
* Le jitter de couleur est appliqué de façon cohérente à chaque image pour éviter toute désynchronisation perceptuelle.
---

## Module 3 — contenu

## Module 3 – Entraînement avancé, réglage d’hyper‑paramètres et interprétabilité des modèles multimodaux  

### 3.1. Gestion de la mémoire et accélération (AMP, gradient accumulation)  

| Technique | Pourquoi c’est utile | Implémentation PyTorch (extrait) |
|-----------|----------------------|----------------------------------|
| **Mixed‑precision (AMP)** | Réduit la consommation GPU tout en conservant la précision numérique grâce à la mise à l’échelle dynamique des gradients. | ```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()
for epoch in range(num_epochs):
    for batch in train_loader: