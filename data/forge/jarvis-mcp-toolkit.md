# AlkymIA-OS MCP Toolkit — 88 Handlers

> Référence `jarvis-mcp-toolkit` · 79 €

## Plan

## Module 1 – Installation, configuration et validation de l’environnement  
**Objectif mesurable** : L’apprenant installe le toolkit AlkymIA‑OS MCP v1.4 sur une machine Ubuntu 22.04, configure les variables d’environnement requises et valide l’installation à l’aide du script `mcp‑verify.sh` (code de retour 0).  

**Notions couvertes**  
1. Prérequis système : Python 3.11, Java 17, Docker ≥ 20.10, PostgreSQL 13.  
2. Installation via le package `.deb` et le dépôt APT interne (`apt-get install alkymia-mcp`).  
3. Gestion des dépendances avec `pip install -r requirements.txt` et `mvn dependency:resolve`.  
4. Configuration des fichiers `config.yaml` et `.env` (clé `MCP_API_KEY`, `DB_URL`).  
5. Procédure de vérification automatisée (`./scripts/mcp‑verify.sh`).  

---

## Module 2 – Architecture du toolkit et flux de données  
**Objectif mesurable** : L’apprenant décrit le diagramme de séquence du traitement d’une requête HTTP vers un handler, identifie les composants critiques et explique le rôle du bus d’événements (`EventBus`).  

**Notions couvertes**  
1. Structure en couches : API Gateway → Dispatcher → Handler → Persistence Layer.  
2. Modèle de messages (`MessageDTO`) et sérialisation JSON via Jackson 2.14.  
3. Bus d’événements interne (implémentation basée sur `Guava EventBus`).  
4. Gestion des transactions avec Spring Boot 3 (annotation `@Transactional`).  
5. Points d’extension : interfaces `IHandler`, `IProcessor`.  

---

## Module 3 – Développement d’un handler personnalisé  
**Objectif mesurable** : L’apprenant crée, compile et déploie un nouveau handler « SentimentAnalyzer » respectant l’interface `IHandler`, le teste avec JUnit 5 (couverture ≥ 80 %) et le rend disponible via le registre dynamique.  

**Notions couvertes**  
1. Implémentation de `IHandler.handle(MessageDTO)` et gestion des exceptions (`HandlerException`).  
2. Utilisation du SDK NLP v2.3 (classe `NLPClient`).  
3. Enregistrement au `HandlerRegistry` (méthode `registerHandler`).  
4. Tests unitaires avec `@SpringBootTest` et `MockMvc`.  
5. Packaging du handler dans un JAR et chargement dynamique avec `URLClassLoader`.  

---

## Module 4 – Intégration, tests fonctionnels et CI/CD  
**Objectif mesurable** : L’apprenant ajoute le handler au pipeline GitLab CI, configure les jobs `build`, `test` et `deploy‑docker`, et valide le déploiement sur un cluster Kubernetes (v1.27) en observant le pod `mcp-sentiment-analyzer`.  

**Notions couvertes**  
1. Fichier `.gitlab-ci.yml` avec stages `compile`, `unit_test`, `docker_build`, `k8s_deploy`.  
2. Construction d’une image Docker multi‑stage (`Dockerfile` avec `builder` et `runtime`).  
3

---

## Module 1 — contenu

## Module 1 – Installation, configuration et validation de l’environnement  

### 1.1 Prérequis système  

| Composant | Version minimale | Vérification |
|-----------|------------------|--------------|
| **Ubuntu** | 22.04 LTS | `lsb_release -rs` → `22.04` |
| **Python** | 3.11 | `python3 --version` → `Python 3.11.x` |
| **Java** | 17 (OpenJDK) | `java -version` → `openjdk version "17.*"` |
| **Docker** | 20.10 | `docker --version` → `Docker version 20.10.*` |
| **PostgreSQL** | 13 | `psql --version` → `psql (PostgreSQL) 13.*` |

> **Note** : les paquets `python3-pip`, `openjdk-17-jdk`, `docker.io` et `postgresql-13` sont disponibles dans les dépôts officiels d’Ubuntu 22.04.  

