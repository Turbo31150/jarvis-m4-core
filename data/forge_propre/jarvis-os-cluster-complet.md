# AlkymIA-OS — Cluster IA Complet

> Référence `jarvis-os-cluster-complet` · 149 €

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
**Objectif** : Créer, packager et déployer un modèle PyTorch 2.3 dans un pod Kubernetes, mesurer le temps de chargement et le débit sur un GPU NVIDIA A100.  
**Notions couvertes**  
- Dockerfile optimisé (multi‑stage, GPU base image nvidia/cuda).  
- Déploiement via Deployment et StatefulSet (persist‑volume claim, storage class).  
- Utilisation de KServe v0.10 pour servir le modèle (inference service, autoscaling).  
- Monitoring des métriques (Prometheus 2.48, Grafana 10, custom exporter).  
- Gestion des versions de modèle (model registry, tagging, rollback).

## Module 3 : Orchestration avancée – pipelines de données et CI/CD  
**Objectif** : Implémenter un pipeline CI/CD complet (GitLab CI, Helm v3, Argo Workflows) qui compile le code, exécute les tests unitaires et déploie automatiquement le modèle en production.  
**Notions couvertes**  
- Chart Helm paramétrable (values.yaml, hooks, post‑install).  
- Argo Workflows : définition de DAG, artefacts, secrets.  
- GitOps avec Flux CD v2 (reconciliation, drift detection).  
- Tests de charge automatisés (Locust 2.15, seuils de latence).  
- Gestion des secrets (Sealed‑Secrets, HashiCorp Vault).

## Module 4 : Sécurité et conformité des IA en production  
**Objectif** : Appliquer les politiques de sécurité (RBAC, PSP/OPA Gatekeeper) et réaliser un audit de conformité (RGPD, ISO 27001) sur le cluster.  
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
> Le *runtime* ne contient que les bibliothèques nécessaires à l’exécution, réduisant la taille de l’image et le temps de pull.

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
| GPU | `docker run --gpus all <image> nvidia-smi` doit afficher le driver du host |

### 2.1.3 Pièges fréquents  

| Symptomome | Cause probable | Remède |
|-----------|----------------|--------|
| `ImportError: libtorch_cuda.so: cannot open shared object file` | Bibliothèque CUDA manquante ou version incompatibles entre driver host et image | Utiliser la même version de CUDA que le driver (`nvidia-smi` → `CUDA Version`). |
| `OSError: [Errno 2] No such file or directory: 'libcudnn.so.8'` | Image `runtime` ne contient pas cuDNN (ou version différente) | Vérifier que le tag `cudnn8` est présent dans le FROM. |
| Temps de démarrage élevé | Chargement du modèle dans le code serveur au premier appel | Charger le modèle au démarrage du processus (module global)