# AlkymIA-OS v17 — Architecture Complète

> Référence `jarvis-architecture` · 129 €

## Plan

## Module 1 – Présentation de l’architecture d’AlkymIA‑OS v17  
**Objectif mesurable** : Être capable de dessiner le diagramme de composants d’AlkymIA‑OS v17 et d’expliquer le rôle de chaque couche dans un diagramme d’interaction UML.  
**Notions couvertes**  
1. Architecture en micro‑services : services de perception, d’orchestration, de décision et d’exécution.  
2. Bus de messages interne (Kafka 2.8) et format de sérialisation (Avro 1.11).  
3. Modèle de déploiement conteneurisé (Docker 20.10, Docker‑Compose 1.29).  
4. Gestion des dépendances via Maven 3.8 et modules OSGi R7.  
5. Sécurité de la couche d’accès (OAuth 2.0, JWT HS256).

## Module 2 – Gestion des flux de données et du raisonnement symbolique  
**Objectif mesurable** : Implémenter un pipeline de traitement de données depuis la capture sensorielle jusqu’à la génération d’un plan d’action en moins de 150 ms sur un jeu de données de 10 000 événements.  
**Notions couvertes**  
1. Ingestion temps réel avec Kafka Streams 3.3 et transformation en Flink 1.16.  
2. Représentation des connaissances (RDF 1.1, SPARQL 1.1) dans le triplestore Blazegraph 2.1.  
3. Moteur de règles Drools 7.73 pour le raisonnement déductif.  
4. Cache de décision (Caffeine 3.0) et invalidation basée sur les événements.  
5. Monitoring des latences (Prometheus 2.45, Grafana 9.4).

## Module 3 – Intégration des modèles d’apprentissage profond  
**Objectif mesurable** : Déployer et interroger un modèle de vision Transformer (ViT‑B/16) via l’API gRPC d’AlkymIA‑OS avec un taux de précision ≥ 92 % sur le jeu de validation ImageNet‑100.  
**Notions couvertes**  
1. Encapsulation des modèles PyTorch 2.2 dans des services TensorRT 8.6.  
2. API gRPC 1.53 avec protobuf 3.21 pour la sérialisation des tenseurs.  
3. Gestion du cycle de vie du modèle (enregistrement, versionnage, hot‑swap) dans MLflow 2.7.  
4. Optimisation du débit (batching dynamique, inference‑server NVIDIA Triton 2.34).  
5. Stratégies de fallback vers des modèles plus légers (MobileNetV3) en cas de surcharge.

