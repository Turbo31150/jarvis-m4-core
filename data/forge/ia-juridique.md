# IA pour le Juridique & RGPD

> Référence `ia-juridique` · 69 €

## Plan

## Module 1 : Principes de l’IA et contraintes légales du traitement de données  
**Objectif mesurable** : L’apprenant pourra identifier les bases légales du RGPD applicables à un modèle d’apprentissage automatique et justifier le choix d’une base juridique pour un jeu de données donné.  
**Notions couvertes**  
1. Traitement de données à caractère personnel : définition et catégories (RGPD art. 4).  
2. Bases légales du traitement (consentement, intérêt légitime, exécution d’un contrat, etc.).  
3. Analyse d’impact relative à la protection des données (DPIA) – exigences et livrables.  
4. Principes de minimisation et de limitation de la conservation dans le cycle de vie d’un modèle.  
5. Documentation de conformité (registre des activités de traitement, registre des modèles IA).

---

## Module 2 : Architecture de pipelines de données conformes au RGPD  
**Objectif mesurable** : L’apprenant sera capable de concevoir, coder et tester un pipeline ETL qui intègre le masquage, la pseudonymisation ou l’anonymisation des données conformément aux exigences du RGPD.  
**Notions couvertes**  
1. Techniques de pseudonymisation et d’anonymisation (k‑anonymat, l‑diversité, t‑closeness).  
2. Gestion des consentements via des métadonnées (schema JSON‑LD, Open Consent).  
3. Utilisation de bibliothèques Python : `pandas`, `pyjanitor`, `faker`, `privacy‑preserving‑ml`.  
4. Orchestration sécurisée (Airflow, Prefect) avec chiffrement des flux (TLS, SOPS).  
5. Validation automatisée de conformité (tests unitaires + règle de conformité Scikit‑Learn‑Compliance).

---

## Module 3 : Modélisation explicable et auditabilité des algorithmes juridiques  
**Objectif mesurable** : L’apprenant pourra générer un rapport d’explicabilité (LIME/SHAP) pour un classificateur juridique et le relier aux exigences de transparence du RGPD (art. 13‑14, art. 15).  
**Notions couvertes**  
1. Méthodes d’explicabilité post‑hoc (LIME, SHAP, Anchor).  
2. Enregistrement des hyper‑paramètres, jeux de données et métriques (MLflow, DVC).  
3. Génération de “model cards” et “datasheets for datasets” selon les standards de Google et IBM.  
4. Audits de biais (disparate impact, fairness metrics).  
5. Production d’un “right‑to‑explain” API conforme aux exigences de portabilité (art. 20).

---

## Module 4 : Déploiement sécurisé et gouvernance des modèles IA en environnement juridique  
**Objectif mesurable** : L’apprenant pourra déployer un modèle de classification juridique dans un conteneur Docker certifié ISO 27001 et configurer les contrôles d’accès basés sur les rôles (RBAC) pour les requêtes de données.  
**Notions couvertes**  
1. Conteneurisation sécurisée (Docker, Docker‑Bench‑Security, images signées).  
2. Orchestration avec Kubernetes : NetworkPolicies, Secrets, Service Mesh

---

## Module 1 — contenu

## 1. Traitement de données à caractère personnel – définition et catégories (RGPD art. 4)

| Article | Définition | Exemple appliqué à l’IA juridique |
|---------|------------|-----------------------------------|
| 4(1)   | « données à caractère personnel » = toute information se rapportant à une personne physique identifiée ou identifiable. | Texte d’un jugement contenant le nom, le numéro de dossier, la date de naissance du justiciable. |
| 4(2)   | « traitement » = toute opération ou ensemble d’opérations effectuées sur des données (collecte, stockage, modification, diffusion, etc.). | Extraction de mentions de parties prenantes depuis un corpus de décisions, puis entraînement d’un modèle de classification. |
| 4(3)   | « sensible » = données révélant l’origine raciale ou ethnique, opinions politiques, convictions religieuses, santé, etc. | Décisions portant sur des motifs de discrimination. |

**Implication IA** : chaque étape du pipeline (ingestion → pré‑traitement → entraînement → inférence) constitue un traitement au sens du RGPD. Le responsable du traitement (souvent le cabinet ou l’entreprise) doit donc documenter chaque opération.

---

## 2. Bases légales du traitement

