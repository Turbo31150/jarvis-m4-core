# IA Healthcare Multi-Agents

> Référence `ia-healthcare` · 79 €

## Plan

## Module 1 – Architecture des systèmes multi‑agents en santé  
**Objectif d’apprentissage :** Concevoir une architecture multi‑agents conforme aux normes HL7 FHIR et capable d’échanger des données patient sécurisées.  

- Modélisation des agents (acteurs, rôles, protocoles de communication).  
- Utilisation de FHIR RESTful API pour l’interopérabilité (resources Patient, Observation, CarePlan).  
- Gestion de la sécurité : OAuth 2.0, scopes, chiffrement TLS 1.3.  
- Orchestration via un broker (ex. RabbitMQ ou Apache Kafka) et pattern publish/subscribe.  


---

## Module 2 – Conception et entraînement de modèles de langage spécialisés  
**Objectif d’apprentissage :** Entraîner un modèle de langage (LLM) sur un corpus de textes médicaux et l’intégrer dans un agent de décision clinique.  

- Sélection de jeux de données (MIMIC‑III, PubMed OA, eICU) et pré‑traitement (dé‑identification, tokenisation médicale).  
- Fine‑tuning d’un LLM open‑source (ex. Llama 2 7B) avec DeepSpeed ou PEFT.  
- Évaluation de la pertinence médicale (BLEU, ROUGE, métriques de précision diagnostique).  
- Implémentation d’un système de récupération augmentée (RAG) avec vecteurs d’embeddings (FAISS).  


---

## Module 3 – Agents conversationnels pour le triage et le suivi patient  
**Objectif d’apprentissage :** Déployer un agent conversationnel capable de réaliser un triage de symptômes et de générer des recommandations conformes aux guidelines (ex. WHO, NICE).  

- Conception de flux de dialogue basés sur les standards de santé (CDS Hooks, SMART on FHIR).  
- Détection d’intentions et extraction d’entités cliniques avec spaCy + scispaCy.  
- Intégration d’un moteur de règles cliniques (Drools ou OpenCDS) pour la validation des réponses.  
- Gestion des limites de l’IA : fallback vers un professionnel, logs d’audit.  


---

## Module 4 – Monitoring, validation et conformité réglementaire  
**Objectif d’apprentissage :** Mettre en place un pipeline de suivi de performance et de conformité (GDPR, HIPAA) pour les agents en production.  

- Collecte de métriques (latence, taux d’erreur, drift du modèle) via Prometheus + Grafana.  
- Tests de robustesse (adversarial, out‑of‑distribution) et recalibrage automatisé.  
- Documentation de la chaîne de responsabilité (Data‑Protection Impact Assessment, registre des traitements).  
- Mise en œuvre du contrôle d’accès basé sur les rôles (RBAC) et journalisation immuable (blockchain ou WORM).  


---

## Module 5 – Déploiement continu et scalabilité sur le cloud  
**Objectif d’apprentissage :** Automatiser le déploiement d’une plateforme multi‑agents sur un environnement cloud (AWS, Azure ou GCP) en garantissant la scalabilité et la résilience.  

- Containerisation avec


---

## Module 1 — contenu

## 1.1 Modélisation des agents en santé  

| Élément | Description | Exemple concret |
|---------|-------------|-----------------|
| **Acteur** | Entité humaine ou logicielle qui possède un objectif métier. | *Médecin*, *Patient*, *Système de facturation*. |
| **Rôle** | Fonction attribuée à un acteur dans le scénario. | `TriageAgent`, `EHRAgent`, `AlertAgent`. |
| **Agent** | Implémentation logicielle d’un rôle, capable de percevoir, raisonner et agir. | Un micro‑service Python exposant des endpoints FHIR. |
| **Protocoles de communication** | Ensemble de messages et de séquences (ex. : FHIR REST, MQTT topics). | `GET /Patient/{id}` → `publish triage/requests`. |
| **Environnement partagé** | Broker (RabbitMQ/Kafka) + registre de services (Consul, etcd). | Tous les agents s’abonnent au topic `patient/updates`. |

**Diagramme simplifié**  

```
+----------------+      +----------------+      +----------------+
|  PatientAgent  | ---> |  Triag eAgent  | ---> |  CarePlanAgent |
+----------------+      +----------------+      +----------------+
        ^                       ^                        ^
        |                       |                        |
        |   publish/subscribe  |   publish/subscribe   |
        +-----------------------+------------------------+
                     RabbitMQ (topic exchange)
```