## Module 4 – Orchestration et résilience des services  
**Objectif mesurable** : Configurer un cluster Kubernetes 1.27 avec Helm 3.12 pour assurer une disponibilité de 99,95 % des services critiques sous charge de 500 requêtes/s.  
**Notions couvertes**  
1. Déploiement des micro‑services via Helm charts paramétrés (values.yaml).  
2. Politique de scaling horizontal (HPA) basée sur les métriques CPU/Memory et custom metrics (latence de traitement).  
3. Gestion des pannes avec circuit‑breaker (Resilience4j 1.7) et retry exponential backoff.  
4. Observabilité distribuée (OpenTelemetry 1.14, Jaeger 1.45).  
5. Stratégies de mise à jour sans interruption (

---

## Module 1 — contenu

## 1.1 Diagramme de composants d’AlkymIA‑OS v17  

| Composant | Responsabilité | Technologies | Points d’exposition |
|----------|----------------|--------------|--------------------|
| **Perception Service** | Capture des flux bruts (capteurs, caméras, logs) | Kafka Producer, Avro serializer, Docker | `kafka:9092` (topic `raw.events`) |
| **Orchestration Service** | Routage, agrégation, déclenchement de pipelines | Kafka Streams, Flink, Docker | `kafka:9092` (topics `processed.*`) |
| **Decision Service** | Raisonnement symbolique, règles Drools, cache Caffeine | Drools, Caffeine, Maven OSGi bundle | REST / gRPC `decision.api` |
| **Execution Service** | Actionneurs, plan d’action, feedback | gRPC, Kubernetes Jobs, Docker | `grpc://execution:50051` |
| **Security Gateway** | Authentification OAuth 2.0, validation JWT HS256 | Spring Security, Keycloak, Docker | `https://gateway/api/**` |
| **Infrastructure** | Bus Kafka, Schema Registry, Triplestore, Monitoring | Kafka 2.8, Confluent Schema Registry, Blazegraph, Prometheus, Grafana, Docker‑Compose | – |

> **UML d’interaction (sequence)**  
> 1. Un capteur publie un message Avro sur `raw.events`.  
> 2. `Orchestration Service` consomme, transforme via Flink, publie `processed.events`.  
> 3. `Decision Service` déclenche un *rule session* Drools, interroge le cache Caffeine, renvoie un plan via gRPC.  
> 4. `Execution Service` exécute le plan et renvoie un ACK.  
> 5. Chaque appel est protégé par le **Security Gateway** qui vérifie le JWT dans le header `Authorization`.

---

## 1.2 Micro‑services et bus de messages  

### 1.2.1 Kafka 2.8 + Avro 1.11  

* **Topic de base** : `raw.events` (partition = 3, replication = 2).  
* **Schéma Avro** (déposé dans le Schema Registry) :

```json
{
  "type": "record",
  "name": "RawEvent",
  "namespace": "com.alkymia.events",
  "fields": [
    {"name": "eventId",   "type": "string"},
    {"name": "timestamp","type": "long"},
    {"name": "payload",  "type": "bytes"}
  ]
}
```

* **Compatibilité** : `BACKWARD` (nouveaux producteurs peuvent écrire avec un schéma plus riche, les consommateurs plus anciens continuent de lire).

### 1.2.2 OSGi R7 et Maven 3.8  

* Chaque micro‑service est un **bundle OSGi** (`Bundle‑SymbolicName`, `Export-Package`, `Import-Package`).  
* Le **pom.xml** utilise le plugin `maven-bundle-plugin` ≥ 5.1.2 pour générer les métadonnées OSGi.

```xml
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.alkymia</groupId>
  <artifactId>perception-service</artifactId>
  <version>1.0.0</version>
  <packaging>bundle</packaging>

  <properties>
    <java.version>11</java.version>
    <kafka.version>2.8.1</kafka.version>
    <avro.version>1.11.0</avro.version>
  </properties>

  <dependencies>
    <dependency>
      <groupId>org.apache.kafka</groupId>
      <artifactId>kafka-clients</artifactId>
      <version>${kafka.version}</version>
    </dependency>
    <dependency>
      <groupId>org.apache.avro</groupId>
      <artifactId>avro</artifactId>
      <version>${avro.version}</version>
    </dependency>
    <!-- OSGi core -->
    <dependency>
      <groupId>org.osgi</groupId>
      <artifactId>org.osgi.core</artifactId>
      <version>6.0.0</version>
      <scope>provided</scope>
    </dependency>
  </dependencies>

  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.felix</groupId>
        <artifactId>maven-bundle-plugin</artifactId>
        <version>5.1.4</version>
        <extensions>true</extensions>
        <configuration>
          <instructions>
            <Bundle-SymbolicName>com.alkymia.perception</Bundle-SymbolicName>
            <Export-Package>com.alkymia.perception.*</Export-Package>
            <Import-Package>*</Import-Package>
          </instructions>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
```

### 1.2.3 Exemple fonctionnel : producteur Kafka Avro OSGi  

```java
package com.alkymia.perception;

import org.apache.avro.Schema;
import org.apache.avro.generic.GenericData;
import org.apache.avro.generic.GenericRecord;
import org.apache.kafka.clients.producer.*;
import org.osgi.service.component.annotations.Activate;
import org.osgi.service.component.annotations.Component;
import java.util.Properties;

/**
 * OSGi component qui publie un RawEvent toutes les 5 s.
 */
@Component(immediate = true)
public class Raw

---

## Module 2 — contenu

## Module 2 – Gestion des flux de données et du raisonnement symbolique  

### 2.1 Architecture du pipeline

```
[Capteur] → Kafka topic « raw‑events » → Kafka Streams (transformation) → Flink job (enrichissement) → 
Blazegraph (triplestore) → Drools (règles) → Caffeine cache (décision) → Prometheus (metrics)
```

| Étape | Technologie | Rôle | Points de contrôle |
|------|-------------|------|-------------------|
| Ingestion | **Kafka 2.8** (topic `raw-events`) | Bufferisation durable, décorrélation producteur/consommateur | `acks=all`, `replication.factor=3` |
| Transformation | **Kafka Streams 3.3** | Filtrage, normalisation, enrichissement léger (ex. conversion d’unités) | `state.dir` sur disque SSD, sérialisation **Avro 1.11** |
| Enrichissement | **Apache Flink 1.16** (JobManager + TaskManagers) | Jointure avec référentiels statiques, agrégation temporelle (tumbling windows) | `checkpointing.interval=5000ms`, `exactly‑once` |
| Persistance sémantique | **Blazegraph 2.1** (RDF 1.1) | Stockage des triplets, requêtes SPARQL | `http://host:9999/bigdata/namespace/kb/sparql` |
| Raisonnement | **Drools 7.73** (KIE‑API) | Application de règles déductives sur le graphe | Session Stateless, `fireAllRules()` |
| Cache de décision | **Caffeine 3.0** | Mémoire locale, TTL = 5 min, invalidation par évènement | `CacheWriter` qui supprime l’entrée dès qu’un nouveau triplet touche le même sujet |
| Monitoring | **Prometheus 2.45** + **Grafana 9.4** | Export des latences (`kafka_consumer_lag`, `flink_job_latency`, `drools_rule_time`) | `scrape_interval=15s` |

---

### 2.2 Sérialisation Avro – schéma partagé

```avro
// file: sensor_event.avsc
{
  "type": "record",
  "name": "SensorEvent",
  "namespace": "com.alkymia.os",
  "fields": [
    {"name": "eventId",   "type": "string"},
    {"name": "sensorId",  "type": "string"},
    {"name": "timestamp", "type": "long"},
    {"name": "type",      "type": "string"},
    {"name": "value",     "type": "double"},
    {"name": "unit",      "type": "string"}
  ]
}
```

*Le même fichier doit être compilé avec `avro-tools` pour les projets Java (Kafka Streams) et Python (`fastavro`) afin d’éviter les incompatibilités de champ.*

---

### 2.3 Exemple complet – pipeline Java (Kafka Streams + Flink + Drools)

> **Pré‑requis** : JDK 17, Maven 3.8, Docker 20.10 (Kafka, Zookeeper, Blazegraph, Prometheus).  
> **Packaging** : chaque composant est un module Maven distinct (`streams`, `flink`, `drools-service`).

#### 2.3.1 `streams` – normalisation et filtrage

```java
// src/main/java/com/alkymia/os/streams/NormalizationTopology.java
package com.alkymia.os.streams;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.*;
import org.apache.kafka.streams.kstream.*;
import com.alkymia.os.avro.SensorEvent;
import io.confluent.kafka.streams.serdes.avro.SpecificAvroSerde;
import java.util.*;

public class NormalizationTopology {

    public static Topology build(Properties props) {
        // Sérialiseur Avro (confluent)
        SpecificAvroSerde<SensorEvent> valueSerde = new SpecificAvroSerde<>();
        valueSerde.configure(Collections.singletonMap("schema.registry.url",
                props.getProperty("schema.registry.url")), false);

        StreamsBuilder builder = new StreamsBuilder();

        KStream<String, SensorEvent> raw = builder.stream("raw-events",
                Consumed.with(Serdes.String(), valueSerde));

        // 1️⃣ Filtrage des valeurs hors limites
        KStream<String, SensorEvent> filtered = raw.filter((k, v) ->
                v.getValue() >= 0 && v.getValue() <= 1000);

        // 2️⃣ Normalisation des unités (ex. °C → K)
        KStream<String, SensorEvent> normalized = filtered.mapValues(event -> {
            if ("C".equals(event.getUnit())) {
                double k = event.getValue() + 273.15;
                event.setValue(k);
                event.setUnit("K");
            }
            return event;
        });

        // 3️⃣ Publication du flux normalisé
        normalized.to("normalized-events", Produced.with(Serdes.String(), valueSerde));

        return builder.build();
    }

    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "alkymia-normalizer");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka:9092");
        props.put("schema.registry.url", "http://schema-registry:8081");
        props.put(StreamsConfig.PROCESSING_G

---

## Module 3 — contenu

## Module 3 – Intégration des modèles d’apprentissage profond  

### 3.1 Encapsulation des modèles PyTorch 2.2 dans des services TensorRT 8.6  

| Étape | Commande / Script | Explication |
|------|-------------------|-------------|
| **Export PyTorch → ONNX** | ```python<br># vit_export.py<br>import torch, torchvision<br>from torchvision.models import vit_b_16<br>model = vit_b_16(pretrained=True).eval()<br>dummy = torch.randn(1, 3, 224, 224)<br>torch.onnx.export(model, dummy, "vit_b_16.onnx", opset_version=16, input_names=["input"], output_names=["logits"], dynamic_axes={"input": {0: "batch"}})<br>``` | `opset_version=16` correspond à la version supportée par TensorRT 8.6. Le `dynamic_axes` permet le batching variable. |
| **Conversion ONNX → TensorRT Engine** | ```bash<br># dans le container TensorRT 8.6 (Ubuntu 22.04)<br>trtexec --onnx=vit_b_16.onnx --saveEngine=vit_b_16.trt --fp16 --maxBatch=32 --workspace=4096<br>``` | `--fp16` réduit la latence d’inférence de ~30 % sur GPU A100. `--workspace` limite la RAM GPU allouée. |
| **Service d’inférence minimal** | ```python<br># trt_server.py<br>import tensorrt as trt, pycuda.driver as cuda, pycuda.autoinit, numpy as np, grpc<br>from concurrent import futures<br>import inference_pb2, inference_pb2_grpc<br><br>TRT_LOGGER = trt.Logger(trt.Logger.INFO)<br>def load_engine(path):<br>    with open(path, "rb") as f:<br>        runtime = trt.Runtime(TRT_LOGGER)<br>        return runtime.deserialize_cuda_engine(f.read())<br><br>class ViTInference(inference_pb2_grpc.InferenceServicer):<br>    def __init__(self, engine_path):<br>        self.engine = load_engine(engine_path)<br>        self.context = self.engine.create_execution_context()<br>        self.input_idx = self.engine.get_binding_index("input")<br>        self.output_idx = self.engine.get_binding_index("logits")<br><br>    def Predict(self, request, context):<br>        # désérialisation du tenseur protobuf (float32, NCHW)<br>        img = np.frombuffer(request.tensor, dtype=np.float32).reshape(request.batch, 3, 224, 224)<br>        d_input = cuda.mem_alloc(img.nbytes)<br>        d_output = cuda.mem_alloc(self.engine.get_binding_shape(self.output_idx).size * request.batch * 4)  # float32\n        cuda.memcpy_htod(d_input, img)\n        self.context.set_binding_shape(self.input_idx, img.shape)\n        self.context.execute_v2([int(d_input), int(d_output)])\n        out = np.empty(self.context.get_binding_shape(self.output_idx), dtype=np.float32)\n        cuda.memcpy_dtoh(out, d_output)\n        # sérialisation protobuf\n        return inference_pb2.Prediction(tensor=out.tobytes())\n<br># serveur gRPC\n> server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))\n> inference_pb2_grpc.add_InferenceServicer_to_server(ViTInference('vit_b_16.trt'), server)\n> server.add_insecure_port('[::]:50051')\n> server.start()\n> server.wait_for_termination()\n``` | Le serveur utilise le binding `input`/`logits` générés par `trtexec`. La fonction `Predict` accepte un batch variable grâce à `set_binding_shape`. |

#### Pièges concrets
* **Mismatch opset** : TensorRT 8.6 ne supporte pas les opérateurs ONNX ≥ 17. Vérifier `opset_version` ≤ 16.
* **Alignement de la mémoire GPU** : `pycuda.autoinit` crée un contexte par processus. En mode multi‑thread, créer un `cuda.Context` partagé ou désactiver le pool de threads.
* **Batch dynamique** : Oublier de déclarer `dynamic_axes` lors de l’export ONNX entraîne l’erreur `TensorRT could not infer shape for input`.  

---

### 3.2 API gRPC 1.53 avec protobuf 3.21 pour la sérialisation des tenseurs  

**Fichier `inference.proto`**  

```proto
syntax = "proto3";

package inference;

// message contenant un tenseur float32 en format row‑major
message Tensor {
  bytes tensor = 1;          // données brutes
  uint32 batch = 2;         // nombre d’exemples
  uint32 channels = 3;      // 3 pour RGB
  uint32 height = 4;        // 224
  uint32 width = 5;         // 224
}

// réponse contenant les logits (classe probabilité)
message Prediction {
  bytes tensor = 1;          // float32 logits (batch x 1000)
}

// service d’inférence
service Inference {
  rpc Predict (Tensor) returns (Prediction);
}
```

*Compilation*  

```bash

---

## Module 4 — contenu

## 4.1 Déploiement des micro‑services avec Helm 3.12  

### 4.1.1 Structure d’un chart minimal  

```
my‑service/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    └── hpa.yaml
```

**Chart.yaml** (méta‑données)  

```yaml
apiVersion: v2
name: my-service
description: Service de perception d’AlkymIA‑OS
type: application
version: 0.4.0          # version du chart
appVersion: "1.2.3"     # version du container
```

**values.yaml** (paramètres configurables)  

```yaml
replicaCount: 3

image:
  repository: registry.example.com/alkymia/perception
  tag: "1.2.3"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8080

resources:
  limits:
    cpu: "500m"
    memory: "512Mi"
  requests:
    cpu: "250m"
    memory: "256Mi"

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  # métrique personnalisée (latence moyenne en ms)
  customMetric:
    enabled: true
    name: latency_ms
    targetValue: "150"
```

### 4.1.2 Template du Deployment (templates/deployment.yaml)  

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-service.fullname" . }}
  labels:
    {{- include "my-service.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "my-service.name" . }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ include "my-service.name" . }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: {{ .Values.service.port }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          env:
            - name: OTEL_EXPORTER_JAEGER_ENDPOINT
              value: "http://jaeger-collector:14268/api/traces"
            - name: RESILIENCE4J_CIRCUIT_BREAKER_ENABLED
              value: "true"
```

### 4.1.3 Service (templates/service.yaml)  

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "my-service.fullname" . }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.port }}
  selector:
    app.kubernetes.io/name: {{ include "my-service.name" . }}
