# AlkymIA-OS — Cluster IA Complet

> Référence `jarvis-os-cluster-complet` · 149 €

## Plan

## Module 1 : Architecture et déploiement du cluster AlkymIA‑OS  
**Objectif** : Installer et configurer un cluster AlkymIA‑OS de 3 nœuds (1 maître, 2 workers) sur des VM Linux Ubuntu 20.04, vérifier le bon fonctionnement via les tests d’intégrité fournis.  
**Notions couvertes**  
- Topologie maître/worker et rôle de chaque composant (etcd, kube‑apiserver, kube‑controller‑manager, kube‑scheduler).  
- Installation automatisée avec Ansible 2.14 et scripts Bash 4.4.  
- Configuration réseau (CNI Calico v3.27, politiques de pod).  
- Gestion des certificats TLS (cert‑manager, rotation automatisée).  
- Validation du cluster (kubectl get nodes, kube‑adm token create, health‑checks).

## Module 2 : Gestion des workloads IA – conteneurs et modèles  
**Objectif** : Créer, packager et déployer un modèle PyTorch 2.3 dans un pod Kubernetes, mesurer le temps de chargement < 200 ms et le throughput > 500 req/s sur un GPU NVIDIA A100.  
**Notions couvertes**  
- Dockerfile optimisé (multi‑stage, GPU base image nvidia/cuda).  
- Déploiement via Deployment et StatefulSet (persist‑volume claim, storage class).  
- Utilisation de KServe v0.10 pour servir le modèle (inference service, autoscaling).  
- Monitoring des métriques (Prometheus 2.48, Grafana 10, custom exporter).  
- Gestion des versions de modèle (model registry, tagging, rollback).

## Module 3 : Orchestration avancée – pipelines de données et CI/CD  
**Objectif** : Implémenter un pipeline CI/CD complet (GitLab CI, Helm v3, Argo Workflows) qui compile le code, exécute les tests unitaires et déploie automatiquement le modèle en production en moins de 10 minutes.  
**Notions couvertes**  
- Chart Helm paramétrable (values.yaml, hooks, post‑install).  
- Argo Workflows : définition de DAG, artefacts, secrets.  
- GitOps avec Flux CD v2 (reconciliation, drift detection).  
- Tests de charge automatisés (Locust 2.15, seuils de latence).  
- Gestion des secrets (Sealed‑Secrets, HashiCorp Vault).

## Module 4 : Sécurité et conformité des IA en production  
**Objectif** : Appliquer les politiques de sécurité (RBAC, PSP/OPA Gatekeeper) et réaliser un audit de conformité (RGPD, ISO 27001) sur le cluster, obtenir un score ≥ 90 % sur le benchmark CIS‑Kubernetes v1.6.  
**Notions couvertes**  
- Contrôle d’accès basé sur les rôles (ClusterRole, RoleBinding).  
- Policies de pod (PodSecurityPolicy, OPA Gatekeeper constraints).  
- Chiffrement des données au repos et en transit (AES‑256, TLS 1.3).  
- Auditing (audit‑policy.yaml, log aggregation avec Loki).

---

## Module 1 — contenu

## 1. Architecture du cluster AlkymIA‑OS  

| Composant | Rôle | Processus (sur le master) | Port(s) d’écoute |
|-----------|------|--------------------------|------------------|
| **etcd** | KV store distribué, source de vérité pour l’état du cluster | `etcd` (systemd) | 2379 (client), 2380 (peer) |
| **kube‑apiserver** | Point d’entrée unique (REST) pour tous les contrôles | `kube-apiserver` (static pod) | 6443 (HTTPS) |
| **kube‑controller‑manager** | Boucle de contrôle (node, service, endpoints…) | `kube-controller-manager` (static pod) | – |
| **kube‑scheduler** | Attribution des pods aux nœuds | `kube-scheduler` (static pod) | – |
| **kubelet** | Agent node, exécute les pods | `kubelet` (systemd) | 10250 (HTTPS), 10255 (read‑only) |
| **kube‑proxy** | Règles iptables/ipvs pour le service networking | `kube-proxy` (daemonset) | – |
| **cni‑calico** | Fournit le réseau pod (IP‑per‑pod) et les policies | DaemonSet `calico-node` | 179 (BGP), 5473 (Typha) |

