# Cluster GPU AlkymIA-OS — LLMs Multi-Machine

> Référence `jarvis-cluster-gpu` · 99 €

## Plan

## Module 1 : Architecture matérielle et logique du cluster AlkymIA‑OS  
**Objectif** – L’apprenant pourra diagrammer l’infrastructure du cluster (nœuds, GPU, interconnexion) et expliquer le rôle de chaque composant dans l’exécution distribuée d’un LLM.  
- Topologie des nœuds : nombre de serveurs, CPU, GPU (ex. NVIDIA A100 40 Go, NVLink 600 GB/s).  
- Réseau haute‑bande : InfiniBand HDR (200 Gb/s) vs Ethernet 25 Gb/s, latence et débit impactant la synchronisation des gradients.  
- Partitionnement du stockage : NVMe RAID 0 local, CephFS partagé, persistance des checkpoints.  
- Pilotes et runtime : NVIDIA Driver 525, CUDA 12.3, cuDNN 8.9, NCCL 2.20 pour la communication collective.  
- Supervision : Prometheus + Grafana, métriques GPU (utilisation, température, ECC errors).

## Module 2 : Orchestration des workloads LLM avec Kubernetes  
**Objectif** – L’apprenant sera capable de déployer, scaler et monitorer un service LLM sur le cluster en utilisant des manifests Kubernetes vérifiables.  
- Pods GPU‑aware : `resourceRequests.limits.nvidia.com/gpu`, taints/tolerations pour les nœuds GPU.  
- Opérateurs spécialisés : Kubeflow Training Operator, Volcano Scheduler pour le placement des jobs.  
- Stratégies de scaling : HPA basé sur GPU‑memory usage, Cluster Autoscaler avec groupes de nœuds.  
- Gestion des secrets et des modèles : ConfigMaps, CSI‑driver pour le stockage sécurisé des checkpoints.  
- Observabilité : logs via Loki, tracing avec OpenTelemetry, alerting sur les dépassements de seuils GPU.

## Module 3 : Distribution du modèle et parallélisme de formation  
**Objectif** – L’apprenant pourra implémenter le parallélisme de données et de modèle (pipeline, tensor‑parallel) sur le cluster et mesurer le gain de performance.  
- Data‑parallel : réplication du modèle, agrégation NCCL All‑Reduce, ajustement du batch size global.  
- Tensor‑parallel (Megatron‑LM) : découpage des matrices de poids, communication de sharding via NCCL.  
- Pipeline‑parallel : découpage du graphe en étapes, gestion du micro‑batching, réduction du temps d’attente.  
- Mixed‑precision training : FP16/TF32, utilisation de `torch.cuda.amp`, impact sur le débit TFLOPS.  
- Profilage : NVIDIA Nsight Systems, PyTorch Profiler, identification des goulots d’étranglement réseau vs compute.

## Module 4 : Optimisation du service d’inférence multi‑GPU  
**Objectif** – L’apprenant pourra configurer un serveur d’inférence capable de servir des requêtes en temps réel avec un taux de réponse ≤ 30 ms pour des prompts de 128 tokens.  
- Serveurs d’inférence : TensorRT‑LLM, vLLM, DeepSpeed‑Inference, comparaison des lat

---

## Module 1 — contenu

## 1.1 Topologie des nœuds  

