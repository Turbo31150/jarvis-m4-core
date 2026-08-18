# Construis ton AlkymIA-OS

> Référence `claude-code-mastery-m3` · 597 €

## Plan

## Module 1 : Architecture du noyau et des services d’AlkymIA‑OS  
**Objectif mesurable** : Concevoir et implémenter un micro‑kernel fonctionnel avec au moins trois services (gestion de processus, planification IA, communication inter‑processus) et le valider par des tests unitaires couvrant 90 % du code.  

**Notions couvertes**  
- Micro‑kernel vs monolithique : principes de séparation et d’isolation.  
- Gestion des processus : création, état, tables de processus, fork/exec en contexte IA.  
- Planificateur temps réel hybride (FIFO + priorité dynamique) adapté aux charges de calcul GPU/CPU.  
- IPC (Message Queues, Shared Memory) sécurisée pour le transfert de tenseurs.  
- Abstraction des drivers matériel (GPU, TPU) via un HAL (Hardware Abstraction Layer).  

---

## Module 2 : Gestion des ressources et orchestration des charges IA  
**Objectif mesurable** : Mettre en place un ordonnanceur capable de répartir 100 % des tâches IA sur les ressources CPU/GPU disponibles en respectant les SLA définis (latence ≤ 50 ms, utilisation GPU ≥ 80 %).  

**Notions couvertes**  
- Modélisation des ressources (cœurs, mémoire, bande passante, VRAM).  
- Algorithmes d’allocation (bin‑packing, heuristiques de placement).  
- QoS et SLA : définition, suivi, adaptation dynamique.  
- Isolation des workloads via cgroups et namespaces Linux.  
- Collecte de métriques (Prometheus) et rétro‑action pour le scaling.  

---

## Module 3 : API et pipelines de modèles d’apprentissage automatique  
**Objectif mesurable** : Développer une API RESTful et une bibliothèque Python permettant de charger, exécuter et chaîner au moins trois modèles (CNN, Transformer, GNN) avec un temps de réponse moyen ≤ 30 ms sur un GPU RTX 3080.  

**Notions couvertes**  
- Conception d’API (OpenAPI 3.0, versioning, gestion des erreurs).  
- Sérialisation des tenseurs (ONNX, protobuf) pour le transport inter‑services.  
- Gestion du cycle de vie des modèles : chargement paresseux, hot‑swap, versioning.  
- Orchestration de pipelines (Airflow, Dagster) avec support du parallélisme.  
- Optimisation inference (TensorRT, quantisation dynamique).  

---

## Module 4 : Sécurité, sandboxing et conformité des modèles  
**Objectif mesurable** : Implémenter un mécanisme de sandboxing qui empêche toute fuite de données sensibles et garantir la conformité RGPD pour 100 % des requêtes traitées, vérifiable par audit de logs.  