*Le master héberge les trois premiers composants en tant que *static pods* dans `/etc/kubernetes/manifests`. Les workers n’exécutent que `kubelet` et `kube-proxy`.*

---

## 2. Prérequis système (Ubuntu 20.04)

```bash
# Désactiver le swap (kubeadm le refuse)
sudo swapoff -a && sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Activer les modules kernel requis
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
br_netfilter
overlay
EOF
sudo modprobe br_netfilter overlay

# Configurer sysctl pour le réseau pod
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.ipv4.ip_forward                 = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF
sudo sysctl --system

# Installer les paquets de base
sudo apt-get update && sudo apt-get install -y \
    apt-transport-https ca-certificates curl gnupg lsb-release

# Ajouter le repo Kubernetes 1.28 (dernier supporté par AlkymIA‑OS)
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
cat <<EOF | sudo tee /etc/apt/sources.list.d/kubernetes.list
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF
sudo apt-get update
sudo apt-get install -y kubeadm=1.28.2-00 kubelet=1.28.2-00 kubectl=1.28.2-00
sudo apt-mark hold kubeadm kubelet kubectl
```

> **Piège :** la version de `kubeadm` doit être exactement la même que celle de `kubelet` et `kubectl`. Un désalignement entraîne l’erreur `kubelet version mismatch`.

---

## 3. Installation automatisée avec Ansible 2.14  

### 3.1 Inventaire (inventory.ini)

```ini
[master]
master01 ansible_host=10.0.0.10 ansible_user=ubuntu

[workers]
worker01 ansible_host=10.0.0.11 ansible_user=ubuntu
worker02 ansible_host=10.0.0.12 ansible_user=ubuntu

[k8s:children]
master
workers
```

### 3.2 Playbook principal (cluster.yml)

```yaml
---
- name: Provisionner le cluster AlkymIA‑OS
  hosts: all
  become: true
  vars:
    kube_version: "1.28.2-00"
    pod_network_cidr: "192.168.0.0/16"
    calico_version: "v3.27.0"
    # token généré à la volée sur le master, partagé avec les workers
    kubeadm_token: "{{ hostvars[groups['master'][0]]['kubeadm_token'] | default('') }}"

  pre_tasks:
    - name: Vérifier la présence de swap
      command: swapon --show
      register: swap_check
      changed_when: false
      failed_when: swap_check.stdout != ""

    - name: Désactiver le swap (idempotent)
      command: swapoff -a
      when: swap_check.stdout != ""

  roles:
    - role: common # installation des paquets + sysctl (voir ci‑dessous)

  tasks:
    - name: Installer kubeadm, kubelet, kubectl
      apt:
        name:
          - "kubeadm={{ kube_version }}"
          - "kubelet={{ kube_version }}"
          - "kubectl={{ kube_version }}"
        state: present
        update_cache: yes
      notify: Restart kubelet

    - name: Activer le service kubelet
      systemd:
        name: kubelet
        enabled: true
        state: started

- name: Initialise le master
  hosts: master
  become: true
  vars:
    pod_network_cidr: "192.168.0.0/16"
  tasks:
    - name: kubeadm init
      command: >-
        kubeadm init
        --pod-network-cidr={{ pod

---

## Module 2 — contenu

## 2.1 Préparer l’image Docker du modèle PyTorch  

### 2.1.1 Choix de la base CUDA  

| Version | CUDA | cuDNN | Compatibilité PyTorch 2.3 |
|--------|------|-------|---------------------------|
| `nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu20.04` | 12.1 | 8 | ✅ (PyTorch 2.3 pré‑compilé) |

> **Pourquoi la version *runtime* ?**  
> Le *runtime* ne contient que les bibliothèques nécessaires à l’exécution, réduisant la taille de l’image (~1 GB) et le temps de pull.

### 2.1.2 Dockerfile multi‑stage  

```Dockerfile
# ---------- Stage 1 – Build ----------
# Image officielle contenant les outils de compilation et les headers CUDA
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu20.04 AS builder

# Versions fixes pour la reproductibilité
ARG PYTORCH_VERSION=2.3.0
ARG TORCHVISION_VERSION=0.18.0
ARG PIP_INDEX_URL=https://pypi.org/simple

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-dev python3-pip git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip et installer les paquets PyTorch avec CUDA 12.1
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install \
    torch==${PYTORCH_VERSION}+cu121 \
    torchvision==${TORCHVISION_VERSION}+cu121 \
    --extra-index-url https://download.pytorch.org/whl/cu121