| Élément | Valeur typique | Rôle dans le calcul distribué |
|--------|----------------|------------------------------|
| **Serveur** | 2 × CPU Intel Xeon 8259CL (32 cœurs) | Orchestration des processus, gestion du trafic réseau, hébergement du système d’exploitation. |
| **GPU** | 4 × NVIDIA A100 40 Go (PCIe 4.0) | Exécution du forward/backward, stockage du modèle en VRAM, calcul des gradients. |
| **Interconnexion GPU‑GPU** | NVLink 2.0, 600 GB/s total (150 GB/s par lien) | Partage de tensors entre GPUs du même nœud, réduction NCCL intra‑node. |
| **Mémoire système** | 512 GiB DDR4‑3200 | Buffers d’entrée, jeu de données, caches d’OS. |
| **Stockage local** | 2 × NVMe PCIe 4.0 2 TB (RAID 0) | Check‑points, modèles temporaires, I/O de données d’entraînement. |
| **Réseau inter‑nœuds** | InfiniBand HDR 200 Gb/s (MLX5 ConnectX‑6) | Synchronisation des gradients (All‑Reduce) entre nœuds, latence < 2 µs. |
| **Alimentation** | 2 × 2000 W redondante | Garantit la stabilité sous charge maximale. |

> **Vérifiable** : La bande passante théorique d’un A100 40 Go en FP16 est 312 TFLOPS (2 × 312 TFLOPS en TF32). La bande passante NVLink 2.0 est 300 GB/s par lien, soit 600 GB/s agrégé sur 4 GPUs (2 liens par GPU).

### 1.1.1 Calcul du débit réseau requis pour la synchronisation des gradients  

Formule simplifiée (Data‑Parallel) :  

\[
B_{\text{req}} = \frac{S_{\text{model}} \times \text{batch\_size\_global}}{t_{\text{comm}}}
\]

- \(S_{\text{model}}\) : taille du modèle en octets (ex. 175 B ≈ 350 Go pour GPT‑3 175 B en FP16).  
- \(\text{batch\_size\_global}\) : nombre total d’échantillons traités par itération.  
- \(t_{\text{comm}}\) : temps cible pour l’All‑Reduce (ex. 2 ms).

Pour un modèle 6 B paramètres (≈ 12 Go FP16) et \(\text{batch\_size\_global}=1024\) samples, on obtient :

\[
B_{\text{req}} = \frac{12\text{ GiB} \times 1024}{0.002\text{ s}} \approx 6.1\text{ TiB/s}
\]

InfiniBand HDR (200 Gb/s ≈ 25 GB/s) ne suffit pas seul ; on utilise le **ring‑All‑Reduce** NCCL qui répartit la charge sur tous les liens, réduisant le facteur de contention. La règle pratique : le débit agrégé du réseau doit être ≥ 10× la taille du modèle / itération pour éviter le goulot.

---

## 1.2 Réseau haute‑bande  

| Technologie | Bande passante (max) | Latence typique | Cas d’usage |
|-------------|----------------------|----------------|------------|
| InfiniBand HDR (MLX5) | 200 Gb/s (≈ 25 GB/s) | 0.5 µs (point‑to‑point) | All‑Reduce, pipeline‑parallel, échange de micro‑batches. |
| Ethernet 25 Gb/s | 25 Gb/s (≈ 3 GB/s) | 5 µs | Gestion du trafic d’administration, accès aux services de stockage partagé. |
| Ethernet 100 Gb/s (option) | 100 Gb/s (≈ 12,5 GB/s) | 2 µs | Scénarios de formation à très grande échelle (> 64 GPU). |

**Pourquoi InfiniBand HDR ?**  
- La latence ultra‑faible minimise le temps d’attente du *ring‑All‑Reduce* NCCL.  
- La bande passante supérieure à 10 × la taille du modèle (en FP16) assure que le temps de communication ne dépasse pas 5 % du temps total d’une itération.

### 1.2.1 Configuration du réseau (exemple de script `ib0`)

