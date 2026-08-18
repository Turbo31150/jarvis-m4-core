# Construis ton AlkymIA-OS

> Référence `claude-code-mastery-m3`

## Plan

## Module 1 : Architecture du noyau et des services d’AlkymIA‑OS  
**Objectif mesurable** : Concevoir et implémenter un micro‑kernel fonctionnel avec au moins trois services (gestion de processus, planification IA, communication inter‑processus) et le valider par des tests unitaires couvrant la majeure partie du code.  

**Notions couvertes**  
- Micro‑kernel vs monolithique : principes de séparation et d’isolation.  
- Gestion des processus : création, état, tables de processus, fork/exec en contexte IA.  
- Planificateur temps réel hybride (FIFO + priorité dynamique) adapté aux charges de calcul GPU/CPU.  
- IPC (Message Queues, Shared Memory) sécurisée pour le transfert de tenseurs.  
- Abstraction des drivers matériel (GPU, TPU) via un HAL (Hardware Abstraction Layer).  

---

## Module 2 : Gestion des ressources et orchestration des charges IA  
**Objectif mesurable** : Mettre en place un ordonnanceur capable de répartir toutes les tâches IA sur les ressources CPU/GPU disponibles en respectant les exigences de service définies (latence maximale et utilisation GPU élevée).  

**Notions couvertes**  
- Modélisation des ressources (cœurs, mémoire, bande passante, VRAM).  
- Algorithmes d’allocation (bin‑packing, heuristiques de placement).  
- QoS et SLA : définition, suivi, adaptation dynamique.  
- Isolation des workloads via cgroups et namespaces Linux.  
- Collecte de métriques (Prometheus) et rétro‑action pour le scaling.  

---

## Module 3 : API et pipelines de modèles d’apprentissage automatique  
**Objectif mesurable** : Développer une API RESTful et une bibliothèque Python permettant de charger, exécuter et chaîner au moins trois modèles (CNN, Transformer, GNN) avec un temps de réponse moyen compatible avec un GPU moderne.  

**Notions couvertes**  
- Conception d’API (OpenAPI 3.0, versioning, gestion des erreurs).  
- Sérialisation des tenseurs (ONNX, protobuf) pour le transport inter‑services.  
- Gestion du cycle de vie des modèles : chargement paresseux, hot‑swap, versioning.  
- Orchestration de pipelines (Airflow, Dagster) avec support du parallélisme.  
- Optimisation inference (TensorRT, quantisation dynamique).  

---

## Module 4 : Sécurité, sandboxing et conformité des modèles  
**Objectif mesurable** : Implémenter un mécanisme de sandboxing qui empêche toute fuite de données sensibles et garantir la conformité RGPD pour toutes les requêtes traitées, vérifiable par audit de logs.  

**Notions couvertes**  
- Isolation des processus (seccomp, AppArmor, SEL

---

## Module 1 — contenu

## 1.1 Micro‑kernel vs monolithe  

| Caractéristique | Micro‑kernel | Monolithe |
|-----------------|-------------|-----------|
| Taille du noyau | petite (exemple : L4, seL4) | grande (ex. Linux) |
| Services | Exécutés en user‑space, communiquent via IPC | Intégrés dans le noyau |
| Isolation | Chaque service possède son propre espace d’adressage | Tous partagent le même espace |
| Débogage | Crash d’un service n’affecte pas le noyau | Un bug kernel peut planter tout le système |
| Overhead | IPC + context‑switch (ordre de microseconde sur x86_64) | Appel système direct (ordre de sous‑microseconde) |

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
   - Priorité initiale définie.  
   - À chaque quantum (une petite unité de temps) : la priorité est ajustée en fonction de la part de VRAM utilisée.  
   - Un coefficient est appliqué (valeur empirique).  
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
    p->priority = /* calcul basé sur VRAM utilisée */;
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
2. **Placement** : chaque tâche est affectée au premier GPU dont la mémoire libre est suffisante.  

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

*Complexité* : proportionnelle au nombre de tâches et de GPU.  

#### 2.2.2 Heuristique de placement dynamique (Score basé sur latence et utilisation)  

```python
def score_gpu(gpu, task, alpha=0.6, beta=0.4):
    """
    Retourne un score où le minimum est préféré.
    - latence estimée = task['vrm_needed'] / (gpu.mem_total - gpu.mem_used)
    - utilisation actuelle = gpu.util / 100
    """
    mem_free = gpu.mem_total - gpu.mem_used
    latency = task['vrm_needed'] / max(mem_free, 1)   # éviter division par 0
    return alpha * latency + beta * (gpu.util / 100)

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
| Latence maximale | `request_latency` (ms) | valeur définie dans les exigences de service | Prometheus `http_request_duration_seconds` |
| Utilisation GPU minimale | `gpu_util` (%) | valeur définie dans les exigences de service | Prometheus `nvidia_gpu_utilization` |
| Mémoire disponible | `gpu_mem_free` (MiB) | valeur définie dans les exigences de service | Prometheus `nvidia_gpu_memory_free` |

**Boucle de rétro‑action** (intervalle de trente secondes) :

1. Scraper Prometheus → tableau `metrics`.  
2. Si l’utilisation GPU est en dessous du seuil **et** la file d’attente contient des éléments → déclencher un scaling‑out (lancer un nouveau conteneur).  
3. Si la latence dépasse le seuil **ou** la mémoire libre est insuffisante → ré‑ordonnancer les tâches.

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
            schema