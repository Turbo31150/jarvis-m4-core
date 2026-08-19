# Monitoring Systèmes IA

> Référence `monitoring-ia`

## Plan

## Module 1 : Architecture de monitoring pour modèles IA  
**Objectif d’apprentissage** : Concevoir et déployer une architecture de monitoring capable de collecter, stocker et visualiser les métriques d’inférence d’un modèle en production avec un taux de disponibilité élevé.  

- Points de collecte (logs, métriques, traces) selon le standard OpenTelemetry.  
- Stockage temporel avec Prometheus (scraping) et/ou InfluxDB (push).  
- Visualisation via Grafana : dashboards dynamiques et alertes basées sur des règles de seuil.  
- Intégration d’un service de découverte (Consul ou Kubernetes Service) pour la mise à jour automatique des cibles.  

## Module 2 : Métriques de performance et de qualité des modèles  
**Objectif d’apprentissage** : Implémenter un jeu de métriques de performance (latence, débit) et de qualité (précision, drift) mesurables en temps réel et automatiser leur agrégation.  

- Latence moyenne, différents percentiles, taux d’erreur HTTP ; mesure avec client‑side instrumentation.  
- Métriques de qualité : accuracy, F1, AUC calculés sur des échantillons de validation en continu.  
- Détection de concept drift : distance de Jensen‑Shannon ou KL entre distributions d’entrée.  
- Gestion de fenêtres temporelles (tumbling, sliding) pour le calcul incrémental.  

## Module 3 : Alerting et réponses automatisées  
**Objectif d’apprentissage** : Configurer des alertes basées sur des seuils statistiques et déclencher des actions correctives via des playbooks Ansible ou des fonctions serverless.  

- Règles d’alerte Prometheus : expression PromQL, seuils dynamiques (percentile‑based).  
- Notification via Alertmanager (email, Slack, webhook).  
- Playbooks Ansible : redéploiement du modèle, rollback à une version antérieure.  
- Fonctions AWS Lambda / Azure Functions pour recalibrage ou mise en pause du trafic.  

## Module 4 : Sécurité et conformité du monitoring  
**Objectif d’apprentissage** : Appliquer les exigences de sécurité (chiffrement, contrôle d’accès) et de conformité (GDPR, ISO 27001) aux pipelines de monitoring.  

- TLS / mTLS pour le transport des métriques et logs.  
- Authentification OAuth2 ou JWT pour l’accès aux API de métriques.  
- Masquage ou pseudonymisation des données sensibles dans les logs (ex. : PII).  
- Audits de conformité : journalisation des accès et conservation des traces selon les politiques de rétention.  

## Module 5 : Optimisation et scalabilité du système de monitoring  
**Objectif d’apprentissage** : Dimensionner le système de monitoring pour supporter un volume de requêtes élevé tout en maintenant un overhead CPU faible sur les services monitorés.  

- Sharding des métriques avec Prometheus Federation ou Cortex.  
- Compression de séries temporelles (Gorilla, Snappy) pour réduire l’usage disque.  
- Autoscaling des agents de collecte (Prometheus Node Exporter, Telegraf) via Kubernetes HPA.  
- Benchmarking de la charge (k6, Locust) et analyse des goulots d’étrang.

---

## Module 1 — contenu

## 1.1 Points de collecte (logs, métriques, traces) – standard OpenTelemetry  

| Type de donnée | OpenTelemetry **instrumentation** | Exporter recommandé | Exemple d’instrumentation (Python) |
|----------------|----------------------------------|--------------------|------------------------------------|
| **Logs** | `opentelemetry-sdk` + `opentelemetry-sdk-logging` | OTLP (gRPC ou HTTP) → Collector → Loki / Elasticsearch | `logger = logging.getLogger("model")` + `log_record = LogRecord(...)` |
| **Métriques** | `opentelemetry-sdk-metrics` (v1.19+) | **OTLP** → Collector → Prometheus **remote_write** ou InfluxDB **write** | `counter = Meter.create_counter("inference_requests_total")` |
| **Traces** | `opentelemetry-sdk-trace` | OTLP → Collector → Jaeger / Tempo | `tracer = trace.get_tracer(__name__)` |

*Toutes les trois dimensions partagent le même **TracerProvider** / **MeterProvider** → configuration unique dans le code.*  

### 1.1.1 Schéma de déploiement minimal  