```bash
#!/usr/bin/env bash
# Configuration d'une interface InfiniBand HDR sur Ubuntu 22.04
# Vérifie que le driver Mellanox (mlx5_core) est chargé
if ! lsmod | grep -q mlx5_core; then
    echo "Driver mlx5_core absent, installation requise."
    exit 1
fi

# Active le mode "Ethernet" (RDMA over Converged Ethernet)
sudo ethtool -s ib0 speed 200 autoneg off advertise 0x8000

# Désactive le flow control qui peut introduire de la latence
sudo ethtool -A ib0 rx off tx off

# Vérifie la MTU (jumbo frames

---

## Module 2 — contenu

## 2.1 Pods GPU‑aware  

| Élément | Valeur attendue | Vérification |
|--------|----------------|--------------|
| **Node selector** | `kubernetes.io/arch: amd64` + `kubernetes.io/os: linux` (facultatif) | `kubectl get nodes -o jsonpath='{.items[*].metadata.labels}'` |
| **Taint du nœud GPU** | `nvidia.com/gpu:NoSchedule` (ou `NoExecute`) | `kubectl describe node <gpu-node>` |
| **Toleration du pod** | `key: "nvidia.com/gpu", operator: "Exists", effect: "NoSchedule"` | `kubectl get pod <pod> -o yaml` |
| **Resource request/limit** | `nvidia.com/gpu: 1` (ou plus) | `kubectl describe pod <pod>` |
| **RuntimeClass** | `nvidia` (si le runtime est installé) | `kubectl get runtimeclass` |

```yaml
# file: gpu-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: llama-inference
spec:
  runtimeClassName: nvidia               # obligatoire si le runtime nvidia est installé
  tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
  containers:
  - name: inference
    image: ghcr.io/vllm/vllm:latest      # image contenant le serveur vLLM
    command: ["python", "-m", "vllm.entrypoints.api_server"]
    args: ["--model", "meta-llama/Meta-Llama-3-8B", "--port", "80"]
    ports:
    - containerPort: 80
    resources:
      limits:
        nvidia.com/gpu: 1               # 1 GPU dédié
        cpu: "8"
        memory: "32Gi"
      requests:
        nvidia.com/gpu: 1
        cpu: "4"
        memory: "16Gi"
    env:
    - name: NCCL_DEBUG
      value: INFO                         # utile pour le debug des communications NCCL
```

**Déploiement**  

```bash
kubectl apply -f gpu-pod.yaml
kubectl wait --for=condition=Ready pod/llama-inference --timeout=120s
```

### 2.2 Opérateurs spécialisés  

| Opérateur | Version stable (au 14/08/2026) | Fonction principale |
|----------|--------------------------------|---------------------|
| **Kubeflow Training Operator** | `v1.7.0` | Crée des `TFJob`, `PyTorchJob`, `MPIJob` qui gèrent automatiquement le lancement de processus de formation distribuée. |
| **Volcano Scheduler** | `v1.9.0` | Scheduler extensible qui accepte des *queues* et des *gang scheduling* pour garantir que tous les pods d’un job démarrent simultanément. |

#### Exemple : PyTorchJob avec data‑parallel sur 4 GPUs (2 nœuds, 2 GPUs chacun)

```yaml
# file: pytorch-job.yaml
apiVersion: "kubeflow.org/v1"
kind: PyTorchJob
metadata:
  name: llama-dp
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:2.2.0-cuda12.3-cudnn9-runtime
            command: ["python", "train.py"]
            env:
            - name: WORLD_SIZE
              value: "4"
            resources:
              limits:
                nvidia.com/gpu: 1
    Worker:
      replicas: 3                # 3 workers + 1 master = 4 processus
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:2.2.0-cuda12.3-cudnn9-runtime
            command: ["python", "train.py"]
            env:
            - name: WORLD_SIZE
              value: "4"
            resources:
              limits:
                nvidia.com/gpu: 1
```

`kubectl apply -f pytorch-job.yaml` crée les pods, le **operator** injecte les variables d’environnement `RANK`, `LOCAL_RANK`, `MASTER_ADDR`, `MASTER_PORT` et lance `torch.distributed.launch`.  

### 2.3 Stratégies de scaling  

#### 2.3.1 HPA basé sur l’utilisation GPU memory  

```yaml
# file: gpu-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vllm-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm-deploy
  minReplicas: 1
  maxReplicas: 8
  metrics:
  - type: External
    external:
      metric:
        name: nvidia_gpu_memory_used_bytes
        selector:
          matchLabels:
            gpu: "true"
      target:
        type: AverageValue
        averageValue: 16Gi   # déclenche le scaling dès que chaque pod utilise > 16 GiB