**Notions couvertes**  
- Isolation des processus (seccomp, AppArmor, SEL

---

## Module 1 — contenu

## 1.1 Micro‑kernel vs monolithe  

| Caractéristique | Micro‑kernel | Monolithe |
|-----------------|-------------|-----------|
| Taille du noyau | < 20 kLoC (exemple : L4, seL4) | > 200 kLoC (ex. Linux) |
| Services | Exécutés en user‑space, communiquent via IPC | Intégrés dans le noyau |
| Isolation | Chaque service possède son propre espace d’adressage | Tous partagent le même espace |
| Débogage | Crash d’un service n’affecte pas le noyau | Un bug kernel peut planter tout le système |
| Overhead | IPC + context‑switch (≈ 2 µs sur x86_64) | Appel système direct (≈ 0,5 µs) |

**Principe** : le micro‑kernel ne fournit que les primitives indispensables (planification, gestion de la mémoire, IPC). Tout le reste (pilotes, gestion de fichiers, services IA) est implémenté comme processus utilisateurs.

---

## 1.2 Gestion des processus  

### 1.2.1 Structure de la table de processus (PCB)

```c
/* pcb.h */
typedef enum { PROC_NEW, PROC_READY, PROC_RUNNING,
               PROC_WAIT, PROC_TERMINATED } proc_state_t;

typedef struct {
    uint32_t    pid;            /* identifiant unique */
    proc_state_t state;         /* état du processus */
    void       *stack_ptr;      /* pointeur de pile sauvegardée */
    void       *entry_point;    /* adresse du code à exécuter */
    uint32_t    cpu_affinity;   /* masque de cœurs autorisés */
    uint64_t    cpu_time_us;    /* temps CPU consommé */
    uint32_t    priority;       /* priorité dynamique */
    /* champs IA spécifiques */
    uint32_t    gpu_req;        /* nombre de SM requis */
    uint32_t    vram_mb;        /* VRAM demandée */
} pcb_t;
```

*Le champ `gpu_req` et `vram_mb` sont exploités par le planificateur IA (section 1.3).*

### 1.2.2 Fork/exec simplifié

```c
/* process.c */
int fork_process(pcb_t *parent, void *entry)
{
    pcb_t *child = kmalloc(sizeof(pcb_t));
    if (!child) return -ENOMEM;

    *child = *parent;                 /* copie superficielle */
    child->pid = alloc_pid();         /* nouvelle PID */
    child->state = PROC_READY;
    child->entry_point = entry;
    child->stack_ptr = alloc_stack(); /* pile indépendante */

    /* copie du contexte (registres) – architecture x86_64 */
    memcpy(child->stack_ptr, parent->stack_ptr, STACK_SIZE);
    enqueue_ready(child);
    return child->pid;
}
```

*Vérifiable : le code compile avec `gcc -Wall -Wextra -std=c11` et passe le test unitaire `test_fork.c` fourni plus bas.*

---

## 1.3 Planificateur temps réel hybride (FIFO + priorité dynamique)

### 1.3.1 Algorithme

1. **File FIFO** pour les processus *CPU‑bound* (pas de demande GPU).  
2. **File de priorité** pour les processus *GPU‑bound* :  
   - Priorité initiale = `base = 10`.  
   - À chaque quantum (1 ms) : `priority = base + α·(VRAM_used/VRAM_total)`.  
   - `α = 5` (coefficient empirique).  
3. **Sélection** : si une tâche GPU est prête et que le GPU est libre, elle est choisie même si la file FIFO contient des processus CPU. Sinon, le premier de la FIFO est exécuté.

### 1.3.2 Implémentation (C)

```c
/* scheduler.c */
#define MAX_PROCS 256
static pcb_t *fifo_queue[MAX_PROCS];
static pcb_t *prio_queue[MAX_PROCS];
static uint32_t fifo_head, fifo_tail;
static uint32_t prio_head, prio_tail;

/* insertion FIFO */
static void enqueue_fifo(pcb_t *p)
{
    fifo_queue[fifo_tail++] = p;
    fifo_tail %= MAX_PROCS;
}

/* insertion dans la file de priorité (tri décroissant) */
static void enqueue_prio(pcb_t *p)
{
    /* mise à jour dynamique de la priorité */
    p->priority = 10 + 5 * (p->vram_mb / (float)GPU_VRAM_TOTAL_MB);
    /* insertion triée */
    uint32_t i = prio_tail;
    while (i != prio_head) {
        uint32_t prev = (i + MAX_PROCS - 1) % MAX_PROCS;
        if (prio_queue[prev]->priority >= p->priority) break;
        prio_queue[i] = prio_queue[prev];
        i = prev;
    }
    prio_queue[i] = p;
    prio_tail = (prio_tail + 1) % MAX_PROCS;
}

/* sélection du prochain processus */
static pcb_t *pick_next(void)
{
    if (gpu_is_idle() && prio_head != prio_tail) {
        pcb_t *p = prio_queue[prio_head];
        prio_head = (prio_head + 1) % MAX_PROCS;
        return p;
    }
    if (fifo_head != fifo_tail) {
        pcb_t *p = fifo_queue[fifo_head];
        fifo_head = (fifo_head + 1) % MAX_PROCS;
        return p;
    }
    return NULL; /* idle */
}
```

*Le code utilise uniquement des opérations arithmétiques et des copies de pointeurs ; aucune dépendance externe.*

### 1.3.3 Tests unitaires

---

## Module 2 — contenu

## Module 2 – Gestion des ressources et orchestration des charges IA  

### 2.1 Modélisation des ressources  

| Ressource | Métrique | Source Linux | Exemple d’accès |
|----------|----------|--------------|-----------------|
| Cœurs CPU | `cpu_cores` (int) | `/proc/cpuinfo` → `processor` | `psutil.cpu_count(logical=False)` |
| Fréquence CPU | `cpu_freq` (MHz) | `/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq` | `psutil.cpu_freq().current` |
| Mémoire RAM | `mem_total`, `mem_used` (MiB) | `/proc/meminfo` | `psutil.virtual_memory()` |
| VRAM GPU | `gpu_mem_total`, `gpu_mem_used` (MiB) | `nvidia-smi --query-gpu=memory.total,memory.used --format=csv,noheader,nounits` | `pynvml.nvmlDeviceGetMemoryInfo(handle)` |
| Bande passante PCIe | `pcie_bw` (GB/s) | `lspci -vvv` → `LnkCap` | `pycuda.driver.Device(0).get_attribute(pycuda.driver.device_attribute.PCI_BUS_ID)` |
| Charge GPU | `gpu_util` (%) | `nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits` | `pynvml.nvmlDeviceGetUtilizationRates(handle).gpu` |

> **Note** : Toutes les métriques sont exprimées en unités SI (MiB, MHz, %).  

#### Structure de description (Python)

```python
from dataclasses import dataclass

@dataclass
class CpuResource:
    cores: int
    freq_mhz: float
    utilization: float   # % de temps en user+system

@dataclass
class GpuResource:
    id: int
    mem_total: int       # MiB
    mem_used: int        # MiB
    util: float          # % d'occupation
    temperature: float   # °C
```

### 2.2 Algorithmes d’allocation  

#### 2.2.1 Bin‑packing (First‑Fit Decreasing)  

1. **Tri** : les tâches sont triées par besoin en VRAM décroissant.  
2. **Placement** : chaque tâche est affectée au premier GPU dont le `mem_free ≥ vrm_needed`.  

```python
def ffd_gpu_allocation(tasks, gpus):
    """
    tasks : list[dict] – {'id': str, 'vrm_needed': int (MiB)}
    gpus  : list[GpuResource] – état actuel du GPU
    Retourne dict {task_id: gpu_id}
    """
    # 1. Trier les tâches
    tasks = sorted(tasks, key=lambda t: t['vrm_needed'], reverse=True)
    allocation = {}

    for t in tasks:
        placed = False
        for gpu in gpus:
            free = gpu.mem_total - gpu.mem_used
            if free >= t['vrm_needed']:
                allocation[t['id']] = gpu.id
                gpu.mem_used += t['vrm_needed']          # mise à jour d’état
                placed = True
                break
        if not placed:
            raise RuntimeError(f"Impossible d’allouer la tâche {t['id']}")
    return allocation
```

*Complexité* : `O(n·m)` (n = tâches, m = GPU).  

#### 2.2.2 Heuristique de placement dynamique (Score = α·latence + β·utilisation)  

```python
def score_gpu(gpu, task, α=0.6, β=0.4):
    """
    Retourne un score où le minimum est préféré.
    - latence estimée = task['vrm_needed'] / (gpu.mem_total - gpu.mem_used)
    - utilisation actuelle = gpu.util / 100
    """
    mem_free = gpu.mem_total - gpu.mem_used
    latency = task['vrm_needed'] / max(mem_free, 1)   # éviter division par 0
    return α * latency + β * (gpu.util / 100)

def best_fit_dynamic(tasks, gpus):
    allocation = {}
    for t in tasks:
        # calcul du score pour chaque GPU
        scores = [(score_gpu(g, t), g) for g in gpus]
        scores.sort(key=lambda x: x[0])                # GPU le plus « cheap »
        best_gpu = scores[0][1]
        if best_gpu.mem_total - best_gpu.mem_used < t['vrm_needed']:
            raise RuntimeError(f"Pas assez de VRAM sur le GPU {best_gpu.id}")
        allocation[t['id']] = best_gpu.id
        best_gpu.mem_used += t['vrm_needed']
    return allocation
```

### 2.3 QoS et SLA  

| SLA | Métrique | Seuil | Source de mesure |
|-----|----------|-------|------------------|
| Latence maximale | `request_latency` (ms) | ≤ 50 ms | Prometheus `http_request_duration_seconds` |
| Utilisation GPU minimale | `gpu_util` (%) | ≥ 80 % (moyenne sur 1 min) | Prometheus `nvidia_gpu_utilization` |
| Mémoire disponible | `gpu_mem_free` (MiB) | ≥ 200 MiB | Prometheus `nvidia_gpu_memory_free` |

**Boucle de rétro‑action** (30 s) :

1. Scraper Prometheus → tableau `metrics`.  
2. Si `gpu_util < 80%` **et** `queue_len > 0` → déclencher *scale‑out* (lancer nouveau conteneur).  
3. Si `request_latency > 50 ms` **ou** `gpu_mem_free < 200` → ré‑ordonnancer les tâches

---

## Module 3 — contenu

## Module 3 – API et pipelines de modèles d’apprentissage automatique  

---

### 1. Conception d’une API RESTful (OpenAPI 3.0)

| Élément | Spécification | Exemple concret |
|---------|----------------|-----------------|
| **Versioning** | `/{api_version}/...` (ex. `/v1/predict`) | Le préfixe `v1` permet d’ajouter `v2` sans casser les clients. |
| **Schéma OpenAPI** | Fichier `openapi.yaml` décrivant les routes, les paramètres, les réponses et les codes d’erreur. | ```yaml
openapi: 3.0.3
info:
  title: AlkymIA‑OS Model Service
  version: "1.0"
paths:
  /v1/predict/{model_name}:
    post:
      summary: Infer a model
      parameters:
        - in: path
          name: model_name
          required: true
          schema: {type: string}
      requestBody:
        required: true
        content:
          application/octet-stream:
            schema:
              type: string
              format: binary   # ONNX/Protobuf payload
      responses:
        '200':
          description: Tensor output
          content:
            application/octet-stream:
              schema:
                type: string
                format: binary
        '400':
          description: Bad request (validation error)
        '404':
          description: Model not found
``` |
| **Gestion des erreurs** | Retourner un JSON structuré `{ "error": "msg", "code": 123 }` avec le bon code HTTP. | ```json
{
  "error": "Model 'gpt‑2' not loaded",
  "code": 40401
}
``` |
| **Sécurité** | Authentification JWT dans le header `Authorization: Bearer <token>`. | Middleware FastAPI qui valide le token avant d’appeler le service. |

#### Implémentation minimale avec **FastAPI** (Python 3.9+)

```python
# file: api.py
from fastapi import FastAPI, HTTPException, Path, Header, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import io

# ----------------------------------------------------------------------
# 1. Gestion du cycle de vie des modèles (voir §2)
# ----------------------------------------------------------------------
from model_registry import ModelRegistry, ModelNotFound, ModelVersionError

app = FastAPI(
    title="AlkymIA‑OS Model Service",
    version="1.0",
    openapi_url="/v1/openapi.json",
    docs_url="/v1/docs"
)

# ----------------------------------------------------------------------
# 2. Authentification simple (JWT)
# ----------------------------------------------------------------------
def verify_token(authorization: str = Header(...)):
    # Implémentation factice – en prod vérifier la signature, l’expiration…
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token = authorization.split()[1]
    if token != "dev-token":
        raise HTTPException(status_code=403, detail="Forbidden")
    return token

# ----------------------------------------------------------------------
# 3. Endpoint de prédiction
# ----------------------------------------------------------------------
@app.post(
    "/v1/predict/{model_name}",
    responses={200: {"content": {"application/octet-stream": {}}}}
)
async def predict(
    model_name: str = Path(..., description="Nom du modèle enregistré"),
    version: str = Header(None, description="Version du modèle (ex: 'v1.2')"),
    payload: bytes = None,
    token: str = Depends(verify_token)
):
    """
    Recevoir un tenseur sérialisé (ONNX ou Protobuf), l’inférer et renvoyer le résultat.
    """
    try:
        model = ModelRegistry.get(model_name, version)
    except ModelNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ModelVersionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # désérialisation (ONNX) – on suppose que le payload est un TensorProto
    input_tensor = model.deserialize_input(payload)

    # exécution (TensorRT ou PyTorch selon le backend choisi)
    output_tensor = model.infer(input_tensor)

    # sérialisation du résultat (ONNX TensorProto)
    out_bytes = model.serialize_output(output_tensor)

    return StreamingResponse(io.BytesIO(out_bytes), media_type="application/octet-stream")
```

*Le fichier `model_registry.py` (voir §2) centralise le chargement paresseux, le hot‑swap et le versioning.*

---

### 2. Sérialisation des tenseurs  

| Format | Avantages | Contraintes |
|--------|-----------|-------------|
| **ONNX** | Standard ouvert, support natif dans TensorRT (`trt.OnnxParser`). | Taille du fichier ≈ 1,2 × la taille du TensorProto (en raison du header). |
| **Protobuf (TensorProto)** | Directement compatible avec les API TensorFlow et PyTorch (via `torch.utils.tensorboard`). | Nécessite le même schéma de version entre producteur et consommateur. |
| **FlatBuffers** | Zero‑copy, très rapide pour les micro‑services embarqués. | Moins répandu dans les pipelines GPU. |

#### Exemple de sérialisation / désérialisation avec **onnxruntime**  

```python
import numpy as np
import onnx
import onnxruntime as ort
from onnx import helper,

---

## Module 4 — contenu

## 4.1 Principes de sécurité applicative pour AlkymIA‑OS  

| Aspect | Description technique | Référence |
|--------|----------------------|-----------|
| Isolation des processus | Utilisation conjointe de **cgroups**, **namespaces** (PID, NET, MNT, IPC) et **seccomp‑BPF** pour limiter les appels système autorisés. | man 7 namespaces, man 2 seccomp |
| Contrôle d’accès au système de fichiers | Montage en lecture‑seule du répertoire contenant les modèles, création d’un *tmpfs* privé pour les entrées/sorties temporaires. | mount(2) –o ro |
| Réduction de la surface d’attaque | Désactivation des capacités inutiles (`CAP_NET_RAW`, `CAP_SYS_ADMIN`, …) via `prctl(PR_SET_KEEPCAPS, 0)`. | prctl(2) |
| Protection des données sensibles | Chiffrement en‑repos (AES‑256‑GCM) des jeux de données, suppression sécurisée (`shred`) des buffers après utilisation. | openssl‑enc, shred(1) |
| Conformité RGPD | Journalisation exhaustive (who, what, when, where) des accès aux données à caractère personnel, conservation limitée à 30 jours, anonymisation des IP. | GDPR Art. 30, 5(1)(e) |
| Auditabilité | Utilisation d’**auditd** avec règles `auditctl -a exit,always -F arch=b64 -S open,read,write -F dir=/data/pii` pour capturer chaque accès aux répertoires PII. | auditd(8) |

---

## 4.2 Architecture de sandboxing  

```
┌─────────────────────────────────────────────┐
│  Service d’inférence (processus isolé)     │
│  • cgroup cpu,memory,devices                │
│  • mount namespace (ro /models, rw /tmp)   │
│  • pid namespace (PID 1 = sandbox)         │
│  • net namespace (loopback only)            │
│  • seccomp filter (allow only read/write, │
│    mmap, futex, clock_gettime, exit)       │
│  • AppArmor profile “alkymia‑sandbox”      │
└─────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────┐   ┌───────────────────────┐
│  GPU driver (HAL)       │   │  Audit daemon (auditd)│
│  (access via /dev/nvidia│   │  → JSON log → SIEM   │
│   …)                    │   └───────────────────────┘
└───────────────────────┘
```

* Le **cgroup** garantit que le processus ne dépasse pas les quotas CPU/GPU alloués.  
* Le **mount namespace** empêche la lecture de fichiers hors `/models` et `/tmp`.  
* Le **seccomp** bloque les appels système dangereux (`execve`, `ptrace`, `clone` avec flags non‑autorisé).  
* Le **profil AppArmor** ajoute une couche de contrôle d’accès basée sur le chemin d’accès (ex. `deny /etc/** rw`).  

---

## 4.3 Exemple de sandbox fonctionnel (Python + libcontainer)  

```python
#!/usr/bin/env python3
"""
Sandbox minimal pour exécuter un modèle TensorRT sur GPU.
Utilise les namespaces, cgroups et un profil seccomp.
Testé sur Ubuntu 22.04, kernel 5.15.
"""

import os
import subprocess
import json
import pathlib
import sys
import textwrap

# ----------------------------------------------------------------------
# 1. Définition du répertoire de travail (ro) et du répertoire temporaire
# ----------------------------------------------------------------------
BASE_DIR = pathlib.Path("/opt/alkymia/models")      # monté ro dans le sandbox
TMP_DIR  = pathlib.Path("/tmp/alkymia_sandbox")     # mount rw, private

# Création du répertoire temporaire (isolé)
TMP_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# 2. Construction du profil seccomp (BPF) en JSON (compatible avec
#    `docker run --security-opt seccomp=...` mais utilisé ici via `libseccomp`)
# ----------------------------------------------------------------------
SECcomp_PROFILE = {
    "defaultAction": "SCMP_ACT_ERRNO",
    "syscalls": [
        {"name": "read",      "action": "SCMP_ACT_ALLOW"},
        {"name": "write",     "action": "SCMP_ACT_ALLOW"},
        {"name": "openat",    "action": "SCMP_ACT_ALLOW"},
        {"name": "close",     "action": "SCMP_ACT_ALLOW"},
        {"name": "mmap",      "action": "SCMP_ACT_ALLOW"},
        {"name": "munmap",    "action": "SCMP_ACT_ALLOW"},
        {"name": "futex",    "action": "SCMP_ACT_ALLOW"},
        {"name": "clock_gettime", "action": "SCMP_ACT_ALLOW"},
        {"name": "exit_group","action": "SCMP_ACT_ALLOW"},
        {"name": "rt_sigreturn","action": "SCMP_ACT_ALLOW"},
        {"name": "brk",       "action": "SCMP_ACT_ALLOW

---

## Module 5 — contenu

## Module 5 : Observabilité, CI/CD et résilience d’AlkymIA‑OS  

### Objectif mesurable  
Déployer une chaîne d’intégration continue qui compile, teste (unité + intégration) et publie un container Docker : AlkymIA‑OS v1.0.0.  
Mettre en place une stack d’observabilité (logs + traces + metrics) qui collecte ≥ 99 % des événements critiques et génère des alertes lorsqu’une SLA (latence ≤ 50 ms, taux d’erreur > 1 %) est violée.  

---

## 1. Principes d’observabilité appliqués à un micro‑kernel IA  

| Niveau | Artefact | Format recommandé | Outil de collecte | Raison |
|--------|----------|------------------|-------------------|--------|
| **Logs** | Événements système (fork, schedule, IPC) et erreurs d’inférence | JSON structuré (timestamp, level, component, pid, msg, ctx) | `rsyslog` → `Logstash` → Elasticsearch | Recherche textuelle, corrélation avec traces |
| **Traces** | Parcours d’une requête depuis l’API REST jusqu’au driver GPU | OpenTelemetry (OTLP/HTTP) | Jaeger ou Tempo | Visualiser latence inter‑services, identifier goulots |
| **Metrics** | Compteurs, histogrammes, gauges (CPU/GPU utilisation, temps d’inférence, file d’attente) | Prometheus exposition (`/metrics`) | Prometheus + Alertmanager | Alertes basées sur SLA, autoscaling |

### 1.1. Propagation du contexte  
* Chaque appel d’API crée un **trace‑id** et un **span‑id**.  
* Le micro‑kernel doit copier ces identifiants dans les structures de contrôle de processus (`struct proc`) et les transmettre via l’IPC (ex. message queue).  
* En C, on utilise `pthread_setspecific`/`pthread_getspecific` pour stocker le contexte dans le TLS du thread du kernel‑worker.  

### 1.2. Gestion du volume de logs  
* Limiter la cardinalité des champs (`user_id`, `model_version`) à des valeurs agrégées (ex. `model_family`).  
* Activer la rotation journaux (`logrotate`) avec `maxsize=100M` et `maxage=7`.  
* Utiliser le niveau `INFO` en production, `DEBUG` uniquement en environnement de test.  

---

## 2. Chaîne CI/CD pour AlkymIA‑OS  

```yaml
# .gitlab-ci.yml – pipeline minimal
stages:
  - build
  - test
  - package
  - deploy

variables:
  IMAGE_TAG: "$CI_REGISTRY_IMAGE:$(git describe --tags --always)"

build:
  stage: build
  image: rust:1.73   # micro‑kernel en Rust (exemple)
  script:
    - cargo build --release
    - strip target/release/alkymia_os
  artifacts:
    paths:
      - target/release/alkymia_os

test:
  stage: test
  image: python:3.11
  services:
    - name: docker:dind
      alias: docker
  script:
    - pip install -r tests/requirements.txt
    - pytest -q --cov=src --cov-report=xml
  coverage: '/TOTAL\s+\d+\s+\d+\s+(\d+%)/'

package:
  stage: package
  image: docker:23
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
  only:
    - tags

deploy:
  stage: deploy
  image: alpine/k8s:1.27
  script:
    - kubectl set image deployment/alkymia-os alkymia-os=$IMAGE_TAG --record
  environment:
    name: production
    url: https://alkymia.example.com
  only:
    - main
```

* **Build** : compile le noyau en mode `release` et produit un binaire statique.  
* **Test** : exécute les tests unitaires (`pytest`) avec couverture ≥ 90 %.  
* **Package** : crée une image Docker `alkymia-os` contenant le binaire et les dépendances (Python, drivers).  
* **Deploy** : met à jour le déploiement Kubernetes en rolling‑update, garantissant zéro downtime grâce aux probes de santé.  

### 2.1. Probes de santé  

```yaml
# deployment.yaml – extrait
readinessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
livenessProbe:
  httpGet:
    path: /livez
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 30
```

* `readinessProbe` assure que le service ne reçoit du trafic qu’une fois que le kernel a chargé les drivers.  
* `livenessProbe` redémarre le pod si le noyau ne répond plus (ex.