| Base juridique | Conditions d’application | Points de vigilance pour l’IA juridique |
|----------------|--------------------------|------------------------------------------|
| **Consentement** (art. 6‑1 a) | Consentement libre, spécifique, éclairé et univoque. | Le consentement doit couvrir *tous* les usages futurs (entraînement, ré‑utilisation, partage). Un consentement « pour la recherche » ne suffit pas si le modèle est commercialisé. |
| **Intérêt légitime** (art. 6‑1 f) | Nécessité d’un test d’équilibre : intérêt du responsable vs. droits/fondements de la personne. | L’intérêt légitime est rarement admis pour des données sensibles sans mesures de mitigation (pseudonymisation, limitation d’accès). |
| **Exécution d’un contrat** (art. 6‑1 b) | Traitement nécessaire à l’exécution d’un contrat auquel la personne est partie. | Utiliser les données d’un contrat client uniquement pour les services prévus dans ce contrat ; pas pour entraîner un modèle externe sans clause supplémentaire. |
| **Obligation légale** (art. 6‑1 c) | Nécessaire au respect d’une obligation juridique. | Conservation obligatoire de certains registres judiciaires (ex. : archives de décisions). |
| **Intérêt public** (art. 6‑1 e) | Autorisé pour des tâches d’intérêt public ou exercice de l’autorité publique. | Les autorités judiciaires peuvent traiter les données sans consentement, mais doivent publier une base juridique claire. |
| **Santé** (art. 9‑2 h) | Traitement nécessaire à des raisons d’intérêt public dans le domaine de la santé. | Rarement pertinent pour le droit, sauf si le modèle porte sur des dossiers médicaux liés à la responsabilité médicale. |

### 2.1. Décision d’une base juridique – démarche pas à pas

1. **Inventaire des données** : identifier chaque attribut (nom, numéro de dossier, texte de jugement, métadonnées).  
2. **Classification** : déterminer si l’attribut est sensible (art. 9).  
3. **Analyse d’usage** : définir les finalités (ex. : classification de type de contentieux).  
4. **Test d’équilibre** (si intérêt légitime) :  
   - **Bénéfice** : amélioration de la productivité juridique, réduction des coûts.  
   - **Risque** : atteinte à la vie privée, discrimination.  
   - **Mesures d’atténuation** : pseudonymisation, accès restreint, audit.  
5. **Documentation** : consigner la base juridique choisie, le test d’équilibre, les mesures de mitigation dans le registre des activités de traitement (ART 30).

---

## 3. Analyse d’impact relative à la protection des données (DPIA)

| Étape | Action concrète | Livrable |
|-------|----------------|----------|
| 1. Décrire le traitement | Diagramme de flux (data‑flow) du pipeline IA. | Diagramme + description textuelle. |
| 2. Identifier les risques | Tableau d’évaluation (probabilité × gravité). | Matrice de risques. |
| 3. Évaluer la nécessité & proportionnalité | Vérifier que chaque donnée est indispensable à la finalité. | Rapport de minimisation. |
| 4. Mesures de mitigation | Pseudonymisation, chiffrement, contrôle d’accès, audit logs. | Plan d’action détaillé. |
| 5. Consultation du DPO | Validation ou recommandation d’ajustement. | Avis du DPO signé. |
| 6. Décision | DPIA approuvée → lancement du projet ; sinon, revoir la conception. | DPIA final signé. |

**Critère de déclenchement** (art. 35) : traitement à grande échelle de catégories de données sensibles ou utilisation de nouvelles technologies (ex. : apprentissage fédéré) → DPIA obligatoire.

---

## 4. Principes de minimisation et de limitation de la conservation

| Principe | Exigence | Implémentation technique |
|----------|----------|---------------------------|
| **Minimisation** | Collecter uniquement ce qui est nécessaire. | Sélection de colonnes, suppression des métadonnées inutiles (`df.drop(columns=[…])`). |
| **Limitation de la conservation** | Définir une durée de rétention (ex. : 2 ans après la clôture du dossier). | Job de purge automatisé (Airflow DAG) qui supprime ou archive les enregistrements expirés. |
| **Exactitude** | Garantir la mise à jour

---

## Module 2 — contenu

## 2.1 Techniques de pseudonymisation et d’anonymisation  