```

*Prerequisite* : le **custom metrics adapter** de Prometheus‑Adapter doit exporter le métrique `nvidia_gpu_memory_used_bytes` depuis le node‑exporter NVIDIA.  

#### 2.3.2 Cluster Autoscaler + node‑group GPU  

```yaml
# fichier de configuration du Cluster Autoscaler (YAML du cloud provider)
apiVersion: autoscaling.k8s.io/v1
kind: NodeGroup
metadata:
  name: gpu-ng
spec:
  minSize:

---

## Module 3 — contenu

## 3.1 Parallélisme de données (Data‑Parallel)

### 3.1.1 Principe
- **Réplique du modèle** sur chaque GPU (ou chaque rang `local_rank` d’un processus).
- Chaque réplique reçoit un sous‑lot (`local_batch`) du lot global.
- Après le **forward**, chaque GPU calcule ses gradients localement.
- Les gradients sont agrégés **All‑Reduce** (NCCL) : `grad_i = (1/WorldSize) * Σ grad_j`.
- Le **step** d’optimisation est exécuté simultanément sur toutes les répliques, garantissant la même mise à jour de poids.

### 3.1.2 Configuration minimale (PyTorch)

```python
# data_parallel.py
import os
import torch
import torch.distributed as dist
import torch.nn as nn
import torch.optim as optim
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, DistributedSampler, TensorDataset

def setup(rank, world_size):
    os.environ["MASTER_ADDR"] = "10.0.0.1"          # IP du node maître
    os.environ["MASTER_PORT"] = "29500"
    dist.init_process_group(backend="nccl", rank=rank, world_size=world_size)

def cleanup():
    dist.destroy_process_group()

def train(rank, world_size, epochs=5):
    setup(rank, world_size)

    # 1️⃣ Modèle simple
    model = nn.Sequential(
        nn.Linear(1024, 4096),
        nn.GELU(),
        nn.Linear(4096, 1024)
    ).cuda(rank)

    # 2️⃣ Enveloppe DDP
    model = DDP(model, device_ids=[rank])

    # 3️⃣ Optimiseur
    optimizer = optim.AdamW(model.parameters(), lr=2e-4)

    # 4️⃣ Jeu de données synthétique
    x = torch.randn(8192, 1024)
    y = torch.randn(8192, 1024)
    dataset = TensorDataset(x, y)

    # 5️⃣ Sampler distribué → chaque rang voit un sous‑ensemble exclusif
    sampler = DistributedSampler(dataset, num_replicas=world_size, rank=rank, shuffle=True)
    loader = DataLoader(dataset, batch_size=32, sampler=sampler, num_workers=2, pin_memory=True)

    # 6️⃣ Boucle d’entraînement
    for epoch in range(epochs):
        sampler.set_epoch(epoch)                # assure un reshuffle cohérent
        for xb, yb in loader:
            xb = xb.cuda(rank, non_blocking=True)
            yb = yb.cuda(rank, non_blocking=True)

            optimizer.zero_grad()
            out = model(xb)
            loss = nn.functional.mse_loss(out, yb)
            loss.backward()
            optimizer.step()

        if rank == 0:
            print(f"epoch {epoch} loss {loss.item():.4f}")

    cleanup()

if __name__ == "__main__":
    # Lancement via torchrun : torchrun --nproc_per_node=8 data_parallel.py
    world_size = int(os.getenv("WORLD_SIZE", "8"))
    rank = int(os.getenv("RANK", "0"))
    train(rank, world_size)
```

