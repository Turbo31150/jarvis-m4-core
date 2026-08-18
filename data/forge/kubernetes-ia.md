# Kubernetes pour l'IA & GPU

> Référence `kubernetes-ia` · 89 €

## Plan

## Module 1 – Architecture Kubernetes adaptée aux charges IA  
**Objectif** : Identifier les composants Kubernetes requis pour exécuter des workloads IA et dimensionner un cluster GPU en fonction d’un cahier des charges donné.  
**Notions couvertes**  
- Rôles du control‑plane (etcd, API server, scheduler, controller manager) et impact sur la latence des jobs IA.  
- Types de nœuds : workers CPU vs workers GPU, labels et taints.  
- Architecture de réseau (CNI, kube‑proxy, overlay) et bande passante requise pour le transfert de modèles.  
- Stratégies de scaling (Cluster Autoscaler, GPU‑autoscaler) et seuils de déclenchement.  

## Module 2 – Provisionnement et gestion des GPU dans Kubernetes  
**Objectif** : Créer, configurer et valider un nœud GPU fonctionnel, puis exposer les ressources via les Device Plugins.  
**Notions couvertes**  
- Installation du NVIDIA GPU Operator (version compatible avec le driver NVIDIA et le runtime container).  
- Configuration du Device Plugin : `resources.limits["nvidia.com/gpu"]`, `requests` et quotas de namespace.  
- Vérification de la visibilité GPU (`kubectl describe node`, `nvidia-smi` dans le conteneur).  
- Gestion des pilotes et du runtime (CUDA 12.x, containerd‑shim‑nvidia).  

## Module 3 – Déploiement de workloads IA (TensorFlow, PyTorch, ONNX)  
**Objectif** : Déployer un job d’entraînement ou d’inférence GPU‑accelerated et mesurer le gain de performance par rapport à une exécution CPU.  
**Notions couvertes**  
- Manifestes Pod/Job avec `resources.limits["nvidia.com/gpu"]` et variables d’environnement CUDA (`CUDA_VISIBLE_DEVICES`).  
- Utilisation de `kubectl run` et de Helm charts officiels (ex. `tensorflow/tensorflow`, `pytorch/pytorch`).  
- Montage de volumes persistants (PVC, CSI) pour les datasets et checkpoints.  
- Collecte de métriques GPU via `nvidia-dcgm-exporter` et Prometheus.  

## Module 4 – Orchestration avancée : pipelines CI/CD et gestion du cycle de vie des modèles  
**Objectif** : Automatiser le build, le test et le déploiement d’un modèle IA sur un cluster GPU à l’aide de GitOps.  
**Notions couvertes**  
- Définition de workflows GitHub Actions ou GitLab CI pour créer des images Docker CUDA‑compatible.  
- Utilisation de Argo Workflows / Tekton pour orchestrer des étapes d’entraînement, de validation et de déploiement.  
- Gestion des versions de modèle avec MLflow ou DVC intégrés au cluster.  
- Rollback et canary deployment via `kubectl rollout` et `Istio` (ou Linkerd) pour le trafic d’inférence.  

## Module 5 – Sécurité, gouvernance et optimisation des coûts GPU  
**Objectif** : Appliquer les meilleures pratiques de sécurité et de contrôle budgétaire pour un cluster IA en production.  
**Notions couvertes**  
- RBAC et admission controllers (PodSecurityPolicy, OPA/Gatekeeper) pour restreindre l’accès aux GPU.  
- Isolation des workloads IA via des namespaces, quotas de ressources et `LimitRange`.

---

## Module 1 — contenu

## 1.1 Rôles du control‑plane et impact sur la latence des jobs IA  