```bash
sudo apt update
sudo apt install -y python3-pip openjdk-17-jdk docker.io postgresql-13
```

#### 1.1.1 Vérification des services  

```bash
# Docker daemon
systemctl is-active --quiet docker && echo "Docker OK" || echo "Docker KO"

# PostgreSQL
sudo -u postgres psql -c "SELECT version();" \
  && echo "PostgreSQL OK" || echo "PostgreSQL KO"
```

### 1.2 Installation du toolkit AlkymIA‑OS MCP v1.4  

#### 1.2.1 Ajout du dépôt interne  

```bash
# 1. Importer la clé publique du dépôt
curl -fsSL https://repo.alkymia.io/gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/alkymia-archive-keyring.gpg

# 2. Ajouter le fichier de sources
echo "deb [signed-by=/usr/share/keyrings/alkymia-archive-keyring.gpg] https://repo.alkymia.io/ubuntu jammy main" \
  | sudo tee /etc/apt/sources.list.d/alkymia.list

# 3. Mettre à jour le cache APT
sudo apt update
```

#### 1.2.2 Installation du paquet  

```bash
sudo apt-get install -y alkymia-mcp=1.4.0
```

> **Vérification** : le binaire `mcp` doit être présent dans `/usr/local/bin/mcp`.  

```bash
which mcp && mcp --version   # → "AlkymIA‑OS MCP version 1.4.0"
```

### 1.3 Gestion des dépendances Python et Maven  

#### 1.3.1 Python  

Le répertoire d’installation (`/opt/alkymia-mcp`) contient `requirements.txt`.  

```bash
cd /opt/alkymia-mcp
python3 -m venv .venv               # création d’un environnement isolé
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

*Vérifier* : `pip list | grep -E 'flask|pydantic'` doit afficher les versions déclarées dans le fichier.  

#### 1.3.2 Maven  

Le projet Java utilise Maven 3.8+. Le wrapper est fourni (`mvnw`).  

```bash
cd /opt/alkymia-mcp/java
./mvnw -q dependency:resolve
```

Le log doit se terminer par `BUILD SUCCESS`.  

### 1.4 Configuration des fichiers `config.yaml` et `.env`  

#### 1.4.1 `config.yaml` (exemple minimal)  

```yaml
# /opt/alkymia-mcp/config.yaml
server:
  port: 8080
  contextPath: /api
logging:
  level: INFO
  file: /var/log/alkymia/mcp.log
```

#### 1.4.2 `.env` (variables d’environnement)  

```dotenv
# /opt/alkymia-mcp/.env
MCP_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DB_URL=jdbc:postgresql://localhost:5432/mcpdb
DB_USER=mcp_user
DB_PASSWORD=StrongP@ssw0rd!
```

*Chargement automatique* : le script d’entrée `mcp` invoque `dotenv` (Python) et `SpringApplication.setDefaultProperties` (Java) pour injecter ces valeurs.  

### 1.5 Procédure de vérification automatisée  

Le script `mcp-verify.sh` se trouve dans `/opt/alkymia-mcp/scripts`.  

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Vérifier la présence du binaire
command -v mcp >/dev/null 2>&1 || { echo "mcp not found"; exit 1; }

# 2. Vérifier la configuration
if [[ ! -f /opt/alkymia-mcp/config.yaml ]]; then
  echo "config.yaml missing"
  exit 2
fi
if [[ ! -f /opt/alkymia-mcp/.env ]]; then
  echo ".env missing"
  exit 3
fi

# 3. Lancer une requête de santé via l’API interne
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/health || echo "000")
if [[ "$STATUS" -ne 200 ]]; then
  echo "Health endpoint unreachable (code $STATUS)"
  exit 4
fi

echo "Verification OK"
exit 0
```

**Exécution**  

```bash
cd /opt/alkymia-mcp/scripts
chmod +x mcp-verify.sh
./mcp-verify.sh
echo $?   # doit afficher 0
```

### 1.6 Pièges concrets  