#### Points de vérification
| Étape | Vérification (commande) | Résultat attendu |
|------|--------------------------|------------------|
| Initialisation NCCL | `torch.distributed.is_initialized()` | `True` |
| Taille du lot global | `len(loader.dataset) // world_size * batch_size` | `8192 / 8 * 32 = 32768` (exemple) |
| Synchronisation des poids | `torch.allclose(model.module[0].weight, model.module[0].weight.clone())` | `True` |

---

## 3.2 Parallélisme de tenseur (Tensor‑Parallel)

### 3.2.1 Concept
- Le **matrice de poids** d’une couche dense est découpée le long de la dimension d’entrée ou de sortie.
- Chaque GPU détient **une tranche** de la matrice et effectue la partie locale du produit matriciel.
- Les **communications NCCL** sont limitées aux **All‑Gather** ou **Reduce‑Scatter** des activations/gradients.
- Implémentations courantes : **Megatron‑LM**, **DeepSpeed‑ZeRO‑3** (sharding de paramètres).

### 3.2.2 Exemple minimal avec Megatron‑LM (v2.4)

> Prérequis : `pip install megatron-lm==2.4 torch==2.2.0`.

```bash
# launch_tensor_parallel.sh
#!/usr/bin/env bash
export MASTER_ADDR=10.0.0.1
export MASTER_PORT=29501
export NCCL_DEBUG=INFO
export TORCH_DISTRIBUTED_DEBUG=DETAIL

# 4 GPUs, tensor‑parallel size = 4 (une tranche par GPU)
torchrun --nproc_per_node=4 \
    --rdzv_id=tp_demo \
    --rdzv_backend=c10d \
    --rdzv_endpoint=$MASTER_ADDR:29501 \
    examples/gpt2_pretrain.py \
    --tensor-model-parallel-size 4 \
    --pipeline-model-parallel-size 1 \
    --num-layers 12 \
    --hidden-size 768 \
    --seq-length 512 \
    --batch-size 8 \
    --train-iters 1000 \
    --data-path /data/gpt2_text_document \
    --lr 6e-4 \
    --log-interval 10
```

#### Ce qui se passe sous le capot
| Opération | Communication NCCL | Taille (exemple 768 × 768) |
|----------|-------------------|----------------

---

## Module 4 — contenu

## Module 4 – Optimisation du service d’inférence multi‑GPU  

### 4.1 Architecture du serveur d’inférence  

| Composant | Rôle | Paramètres critiques |
|-----------|------|----------------------|
| **Load‑balancer** (NGINX + stream) | Répartition TCP/HTTP entre les workers | `worker_processes auto`, `listen 0.0.0.0:8000` |
| **Worker d’inférence** | Exécution du modèle sur un ou plusieurs GPU | `torch.cuda.set_device(gpu_id)`, `torch.backends.cudnn.benchmark = True` |
| **Cache de KV‑cache** (GPU‑SRAM) | Stockage des clés/valeurs pour le décodage auto‑régresseur | Taille = `max_seq_len × num_layers × hidden_dim × 2 × dtype` |
| **Scheduler** (vLLM/DeepSpeed‑Inference) | Découpage du batch en micro‑batch, gestion du pipeline | `max_num_batched_tokens`, `max_num_seqs` |
| **Quantisation** (INT8/FP8) | Réduction de la précision du poids et des activations | `torch.quantization.quantize_dynamic`, `torch.ops.tensorrt.experimental` |

#### 4.1.1 Choix du runtime  

| Runtime | Avantages mesurés (benchmarks 2024) | Contraintes |
|---------|------------------------------------|-------------|
| **TensorRT‑LLM** (v8.6) | Latence 22 ms @ 128 tokens, FP16, 8 GPU A100 | Nécessite conversion ONNX → TRT, support limité de certains ops (e.g. `torch.nn.functional.scaled_dot_product_attention` avant v2.1) |
| **vLLM** (v0.5) | Latence 18 ms @ 128 tokens, FP8/INT8, support de LoRA | Consomme plus de RAM CPU pour le pré‑allocation du KV‑cache |
| **DeepSpeed‑Inference** (v0.12) | Latence 20 ms @ 128 tokens, FP16 + ZeRO‑Inf‑2 | Implémentation plus lourde du partitionnement de modèle, nécessite `deepspeed` ≥ 0.12.0 |