| Composant | Fonction principale | Influence sur les jobs IA |
|-----------|--------------------|---------------------------|
| **etcd** | KV‑store fortement consistant. Stocke les objets API (Pods, Nodes, CRDs). | Un quorum (3 ou 5) avec latence < 5 ms assure que la création d’un `Job` ou `Pod` GPU est répercutée rapidement aux nœuds. Un etcd sous‑dimensionné (CPU < 2 cores, IOPS < 10 k) peut ajouter 100‑200 ms de retard à chaque planification. |
| **API Server** | Point d’entrée RESTful. Authentifie, valide, persiste les requêtes. | Le temps de réponse (latence) + temps de validation (admission controllers) + temps de persistance (etcd) = **latence de soumission**. Pour les entraînements interactifs (< 1 s de démarrage), viser < 30 ms de latence API. |
| **Scheduler** | Associe chaque Pod à un Node en fonction des contraintes (`nodeSelector`, `affinity`, `resource requests`). | Le scheduler ne considère pas la topologie GPU par défaut. Il faut activer le **GPU‑aware scheduler** (via `--feature-gates=GPUResourceScheduling=true`) pour éviter le « GPU fragmentation ». |
| **Controller‑manager** | Gère les contrôleurs (ReplicaSet, Job, CronJob, etc.). | Le `job-controller` crée les Pods d’un Job IA. Un intervalle de re‑conciliation trop long (default 10 s) retarde la relance en cas d’échec de Pod. On peut réduire `--controller-startup-timeout` à 5 s pour les workloads critiques. |

### Points de vérification rapides  

```bash
# etcd health (assume etcd v3.5+)
ETCDCTL_API=3 etcdctl endpoint health --cluster
# API server latency (average over 30 s)
kubectl get --raw='/metrics' | grep apiserver_request_duration_seconds_bucket | \
  awk '{print $2}' | sort -n | tail -1
# Scheduler queue length
kubectl get --raw='/metrics' | grep scheduler_queue_length | awk '{print $2}'
```

*Si l’un de ces indicateurs dépasse les seuils indiqués, la latence perçue par les jobs IA augmentera.*

---

## 1.2 Types de nœuds : workers CPU vs workers GPU, labels et taints  

| Type de nœud | Usage typique | Labels recommandés | Taints recommandés |
|-------------|---------------|-------------------|--------------------|
| **worker‑cpu** | Pré‑traitement, orchestration, services non‑GPU (API, UI). | `node-role.kubernetes.io/worker=cpu`<br>`kubernetes.io/arch=amd64` | `node.kubernetes.io/gpu:NoSchedule` (empêche le scheduler de placer des Pods GPU) |
| **worker‑gpu** | Entraînement, inférence, pipelines de conversion de modèles. | `node-role.kubernetes.io/worker=gpu`<br>`nvidia.com/gpu.present=true`<br>`kubernetes.io/arch=amd64` | `nvidia.com/gpu:NoSchedule` (ou `NoExecute` si vous voulez évacuer les Pods en cas de perte de GPU) |

### Exemple de `Node` manifest (appliqué via `kubectl label` / `kubectl taint`)

```yaml
# 1️⃣ Ajouter les labels au nœud GPU existant (nom: gpu-node-01)
apiVersion: v1
kind: Node
metadata:
  name: gpu-node-01
  labels:
    node-role.kubernetes.io/worker: "gpu"
    nvidia.com/gpu.present: "true"
    kubernetes.io/arch: "amd64"
---
# 2️⃣ Appliquer le taint qui empêche les pods non‑GPU d’y être planifiés
apiVersion: v1
kind: Node
metadata:
  name: gpu-node-01
spec:
  taints:
  - key: nvidia.com/gpu
    effect: NoSchedule
    # value: "true"  # optionnel, le scheduler ne regarde que la clé+effect
```

*Après application, `kubectl get nodes --show-labels` doit afficher les deux labels, et `kubectl describe node gpu-node-01 | grep -i taint` doit lister le taint.*

---

## 1.3 Architecture réseau (CNI, kube‑proxy, overlay) et bande passante requise  