```

### 4.1.4 HPA avec métrique personnalisée (templates/hpa.yaml)  

```yaml
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "my-service.fullname" . }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "my-service.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
    {{- if .Values.autoscaling.customMetric.enabled }}
    - type: External
      external:
        metric:
          name: {{ .Values.autoscaling.customMetric.name }}
        target:
          type: Value
          value: "{{ .Values.autoscaling.customMetric.targetValue }}"
    {{- end }}
{{- end }}
```

**Installation**  

```bash
helm upgrade --install perception ./my-service \
  --namespace alkymia \
  --create-namespace
```

---

## 4.2 Politique de scaling horizontal (HPA)  

* **CPU/Memory** : métriques natives exposées par le *kube‑metrics‑server* (v0.6).  
* **Custom metric** : nécessite un *Prometheus Adapter* (v0.11) configuré avec la règle suivante :

```yaml
rules:
  - seriesQuery: 'latency_ms{service="perception"}'
    resources:
      overrides:
        namespace: {resource: "namespace"}
        pod: {resource: "pod"}
    name:
      matches: "latency_ms"
      as: "latency_ms"
    metricsQuery: <<.Series>>{<<.LabelMatchers>>}
```

* Le *Prometheus Adapter* expose les métriques sous `/apis/custom.metrics.k8s.io/v1beta1/...` ; l’HPA les consomme directement.

### 4.2.1 Piège : délai de propagation  

Les métriques externes ont un **scrape interval** (par défaut 30 s). Si le HPA s’appuie sur une métrique avec un intervalle trop long, le scaling réagit avec un retard qui peut dépasser le SLA de 150 ms. Solution : réduire `scrape_interval` à 5 s et activer `honor_labels: true` pour éviter la perte de tags.

---

## 4.3 Gestion des pannes avec Resilience4j 1.7  

###

---

## Module 5 — contenu

## Module 5 – Tests automatisés, CI/CD et déploiement continu  

### 5.1 Objectif mesurable  
Mettre en place une chaîne d’intégration continue (CI) et de déploiement continu (CD) qui, pour chaque commit :  

* exécute les tests unitaires et d’intégration (coverage ≥ 80 %);  
* compile le projet Maven, génère l’image Docker et la pousse vers un registre privé : `registry.example.com/alkymia/<service>:<git‑sha>`;  
* déclenche un déploiement Helm « canary » sur le cluster Kubernetes 1.27, puis, après validation de la santé (probe = 200 ms), effectue le « roll‑out full ».  

Le tout doit être réalisable en < 5 minutes sur un runner GitHub Actions 2‑core / 4 GiB.  

---

### 5.2 Architecture du pipeline  

| Étape | Outil | Artefact produit | Points de contrôle |
|------|------|------------------|--------------------|
| **SCM** | GitHub | Commit SHA | Pull‑request (PR) déclenchée |
| **CI** | GitHub Actions (ubuntu‑latest) | JUnit‑XML, JaCoCo report, Docker image (local) | `mvn verify` → `docker build` |
| **Registry** | Docker Registry (Harbor 2.6) | Image taggée | Auth via OIDC, scan Trivy 0.44 |
| **CD** | GitHub Actions + Helm 3.12 | Release Helm chart (values‑canary.yaml) | `helm upgrade --install` avec `--wait` |
| **Validation** | K8s probes + Prometheus alert | Aucun rollback si OK | `kubectl rollout status` + `curl` health‑endpoint |
| **Promotion** | Helm upgrade (values‑prod.yaml) | Service en production | `helm upgrade` après 2 min de monitoring |

---

### 5.3 Exemple fonctionnel : pipeline GitHub Actions pour le service **perception‑service**  

```yaml
# .github/workflows/ci-cd-perception.yml
name: CI/CD – perception-service

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: registry.example.com/alkymia
  IMAGE_NAME: perception-service
  K8S_NAMESPACE: alkymia
  HELM_RELEASE: perception
  # Le token OIDC de GitHub est injecté automatiquement dans le runner

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      # 1️⃣ Checkout du code
      - name: Checkout repository
        uses: actions/checkout@v4

      # 2️⃣ Cache Maven (déjà validé par Maven 3.8)
      - name: Cache Maven repository
        uses: actions/cache@v3
        with:
          path: ~/.m2/repository
          key: ${{ runner.os }}-m2-${{ hashFiles('**/pom.xml') }}
          restore-keys: ${{ runner.os }}-m2-

      # 3️⃣ Lancer les tests unitaires + coverage
      - name: Run Maven tests
        run: |
          mvn -B verify \
            -DskipITs=false \
            -Djacoco.outputDirectory=target/jacoco \
            -Djacoco.reportFormat=xml
        env:
          MAVEN_OPTS: "-Xmx2g"

      # 4️⃣ Publier le rapport de couverture (JaCoCo 0.8.9)
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: target/site/jacoco/jacoco.xml
          flags: perception-service
          name: coverage-perception

      # 5️⃣ Build de l’image Docker (Docker 20.10, BuildKit activé)
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Harbor registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.HARBOR_USER }}
          password: ${{ secrets.HARBOR_PASSWORD }}

      - name: Build and push Docker image
        id: docker_build
        uses: docker/build-push-action@v5
        with:
          context: .
          file: Dockerfile
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:cache
          cache-to: type=inline
          build-args: |
            JAR_FILE=target/perception-service.jar

      # 6️⃣ Scan de sécurité avec Trivy (v0.44)
      - name: Scan image with Trivy
        uses: aquasecurity/trivy-action@0.12
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github