### 1.2 Utilisation de l’API FHIR RESTful  

*FHIR* (Fast Healthcare Interoperability Resources) définit des **ressources** (Patient, Observation, CarePlan…) accessibles via HTTP/HTTPS.  
Les conventions essentielles :  

| Méthode | URI | Action | Code HTTP |
|--------|-----|--------|------------|
| `GET` | `/Patient/{id}` | Lire un patient | `200 OK` |
| `POST` | `/Observation` | Créer une observation | `201 Created` |
| `PUT` | `/CarePlan/{id}` | Remplacer un CarePlan | `200 OK` |
| `DELETE` | `/Observation/{id}` | Supprimer | `204 No Content` |

**Headers obligatoires**  

```http
Accept: application/fhir+json
Content-Type: application/fhir+json
Authorization: Bearer <access_token>
```

### 1.3 Gestion de la sécurité  

| Composant | Rôle | Implémentation typique |
|-----------|------|------------------------|
| **OAuth 2.0** | Délivre un *access token* limité à des *scopes* (ex. `patient.read`, `observation.write`). | Authorization Server (Keycloak, Auth0) avec flux *client‑credentials* pour les agents serveur‑à‑serveur. |
| **TLS 1.3** | Chiffrement de bout en bout du canal HTTP et du broker. | Certificats X.509 signés par une CA interne ; configuration `ssl_version=TLSv1_3` dans `aiohttp` ou `paho‑mqtt`. |
| **Scopes FHIR** | Filtrage granulaire côté serveur FHIR. | `patient.read` autorise uniquement `GET /Patient/*`. |
| **Audience** | Vérifie que le token a été émis pour le service cible (`aud = "ehr-service"`). | Validation via `jwt.decode(token, key, audience="ehr-service")`. |

### 1.4 Orchestration via un broker (RabbitMQ)  

*Pattern publish/subscribe* : chaque agent publie des messages sur un **exchange** de type `topic`. Les consommateurs s’abonnent à des **routing keys** qui décrivent le domaine fonctionnel.

```text
exchange: health.events (type=topic)

routing keys:
  patient.created
  observation.new
  triage.request
  careplan.update
```

RabbitMQ garantit :  

* **Durabilité** (`delivery_mode=2`) → messages persistés sur disque.  
* **Ack/Nack** : l’agent consomme avec `basic_ack` pour éviter les pertes.  
* **QoS** (`prefetch_count=1`) : un agent ne reçoit qu’un message à la fois, limitant le back‑pressure.

### 1.5 Exemple de code complet (Python 3.11)  

> **Objectif** : Agent `Triag eAgent` qui reçoit une demande de triage (`triage.request`), interroge le serveur FHIR pour le patient, crée une `Observation` et publie le résultat (`triage.result`).  
> Technologies : `FastAPI` (exposition FHIR), `httpx` (client HTTP), `pika` (RabbitMQ), `python‑jwt` (validation OAuth).

```python
# triage_agent.py
import os
import json
import logging
from typing import Any, Dict

import httpx
import jwt  # pyjwt
import pika
from fastapi import FastAPI, Request, HTTPException, Header

# ----------------------------------------------------------------------
# 1. Configuration (variables d'environnement)
# ----------------------------------------------------------------------
FHIR_BASE   = os.getenv("FHIR_BASE", "https://ehr.example.com/fhir")
RABBIT_URL  = os.getenv("RABBIT_URL", "amqps://user:pwd@rabbitmq:5671/")
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")   # PEM
EXPECTED_AUD = "triage-agent"

# ----------------------------------------------------------------------
# 2. FastAPI – mini‑serveur FHIR (expose uniquement /metadata)
# ----------------------------------------------------------------------
app = FastAPI()


@app.get("/metadata")
async def metadata():
    """Retourne le CapabilityStatement minimal requis par le test FHIR."""
    return {


---

## Module 2 — contenu

## 2.1 Sélection et préparation du corpus médical  

| Source | Taille (records) | Licence | Particularités |
|--------|------------------|---------|----------------|
| **MIMIC‑III** | 53 k admissions | CC‑BY‑SA 4.0 (après formation) | Contient PHI – nécessite dé‑identification et accord d’accès (CITI). |
| **PubMed OA** | ~2 M abstracts | PubMed Free PMC Article Set (CC‑BY) | Texte en anglais, riche en terminologie biomédicale. |
| **eICU** | 200 k stays | CC‑BY‑NC‑SA 4.0 | Données structurées (vitals, labs). |

### 1. Dé‑identification  
```python
import re