| Couche | Implémentation courante | Paramètre critique pour IA |
|--------|------------------------|----------------------------|
| **CNI** | Calico (BGP), Cilium (eBPF), Flannel (VXLAN) | **MTU** : 1500 vs 9000 (jumbo frames). Les transferts de modèles (> 1 GB) bénéficient d’un MTU = 9000 et d’une bande passante ≥ 10 Gbps entre les nœuds GPU. |
| **kube‑proxy** | iptables (mode `iptables`) ou IPVS. | IPVS offre un **throughput** supérieur (≈ 2×) et une latence de connexion plus stable. Recommandé pour les services d’inférence à haute fréquence. |
| **Overlay** | VXLAN (default `flannel`

---

## Module 2 — contenu

## Module 2 – Provisionnement et gestion des GPU dans Kubernetes  

### 2.1. Prérequis système  

| Élément | Version minimale | Raison |
|--------|------------------|--------|
| **OS des nœuds** | Ubuntu 22.04 LTS (ou RHEL 8.6) | Support du driver NVIDIA 550+ et du runtime containerd‑shim‑nvidia |
| **Kubernetes** | v1.26 – v1.29 | GPU Operator utilise les API `DevicePlugin` et `NodeFeatureDiscovery` introduites depuis v1.20, mais les chartes sont testées jusqu’à v1.29 |
| **Container runtime** | containerd 1.6+ **ou** Docker 20.10+ (avec `nvidia-docker2` désactivé) | Le GPU Operator installe `nvidia-container-runtime` et configure le shim automatiquement |
| **GPU** | NVIDIA A100, V100, T4, RTX A6000, etc. | Le driver doit être compatible avec le modèle (ex. driver 550.54.15 pour A100) |
| **Accès internet** | Oui (pour télécharger les images du Operator) | Le chart hérite de `nvidia-driver` et `cuda` images publiques |

> **Vérification** : `kubectl version --short` doit renvoyer le même numéro de version pour client et serveur.  

---

### 2.2. Installation du NVIDIA GPU Operator  

Le GPU Operator regroupe driver, runtime, device‑plugin et exporter DCGM.  
Il s’installe via Helm 3 (ou `kubectl apply` d’un manifest).  

#### 2.2.1. Création du namespace dédié  

```bash
kubectl create namespace gpu-operator
```

#### 2.2.2. Ajout du repo Helm NVIDIA  

```bash
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update
```

#### 2.2.3. Valeurs de configuration essentielles  

| Clé Helm | Valeur recommandée | Explication |
|----------|-------------------|-------------|
| `driver.repository` | `nvcr.io/nvidia/driver` | Registry contenant les drivers pré‑compilés. |
| `driver.version` | `550.54.15` | Doit correspondre au driver supporté par le GPU. |
| `driver.enabled` | `true` | Active le daemonset d’installation du driver. |
| `operator.enabled` | `true` | Déploie le contrôleur qui crée les CRD. |
| `toolkit.repository` | `nvcr.io/nvidia/k8s/cuda` | Contient le runtime `nvidia-container-runtime`. |
| `toolkit.version` | `12.2.0` | CUDA 12.2, compatible avec les images TensorFlow/PyTorch officielles. |
| `dcgm.enabled` | `true` | Installe `nvidia-dcgm-exporter` pour la télémétrie. |
| `psp.enabled` | `false` | PodSecurityPolicy est obsolète depuis k8s 1.25. Utiliser OPA/Gatekeeper à la place. |

#### 2.2.4. Déploiement (exemple complet)  

```bash
helm upgrade --install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --set driver.version=550.54.15 \
  --set toolkit.version=12.2.0 \
  --set dcgm.enabled=true \
  --set driver.repository=nvcr.io/nvidia/driver \
  --set toolkit.repository=nvcr.io/nvidia/k8s/cuda \
  --wait
```

*`--wait`* bloque le CLI jusqu’à ce que tous les pods du chart soient `Ready`.  

---

### 2.3. Vérification du provisioning GPU  

#### 2.3.1. Node inspection  

```bash
kubectl get nodes -L nvidia.com/gpu.product
```

*Résultat attendu* (exemple) :

```
NAME          STATUS   ROLES    AGE   VERSION   nvidia.com/gpu.product
worker-gpu-1  Ready    <none>   12h   v1.28.2   NVIDIA-A100-SXM4-40GB
```

#### 2.3.2. Pods du GPU Operator  

```bash
kubectl -n gpu-operator get pods -o wide
```

Les pods `driver`, `device-plugin`, `dcgm-exporter` doivent être `Running`.  

#### 2.3.3. Test d’accès GPU depuis un conteneur  

```yaml
# file: gpu-test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-test
  namespace: default
spec:
  restartPolicy: Never
  containers:
  - name: cuda
    image: nvcr.io/nvidia/cuda:12.2.0-base-ubuntu22.04
    command: ["sleep"]
    args: ["infinity"]
    resources:
      limits:
        nvidia.com/gpu: 1   # demande 1 GPU
```

```bash
kubectl apply -f gpu-test-pod.yaml
kubectl wait --for=condition=Ready pod/gpu-test --timeout=60s
kubectl exec -it gpu-test -- nvidia-smi
```

*Sortie attendue* : tableau `nvidia-smi` affichant le driver 550.54.15 et le modèle GPU.  

---

### 2.4. Configuration du Device Plugin  

Le GPU Operator crée automatiquement le `DevicePlugin` `nvidia.com/gpu`.  
Toutefois, il faut paramétrer les **limits** et **requests** au niveau du pod et, si besoin, appliquer des **quotas** au niveau du namespace.

#### 2.4.1. Manifest de pod avec limites & requests  

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: tf-gpu
  namespace: ml-workloads
spec

---

## Module 3 — contenu

## Module 3 – Déploiement de workloads IA (TensorFlow, PyTorch, ONNX)

### 1. Manifestes de base pour un pod GPU

```yaml
# tensorflow-gpu-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: tf-train
  labels:
    app: tensorflow
spec:
  # Le scheduler ne place le pod que sur des nœuds possédant le label
  #   node.kubernetes.io/gpu: "true"
  nodeSelector:
    nvidia.com/gpu.product: "Tesla-V100"
  containers:
  - name: trainer
    image: tensorflow/tensorflow:2.13.0-gpu
    command: ["python", "/app/train.py"]
    # Le Device Plugin expose la ressource nvidia.com/gpu
    resources:
      limits:
        nvidia.com/gpu: 2          # demande 2 GPU
      requests:
        nvidia.com/gpu: 2
    env:
    - name: CUDA_VISIBLE_DEVICES
      value: "0,1"                 # explicite les GPU visibles dans le conteneur
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: dataset-pvc
```

* **nodeSelector** : le GPU Operator ajoute le label `nvidia.com/gpu.product` avec la valeur du modèle détecté (ex. `Tesla-V100`).  
* **resources.limits** : obligatoire pour que le Device Plugin alloue les GPU. Si `requests` est omis, le scheduler utilise `limits` comme demande.  
* **CUDA_VISIBLE_DEVICES** : le runtime NVIDIA masque les GPU non alloués. La variable doit correspondre à l’ordre d’allocation (0 = premier GPU du nœud, 1 = second, …).  

### 2. Job d’entraînement (batch) avec `kubectl run`

```bash
kubectl run tf-job \
  --image=tensorflow/tensorflow:2.13.0-gpu \
  --restart=Never \
  --limits=nvidia.com/gpu=1 \
  --env="CUDA_VISIBLE_DEVICES=0" \
  --command -- python /app/train.py \
  -- \
  --epochs=10 \
  --batch-size=128
```

* `--restart=Never` crée un **Pod** (pas de réplication).  
* Le flag `--limits` ajoute automatiquement la section `resources.limits` dans le pod manifest.  
* Le séparateur `--` indique à `kubectl` que les arguments suivants appartiennent à la commande du conteneur, pas à `kubectl` lui‑même.  

### 3. Utilisation d’un Helm chart officiel

```bash
helm repo add pytorch https://helm.pytorch.org
helm repo update
helm install my-pytorch pytorch/pytorch \
  --set image.repository=pytorch/pytorch \
  --set image.tag=2.2.0-cuda12.1-cudnn8-runtime \
  --set resources.limits.nvidia\.com/gpu=1 \
  --set nodeSelector."nvidia\.com/gpu.product"=Tesla-T4 \
  --set persistence.enabled=true \
  --set persistence.storageClass=fast-ssd \
  --set persistence.size=200Gi
```

* Le caractère `\` échappe le point (`.`) dans les clés Helm.  
* `persistence.enabled` crée un PVC nommé `my-pytorch-pvc` monté dans le conteneur sous `/workspace`.  

### 4. Montage de volumes persistants

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dataset-pvc
spec:
  storageClassName: fast-ssd      # CSI provisioner qui expose une bande passante ≥ 1 GB/s
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 500Gi
```

* **CSI** : le driver `csi-driver-nfs` ou `csi-driver-aws-ebs` expose les métriques de bande passante.  
* **ReadWriteOnce** : un seul pod à la fois peut écrire, mais plusieurs peuvent lire en mode `ReadOnlyMany` si le driver le supporte.  

### 5. Collecte de métriques GPU avec `nvidia-dcgm-exporter`

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nvidia-dcgm-exporter
  namespace: monitoring
spec:
  selector:
    matchLabels:
      name: nvidia-dcgm-exporter
  template:
    metadata:
      labels:
        name: nvidia-dcgm-exporter
    spec:
      containers:
      - name: exporter
        image: nvcr.io/nvidia/k8s/dcgm-exporter:3.2.5-ubuntu20.04
        securityContext:
          privileged: true          # DCGM a besoin d’un accès bas‑niveau au driver
        ports:
        - containerPort: 9400
          name: metrics
        volumeMounts:
        - name: dev
          mountPath: /dev
        - name: run
          mountPath: /run
      volumes:
      - name: dev
        hostPath:
          path: /dev
      - name: run
        hostPath:
          path: /run
```

* Le DaemonSet crée un exporter sur chaque nœud GPU.  
* Prometheus doit scraper `http://<node-ip>:9400/metrics`.  

### 6. Comparaison de performance CPU vs GPU

| Charge | Image Docker | CPU (2 vCPU) | GPU (1 V100) | Accélération |
|--------|--------------|--------------|--------------|--------------|
| TF ResNet‑50 (training, 10 ép.) | `tensorflow/tensorflow:2.13.0-gpu` | 2 h 12 min | 18 min | × 7,3 |
| PyTorch BERT (inférence, batch =

---

## Module 4 — contenu

## Module 4 – Orchestration avancée : pipelines CI/CD et gestion du cycle de vie des modèles  

### 4.1. Workflow GitHub Actions pour construire une image CUDA‑compatible  

```yaml
# .github/workflows/build‑push‑image.yml
name: Build & push CUDA image

on:
  push:
    branches: [ main ]
    paths:
      - 'docker/**'
      - '.github/workflows/**'
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/pytorch‑gpu
  CUDA_VERSION: "12.2.0"
  PYTHON_VERSION: "3.10"

jobs:
  build:
    runs-on: ubuntu‑22.04
    permissions:
      contents: read
      packages: write
    steps:
      - name: Checkout source
        uses: actions/checkout@v4

      - name: Set up QEMU (multi‑arch)
        uses: docker/setup-qemu-action@v3
        with:
          platforms: linux/amd64,linux/arm64

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build & push
        uses: docker/build-push-action@v5
        with:
          context: ./docker
          file: ./docker/Dockerfile
          platforms: linux/amd64
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          build-args: |
            CUDA_VERSION=${{ env.CUDA_VERSION }}
            PYTHON_VERSION=${{ env.PYTHON_VERSION }}
```

**Explications**  

| Étape | Pourquoi | Vérifiable |
|------|----------|------------|
| `setup-qemu-action` | Active l’émulation pour les architectures non‑native (ex. arm64) – utile si le registre doit servir plusieurs plateformes. | Documenté dans le README du projet QEMU. |
| `setup-buildx-action` | Crée un builder Docker capable de produire des images multi‑arch et d’utiliser le cache. | `docker buildx version` renvoie la version. |
| `docker/login-action` | Authentifie le runner auprès du registre GitHub Container Registry (GHCR). | Le token `GITHUB_TOKEN` possède le scope `write:packages`. |
| `docker/build-push-action` | Construit l’image avec les arguments `CUDA_VERSION` et `PYTHON_VERSION`, puis la pousse. | Les tags `sha` et `latest` sont créés, visibles dans le registre. |

**Pièges concrets**  

* **Version du driver NVIDIA sur le nœud** – L’image doit être construite avec le même *runtime* CUDA que le driver du nœud (ex. driver 525 + CUDA 12.2). Si le driver est plus ancien, le conteneur échouera au lancement (`CUDA driver version is insufficient`).  
* **Taille de l’image** – Un `Dockerfile` qui copie l’ensemble du répertoire `src/` avant l’installation des dépendances crée un cache inutilisable. Placez `COPY requirements.txt` avant `RUN pip install -r requirements.txt`.  
* **Secrets dans le build** – Ne jamais injecter de clés d’API via `--build-arg` ; utilisez les secrets de GitHub Actions uniquement au moment du déploiement.  

---

### 4.2. Déploiement automatisé avec Argo Workflows  

```yaml
# argo/pipeline‑train.yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: pytorch-train-
  namespace: ml‑pipeline
spec:
  entrypoint: train
  serviceAccountName: argo-workflow
  volumeClaimTemplates:
    - metadata:
        name: data-pvc
      spec:
        accessModes: [ "ReadWriteOnce" ]
        resources:
          requests:
            storage: 50Gi
  templates:
    - name: train
      steps:
        - - name: build-image
            template: kaniko
        - - name: run-training
            template: training-pod
        - - name: register-model
            template: mlflow-register

    - name: kaniko
      container:
        image: gcr.io/kaniko-project/executor:latest
        command: ["/kaniko/executor"]
        args:
          - "--context=git://{{workflow.parameters.repo_url}}#{{workflow.parameters.sha}}"
          - "--dockerfile=Dockerfile"
          - "--destination={{workflow.parameters.registry}}/{{workflow.parameters.image}}:{{workflow.parameters.sha}}"
          - "--cache=true"
      env:
        - name: DOCKER_CONFIG
          value: /kaniko/.docker/
      volumeMounts:
        - name: docker-config
          mountPath: /kaniko/.docker/
    - name: training-pod
      container:
        image: "{{workflow.parameters.registry}}/{{workflow.parameters.image}}:{{workflow.parameters.sha}}"
        resources:
          limits:
            nvidia.com/gpu: 1
        env:
          - name: CUDA_VISIBLE_DEVICES
            value: "0"
          - name: DATA_PATH
            value: "/mnt/data"
        volumeMounts:
          - name: data-pvc
            mountPath: /mnt/data
      command: ["python", "train.py"]
    - name: mlflow-register
      container:
        image: ghcr.io/mlflow/mlflow:2.12.1
        command:

---

## Module 5 — contenu

## 5.1 RBAC : contrôle d’accès granulaire aux GPU  

| Ressource | Verbe | Raison d’autoriser | Exemple de règle |
|-----------|-------|--------------------|------------------|
| `nodes`   | `get`, `list` | Lecture de la capacité GPU (et du label `nvidia.com/gpu.present`) | `apiGroups: [""]` `resources: ["nodes"]` `verbs: ["get","list"]` |
| `pods`    | `create`, `delete` | Lancer ou stopper un job GPU | `apiGroups: [""]` `resources: ["pods"]` `verbs: ["create","delete"]` |
| `pods/exec` | `create` | Debugger un conteneur GPU (ex. `kubectl exec …`) | `apiGroups: [""]` `resources: ["pods/exec"]` `verbs: ["create"]` |
| `resourcequotas` | `create` | Autoriser la création de quotas dans le namespace | `apiGroups: [""]` `resources: ["resourcequotas"]` `verbs: ["create"]` |

### 5.1.1 Définition d’un `ClusterRole` dédié aux GPU  

```yaml
# file: gpu-operator-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: gpu-job-runner
rules:
  # Lecture des nœuds GPU
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["get", "list"]
    # Filtrer sur le label GPU via un admission controller (voir 5.2)
  # Gestion des pods qui demandent des GPU
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["create", "delete", "get", "list", "watch"]
  # Exécution dans les pods (debug)
  - apiGroups: [""]
    resources: ["pods/exec"]
    verbs: ["create"]
  # Accès aux quotas de ressources
  - apiGroups: [""]
    resources: ["resourcequotas"]
    verbs: ["create", "get", "list"]
```

### 5.1.2 Binding au `ServiceAccount` de l’équipe  

```yaml
# file: gpu-namespace-binding.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: team-ml-gpu-binding
  namespace: team-ml
subjects:
  - kind: ServiceAccount
    name: ml-runner   # créé dans le namespace team-ml
    namespace: team-ml
roleRef:
  kind: ClusterRole
  name: gpu-job-runner
  apiGroup: rbac.authorization.k8s.io
```

**Piège :**  
- **Oublier le `namespace`** dans le `RoleBinding` : le binding s’applique alors au namespace par défaut, laissant le compte de service sans droits dans `team-ml`.  
- **Attribuer `cluster-admin`** à un compte de service dédié au training : cela ouvre la porte à l’escalade vers le control‑plane et à la fuite de données GPU.

---

## 5.2 Admission Controllers : blocage des pods non‑conformes  

### 5.2.1 PodSecurityPolicy (dépréciée ; à remplacer par PSP‑like via OPA)  

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: gpu-psp
spec:
  privileged: false
  volumes:
    - "configMap"
    - "secret"
    - "persistentVolumeClaim"
  allowedHostPaths: []          # interdiction d’accès direct au host
  seLinux:
    rule: RunAsAny
  runAsUser:
    rule: MustRunAsNonRoot
  supplementalGroups:
    rule: MustRunAs
    ranges:
      - min: 1000
        max: 65535
  fsGroup:
    rule: MustRunAs
    ranges:
      - min: 1000
        max: 65535
  # GPU‑specific
  allowedCapabilities: []       # pas de capabilité supplémentaire
  requiredDropCapabilities:
    - ALL
  # Force le label `nvidia.com/gpu.present=true` sur le node
  nodeSelector:
    nvidia.com/gpu.present: "true"
```

> **Note :** Depuis Kubernetes 1.25, les PSP sont retirés. La même logique doit être reproduite avec **OPA/Gatekeeper** (section 5.3).

### 5.2.2 OPA + Gatekeeper : politique d’obligation de `limits` GPU  

```yaml
# file: gpu-limit-constraint.yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: gpu-limit-required
spec:
  enforcementAction: deny
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces: ["team-ml", "research"]
  parameters: {}
---
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8srequiredgpus
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredGPUs
      validation:
        openAPIV3Schema:
          type: object
  targets:
    - target: admission.k