| Situation | Cause fréquente | Remède |
|-----------

---

## Module 2 — contenu

## 2.1 Structure en couches  

| Couche | Responsabilité | Technologie principale |
|--------|----------------|------------------------|
| **API Gateway** | Expose les points d’entrée HTTP, authentifie, valide le schéma JSON. | Spring Boot 3, Spring WebFlux (optionnel) |
| **Dispatcher** | Reçoit le `MessageDTO`, sélectionne le handler approprié via `HandlerRegistry`, publie l’événement sur `EventBus`. | Spring DI, Guava `EventBus` |
| **Handler** | Implémente `IHandler.handle(MessageDTO)`. Contient la logique métier (ex. appel à un service externe). | Java 17, SDK métier |
| **Persistence Layer** | Gère la lecture/écriture des entités, assure la cohérence transactionnelle. | Spring Data JPA, PostgreSQL 13 |

Le flux typique :

1. `POST /api/v1/messages` → **API Gateway**  
2. Validation du JSON → `MessageDTO` (Jackson)  
3. `Dispatcher.dispatch(message)` → recherche du handler dans `HandlerRegistry`  
4. Publication de `MessageEvent` sur `EventBus`  
5. Le handler abonné consomme l’événement, exécute la logique, persiste le résultat.

---

## 2.2 Modèle de messages (`MessageDTO`)  

```java
package com.alkymia.mcp.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.time.Instant;

/**
 * Représente le contrat JSON échangé entre le client et le MCP.
 * La sérialisation/désérialisation est assurée par Jackson 2.14.
 */
public final class MessageDTO {

    /** Identifiant unique fourni par le client (UUID v4). */
    @NotBlank
    @JsonProperty("message_id")
    private final String messageId;

    /** Payload brut du client, encodé en UTF‑8. */
    @NotBlank
    private final String payload;

    /** Horodatage ISO‑8601, généré côté client. */
    @NotNull
    private final Instant timestamp;

    public MessageDTO(
            @JsonProperty("message_id") String messageId,
            @JsonProperty("payload") String payload,
            @JsonProperty("timestamp") Instant timestamp) {
        this.messageId = messageId;
        this.payload = payload;
        this.timestamp = timestamp;
    }

    // Getters immuables
    public String getMessageId() { return messageId; }
    public String getPayload()   { return payload; }
    public Instant getTimestamp() { return timestamp; }
}
```

*Points de vigilance*  

* **Nom de champ** : `@JsonProperty` doit correspondre exactement au JSON attendu (`snake_case`).  
* **Immutabilité** : le DTO ne doit pas contenir de setters ; cela évite les effets de bord pendant la propagation d’événements.  
* **Serialisation des dates** : Jackson utilise par défaut le module `JavaTimeModule`. Le `ObjectMapper` du projet doit être configuré :  

```java
ObjectMapper mapper = new ObjectMapper()
        .registerModule(new JavaTimeModule())
        .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
```

---

## 2.3 Bus d’événements interne (`EventBus`)  

Le MCP utilise **Guava EventBus** (v31.1). Le bus est déclaré comme bean singleton afin d’être partagé entre le dispatcher et tous les handlers.

```java
package com.alkymia.mcp.bus;

import com.google.common.eventbus.EventBus;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Configuration Spring du bus d’événements interne.
 * Le bus est thread‑safe, mais les abonnés doivent être
 * stateless ou gérer leur propre synchronisation.
 */
@Configuration
public class EventBusConfig {

    @Bean
    public EventBus eventBus() {
        // Le nom aide au debugging (log du thread de publication)
        return new EventBus("MCP-Internal-Bus");
    }
}
```

### Publication d’un événement  