# Copie du code source du modèle (assume ./src dans le contexte de build)
WORKDIR /app
COPY src/ ./src/
COPY requirements.txt .

# Installation des dépendances Python du projet (exclut torch)
RUN python3 -m pip install -r requirements.txt

# ---------- Stage 2 – Runtime ----------
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu20.04 AS runtime

# Crée un utilisateur non‑root (sécurité)
ARG USERNAME=appuser
ARG UID=10001
RUN useradd -m -u ${UID} ${USERNAME}

# Copie uniquement les artefacts nécessaires depuis le builder
COPY --from=builder /usr/local/lib/python3.10/dist-packages/torch /usr/local/lib/python3.10/dist-packages/torch
COPY --from=builder /usr/local/lib/python3.10/dist-packages/torchvision /usr/local/lib/python3.10/dist-packages/torchvision
COPY --from=builder /app /app

# Réglage du répertoire de travail
WORKDIR /app

# Expose le port attendu par KServe (par défaut 8080)
EXPOSE 8080

# Lancement du serveur d’inférence (exemple avec FastAPI + Uvicorn)
ENTRYPOINT ["python3", "-m", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### Points de contrôle  

| Étape | Vérification |
|------|--------------|
| `builder` → `runtime` copy | Les dossiers `torch` et `torchvision` existent dans le runtime (`ls /usr/local/lib/python3.10/dist-packages/torch`) |
| Permissions | L’utilisateur `appuser` possède les droits d’exécution sur `/app` (`su appuser -c "python3 -c 'print(1)'"`) |
| Taille finale | `docker image ls` → < 1 200 Mo (runtime + dépendances) |
| GPU | `docker run --gpus all <image> nvidia-smi` doit afficher le driver du host |

### 2.1.3 Pièges fréquents  

| Symptomome | Cause probable | Remède |
|-----------|----------------|--------|
| `ImportError: libtorch_cuda.so: cannot open shared object file` | Bibliothèque CUDA manquante ou version incompatibles entre driver host et image | Utiliser la même version de CUDA que le driver (`nvidia-smi` → `CUDA Version`). |
| `OSError: [Errno 2] No such file or directory: 'libcudnn.so.8'` | Image `runtime` ne contient pas cuDNN (ou version différente) | Vérifier que le tag `cudnn8` est présent dans le FROM. |
| Temps de démarrage > 500 ms | Chargement du modèle dans le code serveur au premier appel | Charger le modèle au démarrage du processus (module global) et désactiver le *lazy loading* de PyTorch (`torch.backends.cudnn.benchmark = True`). |
| Image > 2 GB | Copie de tout le répertoire `/usr/local/lib/python3.10/dist-packages` au lieu de seulement `torch*` | Restreindre la copie aux dossiers nécessaires (voir Dockerfile). |

---

## 2.2 Déployer le modèle avec KServe  

### 2.2.1 Installation de KServe (v0.10)  

```bash
# Prérequis : cluster Kubernetes ≥ 1.24, kubectl configuré
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.10.0/kserve.yaml
# Vérifier les pods dans le namespace kserve-system
kubectl -n kserve-system get pods -w
```

### 2.2.2 Manifest `InferenceService`  

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name:

---

## Module 3 — contenu

## Module 3 – Orchestration avancée – pipelines de données et CI/CD  

### 3.1 Architecture du pipeline  

| Étape | Outil | Artefact produit | Trigger |
|------|-------|-------------------|---------|
| **Build** | `gitlab-runner` (Docker‑executor) | Image Docker `registry.example.com/project/model:<git‑sha>` | Push sur branche `feature/*` ou `main` |
| **Tests unitaires** | `gitlab-runner` (Docker‑executor) | Rapport JUnit `reports/unit.xml` | Après le build |
| **Lint & Scan** | `hadolint`, `trivy` | Rapports `hadolint.txt`, `trivy.json` | Après les tests |
| **Package Helm** | `helm` | Chart tarball `model-<version>.tgz` | Après le scan |
| **Push Helm** | `helm push` (chartmuseum) | Chart dans le repo `helm.example.com` | Après le package |
| **Argo Workflows** | `argo submit` | Artefact `model-<version>.tgz` | Après le push Helm |
| **Déploiement** | `helm upgrade --install` (via Argo) | Release `model-prod` dans le namespace `prod` | Workflow Argo |
| **Tests de charge** | `locust` (Docker) | Rapport `locust-report.html` | Post‑déploiement |
| **GitOps sync** | `flux reconcile` | État du cluster conforme au manifeste `Kustomization` | Après le workflow (optionnel) |

---

### 3.2 Fichier `.gitlab-ci.yml` complet  

```yaml
# .gitlab-ci.yml – GitLab CI/CD (v15.11)
# Variables globales
variables:
  IMAGE_REGISTRY: registry.example.com
  IMAGE_NAME: $IMAGE_REGISTRY/project/model
  HELM_REPO: https://helm.example.com
  HELM_CHART: model
  KUBE_CONTEXT: prod-cluster
  KUBE_NAMESPACE: prod
  GIT_SUBMODULE_STRATEGY: recursive
  # Secrets injectés via GitLab CI/CD variables (masked, protected)
  VAULT_ADDR: https://vault.example.com
  VAULT_ROLE_ID: $VAULT_ROLE_ID
  VAULT_SECRET_ID: $VAULT_SECRET_ID

stages:
  - build
  - test
  - scan
  - package
  - deploy
  - load-test
  - gitops

# -------------------------------------------------
# 1️⃣ Build de l’image Docker
# -------------------------------------------------
docker-build:
  stage: build
  image: docker:24.0.5
  services:
    - docker:24.0.5-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $IMAGE_REGISTRY
    - |
      docker build \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        -t $IMAGE_NAME:${CI_COMMIT_SHA:0:8} \
        -f Dockerfile .
    - docker push $IMAGE_NAME:${CI_COMMIT_SHA:0:8}
  only:
    - main
    - /^feature\/.*$/

# -------------------------------------------------
# 2️⃣ Tests unitaires (pytest + coverage)
# -------------------------------------------------
unit-test:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install -r requirements.txt -r test-requirements.txt
  script:
    - pytest --junitxml=reports/unit.xml --cov=app tests/
  artifacts:
    reports:
      junit: reports/unit.xml
    paths:
      - reports/
  only:
    - main
    - /^feature\/.*$/

# -------------------------------------------------
# 3️⃣ Analyse de sécurité (Hadolint + Trivy)
# -------------------------------------------------
security-scan:
  stage: scan
  image: aquasec/trivy:0.46.0
  before_script:
    - apk add --no-cache hadolint
  script:
    - hadolint Dockerfile > reports/hadolint.txt || true
    - trivy image --format json -o reports/trivy.json $IMAGE_NAME:${CI_COMMIT_SHA:0:8}
  artifacts:
    paths:
      - reports/
  only:
    - main
    - /^feature\/.*$/

# -------------------------------------------------
# 4️⃣ Packaging Helm (chartmuseum)
# -------------------------------------------------
helm-package:
  stage: package
  image: alpine/helm:3.13.2
  script:
    - |
      helm dependency update charts/$HELM_CHART
      helm lint charts/$HELM_CHART
      helm package charts/$HELM_CHART \
        --app-version ${CI_COMMIT_SHA:0:8} \
        --version $(git describe --tags --abbrev=0 | tr -d 'v')
    - |
      curl --data-binary "@${HELM_CHART}-$(git describe --tags --abbrev=0 | tr -d 'v').tgz" \
        $HELM_REPO/api/charts
  artifacts:
    paths:
      - ${HELM_CHART}-*.tgz
  only:
    - main
    - /^release\/.*$/

# -------------------------------------------------
# 5️⃣ Déploiement via Argo Workflows
# -------------------------------------------------
argo-deploy:
  stage: deploy
  image: argoproj/argocli:v3.5.8
  script:
    # 5.1 – Crée le workflow qui lance le helm upgrade
    - |
      cat > workflow.yaml <<'EOF'
      apiVersion: argoproj.io/v1alpha1
      kind: Workflow
      metadata:
        generateName

---

## Module 4 — contenu

## 4.1 Contrôle d’accès basé sur les rôles (RBAC)

| Ressource | API Group | Verbe | Exemple d’objet |
|-----------|-----------|------|-----------------|
| pods      | ""        | get  | `apiVersion: v1` |
| deployments| apps      | create| `apiVersion: apps/v1` |
| secrets   | ""        | list | `apiVersion: v1` |

### 4.1.1 Principes

* **Subject** : `User`, `Group` ou `ServiceAccount`.  
* **Role** : ensemble de règles (rules) limité à un namespace.  
* **ClusterRole** : même structure, appliquée à l’ensemble du cluster.  
* **RoleBinding / ClusterRoleBinding** : associe un (Cluster)Role à un (Cluster)Subject.

> **Vérifiable** : `kubectl api-resources --api-group=rbac.authorization.k8s.io` liste `roles`, `rolebindings`, `clusterroles`, `clusterrolebindings`.

### 4.1.2 Exemple fonctionnel – Limiter l’accès aux modèles

```yaml
# file: rbac/model-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role                      # limité au namespace "ml-models"
metadata:
  name: model-reader
  namespace: ml-models
rules:
- apiGroups: [""]               # core API
  resources: ["configmaps","secrets"]
  verbs: ["get","list"]
- apiGroups: ["serving.kserve.io"]
  resources: ["inferenceservices"]
  verbs: ["get","list","watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: model-reader-binding
  namespace: ml-models
subjects:
- kind: ServiceAccount
  name: inference-worker      # créé par le Deployment KServe
  namespace: ml-models
roleRef:
  kind: Role
  name: model-reader
  apiGroup: rbac.authorization.k8s.io
```

*Le ServiceAccount `inference-worker` ne pourra plus créer ou modifier de ConfigMap, ni accéder aux ressources hors du namespace.*  

**Pitfall :** Oublier le `namespace` dans le `RoleBinding` crée un binding global (ClusterRoleBinding) qui élargit les droits ; toujours vérifier `kubectl get rolebinding -n <ns>`.

---

## 4.2 Politiques de sécurité des pods (PSP → OPA Gatekeeper)

> **PSP** a été déprécié depuis Kubernetes 1.25. On utilise **OPA Gatekeeper** (v3.15+).  

### 4.2.1 Installation minimale

```bash
# 1. Installer le chart Helm officiel
helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
helm repo update
helm upgrade --install gatekeeper gatekeeper/gatekeeper \
  --namespace gatekeeper-system \
  --create-namespace \
  --set controllerManager.enabled=true \
  --set audit.enabled=true
```

*Vérifiable* : `kubectl get pods -n gatekeeper-system -l app=gatekeeper` doit afficher `gatekeeper-controller-manager`.

### 4.2.2 Contraintes de base

#### 4.2.2.1 Interdire les conteneurs root

```yaml
# file: constraints/no-root.yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sAllowedCapabilities
metadata:
  name: disallow-root
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
  parameters:
    allowedCapabilities: []          # aucune capability supplémentaire
    requiredDropCapabilities:
    - ALL
  enforcementAction: deny
```

#### 4.2.2.2 Forcer le label `team` sur chaque namespace

```yaml
# file: constraints/require-team-label.yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: namespace-team-label
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Namespace"]
  parameters:
    labels: ["team"]
  enforcementAction: dryrun   # passe en deny après validation
```

**Pitfall :** Les contraintes `dryrun` n’empêchent pas la création d’objets. Avant de passer en `deny`, exécuter `kubectl get constrainttemplate,constraint -A` pour vérifier les violations.

### 4.2.3 Audits automatisés

```bash
kubectl get constraint -A -o yaml | \
  grep -E 'status:\s*violations' -B2 -A2
```

Le champ `status.violations` indique les ressources non‑conformes. Un pipeline CI peut bloquer le merge si le nombre de violations > 0.

---

## 4.3 Chiffrement des données au repos et en transit

| Niveau | Méthode | Implémentation Kubernetes |
|--------|---------|---------------------------|
| **Transit** | TLS 1.3 | `kube-apiserver` `--tls-min-version=VersionTLS13` ; `etcd` `--peer-auto-tls` |
| **Repos**   | AES‑256‑GCM | `etcd` `--cipher-suites=TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384` + `--auto-tls` |
| **Volumes**| Encryption at Rest (EBS‑encrypted, CSI‑Encryption) | `storageclass` avec `encrypted: true` ou CSI driver `secrets-store-csi-driver` + `encryptionKey` |

### 4.3.1 Exemple – CSI Encryption avec `secrets-store-csi-driver`

```yaml
# file: csi/encrypted-pvc.yaml
apiVersion: storage.k8s.io/v1
kind: Storage

---

## Module 5 — contenu

## Module 5 : Observabilité avancée & optimisation des performances IA

### 5.1 Traçage distribué avec OpenTelemetry

| Étape | Action | Détails vérifiables |
|------|--------|----------------------|
| 5.1.1 | Installer les dépendances | `pip install opentelemetry-sdk opentelemetry-instrumentation-flask opentelemetry-exporter-otlp` (versions ≥ 1.22.0) |
| 5.1.2 | Configurer l’exporter OTLP vers le collector | `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317` |
| 5.1.3 | Instrumenter l’application Flask | Voir le code complet § 5.2 |
| 5.1.4 | Déployer le **OpenTelemetry Collector** en mode **gateway** (image `otel/opentelemetry-collector-contrib:0.98.0`) avec le pipeline `receivers: otlp`, `exporters: prometheus, logging`, `processors: batch` |
| 5.1.5 | Vérifier la présence de traces dans Grafana Tempo (ou Jaeger) | `curl -s http://tempo:3200/api/traces?serviceName=ml-inference` doit retourner un JSON non‑vide |

#### Pièges courants
* **Conflit de ports** : le collector expose le port 4317 (gRPC) ; assurez‑vous que le service Kubernetes ne le mappe pas ailleurs.
* **Propagation du contexte** : si vous lancez des sous‑processus (ex. `torch.multiprocessing`), le contexte OpenTelemetry ne se transmet pas automatiquement ; utilisez `opentelemetry.instrumentation.subprocess`.
* **Overhead de sérialisation** : désactivez le **batch processor** en phase de test de charge pour éviter la latence supplémentaire due au buffer.

---

### 5.2 Exemple complet : Service d’inférence Flask avec traçage & métriques GPU

```python
# file: app.py
"""
Inference service exposing:
- /predict  : POST JSON {"input": [...]} → tensor → modèle PyTorch
- /metrics  : Prometheus exporter (GPU utilisation + latence)
Traçage OpenTelemetry vers le Collector OTLP.
"""

import os
import time
from flask import Flask, request, jsonify
import torch
import torch.nn as nn
import numpy as np

# ---------- OpenTelemetry ----------
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

resource = Resource(attributes={"service.name": "ml-inference"})
trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
tracer = trace.get_tracer(__name__)

# ---------- Prometheus ----------
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    "ml_inference_requests_total",
    "Total number of inference requests",
    ["method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "ml_inference_request_latency_seconds",
    "Latency of inference requests",
    ["endpoint"]
)
GPU_UTIL = Gauge(
    "ml_gpu_utilization_percent",
    "GPU utilisation as reported by nvidia-smi"
)

# ---------- Model ----------
class SimpleNet(nn.Module):
    def __init__(self, in_features=10, hidden=32, out_features=1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden),
            nn.ReLU(),
            nn.Linear(hidden, out_features)
        )
    def forward(self, x):
        return self.net(x)

model = SimpleNet()
model.eval()
# Charger le poids pré‑entraîné (exemple)
model_path = "/models/simplenet.pt"
if os.path.isfile(model_path):
    model.load_state_dict(torch.load(model_path, map_location="cpu"))

# ---------- Flask ----------
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)   # <-- injection du middleware OpenTelemetry

def _update_gpu_metrics():
    """Appel léger à nvidia‑smi, parse le pourcentage d’utilisation."""
    try:
        out = os.popen("nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits").read()
        util = float(out.strip().split("\n")[0])
        GPU_UTIL.set(util)
    except Exception:
        GPU_UTIL.set(0.0)

@app.route("/predict", methods=["POST"])
def predict():
    start = time.time()
    REQUEST_COUNT.labels(method="POST", endpoint="/predict", http_status=200).inc()
    payload = request.get_json(force=True)
    data = torch.tensor(payload["input"], dtype=torch.float32)
    with torch.no_grad():
        out = model(data).numpy().tolist()
    latency = time.time() - start
    REQUEST_LATENCY.labels(endpoint="/predict").observe(latency)
    _update_gpu_metrics()
    return jsonify({"output": out})

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__