| Technique | Objectif | Garantie RGPD | Implémentation courante (Python) |
|-----------|----------|----------------|----------------------------------|
| **k‑anonymat** | Chaque combinaison de quasi‑identifiants apparaît au moins *k* fois. | Réduction du risque de ré‑identification ; requis pour l’anonymisation « dé‑identifiée ». | `sdc.k_anonymity(df, quasi_identifiers, k=5)` (module `sdc‑kit`). |
| **l‑diversité** | Au sein de chaque groupe k‑anonyme, il existe au moins *l* valeurs distinctes pour l’attribut sensible. | Empêche l’inférence d’un attribut sensible même si le groupe est identifié. | `sdc.l_diversity(df, quasi_identifiers, sensitive, l=3)`. |
| **t‑closeness** | La distribution de l’attribut sensible dans chaque groupe k‑anonyme ne diffère pas de plus de *t* de la distribution globale (distance de Earth Mover). | Renforce la protection contre les attaques de distribution. | `sdc.t_closeness(df, quasi_identifiers, sensitive, t=0.2)`. |
| **Pseudonymisation** | Remplacement d’un identifiant direct par un pseudonyme réversible (ex. hash + sel). | Conformité si la clé de décodage est séparée et sécurisée. | `hashlib.pbkdf2_hmac('sha256', id.encode(), salt, 100_000).hex()`. |
| **Anonymisation** | Suppression ou transformation irréversible des identifiants. | Conformité si le processus est certifié irréversible (ex. suppression totale, bruit différentiel). | `diffprivlib.mechanisms.Laplace(epsilon=1.0).randomise(value)`. |

### 2.1.1 Choix de la technique  

1. **Nature du jeu de données** – Si le jeu contient uniquement des données d’entreprise (B2B) et aucun identifiant personnel, la pseudonymisation suffit.  
2. **Exigence de ré‑identification** – Si le modèle doit être ré‑entraîné avec les mêmes individus, conservez le mapping dans un coffre‑fort (ex. HashiCorp Vault) et utilisez la pseudonymisation.  
3. **Complexité du traitement** – k‑anonymat + l‑diversité sont simples à implémenter avec `pandas`; t‑closeness nécessite un calcul de distribution plus coûteux.  

---

## 2.2 Gestion des consentements via des métadonnées  

### 2.2.1 Schéma JSON‑LD de consentement  

```json
{
  "@context": "https://schema.org/",
  "@type": "Consent",
  "identifier": "consent-2024-001",
  "dateCreated": "2024-03-15",
  "hasConsent": true,
  "grantedThrough": {
    "@type": "DataProcessingAgreement",
    "name": "Analyse juridique des contrats"
  },
  "purpose": {
    "@type": "MedicalStudy",
    "name": "Modélisation de clauses de responsabilité"
  },
  "subject": {
    "@type": "Person",
    "identifier": "hashed-8f3c2a..."
  }
}
```

*Le champ `subject.identifier` doit contenir le même pseudonyme que celui utilisé dans le pipeline.*  

### 2.2.2 Intégration dans le flux ETL  

```python
def load_consent_metadata(path: str) -> dict:
    """Lit le fichier JSON‑LD et renvoie le dictionnaire."""
    import json, pathlib
    return json.loads(pathlib.Path(path).read_text())

def filter_by_consent(df: pd.DataFrame, consent: dict) -> pd.DataFrame:
    """Ne conserve que les lignes dont le sujet a donné son consentement."""
    if not consent.get("hasConsent"):
        return pd.DataFrame(columns=df.columns)  # rien à garder
    # le pseudonyme est stocké dans consent["subject"]["identifier"]
    allowed_id = consent["subject"]["identifier"]
    return df[df["pseudonym"] == allowed_id]
```

---

## 2.3 Bibliothèques Python utiles  

| Bibliothèque | Fonction principale | Exemple d’import |
|--------------|---------------------|------------------|
| `pandas` | Manipulation tabulaire | `import pandas as pd` |
| `pyjanitor` | Nettoyage fluide (`clean_names`, `remove_columns`) | `import janitor` |
| `faker` | Génération de données factices (test) | `from faker import Faker` |
| `privacy‑preserving‑ml` | Algorithmes de ML compatibles DP (DP‑SVM, DP‑LogReg) | `from privacy_preserving_ml import DPLogisticRegression` |
| `sdc‑kit` (ou `sdv`) | k‑anonymat, l‑diversité, t‑closeness | `from sdc_kit import k_anonymity` |
| `airflow` / `prefect` | Orchestration | `from airflow import DAG` |
| `cryptography` | Chiffrement des flux (TLS, SOPS) | `from cryptography.fernet import Fernet` |

---

## 2.4 Orchestration sécurisée  

### 2.4.1 Exemple Airflow (DAG minimal)  

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import hashlib
import json