```java
package com.alkymia.mcp.dispatcher;

import com.alkymia.mcp.bus.EventBusConfig;
import com.alkymia.mcp.dto.MessageDTO;
import com.alkymia.mcp.events.MessageEvent;
import com.google.common.eventbus.EventBus;
import org.springframework.stereotype.Component;

@Component
public class Dispatcher {

    private final EventBus eventBus;
    private final HandlerRegistry registry;

    public Dispatcher(EventBus eventBus, HandlerRegistry registry) {
        this.eventBus = eventBus;
        this.registry = registry;
    }

    /**
     * Sélectionne le handler et publie l’événement.
     * Retourne true si un handler a été trouvé, false sinon.
     */
    public boolean dispatch(MessageDTO message) {
        IHandler handler = registry.findHandlerFor(message);
        if (handler == null) {
            return false;
        }
        // Le handler s’abonne à MessageEvent via @Subscribe
        eventBus.register(handler);
        eventBus.post(new MessageEvent(message));
        // Le handler se désinscrit automatiquement après traitement
        // (voir MessageEventProcessor.handle)
        return true;
    }
}
```

### Exemple d’un handler abonné  

```java
package com.alkymia.mcp.handlers;

import com.alkymia.mcp.dto.MessageDTO;
import com.alkymia.mcp.events.MessageEvent;
import com.google.common.eventbus.Subscribe;
import org.springframework.stereotype.Component;

/**
 * Exemple minimal d’un handler qui loggue le payload.
 * Implémente IHandler uniquement pour la découverte via le registre.
 */
@Component
public class LoggingHandler implements IHandler {

    @Override
    public boolean canHandle(MessageDTO msg) {
        // Ce handler accepte tout type de message
        return

---

## Module 3 — contenu

## Module 3 – Développement d’un handler personnalisé  

### 1. Rappel de l’interface `IHandler`  

```java
package com.alkymia.mcp.handler;

import com.alkymia.mcp.dto.MessageDTO;
import com.alkymia.mcp.exception.HandlerException;

/**
 * Tous les handlers doivent implémenter cette interface.
 */
public interface IHandler {

    /**
     * Traite le message entrant et retourne un MessageDTO enrichi.
     *
     * @param input le message reçu du dispatcher
     * @return le message modifié ou enrichi
     * @throws HandlerException si une erreur métier ou technique survient
     */
    MessageDTO handle(MessageDTO input) throws HandlerException;
}
```

- `MessageDTO` possède les champs `id` (UUID), `payload` (String JSON), `metadata` (Map<String,String>).
- `HandlerException` étend `RuntimeException` et porte un code d’erreur (enum `ErrorCode`).  

### 2. Étapes de création du handler « SentimentAnalyzer »  

| Étape | Action | Commande / Code |
|------|--------|-----------------|
| 2.1 | Créer le package `com.alkymia.mcp.handler.sentiment` | `mkdir -p src/main/java/com/alkymia/mcp/handler/sentiment` |
| 2.2 | Implémenter la classe `SentimentAnalyzerHandler` | voir § 2.3 |
| 2.3 | Ajouter la dépendance du SDK NLP v2.3 dans `pom.xml` | ```xml<br><dependency><groupId>com.alkymia.sdk</groupId><artifactId>nlp-client</artifactId><version>2.3.0</version></dependency>``` |
| 2.4 | Enregistrer le handler dans le registre dynamique | voir § 2.5 |
| 2.5 | Configurer le bean Spring (facultatif) | `@Component` ou `@Service` |
| 2.6 | Compiler le module en JAR | `mvn clean package -DskipTests` |
| 2.7 | Charger le JAR à l’exécution avec `URLClassLoader` | voir § 2.8 |

---

### 2.3 Implémentation du handler  

```java
package com.alkymia.mcp.handler.sentiment;

import com.alkymia.mcp.dto.MessageDTO;
import com.alkymia.mcp.exception.HandlerException;
import com.alkymia.mcp.handler.IHandler;
import com.alkymia.sdk.nlp.NLPClient;
import com.alkymia.sdk.nlp.SentimentResult;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

/**
 * Analyse le sentiment du texte présent dans le champ "text" du payload.
 * Le résultat est injecté dans la métadonnée "sentiment".
 */
@Component   // Permet à Spring de détecter le bean si on utilise le scan de composants
public class SentimentAnalyzerHandler implements IHandler {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private final NLPClient nlpClient;