### 4.2 Pipeline d’inférence détaillé  

1. **Pré‑traitement**  
   ```python
   def tokenize(text: str, tokenizer) -> torch.Tensor:
       # Retourne un tensor int64 sur CPU
       ids = tokenizer.encode(text, add_special_tokens=False)
       return torch.tensor(ids, dtype=torch.long)
   ```
2. **Placement du batch**  
   ```python
   # batch = List[torch.Tensor]  # chaque tensor = séquence tokenisée
   batch = [tokenize(p, tokenizer) for p in prompts]
   seq_lens = [t.shape[0] for t in batch]
   max_len = max(seq_lens)
   # Pad à max_len (GPU‑friendly)
   padded = torch.nn.utils.rnn.pad_sequence(batch,
                                            batch_first=True,
                                            padding_value=tokenizer.pad_token_id)
   padded = padded.to('cuda')
   ```
3. **Appel du modèle** (exemple avec vLLM)  
   ```python
   from vllm import LLM, SamplingParams

   # Chargement unique, partagé entre workers
   llm = LLM(model="meta-llama/Meta-Llama-3-8B",
             tensor_parallel_size=8,   # 8 GPU A100
             dtype="float16",
             max_seq_len=4096,
             gpu_memory_utilization=0.90)   # 90 % de la VRAM

   sampling_params = SamplingParams(
       temperature=0.7,
       top_p=0.9,
       max_tokens=128,
       stop=["\n"]
   )

   # inference synchronisée
   outputs = llm.generate(prompts, sampling_params)
   # `outputs` est une liste d'objets contenant `prompt`, `outputs`, `token_ids`
   ```
4. **Post‑traitement**  
   ```python
   def detokenize(output_obj, tokenizer):
       return tokenizer.decode(output_obj.outputs[0].token_ids,
                               skip_special_tokens=True)

   responses = [detokenize(o, tokenizer) for o in outputs]
   ```

### 4.3 Optimisations GPU spécifiques  

| Optimisation | Implémentation | Impact mesuré |
|--------------|----------------|---------------|
| **Tensor Cores FP16/TF32** | `torch.backends.cuda.matmul.allow_tf32 = True` (TF32) ou `dtype=torch.float16` (FP16) | +30 % TFLOPS, latence ↓ 10 % |
| **Fusion de kernels** (NVIDIA **Cutlass** via TensorRT) | `trt_engine = torch_tensorrt.compile(model, inputs=[torch.randn(1, seq_len, hidden_dim).to('cuda')], enabled_precisions={torch.float16})` | Réduction du nombre d’appels CUDA de 3×, latence ↓ 12 % |
| **KV‑cache en FP8** (vLLM ≥ 0.5) | `llm = LLM(..., dtype="float8")` | Mémoire ↓ 75 %, débit ↑ 5 % pour séquences > 2048 tokens |
| **Batching dynamique** | `max_num_batched_tokens = 4096` dans `SamplingParams` | Remplit les GPU sans sous‑utilisation, latence moyenne 18 ms @ 128 tokens, charge 95 % GPU |
| **Pinned memory for host‑GPU transfer** | `torch.utils.data.DataLoader(..., pin_memory=True)` | Throughput d’IO ↑ 20 % |

### 4.4 Gestion du KV‑cache  

