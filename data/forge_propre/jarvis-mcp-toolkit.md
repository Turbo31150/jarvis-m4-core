# AlkymIA-OS MCP Toolkit — 88 Handlers

> Référence `jarvis-mcp-toolkit`  

## Plan

## Module 1 – Installation, configuration et validation de l’environnement  
**Objectif mesurable** : L’apprenant installe le toolkit AlkymIA‑OS MCP sur une machine Ubuntu, configure les variables d’environnement requises et valide l’installation à l’aide du script `mcp‑verify.sh` (code de retour 0).  

**Notions couvertes**  
1. Prérequis système : Python, Java, Docker, PostgreSQL.  
2. Installation via le package `.deb` et le dépôt APT interne (`apt-get install alkymia-mcp`).  
3. Gestion des dépendances avec `pip install -r requirements.txt` et `mvn dependency:resolve`.  
4. Configuration des fichiers `config.yaml` et `.env` (clé `MCP_API_KEY`, `DB_URL`).  
5. Procédure de vérification automatisée (`./scripts/mcp‑verify.sh`).  

---

## Module 2 – Architecture du toolkit et flux de données  
**Objectif mesurable** : L’apprenant décrit le diagramme de séquence du traitement d’une requête HTTP vers un handler, identifie les composants critiques et explique le rôle du bus d’événements (`EventBus`).  

**Notions couvertes**  
1. Structure en couches : API Gateway → Dispatcher → Handler → Persistence Layer.  
2. Modèle de messages (`MessageDTO`) et sérialisation JSON via Jackson.  
3. Bus d’événements interne (implémentation basée sur `Guava EventBus`).  
4. Gestion des transactions avec Spring Boot (annotation `@Transactional`).  
5. Points d’extension : interfaces `IHandler`, `IProcessor`.  

---

## Module 3 – Développement d’un handler personnalisé  
**Objectif mesurable** : L’apprenant crée, compile et déploie un nouveau handler « SentimentAnalyzer » respectant l’interface `IHandler`, le teste avec JUnit 5 (couverture suffisante) et le rend disponible via le registre dynamique.  

**Notions couvertes**  
1. Implémentation de `IHandler.handle(MessageDTO)` et gestion des exceptions (`HandlerException`).  
2. Utilisation du SDK NLP.  
3. Enregistrement au `HandlerRegistry` (méthode `registerHandler`).  
4. Tests unitaires avec `@SpringBootTest` et `MockMvc`.  
5. Packaging du handler dans un JAR et chargement dynamique avec `URLClassLoader`.  

---

## Module 4 – Intégration, tests fonctionnels et CI/CD  
**Objectif mesurable** : L’apprenant ajoute le handler au pipeline GitLab CI, configure les jobs `build`, `test` et `deploy‑docker`, et valide le déploiement sur un cluster Kubernetes en observant le pod `mcp-sentiment-analyzer`.  

**Notions couvertes**  
1. Fichier `.gitlab-ci.yml` avec stages `compile`, `unit_test`, `docker_build`, `k8s_deploy`.  
2. Construction d’une image Docker multi‑stage (`Dockerfile` avec `builder` et `runtime`).  
3.  

---

## Module 1 — contenu

## Module 1 – Installation, configuration et validation de l’environnement  

### 1.1 Prérequis système  

| Composant | Vérification |
|-----------|--------------|
| **Ubuntu** | `lsb_release -rs` |
| **Python** | `python3 --version` |
| **Java** | `java -version` |
| **Docker** | `docker --version` |
| **PostgreSQL** | `psql --version` |

> **Note** : les paquets `python3-pip`, `openjdk-17-jdk`, `docker.io` et `postgresql` sont disponibles dans les dépôts officiels d’Ubuntu.  

```bash
sudo apt update
sudo apt install -y python3-pip openjdk-17-jdk docker.io postgresql
```

#### 1.1.1 Vérification des services  

```bash
# Docker daemon
systemctl is-active --quiet docker && echo "Docker OK" || echo "Docker KO"

# PostgreSQL
sudo -u postgres psql -c "SELECT version();" \
  && echo "PostgreSQL OK" || echo "PostgreSQL KO"
```

### 1.2 Installation du toolkit AlkymIA‑OS MCP  

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
sudo apt-get install -y alkymia-mcp
```

> **Vérification** : le binaire `mcp` doit être présent dans `/usr/local/bin/mcp`.  

```bash
which mcp && mcp --version
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

Le projet Java utilise Maven. Le wrapper est fourni (`mvnw`).  

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
|-----------|------------------|--------|

---

## Module 2 — contenu

## 2.1 Structure en couches  

| Couche | Responsabilité | Technologie principale |
|--------|----------------|------------------------|
| **API Gateway** | Expose les points d’entrée HTTP, authentifie, valide le schéma JSON. | Spring Boot, Spring WebFlux (optionnel) |
| **Dispatcher** | Reçoit le `MessageDTO`, sélectionne le handler approprié via `HandlerRegistry`, publie l’événement sur `EventBus`. | Spring DI, Guava `EventBus` |
| **Handler** | Implémente `IHandler.handle(MessageDTO)`. Contient la logique métier (ex. appel à un service externe). | Java, SDK métier |
| **Persistence Layer** | Gère la lecture/écriture des entités, assure la cohérence transactionnelle. | Spring Data JPA, PostgreSQL |

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
 * La sérialisation/désérialisation est assurée par Jackson.
 */
public final class MessageDTO {

    /** Identifiant unique fourni par le client (UUID). */
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
* **Serialisation des dates** : Jackson utilise le module `JavaTimeModule`. Le `ObjectMapper` du projet doit être configuré :  

```java
ObjectMapper mapper = new ObjectMapper()
        .registerModule(new JavaTimeModule())
        .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
```

---

## 2.3 Bus d’événements interne (`EventBus`)  

Le MCP utilise **Guava EventBus**. Le bus est déclaré comme bean singleton afin d’être partagé entre le dispatcher et tous les handlers.

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