    // Le client NLP est créé à partir de la clé API définie dans .env (MCP_NLP_API_KEY)
    public SentimentAnalyzerHandler() {
        String apiKey = System.getenv("MCP_NLP_API_KEY");
        if (apiKey == null) {
            throw new IllegalStateException("MCP_NLP_API_KEY non définie dans l'environnement");
        }
        this.nlpClient = new NLPClient(apiKey);
    }

    @Override
    public MessageDTO handle(MessageDTO input) throws HandlerException {
        try {
            // 1️⃣ Désérialiser le payload JSON
            Map<String, Object> payloadMap = MAPPER.readValue(input.getPayload(), Map.class);
            String text = (String) payloadMap.get("text");
            if (text == null) {
                throw new HandlerException("Champ 'text' manquant", HandlerException.ErrorCode.INVALID_INPUT);
            }

            // 2️⃣ Appeler le SDK NLP
            SentimentResult result = nlpClient.analyzeSentiment(text);

            // 3️⃣ Enrichir les métadonnées
            Map<String, String> meta = new HashMap<>(input.getMetadata());
            meta.put("sentiment", result.getSentiment().name()); // POSITIVE / NEGATIVE / NEUTRAL
            meta.put("confidence", String.format("%.2f", result.getConfidence()));

            // 4️⃣ Retourner le MessageDTO modifié (payload inchangé)
            return new MessageDTO(input.getId(), input.getPayload(), meta);
        } catch (HandlerException he) {
            // Propagation directe pour conserver le code d’erreur d’origine
            throw he;
        } catch (Exception e) {
            // Capture toute exception inattendue et la transforme en HandlerException générique
            throw new HandlerException("Erreur interne du SentimentAnalyzer", HandlerException.ErrorCode.INTERNAL_ERROR, e);
        }
    }
}
```

#### Points de vérification immédiate  

1. **Clé API** – La variable d’environnement `MCP_NLP_API_KEY` doit être exportée avant le démarrage du service (`export MCP_NLP_API_KEY=xxxx`).  
2. **Structure du payload** – Le JSON doit contenir `"text"` au niveau racine. Exemple valide : `{"text":"J’aime ce produit"}`.  
3. **Gestion des exceptions** – `HandlerException` doit être lancé avec le bon `ErrorCode` pour que le dispatcher puisse appliquer la stratégie de retry.  

---

### 2.4 Enregistrement dynamique au `HandlerRegistry`  

Le registre est un singleton thread‑safe qui maintient une map `Map<String, IHandler>`.  

```java
package com.alkymia.mcp.registry;

import com.alkymia.mcp.handler.IHandler;
import java.util.concurrent.ConcurrentHashMap

---

## Module 4 — contenu

## Module 4 – Intégration, tests fonctionnels et CI/CD  

### 4.1. Ajout du handler au pipeline GitLab CI  

#### 4.1.1. Structure du fichier `.gitlab-ci.yml`  