- **Dimension** : `cache_size = max_seq_len × num_layers × hidden_dim × 2 × dtype_size`.  
  Exemple : `max_seq_len=4096`, `num_layers=32`, `hidden_dim=4096`, `dtype=fp

---

## Module 5 — contenu

## Module 5 : CI/CD et automatisation du déploiement de modèles LLM sur le cluster AlkymIA‑OS  

### 5.1 Principes de GitOps appliqués aux LLM  
| Concept | Description | Référence vérifiable |
|--------|-------------|----------------------|
| **Source‑of‑Truth** | Tout le manifeste Kubernetes (Helm, Kustomize) est versionné dans un dépôt Git. | Argo CD v2.7.0 « GitOps » |
| **Déploiement déclaratif** | L’état souhaité du cluster est décrit par des manifests ; le contrôleur Argo CD applique les changements jusqu’à convergence. | `argocd app sync` |
| **Rollback atomique** | Un commit Git identifie un SHA ; Argo CD peut revenir à cet SHA en une seule opération. | `argocd app rollback <app> --revision <sha>` |
| **Audits immuables** | Chaque modification est tracée dans l’historique Git et dans les événements d’API Kubernetes (`kubectl get events`). | Git log + `kubectl get events -A` |

### 5.2 Chaîne CI / CD typique pour un modèle LLM  

```
git push → GitHub Actions (ou GitLab CI) → 
   1️⃣ Build du container (Dockerfile) → image tagée <model>-<git‑sha>
   2️⃣ Push vers le registre privé (Harbor v2.9, OCI‑compliant) 
   3️⃣ Mise à jour du chart Helm (values.yaml) avec le nouveau tag → commit
   4️⃣ Argo CD détecte le commit → sync → déploiement
```

- **Dockerfile** minimal : utilise `nvidia/cuda:12.3.2-runtime-ubuntu22.04` + `pip install vllm==0.4.0 torch==2.2.0`.  
- **Registry** : `harbor.mycorp.io/llm` ; les images sont signées avec **cosign** (`cosign sign -key <key> <image>`).  
- **Helm** : chart `llm-inference` version 1.2.3, dépendance `nvidia-device-plugin` (v0.14.0).  

### 5.3 Exemple complet : chart Helm + manifest Argo CD  

#### 5.3.1 `Chart.yaml` (v1.2.3)

```yaml
apiVersion: v2
name: llm-inference
description: Serveur d’inférence LLM (vLLM) GPU‑aware
type: application
version: 1.2.3
appVersion: "0.4.0"
dependencies:
  - name: nvidia-device-plugin
    version: "0.14.0"
    repository: https://nvidia.github.io/k8s-device-plugin
```

#### 5.3.2 `values.yaml` (extrait)

```yaml
replicaCount: 2

image:
  repository: harbor.mycorp.io/llm/vllm
  tag: "v0.4.0-{{ .Release.Revision }}"   # remplacé par le SHA dans CI
  pullPolicy: IfNotPresent

resources:
  limits:
    nvidia.com/gpu: 1               # 1 GPU par pod
    cpu: "8"
    memory: "32Gi"
  requests:
    nvidia.com/gpu: 1
    cpu: "4"
    memory: "16Gi"

service:
  type: ClusterIP
  port: 80

# Configuration du serveur vLLM
vllm:
  model: "EleutherAI/gpt-neox-20b"
  max_total_tokens: 2048
  dtype: "float16"
  # micro‑batch size pour le serveur (définit la mémoire GPU)
  max_batch_size: 8
```

#### 5.3.3 `templates/deployment.yaml` (extrait)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "llm-inference.fullname" . }}
  labels: {{- include "llm-inference.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "llm-inference.name" . }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ include "llm-inference.name" . }}
    spec:
      containers:
        - name: vllm
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          command: ["python", "-m", "vllm.entrypoints.api_server"]
          args:
            - "--model"
            - "{{ .Values.vllm.model }}"
            - "--dtype"
            - "{{ .Values.vllm.dtype }}"
            - "--max-total-tokens"
            - "{{ .Values.vllm.max_total_tokens }}"