```
+-------------------+      OTLP (gRPC)      +-------------------+      Prometheus      +-------------------+
|   Application IA  | ───────────────────► |  OpenTelemetry   | ─────────────────► |    Prometheus    |
| (FastAPI, Flask…)|   (metrics, logs,    |   Collector      |   (scrape / remote_write) |   (TSDB)       |
|                   |    traces)           |   (sidecar)       |                     |                   |
+-------------------+                      +-------------------+                     +-------------------+
        |                                                                      |
        |                                                                      ▼
        |                                                            +-------------------+
        |                                                            |      Grafana      |
        |                                                            | (dashboards,alert)|
        ▼                                                            +-------------------+
+-------------------+
|   Service Discovery|
| (Consul / K8s)    |
+-------------------+
```

*Le Collector agit comme **gateway** : il reçoit les données en OTLP, les transforme (ex. : `metrics` → `prometheus`), applique des pipelines de traitement (batch, filtrage, enrichissement).*

---

## 1.2 Stockage temporel  

### 1.2.1 Prometheus (scraping)  

* **Mode** : pull. Le serveur Prometheus interroge périodiquement les endpoints `/metrics` exposés par chaque instance d’application.  
* **Intervalle de scrape** recommandé : `15s` (balance entre fraîcheur et charge).  
* **Retention** : `15d` par défaut ; configurable via `--storage.tsdb.retention.time`.  

#### Exemple de configuration `prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 30s

scrape_configs:
  - job_name: "model_inference"
    kubernetes_sd_configs:
      - role: endpoints
    relabel_configs:
      # ne garder que les pods portant le label app=model
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: model
        action: keep
    metric_relabel_configs:
      # supprimer les métriques à haute cardinalité (ex. user_id)
      - source_labels: [__name__]
        regex: ".*_by_user_.*"
        action: drop
```

### 1.2.2 InfluxDB (push)  

* **Mode** : push via le protocole **Line Protocol** ou le client HTTP `/api/v2/write`.  
* **Avantage** : les agents qui ne peuvent pas être scrappés (ex. : fonctions serverless) peuvent pousser leurs métriques.  
* **Retention policy** : `autogen` avec `duration = 30d`.  

#### Exemple d’écriture depuis le Collector (OTLP → InfluxDB)

```yaml
exporters:
  influxdb:
    endpoint: http://influxdb:8086
    token: ${INFLUX_TOKEN}
    organization: myorg
    bucket: model_metrics
    timeout: 10s
    headers:
      "Content-Type": "application/octet-stream"
```

---

## 1.3 Visualisation avec Grafana  

* **Datasource** : `Prometheus` et/ou `InfluxDB`.  
* **Dashboard** type :  
  * **Inference latency** – histogrammes `http_request_duration_seconds_bucket`.  
  * **Throughput** – `rate(inference_requests_total[1m])`.  
  * **Error rate** – `sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m]))`.  
  * **Drift** – métrique personnalisée `input_distribution_jsd`.  

### 1.3.1 Exemple de panel (JSON) – latence p95  

```json
{
  "type": "graph",
  "title": "Latence 95e percentile",
  "targets": [
    {
      "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
      "legendFormat": "p95",
      "refId": "A"
    }
  ],
  "datasource": "Prometheus",
  "yaxes": [
    { "format": "s", "label": "seconds" },
    { "format": "short" }
  ]
}
```

---

## 1.4 Intégration du service de



---

## Module 2 — contenu

## 2.1 Métriques de performance d’inférence  

| Métrique | Formule | Source de mesure | Granularité recommandée |
|----------|---------|------------------|------------------------|
| **Latence moyenne** | `mean(latency_ms)` | Temps entre réception de la requête HTTP et renvoi du corps de réponse | granularité adaptée |
| **p95 / p99 latence** | `percentile(latency_ms, 0.95)` | Même source que ci‑dessus | granularité adaptée |
| **Débit (RPS)** | `count(requests) / interval` | Compteur d’appels HTTP | granularité adaptée |
| **Taux d’erreur HTTP** | `sum(errors) / sum(requests)` | `errors = status >= 500` | granularité adaptée |

> **Vérifiable** : les métriques ci‑dessus sont exposées par le standard OpenTelemetry / Prometheus client.  

### 2.1.1 Instrumentation client‑side (Python)

```python
# file: monitoring.py
from prometheus_client import Counter, Histogram, start_http_server
import time
import random