default_args = {
    "owner": "ia_rgpd",
    "depends_on_past": False,
    "retries":

---

## Module 3 — contenu

## 3.1 Méthodes d’explicabilité post‑hoc  

| Méthode | Bibliothèque | Principe | Sortie typique |
|--------|--------------|----------|----------------|
| **LIME** (Local Interpretable Model‑agnostic Explanations) | `lime` | Approxime localement le modèle par un modèle linéaire pondéré | Vecteur de poids par feature pour un échantillon |
| **SHAP** (SHapley Additive exPlanations) | `shap` | Valeurs de Shapley issues de la théorie des jeux, distribuées de façon additive | Valeur de contribution de chaque feature (positif/ négatif) |
| **Anchor** | `alibi` | Règles “if‑then” qui garantissent une précision locale > α | Ensemble de conditions (anchors) et couverture |

> **Vérifiable** : les implémentations officielles de `lime`, `shap` et `alibi` sont publiées sur PyPI (versions ≥ 0.2.0, 0.39.0, 0.7.0 respectivement) et les articles originaux (Ribeiro et al., 2016; Lundberg & Lee, 2017; Ribeiro et al., 2018) décrivent les algorithmes.

### 3.1.1 Exemple : SHAP avec un classificateur juridique  

```python
# -*- coding: utf-8 -*-
"""
Exemple complet d’explicabilité SHAP pour un classificateur de texte juridique.
Pré‑requis : scikit‑learn, transformers, shap, pandas, torch
"""

import pandas as pd
import numpy as np
import shap
import torch
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 1. Chargement d’un petit jeu de données (ex. 1 000 contrats)
df = pd.read_csv("contracts.csv")               # colonnes : text, label
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
)

# 2. Tokenizer + modèle pré‑entraîné (distilbert-base‑uncased‑fine‑tuned‑legal)
model_name = "nlpaueb/legal-bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name, num_labels=df["label"].nunique()
)

# 3. Fonction de pré‑traitement compatible avec SHAP
def preprocess(texts: list[str]) -> dict:
    """Retourne les tenseurs attendus par le modèle."""
    enc = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )
    return enc

# 4. Wrapper scikit‑learn (fit/ predict) pour réutiliser le pipeline
class LegalClassifier:
    def __init__(self, model):
        self.model = model
        self.model.eval()

    def fit(self, X, y):
        # Pas d’entraînement supplémentaire dans cet exemple
        return self

    def predict(self, X):
        enc = preprocess(X)
        with torch.no_grad():
            logits = self.model(**enc).logits
        return logits.argmax(dim=1).cpu().numpy()

    def predict_proba(self, X):
        enc = preprocess(X)
        with torch.no_grad():
            logits = self.model(**enc).logits
        probs = torch.softmax(logits, dim=1)
        return probs.cpu().numpy()

clf = LegalClassifier(model)

# 5. Évaluation rapide
y_pred = clf.predict(X_test.tolist())
print(classification_report(y_test, y_pred))

# 6. SHAP explainer – KernelExplainer (model‑agnostic, compatible GPU/CPU)
explainer = shap.KernelExplainer(
    clf.predict_proba,                     # fonction de probas
    shap.sample(X_train.tolist(), 100)    # jeu de référence (100 échantillons)
)

# 7. Sélection d’un cas d’usage (10 contrats du set test)
sample_texts = X_test.iloc[:10].tolist()
shap_values = explainer.shap_values(sample_texts, nsamples=200)

# 8. Visualisation – texte + contributions
for i, txt in enumerate(sample_texts):
    print("\n=== Contrat #{} ===".format(i + 1))
    print(txt[:200] + "…")                     # tronque pour lisibilité
    shap.initjs()
    # shap.text_plot attend une liste de tokens, on utilise le tokenizer
    tokens = tokenizer.tokenize(txt)[:512]
    shap.text_plot(
        shap.Explanation(
            values=shap_values[0][i][: len(tokens)],   # classe 0 (ex. "non conforme")
            data=tokens,
            base_values=explainer.expected_value[0],
        )
    )
```

**Commentaires clés**  

* `shap.KernelExplainer` fonctionne avec n’importe quel modèle tant que `predict_proba` renvoie un tableau `[n_samples, n_classes]`.  
* `nsamples=200` limite le nombre d’échantillons Monte‑Carlo, compromis entre précision et temps d’exécution (≈ 30 s pour 10 textes).  
* La fonction `preprocess` doit être **déterministe** : aucun `torch.manual_seed` n’est nécessaire, mais le tokeniseur doit toujours renvoyer le même découpage pour garantir la reproduct

---

## Module 4 — contenu

## 4.1 Conteneurisation sécurisée  

### 4.1.1 Dockerfile minimal conforme ISO 27001  
```dockerfile
# syntax=docker/dockerfile:1.4
FROM python:3.11-slim@sha256:0c2e5c4a0c8c5b2d2f7d1a7c5e8c1d9f0b6a3e2f5c7d8e9f1a2b3c4d5e6f7a8b   # image officielle, hash vérifié

# 1. Utilisateur non‑root
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN addgroup --gid $GROUP_ID appgroup && \
    adduser --uid $USER_ID --gid $GROUP_ID --disabled-password --gecos "" appuser

# 2. Réduction de la surface d’attaque
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgomp1 && \
    rm -rf /var/lib/apt/lists/*

# 3. Copie du code en lecture‑seule
WORKDIR /app
COPY --chown=appuser:appgroup requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appgroup src/ ./src/
RUN chmod -R 755 /app/src

# 4. Point d’entrée non‑root
USER appuser
EXPOSE 8080/tcp
ENTRYPOINT ["python", "-m", "src.main"]
```
* **ISO 27001 A.12.4.1** – « protéger les actifs contre les logiciels malveillants » : l’image est figée par son hash, aucune mise à jour dynamique n’est autorisée.  
* **Docker‑Bench‑Security** (outil CIS Docker Benchmark) signale : `USER` non‑root, `apt-get clean`, `no‑install‑recommends`.  

### 4.1.2 Signature d’image avec `cosign`  
```bash
# Génération d’une clé de signature (une seule fois)
cosign generate-key-pair

# Build et signature
docker build -t registry.example.com/legal‑clf:1.0 .
cosign sign --key cosign.key registry.example.com/legal‑clf:1.0

# Vérification en CI/CD
cosign verify --key cosign.pub registry.example.com/legal‑clf:1.0
```
* La signature garantit l’intégrité et l’authenticité de l’image lors du pull (CIS Docker Benchmark 3.5).  

### 4.1.3 Docker‑Bench‑Security – exécution automatisée  
```bash
docker run -it --net host --pid host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /etc:/etc:ro -v /usr/bin/docker:/usr/bin/docker \
  docker/docker-bench-security
```
* Le rapport doit afficher **PASS** pour les contrôles : `1.1 – Ensure a user for the container has been created`, `2.3 – Ensure that the container is not running as privileged`.  

---

## 4.2 Orchestration Kubernetes : contrôle d’accès et isolation réseau  

### 4.2.1 Manifeste RBAC minimal (Namespace `legal‑svc`)  

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: legal-svc
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: legal-svc
  name: legal-model-reader
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: legal-model-reader-binding
  namespace: legal-svc
subjects:
- kind: ServiceAccount
  name: legal-consumer
  namespace: legal-svc
roleRef:
  kind: Role
  name: legal-model-reader
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: legal-consumer
  namespace: legal-svc
```
* Seuls les pods utilisant le `ServiceAccount legal-consumer` peuvent interroger le service.  
* Conformité **ISO 27001 A.9.2.1** – contrôle d’accès basé sur le principe du moindre privilège.  

### 4.2.2 Secret Kubernetes (chiffrement au repos)  

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: legal-db-cred
  namespace: legal-svc
type: Opaque
data:
  username: bGVnYWw=          # base64('legal')
  password: c2VjcmV0cGFzcw==  # base64('secretpass')
```
* Le secret doit être stocké dans un `etcd` chiffré (`EncryptionConfiguration` du kube‑apiserver).  
* **Pitfall** : ne jamais injecter le secret dans le manifeste via `envFrom: secretRef` sans `readOnly: true` – cela crée un fichier temporaire en clair dans le conteneur.  

### 4.2.3 NetworkPolicy pour isolement du trafic  

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-except-

---

## Module 5 — contenu

## Module 5 : Surveillance, mise à jour et retrait des modèles IA en contexte juridique  

### Objectif mesurable  
L’apprenant pourra mettre en place un dispositif de monitoring continu (drift, performance, conformité) d’un modèle juridique, automatiser la génération de rapports de conformité et déclencher le retrait ou la re‑entraînement du modèle lorsqu’une condition de non‑conformité est détectée.

---

## 5.1. Concepts clés  

| Concept | Description vérifiable |
|---------|------------------------|
| **Data drift** | Variation statistique du jeu de données d’inférence par rapport à celui d’entraînement, mesurée par des tests de Kolmogorov‑Smirnov ou Wasserstein. |
| **Concept drift** | Modification du mapping input→output (ex. évolution de la jurisprudence). Détectable via une dégradation continue du score de précision ou de F1. |
| **Model monitoring stack** | Collecte de métriques (Prometheus), logs structurés (ELK/EFK), alerting (Alertmanager), tableau de bord (Grafana). |
| **Compliance drift** | Évolution des exigences légales (ex. nouvelles clauses du RGPD) qui rend le modèle non‑conforme. |
| **Retrait automatisé** | Processus CI/CD qui, à la réception d’une alerte critique, désactive le service, archive le conteneur et notifie le DPO. |
| **Versioning & lineage** | Chaque artefact (dataset, modèle, script) possède un identifiant unique (SHA‑256) stocké dans un registre (MLflow, DVC). |
| **Audit trail** | Chaîne immuable d’évènements (timestamp, acteur, action) signée (GPG) et stockée en écriture‑seule (S3 Object Lock). |

---

## 5.2. Architecture de surveillance recommandée  

```mermaid
graph TD
    A[API d’inférence] -->|requêtes| B[Side‑car Prometheus exporter]
    B --> C[Prometheus]
    C --> D[Alertmanager]
    D -->|alertes| E[GitLab CI/CD pipeline]
    E -->|trigger| F[Docker Swarm / K8s rollback]
    A --> G[Logstash]
    G --> H[Elasticsearch]
    H --> I[Grafana dashboards]
    A --> J[Kafka topic “model‑events”]
    J --> K[Stream processing (Flink) → drift detection]
    K --> L[MLflow tracking server]
```

* **Exporter** : expose `/metrics` (latence, taux d’erreur, distribution des scores).  
* **Drift detector** : job batch quotidien qui compare les statistiques du batch d’inférence (ex. moyenne des embeddings) avec le snapshot d’entraînement stocké dans MLflow.  
* **Alert rule** (Prometheus) :  

```yaml
# alert_rules.yml
groups:
  - name: model_compliance
    rules:
      - alert: DataDriftDetected
        expr: |-
          histogram_quantile(0.99, sum(rate(model_input_feature_bucket[5m])) by (le)) 
          > 1.5 * on() vector(0.8)   # seuil 80 % de la valeur d’entraînement
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Data drift > 80 % sur la feature X"
          description: "Le distribution de la feature X a changé de façon significative. Vérifier la conformité du jeu de données."
```

---

## 5.3. Exemple de code : Détection de data drift avec `scikit‑learn` et `prometheus_client`

```python
# file: drift_monitor.py
"""
Module de monitoring de data drift pour un modèle juridique.
- Charge les statistiques d’entraînement depuis MLflow (means, stds).
- Calcule les mêmes statistiques sur le batch d’inférence actuel.
- Expose une métrique Prometheus "data_drift_score".
- Envoie une alerte via Alertmanager si le score dépasse le seuil.
"""

import os
import json
import numpy as np
from prometheus_client import start_http_server, Gauge
from mlflow.tracking import MlflowClient
import requests

# -------------------------------------------------
# Configuration (variables d’environnement)
# -------------------------------------------------
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
RUN_ID = os.getenv("MLFLOW_RUN_ID")               # run d’entraînement du modèle
BATCH_PATH = os.getenv("INFERENCE_BATCH")        # CSV du batch d’inférence
ALERTMANAGER_URL = os.getenv("ALERTMANAGER_URL", "http://alertmanager:9093/api/v1/alerts")
DRIFT_THRESHOLD = float(os.getenv("DRIFT_THRESHOLD", "0.8"))

# -------------------------------------------------
# Prometheus gauge
# -------------------------------------------------
drift_gauge = Gauge(
    "data_drift_score",
    "Score de data drift (0 = aucun, 1 = drift maximal)",
    ["feature"]
)

def load_training_stats(client: MlflowClient, run_id: str) -> dict:
    """Récupère les statistiques d’entraînement stockées dans le artefact `train_stats.json`."""
    artifact_path = client.download_artifacts(run_id, "train_stats.json")
    with open(artifact_path, "r") as f:
        return json.load(f)   # {"feature_name": {"mean": ..., "std": ...}, ...}

def compute_batch_stats(csv_path: str) -> dict:
    """Calcule moyenne et écart‑type sur chaque colonne numérique du batch."""
    data = np.genfromtxt(csv_path, delimiter=",", names=True