def deidentify(text: str) -> str:
    """
    Supprime les entités PHI simples (date, numéro de dossier, nom).
    Utilise des regex basiques – à adapter selon le corpus.
    """
    # Dates (ex. 2021-03-15 ou 15/03/2021)
    text = re.sub(r'\b\d{4}[-/]\d{2}[-/]\d{2}\b', '[DATE]', text)
    # Numéros de dossier (ex. 12345678)
    text = re.sub(r'\b\d{7,9}\b', '[ID]', text)
    # Noms propres (ex. Dr. Smith)
    text = re.sub(r'\bDr\.?\s+[A-Z][a-z]+', '[PROF]', text)
    return text
```
*Piège* : les regex ne capturent pas les variantes locales (ex. « 12‑Mar‑2020 »). Utiliser **Philter** ou **MIT deid** pour un pipeline complet.

### 2. Tokenisation médicale  
```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")
# Ajout de tokens spécifiques (ex. « HbA1c », « ECG »)
new_tokens = ["HbA1c", "ECG", "CRP", "IL‑6"]
tokenizer.add_tokens(new_tokens)
```
*Piège* : ne pas mettre à jour le **embedding matrix** du modèle après l’ajout de tokens.  

```python
model.resize_token_embeddings(len(tokenizer))
```

---

## 2.2 Fine‑tuning d’un LLM open‑source  

### 2.2.1 Environnement (DeepSpeed + PEFT)  

```bash
# 1. Crée un environnement conda minimal
conda create -n llama_med python=3.10 -y
conda activate llama_med

# 2. Installe les dépendances
pip install torch==2.2.0 transformers==4.40.0 \
            accelerate==0.28.0 deepspeed==0.13.2 \
            peft==0.7.1 datasets==2.18.0
```

### 2.2.2 Jeu de données au format **jsonl**  

```json
{"prompt":"Patient: 45 ans, toux sèche depuis 3 jours. Quels diagnostics envisager ?\nAssistant:", "completion":"Les diagnostics différentiels incluent infection virale, bronchite aiguë, etc."}
```

*Piège* : **leakage** – ne jamais inclure la réponse dans le prompt d’entraînement.  

### 2.2.3 Script de fine‑tuning (PEFT LoRA)  

```python
# fine_tune_llama.py
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from peft import get_peft_model, LoraConfig, prepare_model_for_int8_training

# 1. Chargement du modèle et du tokenizer
model_name = "meta-llama/Llama-2-7b-hf"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
    load_in_8bit=True,          # économise la VRAM
)

# 2. Pré‑préparer le modèle pour l’entraînement 8‑bit
model = prepare_model_for_int8_training(model)

# 3. Config LoRA (Low‑Rank Adaptation)
lora_cfg = LoraConfig(
    r=16,               # rang
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],  # modules linéaires clés
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_cfg)

# 4. Chargement du dataset (local jsonl)
dataset = load_dataset("json", data_files={"train": "train.jsonl", "validation": "val.jsonl"})

def tokenize_fn(example):
    # concatène prompt + completion, ajoute EOS token
    tokenized = tokenizer(
        example["prompt"] + example["completion"],
        truncation=True,
        max_length=1024,
        padding="max_length",
    )
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

tokenized_ds = dataset.map(tokenize_fn, batched=True, remove_columns=dataset["train"].column_names)