# Compteurs
REQUESTS = Counter(
    "model_requests_total",
    "Nombre total de requêtes d’inférence",
    ["model_name", "status_code"]
)

# Histogramme de latence (en ms) avec buckets adaptés aux SLA
LATENCY = Histogram(
    "model_inference_latency_ms",
    "Latence d’inférence en millisecondes",
    ["model_name"],
    buckets=[]  # à configurer selon les exigences de service
)

def infer(payload):
    """Fonction d’inférence factice – à remplacer par le vrai modèle."""
    start = time.time()
    # Simuler temps de calcul et erreurs aléatoires
    time.sleep(random.random())
    if random.random() < 0.0:  # probabilité d’erreur à configurer
        status = 500
        result = None
    else:
        status = 200
        result = {"prediction": random.choice([0, 1])}
    # Enregistrement des métriques
    elapsed_ms = (time.time() - start) * 1000
    LATENCY.labels(model_name="spam_detector").observe(elapsed_ms)
    REQUESTS.labels(model_name="spam_detector", status_code=str(status)).inc()
    return result, status

if __name__ == "__main__":
    # Expose /metrics sur le port configurable
    start_http_server(8000)
    while True:
        infer({"text": "example"})   # boucle de test
```

*Le serveur expose `http://localhost:8000/metrics` au format texte Prometheus.*  

### 2.1.2 Points de vigilance  

| Risque | Symptom | Remède |
|--------|---------|--------|
| **Cardinalité explosive** (ex. label `user_id`) | Explosion du nombre de séries temporelles, OOM du serveur Prometheus | N’utiliser que des labels à faible cardinalité ; agrégations côté client si besoin. |
| **Métriques manquantes** (instrumentation oubliée) | Gaps dans les dashboards, alertes qui ne se déclenchent jamais | Automatiser le test d’exposition (`curl http://.../metrics`) dans le pipeline CI. |
| **Synchronisation d’horloge** | Latence affichée négative ou incohérente | Activer NTP/chrony sur tous les nœuds, ou injecter un `timestamp` explicite dans les métriques push. |
| **Biais de mesure** (payload trop petit) | Latence sous‑estimée | Simuler des charges réalistes, inclure le temps de désérialisation et de pré‑traitement. |

---

## 2.2 Métriques de qualité du modèle en continu  

### 2.2.1 Calcul incrémental d’accuracy, F1, AUC  

Les métriques de classification sont agrégées sur une **fenêtre glissante** afin d’éviter le stockage complet du jeu de validation.  

```python
# file: quality.py
import collections
import numpy as np
from sklearn.metrics import f1_score, roc_auc_score

# Structure de stockage : deque de taille fixe (à configurer)
WINDOW_SIZE = None  # définir la taille de fenêtre souhaitée
window = collections.deque(maxlen=WINDOW_SIZE)

def update_quality(y_true, y_pred_proba):
    """
    Ajoute un nouveau couple (vérité, probabilité) et renvoie les métriques
    sur la fenêtre actuelle.
    """
    window.append((y_true, y_pred_proba))
    if len(window) < 2:               # besoin d'au moins deux points pour AUC
        return None

    y_true_arr = np.fromiter((t[0] for t in window), dtype=int)
    y_score_arr = np.fromiter((t[1] for t in window), dtype=float)

    y_pred_arr = (y_score_arr >= 0.5).astype(int)

    acc = (y_pred_arr == y_true_arr).mean()
    f1 = f1_score(y_true_arr, y_pred_arr, zero_division=0)
    auc = roc_auc_score(y_true_arr, y_score_arr)

    return {"accuracy": acc, "f1": f1, "auc": auc}
```

*Le `deque` garantit O(1) pour l’ajout et la suppression d’éléments, évitant un coût mémoire linéaire.*  

### 2.2.2

---

## Module 3 — contenu

## 3.1 Alertes Prometheus – définition et bonnes pratiques  

| Élément | Description vérifiable | Exemple de syntaxe |
|--------|------------------------|--------------------|
| **Rule file** | Fichier YAML chargé par le serveur Prometheus (`prometheus.yml` → `rule_files`). | `rule_files: - "alert_rules.yml"` |
| **Expression** | Requête PromQL qui renvoie une série booléenne (1 = alerte, 0 = OK). | `sum(rate(http_requests_total{job="model-serving",code=~"5.."}[5m])) / sum(rate(http_requests_total{job="model-serving"}[5m])) > <seuil>` |
| **For** | Durée pendant laquelle la condition doit rester vraie avant de passer en état *firing*. Empêche les « flipping ». | `for: <durée>` |
| **Labels** | Metadonnées utilisées par Alertmanager (severity, service, team). | `labels: severity: critical` |
| **Annotations** | Texte affiché dans les notifications (summary, description). | `annotations: summary: "Taux d’erreur HTTP 5xx > un seuil"` |