```yaml
# .gitlab-ci.yml
# -------------------------------------------------
#  Stages du pipeline
# -------------------------------------------------
stages:
  - compile
  - unit_test
  - docker_build
  - k8s_deploy

# -------------------------------------------------
#  Variables d’environnement (définies dans le projet)
# -------------------------------------------------
variables:
  MAVEN_OPTS: "-Dmaven.repo.local=$CI_PROJECT_DIR/.m2/repository"
  DOCKER_REGISTRY: "registry.example.com"
  IMAGE_NAME: "$DOCKER_REGISTRY/alkymia/mcp-sentiment-analyzer"
  K8S_NAMESPACE: "mcp-prod"
  K8S_DEPLOYMENT: "mcp-sentiment-analyzer"

# -------------------------------------------------
#  Job : compilation du code Java
# -------------------------------------------------
compile:
  stage: compile
  image: maven:3.9.6-openjdk-17
  script:
    - mvn clean compile -DskipTests
  artifacts:
    paths:
      - target/*.jar
    expire_in: 1h

# -------------------------------------------------
#  Job : tests unitaires + couverture
# -------------------------------------------------
unit_test:
  stage: unit_test
  image: maven:3.9.6-openjdk-17
  script:
    - mvn test jacoco:report
  artifacts:
    reports:
      junit: target/surefire-reports/*.xml
    paths:
      - target/site/jacoco
    expire_in: 1h
  coverage: '/TOTAL\s+\|\s+([\d\.]+)%/'

# -------------------------------------------------
#  Job : construction de l’image Docker (multi‑stage)
# -------------------------------------------------
docker_build:
  stage: docker_build
  image: docker:24.0.5
  services:
    - docker:24.0.5-dind
  script:
    - docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" $DOCKER_REGISTRY
    - docker build -t $IMAGE_NAME:$CI_COMMIT_SHORT_SHA .
    - docker push $IMAGE_NAME:$CI_COMMIT_SHORT_SHA
  only:
    - main
    - tags

# -------------------------------------------------
#  Job : déploiement sur le cluster Kubernetes
# -------------------------------------------------
k8s_deploy:
  stage: k8s_deploy
  image: bitnami/kubectl:1.27
  script:
    - |
      # Remplace l’image du conteneur dans le Deployment
      kubectl set image deployment/$K8S_DEPLOYMENT \
        $K8S_DEPLOYMENT=$IMAGE_NAME:$CI_COMMIT_SHORT_SHA \
        --namespace $K8S_NAMESPACE
    - |
      # Attente de la mise à jour du pod (max 120 s)
      kubectl rollout status deployment/$K8S_DEPLOYMENT \
        --namespace $K8S_NAMESPACE \
        --timeout=120s
  environment:
    name: production
    url: https://api.example.com/mcp
  only:
    - main
    - tags
```

**Points clés**  

| Ligne | Raison | Piège fréquent |
|------|--------|----------------|
| `MAVEN_OPTS` | Cache local du repo Maven pour éviter le téléchargement à chaque run. | Oublier de créer le répertoire `.m2`; le job échoue avec `Permission denied`. |
| `coverage` regex | GitLab extrait le pourcentage de couverture depuis le rapport JaCoCo. | Regex mal formé → aucune donnée de couverture affichée. |
| `docker:dind` service | Nécessaire pour le daemon Docker dans le job. | Oublier `privileged: true` sur les runners Docker‑in‑Docker ; le build échoue avec `Cannot connect to the Docker daemon`. |
| `kubectl set image` | Met à jour le conteneur sans recréer le Deployment. | Utiliser le nom du **container** au lieu du **deployment** → aucune mise à jour. |
| `--timeout` | Empêche le job de rester bloqué indéfiniment. | Timeout trop court (< 30 s) sur clusters lents → échec du job. |

---

### 4.2. Dockerfile multi‑stage pour le handler  

```dockerfile
# -------------------------------------------------
#  Étape 1 – Builder (Maven + JDK 17)
# -------------------------------------------------
FROM maven:3.9.6-openjdk-17 AS builder
WORKDIR /app

# Copie uniquement les fichiers de configuration Maven pour profiter du cache
COPY pom.xml .
COPY src/main/resources/ src/main/resources/
RUN mvn dependency:go-offline -B

# Copie le code source complet et compile
COPY src/ src/
RUN mvn clean package -DskipTests -B

# -------------------------------------------------
#  Étape 2 – Runtime (JRE 17 + Alpine)
# -------------------------------------------------
FROM eclipse-temurin:17-jre-alpine AS runtime
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Création de l’utilisateur non‑root
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Répertoire de l’application
WORKDIR /opt/mcp

# Copie du JAR produit par l’étape builder
COPY --from=builder /app/target/mcp-sentiment-analyzer.jar ./app.jar

# Variables d’environnement obligatoires (définies à l’exécution)
ENV MCP_API_KEY= \
    DB_URL=jdbc:postgresql://postgres:5432/mcp

# Point d’entrée
ENTRYPOINT ["java","-jar","/opt/mcp/app.jar"]
```

**Explications**  