# 5. Arguments d’entraînement DeepSpeed
ds_cfg = {
    "zero_optimization": {"stage": 2},
    "gradient_accumulation_steps": 4,
    "train_batch_size": 8,
    "gradient_clipping": 1


---

## Module 3 — contenu

## 3.1 Architecture fonctionnelle de l’agent de triage  

| Composant | Rôle | Interface | Norme / Librairie |
|-----------|------|-----------|-------------------|
| **Front‑end conversationnel** | Capture du texte vocal ou écrit, affichage des réponses | WebSocket / HTTP | React + BotFramework-WebChat |
| **Gateway API** | Point d’entrée unique, authentifie le client, applique le scope `triage.read` | REST (HTTPS) | FastAPI, OAuth2‑Bearer |
| **Agent Dialogue** | Orchestration du flux de dialogue (états, transitions) | Appel interne (Python) | `transitions` (state‑machine) |
| **NLP Pipeline** | Détection d’intentions, extraction d’entités cliniques | Fonction `process(text)` | spaCy + scispaCy, modèle `en_core_sci_md` |
| **Moteur de règles cliniques** | Validation des recommandations selon les guidelines | API interne `evaluate(context)` | Drools (via `jpy`), ou OpenCDS (REST) |
| **Knowledge Store (RAG)** | Recherche de documents pertinents (guidelines, articles) | Vector search `search(query, k)` | FAISS + embeddings `sentence‑transformers/biobert-base` |
| **FHIR Connector** | Lecture/écriture de ressources Patient, Observation, CarePlan | RESTful FHIR | `fhirclient` (Python) |
| **Fallback & Audit** | Redirection vers un professionnel, journalisation immuable | Kafka topic `triage.audit` | Confluent‑Kafka, log‑hash SHA‑256 |

Le diagramme d’interaction (simplifié) :

```
User → Front‑end → Gateway → Agent Dialogue
Agent Dialogue → NLP Pipeline → intent/slots
Agent Dialogue → Knowledge Store → docs
Agent Dialogue → Rules Engine → decision
Decision → FHIR Connector (création Observation/CarePlan)
Decision → Front‑end (réponse)
Decision → Audit (Kafka)
```

---

## 3.2 Construction du pipeline NLP  

```python
# fichier: nlp_pipeline.py
import spacy
import scispacy
from scispacy.linking import EntityLinker
from typing import Dict, List

# Chargement du modèle scispaCy pré‑entraîné (compatible UMLS)
nlp = spacy.load("en_core_sci_md")
# Ajout du linker UMLS (version 2023AA)
linker = EntityLinker(resolve_abbreviations=True, name="umls")
nlp.add_pipe("scispacy_linker", config={"resolve_abbreviations": True, "linker_name": "umls"})

# Intentions pré‑définies (simple dictionnaire, extensible)
INTENT_KEYWORDS = {
    "triage": ["pain", "fever", "cough", "shortness of breath", "headache"],
    "info": ["what", "how", "why"],
    "exit": ["quit", "stop", "cancel"]
}

def detect_intent(text: str) -> str:
    """Retourne l’intention la plus probable parmi les clés d'INTENT_KEYWORDS."""
    lowered = text.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(k in lowered for k in keywords):
            return intent
    return "unknown"

def extract_clinical_entities(text: str) -> List[Dict]:
    """
    Retourne une liste de dicts :
    {
        "text": "chest pain",
        "cui": "C0008031",
        "semtype": ["T047"],   # symptom
        "score": 0.92
    }
    """
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        # Le linker peut renvoyer plusieurs concepts, on garde le top‑1
        if ent._.kb_ents:
            cui, score = ent._.kb_ents[0]
            entities.append({
                "text": ent.text,
                "cui": cui,
                "semtype": ent._.umls_ents[0][1] if ent._.umls_ents else [],
                "score": score
            })
    return entities

def process(text: str) -> Dict:
    """Pipeline complète – intent + entités."""
    return {
        "intent": detect_intent(text),
        "entities": extract_clinical_entities(text)
    }

# Exemple d’utilisation
if __name__ == "__main__":
    sample = "I have a sharp chest pain and shortness of breath for 2 days."
    print(process(sample))
```

**Points de vérification**  

* Le modèle `en_core_sci_md` a été publié par AllenAI + scispaCy v0.5.1, compatible avec Python 3.9+.  
* Le linker UMLS nécessite le fichier `umls-2023AA` téléchargé via le script `scispacy download`.  
* La fonction `detect_intent` repose sur une recherche de mots‑clés ; pour une production à grande échelle, remplacer par un classifieur fine‑tuned (ex. BERT‑Clinical).  

---

## 3.3 Intégration du moteur de règles cliniques  

### 3.3.1 Drools (JVM) via `jpy`  

```python
# fichier: rules_engine.py
import jpy
from typing import Dict, Any

# Chargement du fichier .drl contenant les règles WHO‑COVID‑19 triage
# Exemple de règle (dans triage_rules.drl) :
# rule "Severe COVID suspicion"
# when
#   $c : ClinicalContext(symptom == "shortness of breath", duration > 3)
# then
#   $c.setRisk("high");
#   modify($c) { setRecommendation("Seek emergency care") };
# end
jvm =


---

## Module 4 — contenu

## 4.1 Collecte et visualisation des métriques d’exploitation  

### 4.1.1 Exporter Prometheus en Python  

```python
# file: agent_exporter.py
"""
Exporter Prometheus pour un agent de triage clinique.
Expose les métriques suivantes :
- request_total : nombre total de requêtes traitées (counter)
- request_duration_seconds : latence moyenne d’une requête (summary)
- model_drift_score : valeur de drift calculée par un job de recalibrage (gauge)
"""

from prometheus_client import Counter, Summary, Gauge, start_http_server
import time
import random

# Compteur incrémenté à chaque appel d’API
REQUEST_TOTAL = Counter(
    "agent_triage_requests_total",
    "Nombre total de requêtes traitées par l'agent",
    ["status"]  # success / error
)

# Summary qui calcule la moyenne, le max, le min, etc.
REQUEST_DURATION = Summary(
    "agent_triage_request_duration_seconds",
    "Durée d'exécution d'une requête de triage"
)

# Gauge mise à jour par le job de détection de drift
MODEL_DRIFT = Gauge(
    "agent_triage_model_drift_score",
    "Score de drift du modèle (stable à critique)",
    ["model_version"]
)

# Exemple de fonction métier à monitorer
@REQUEST_DURATION.time()          # décorateur qui mesure la durée
def handle_triage(payload: dict) -> dict:
    """Simule le traitement d’une requête de triage."""
    # 1. validation du payload (omise)
    # 2. appel du LLM (simulé)
    # time.sleep(random.uniform(...))   # latence variable
    # 3. génération de la réponse
    response = {"triage": "low", "advice": "surveiller 48h"}
    # 4. mise à jour du compteur
    REQUEST_TOTAL.labels(status="success").inc()
    return response

def simulate_errors():
    """Génère aléatoirement des erreurs pour illustrer le label 'error'."""
    # if random.random() < ...:   # probabilité d’erreurs
    #     REQUEST_TOTAL.labels(status="error").inc()
    #     raise RuntimeError("Erreur simulée du service")
    pass

def update_drift_score(version: str, score: float):
    """Met à jour le gauge du drift. Doit être appelée par le job de recalibrage."""
    MODEL_DRIFT.labels(model_version=version).set(score)

if __name__ == "__main__":
    # Démarrage du serveur HTTP qui expose /metrics
    start_http_server(8000)
    print("Exporter Prometheus démarré sur le port 8000")
    while True:
        try:
            handle_triage({"symptom": "cough"})
            simulate_errors()
        except Exception as e:
            # Log d’erreur minimal – le compteur d’erreur a déjà été incrémenté
            pass
        # Exemple de mise à jour du drift périodiquement
        # update_drift_score("llama2-7b-v1", ...)
        time.sleep(1)
```

**Explications**  
- `prometheus_client` crée automatiquement l’endpoint `/metrics`.  
- `Counter` doit être **monotone** ; il ne doit jamais être décrémenté.  
- `Summary` agrège automatiquement les quantiles ; pour un contrôle plus fin, préférer `Histogram`.  
- Le **label** `status` permet de distinguer les succès des erreurs dans Grafana.  
- Le `Gauge` est mis à jour par un job externe (ex. un script de détection de drift basé sur la distance de Mahalanobis entre embeddings du jeu de validation et du flux en production).  

### 4.1.2 Tableau de bord Grafana (extrait de JSON)

```json
{
  "dashboard": {
    "title": "Monitoring Agent de triage",
    "panels": [
      {
        "type": "graph",
        "title": "Requêtes par seconde",
        "targets": [
          {
            "expr": "rate(agent_triage_requests_total[1m])",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "type": "graph",
        "title": "Latence moyenne (s)",
        "targets": [
          {
            "expr": "avg(agent_triage_request_duration_seconds)",
            "legendFormat": "latence moyenne"
          }
        ]
      },
      {
        "type": "gauge",
        "title": "Score de drift du modèle",
        "targets": [
          {
            "expr": "agent_triage_model_drift_score",
            "legendFormat": "{{model_version}}"
          }
        ],
        "options": {}
      }
    ]
  }
}
```

Importez ce JSON via *Dashboard → Import* dans Grafana.  

---

## 4.2 Tests de robustesse et recalibrage automatisé  

| Type de test | Outil | Métrique clé | Seuil d’alerte (exemple) |
|--------------|-------|--------------|--------------------------|
| **Adversarial** | TextAttack (Python) | taux d’erreur sur inputs perturbés | dépasse un seuil défini |
| **Out‑of‑Distribution (OOD)** | Scikit‑learn – IsolationForest | score d’anomalie moyen | dépasse un seuil défini |
| **Drift de données** | Evidently AI | `data_drift` (p‑value) | p‑value inférieure à un seuil |
| **Drift de modèle** | Evidently AI – `model_performance` | différence de ROC‑AUC | dépasse un seuil défini |
---

## Module 5 — contenu

## Module 5 – Déploiement continu et scalabilité sur le cloud  

### 5.1 Architecture cible  

| Composant | Rôle | Technologie conseillée |
|-----------|------|------------------------|
| **Containerisation** | Isoler chaque agent (triage, RAG, règle clinique) | Docker ≥ 20.10 |
| **Orchestrateur** | Gestion du cycle de vie, scaling, tolérance aux pannes | Kubernetes (K8s) 1.27+ |
| **Gestion des chartes** | Versionner les manifests K8s, paramétrer les environnements | Helm 3 |
| **Infrastructure as Code** | Provisionner réseau, clusters, IAM, bases de données | Terraform ≥ 1.5 |
| **CI/CD** | Build, test, push d’images, déploiement automatisé | GitHub Actions / GitLab CI |
| **Observabilité** | Métriques, logs, traces | Prometheus + Grafana, Loki, OpenTelemetry |
| **Service‑mesh** | Sécuriser les appels inter‑agents, retries, circuit‑breaker | Istio 1.18 ou Linkerd 2.14 |
| **Gestion des secrets** | Stockage chiffré, rotation automatisée | AWS Secrets Manager / Azure Key Vault / GCP Secret Manager + Sealed‑Secrets |
| **Stockage persistant (si besoin)** | Historique de sessions, modèles fine‑tuned | Cloud‑SQL (PostgreSQL) ou Cloud‑Spanner, PVC avec CSI CSI‑driver |

> **Schéma simplifié**  
> ```
>   Git repo
>      │
>   CI (GitHub Actions) ──► Docker Registry (ECR/ACR/GCR)
>      │
>   Terraform (plan/apply) ──► K8s cluster (EKS/AKS/GKE)
>      │
>   Helm release (agents‑svc) ──► Pods (Docker images)
>      │
>   Istio ↔ Prometheus ↔ Grafana ↔ Loki
> ```

---

### 5.2 Containerisation des agents  

#### 5.2.1 Dockerfile minimal (Python 3.11, Llama‑2 7B, FastAPI)  

```Dockerfile
# syntax=docker/dockerfile:1.4
FROM python:3.11-slim@sha256:2c0e5e3f1c3a5b9e0d6c5b1c9e8f2a1b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f

# 1️⃣ Mettre à jour le système et installer les dépendances système requises
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# 2️⃣ Créer un user non‑root
RUN groupadd -r app && useradd -r -g app app
WORKDIR /app
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3️⃣ Copier le code source (exemple d’API FastAPI)
COPY --chown=app:app src/ . 

# 4️⃣ Exposer le port HTTP
EXPOSE 8080

# 5️⃣ Entrypoint sécurisé
USER app
ENTRYPOINT ["uvicorn"]
CMD ["main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
```

*Points de vérification*  

| Étape | Vérification |
|------|--------------|
| `FROM` | Utiliser une image digestée (sha256) pour garantir l’immuabilité. |
| `apt-get` | Nettoyer le cache (`rm -rf /var/lib/apt/lists/*`) afin de réduire la taille de l’image. |
| `useradd` | Exécuter le conteneur en non‑root pour limiter l’impact d’une compromission. |
| `requirements.txt` | Geler les versions (`pandas==2.1.3`) pour la reproductibilité. |
| `uvicorn` | `--workers` = `CPU cores` du pod (défini via `resources.limits.cpu`). |

---

### 5.3 Helm chart de base  

```yaml
# charts/agent/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "agent.fullname" . }}
  labels: {{- include "agent.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "agent.name" . }}
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "{{ .Values.service.port }}"
      labels:
        app.kubernetes.io/name: {{ include "agent.name" . }}
    spec:
      serviceAccountName: {{ include "agent.serviceAccountName" . }}
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: {{ .Values.service.port }}
          envFrom:
            - secretRef:
                name: {{ include "agent.fullname" . }}-secrets
          resources:
            limits:
              cpu: {{ .Values.resources.limits.cpu }}
              memory