```yaml
# alert_rules.yml
groups:
  - name: model-serving
    rules:
      - alert: HighHttp5xxRate
        expr: |
          sum(rate(http_requests_total{job="model-serving",code=~"5.."}[5m]))
          /
          sum(rate(http_requests_total{job="model-serving"}[5m])) > <seuil>
        for: <durée>
        labels:
          severity: critical
          service: model-serving
        annotations:
          summary: "Taux d’erreur HTTP 5xx > un seuil sur le service de modèle"
          description: |
            Le service {{ $labels.service }} génère plus d’un seuil d’erreurs 5xx sur les
            dernières minutes (actuel : {{ $value | printf \"%.2f\" }}).
```

### Pièges courants  

| Symptomome | Cause typique | Remède |
|------------|---------------|--------|
| Alertes qui s’enclenchent puis disparaissent en quelques secondes | `for` trop court ou métrique bruitée | Augmenter la durée `for` ou appliquer un `rate(...[5m])` plus large |
| Alerte qui ne se déclenche jamais malgré un problème visible | Labels manquants ou incohérents entre Prometheus et Alertmanager | Vérifier que les mêmes `job`/`instance` apparaissent dans les deux configurations |
| Alertmanager envoie plusieurs copies du même message | Routes dupliquées ou `group_by` trop large | Restreindre `group_by: ['alertname', 'service']` et consolider les `repeat_interval` |
| Saturation du serveur Prometheus lors du scraping | Interrogations `rate(...[1m])` sur séries très haute cardinalité | Utiliser `subquery` ou `increase(...[1m])` pour réduire le nombre de points évalués |

---

## 3.2 Alertmanager – routage, silences et notifications  

```yaml
# alertmanager.yml
global:
  resolve_timeout: <durée>
  smtp_smarthost: smtp.example.com:587
  smtp_from: prometheus@example.com
  smtp_auth_username: prometheus
  smtp_auth_password: "********"

route:
  receiver: slack-notifications
  group_by: ['alertname', 'service']
  group_wait: <durée>
  group_interval: <durée>
  repeat_interval: <durée>
  routes:
    - match:
        severity: critical
      receiver: pagerduty
    - match:
        severity: warning
      receiver: email-warnings

receivers:
  - name: slack-notifications
    slack_configs:
      - api_url: https://hooks.slack.com/services/VOTRE/WEBHOOK/ICI
        channel: "#ml-ops"
        title: "{{ .CommonAnnotations.summary }}"
        text: "{{ .CommonAnnotations.description }}\nLabels: {{ .CommonLabels }}"

  - name: pagerduty
    pagerduty_configs:
      - service_key: "YOUR_PAGERDUTY_INTEGRATION_KEY"
        severity: "{{ .CommonLabels.severity }}"

  - name: email-warnings
    email_configs:
      - to: "ml-team@example.com"
        send_resolved: true
```

*Points de vigilance*  

- **`resolve_timeout`** doit être supérieur à la plus longue durée de `for` + `repeat_interval`.  
- **`group_by`** doit inclure `alertname`; sinon les alertes distinctes seront fusionnées de façon indésirable.  
- Les **webhooks** (Slack, Teams) doivent être protégés par un secret partagé ; ne jamais exposer l’URL dans un dépôt public.  

---

## 3.3 Playbooks Ansible – rollback ou redéploiement automatisé  

```yaml
# rollback_model.yml
- name: Rollback du modèle de machine learning
  hosts: model-serving
  become: true
  vars:
    target_version: "v1.3.2"   # version stable connue
  tasks:
    - name: Vérifier la version actuelle du conteneur
      command: docker inspect --format='{{ .Config.Labels.version }}' {{ inventory_hostname }}
      register: current_version
      changed_when: false

    - name: Stopper le conteneur en cours
      docker_container:
        name: "{{ inventory
```
---

## Module 4 — contenu

## 4.1 Chiffrement du transport (TLS / mTLS)