- **Builder** : le cache Maven est exploité en séparant la résolution des dépendances (`dependency:go-offline`) du code source.  
- **Runtime** : image Alpine (~30 Mo) réduit

---

## Module 5 — contenu

## Module 5 – Observabilité, métriques et gestion des incidents  

### 5.1 Objectif mesurable  
L’apprenant intègre la collecte de métriques, les logs structurés et le tracing distribué dans le toolkit AlkymIA‑OS MCP, configure Prometheus + Grafana pour la surveillance en temps réel, et met en place une alerte de dépassement de latence d’un handler (seuil = 500 ms). Validation : le job `ci‑monitoring` du pipeline CI passe (code 0) et l’alerte apparaît dans Grafana.

---

### 5.2 Concepts clés  

| Concept | Description vérifiable |
|---------|------------------------|
| **Spring Boot Actuator 3.x** | Fournit les endpoints `/actuator/metrics`, `/actuator/prometheus`, `/actuator/health`. |
| **Micrometer 1.12** | Bibliothèque d’instrumentation qui expose les métriques au format Prometheus via `PrometheusMeterRegistry`. |
| **OpenTelemetry 1.30** | SDK Java qui crée des traces compatibles avec Jaeger ou Zipkin. |
| **Logback 1.4** + **Logstash‑Encoder** | Génère des logs JSON (`%msg%n`) pouvant être ingérés par Elasticsearch. |
| **Prometheus 2.48** | Scrape les métriques exposées sur le port `9090` du pod. |
| **Grafana 10.2** | Tableau de bord qui interroge Prometheus via la query `rate(mcp_handler_latency_seconds_sum[1m]) / rate(mcp_handler_latency_seconds_count[1m])`. |
| **Alertmanager** | Envoie un webhook Slack quand la latence moyenne dépasse 500 ms pendant 2 min. |
| **CircuitBreaker (Resilience4j 2.1)** | Coupe les appels au handler en cas d’erreur répétée (> 5 % sur 1 min). |

---

### 5.3 Implémentation détaillée  

#### 5.3.1 Dépendances Maven  

```xml
<!-- pom.xml -->
<dependencies>
    <!-- Actuator + Micrometer -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-actuator</artifactId>
        <version>3.2.5</version>
    </dependency>
    <dependency>
        <groupId>io.micrometer</groupId>
        <artifactId>micrometer-registry-prometheus</artifactId>
        <version>1.12.2</version>
    </dependency>

    <!-- OpenTelemetry -->
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-api</artifactId>
        <version>1.30.0</version>
    </dependency>
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-sdk</artifactId>
        <version>1.30.0</version>
    </dependency>

    <!-- Logstash encoder -->
    <dependency>
        <groupId>net.logstash.logback</groupId>
        <artifactId>logstash-logback-encoder</artifactId>
        <version>7.4</version>
    </dependency>

    <!-- Resilience4j CircuitBreaker -->
    <dependency>
        <groupId>io.github.resilience4j</groupId>
        <artifactId>resilience4j-spring-boot3</artifactId>
        <version>2.1.0</version>
    </dependency>
</dependencies>
```

#### 5.3.2 Configuration `application.yaml`  

```yaml
server:
  port: 8080
  servlet:
    context-path: /mcp

management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  metrics:
    export:
      prometheus:
        enabled: true
        step: 30s   # intervalle de push vers Prometheus
  health:
    probes:
      enabled: true

logging:
  level:
    root: INFO
    com.alkymia.mcp: DEBUG
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss.SSS} %-5level %logger{36} - %msg%n"
  logstash:
    enabled: true
    encoder:
      include-context: true
      include-thread-name: true

resilience4j:
  circuitbreaker:
    instances:
      handlerCircuit:
        registerHealthIndicator: true
        slidingWindowSize: 100
        failureRateThreshold: 5
        waitDurationInOpenState: 30s
```

#### 5.3.3 Enregistrement d’une métrique de latence personnalisée  

```java
package com.alkymia.mcp.metrics;

import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.springframework.stereotype.Component;

/