| Niveau | Objectif | Implémentation concrète |
|--------|----------|------------------------|
| **TLS** (unidirectionnel) | Garantir la confidentialité et l’intégrité des métriques/logs entre l’agent (ex. `node_exporter`, `telegraf`) et le serveur de collecte (`Prometheus`, `InfluxDB`, `Loki`). | - Générer une clé RSA 2048 bits et un certificat X.509 signé par une CA interne.<br>- Configurer le serveur : `--web.listen-address=:9090 --web.config.file=/etc/prometheus/web.yml` où `web.yml` contient `tls_server_config` avec `cert_file` et `key_file`.<br>- Configurer l’agent : `--web.listen-address=:9100 --web.tls-cert-file=/etc/node_exporter/cert.pem --web.tls-key-file=/etc/node_exporter/key.pem` (ou via `tls_config` dans le `scrape_config`). |
| **mTLS** (mutuel) | Authentifier chaque client afin d’éviter les « scrape » non‑autorisé et de lier les métriques à une identité vérifiable (utile pour l’audit). | - Sur le serveur : ajouter `tls_config: { ca_file: /etc/prometheus/ca.pem, cert_file: /etc/prometheus/server.pem, key_file: /etc/prometheus/server.key, client_auth_type: RequireAndVerifyClientCert }` dans chaque `scrape_config`.<br>- Sur chaque agent : fournir un certificat client signé par la même CA (`client_cert.pem`, `client_key.pem`). |

**Exemple de configuration `prometheus.yml` (mTLS) :**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'node_exporter'
    scheme: https                     # obligatoire avec TLS
    tls_config:
      ca_file: /etc/prometheus/ca.pem
      cert_file: /etc/prometheus/server.pem
      key_file: /etc/prometheus/server.key
      # Le serveur exigera un certificat client valide
      server_name: node-exporter.local
    static_configs:
      - targets: ['node-exporter-01:9100']
```

*Commentaire* : `server_name` doit correspondre au CN/SAN du certificat du client, sinon la validation échoue.

### Pièges courants
| Symptom | Cause probable | Remédiation |
|--------|----------------|-------------|
| `scrape` échoue avec *certificate signed by unknown authority* | La CA du client n’est pas incluse dans `ca_file` du serveur. | Ajouter le certificat de la CA à `ca_file` ou concaténer plusieurs CA. |
| Connexion refusée après rotation de certificat | Les agents continuent d’utiliser l’ancien certificat qui n’est plus reconnu. | Automatiser le rechargement (`promtool reload`) ou déployer les certificats via un `ConfigMap`/`Secret` mis à jour puis redémarrer les pods. |
| TLS handshake coûteux sur chaque scrape. | Activer le **keep‑alive** HTTP (`http_config: { idle_conn_timeout: 30s }`) ou passer à un **push‑gateway** avec authentification mTLS. |

---

## 4.2 Contrôle d’accès aux API de métriques (OAuth2 / JWT)

### 4.2.1 Modèle d’autorisation

| Ressource | Scope OAuth2 | Exemple de rôle |
|-----------|--------------|-----------------|
| `/api/v1/query` (lecture) | `metrics:read` | `monitoring_viewer` |
| `/api/v1/alerts` (gestion) | `alerts:manage` | `monitoring_operator` |
| `/loki/api/v1/query_range` (logs) | `logs:read` | `log_analyst` |

### 4.2.2 Mise en œuvre avec **Grafana** (proxy OAuth2)

1. Créer un client OAuth2 dans Keycloak (ou Azure AD) :
   - `client_id = grafana`
   - `redirect_uri = https://grafana.example.com/login/generic_oauth`
   - Scopes : `openid profile email metrics:read logs:read`
2. Configurer `grafana.ini`  :

```ini
[auth.generic_oauth]
enabled = true
name = OAuth
allow_sign_up = true
client_id = grafana
client_secret = <secret>
scopes = openid profile email metrics:read logs:read
auth_url = https://keycloak.example.com/realms/monitoring/protocol/openid-connect/auth
token_url = https://keycloak.example.com/realms/monitoring/protocol/openid-connect/token
api_url = https://keycloak.example.com/realms/monitoring/protocol/openid-connect/userinfo
role_attribute_path = contains(roles[*], 'monitoring_viewer') && 'Viewer' || contains(roles[*], 'monitoring_operator') && 'Editor' || 'Viewer'
```

3. Activer le **proxy** : toutes les requêtes `/api/prometheus/*` sont transmises avec le **Bearer** token du JWT.

### 4.2.3 Exemple de validation JWT dans **Prometheus Remote Write**

---

## Module 5 — contenu

## 5. Optimisation et scalabilité du système de monitoring  

### 5.1 Dimensionnement de la collecte – sharding et federation  

| Composant | Rôle | Paramètre clé |
|-----------|------|----------------|
| **Prometheus** (instance “edge”) | Scrape les métriques locales (Node Exporter, OpenTelemetry Collector) | `scrape_interval` |
| **Prometheus Federation** | Agrège les séries de plusieurs “edge” vers un “central” | `honor_labels: true` + `match[]` |
| **Cortex / Thanos** | Stockage à long terme et mise à l’échelle horizontale | `replication_factor` |
| **Remote Write** | Envoi asynchrone vers Cortex/Thanos | `queue_config.max_shards` |
| **Prometheus Operator** (K8s) | Gestion du lifecycle | `replicas` (statefulset) |

#### 5.1.1 Exemple de configuration Federation (prometheus.yml)  

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 30s

scrape_configs:
  - job_name: 'edge-node'
    static_configs:
      - targets: ['edge-1:9090', 'edge-2:9090', 'edge-3:9090']

remote_write:
  - url: "http://cortex-write:9009/api/v1/push"
    queue_config:
      max_shards: 8
      capacity: 2500
      max_samples_per_send: 10000

# Federation from edge to central
rule_files:
  - "federation_rules.yml"
```

```yaml
# federation_rules.yml
groups:
  - name: federation
    interval: 1m
    rules:
      - record: job:http_requests_total:sum
        expr: sum by (job) (http_requests_total)
```

*Les `remote_write` sont en mode push, ce qui évite le dépassement du quota de scrape sur le serveur central.*

### 5.2 Compression des séries temporelles  

| Algorithme | Implémentation dans Prometheus |
|-----------|-------------------------------|
| **Gorilla** (Delta‑of‑Delta) | natif, utilisé pour les blocs TSDB |
| **Snappy** (block compression) | appliqué sur chaque bloc de 2 h |
| **ZSTD (Cortex/Thanos)** | option `-storage.tsdb.compaction.max-block-duration` |

#### 5.2.1 Forcer la compression dans un `StatefulSet` Prometheus  

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: prometheus
spec:
  serviceName: prometheus
  replicas: 3
  template:
    spec:
      containers:
        - name: prometheus
          image: prom/prometheus:v2.48.0
          args:
            - "--storage.tsdb.path=/prometheus"
            - "--storage.tsdb.min-block-duration=2h"
            - "--storage.tsdb.max-block-duration=2h"
            - "--storage.tsdb.compaction.max-block-duration=2h"
            - "--storage.tsdb.retention.time=30d"
            - "--storage.tsdb.no-lockfile"
            - "--storage.tsdb.wal-compression=true"   # active Snappy sur le WAL
```

*Le paramètre `--storage.tsdb.wal-compression` active la compression Snappy du Write‑Ahead Log, réduisant le trafic réseau entre le collector et le stockage persistant.*

### 5.3 Autoscaling des agents de collecte  

| Agent | Métrique de scaling | Min/Max pods |
|------|----------------------|--------------|
| **Prometheus Node Exporter** | `cpu_utilization_percentage` | 2 / 20 |
| **Telegraf** (collecte logs) | `memory_usage_bytes` | 1 / 15 |
| **OpenTelemetry Collector** | `custom_metric:otc_queue_length` | 2 / 30 |

#### 5.3.1 HPA sur le collector (K8s)  

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: otel-collector-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: otel-collector
  minReplicas: 2
  maxReplicas: 30
  metrics:
    - type: Pods
      pods:
        metric:
          name: otc_queue_length
        target:
          type: AverageValue
          averageValue: "1000"
```

*Le collector expose `otc_queue_length` via le exporter `/metrics`. Le HPA augmente le nombre de pods dès que la file d’attente dépasse le seuil configuré, évitant la perte de points de données.*

### 5.4 Benchmarking de charge  

| Outil | Scénario | Commande de base |
|------|----------|-----------------|
| **k6** | Charge élevée sur `/metrics` (scrape) | `k6 run --vus 200 --duration 5m script.js` |
| **Locust** | Charge élevée sur endpoint d’inférence + `/metrics` | `locust -f locustfile.py --users 5000 --spawn-rate 1000` |

#### 5.4