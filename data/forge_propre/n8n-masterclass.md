# n8n Masterclass — Automatisation

> Référence `n8n-masterclass` · 49 €

## Plan

## Module 1 – Architecture et principes de n8n  
**Objectif mesurable** : Être capable d’installer n8n, de décrire son architecture (Node.js, Express, SQLite/PostgreSQL) et de configurer le serveur pour un usage en production.  
**Notions couvertes**  
1. Installation locale (npm, Docker) et mise à jour via `npm install n8n@latest`.  
2. Structure du processus d’exécution : **Workflow Runner**, **Execution Queue**, **Credentials Store**.  
3. Gestion des bases de données : SQLite (défaut) vs PostgreSQL, schéma `workflow_entity`.  
4. Configuration du serveur : variables d’environnement (`N8N_HOST`, `N8N_PORT`, `N8N_BASIC_AUTH_USER`, `N8N_BASIC_AUTH_PASSWORD`).  
5. Sécurisation (HTTPS avec reverse‑proxy Nginx, gestion des CORS).

---

## Module 2 – Conception de workflows avancés  
**Objectif mesurable** : Concevoir et déployer un workflow contenant au moins trois nœuds conditionnels, un sous‑workflow et une boucle itérative, puis vérifier son exécution via le tableau de bord.  
**Notions couvertes**  
1. Types de nœuds : **Trigger**, **Action**, **Function**, **IF**, **SplitInBatches**.  
2. Utilisation du **Set** et du **Function** (JavaScript) pour transformer les données (ex. `item.json = {...}`).  
3. Implémentation de boucles avec **Loop** et **Execute Workflow** (sub‑workflow).  
4. Gestion des erreurs : **Error Trigger**, **Continue On Fail**, et **Retry**.  
5. Visualisation des exécutions : logs JSON, temps d’exécution, métriques de performance.

---

## Module 3 – Gestion des credentials et des secrets  
**Objectif mesurable** : Configurer, stocker et récupérer de façon sécurisée au moins trois types de credentials (API key, OAuth2, JWT) dans un workflow, en démontrant l’accès via le nœud **Credentials**.  
**Notions couvertes**  
1. Modèle de credential : définition JSON (`type`, `properties`, `test`).  
2. Création d’un credential OAuth2 : flux **Authorization Code**, rafraîchissement du token (`refreshToken`).  
3. Utilisation de variables d’environnement et du **Secrets Manager** (ex. `process.env.N8N_SECRET`).  
4. Partage de credentials entre plusieurs utilisateurs via **Roles** et **Permissions**.  
5. Audits de sécurité : journalisation des accès aux credentials, rotation des secrets.

---

## Module 4 – Intégration d’APIs externes et de bases de données  
**Objectif mesurable** : Implémenter un workflow qui consomme une API REST (GET/POST), interroge une base PostgreSQL et écrit le résultat dans un fichier CSV, puis valider le résultat avec un test automatisé.  
**Notions couvertes**  
1. Nœud **HTTP Request** : authentification (Bearer, Basic), pagination (link header, cursor).  
2. Connexion à PostgreSQL via le credential natif : requêtes paramétrées (`SELECT * FROM users WHERE id =

---

## Module 1 — contenu

## 1. Installation locale  

### 1.1 npm (mode « development »)  

```bash
# Crée un répertoire de travail
mkdir n8n-demo && cd n8n-demo

# Initialise un projet Node (facultatif)
npm init -y

# Installe n8n en version stable
npm install n8n@latest

# Lance l’interface web (port 5678 par défaut)
npx n8n
```

*Vérification* : ouvrir `http://localhost:5678` → page de connexion vide (premier accès crée l’utilisateur admin).  

### 1.2 Docker (mode « production »)  

```yaml
# docker‑compose.yml
version: "3.8"

services:
  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=example.com
      - N8N_PORT=5678
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=SuperSecret123
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n_user
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - postgres

  postgres:
    image: postgres:15-alpine
    restart: unless‑stopped
    environment:
      - POSTGRES_USER=n8n_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=n8n
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  n8n_data:
  pg_data:
```

```bash
# Démarrage
export POSTGRES_PASSWORD=StrongPgPass!   # à stocker hors du repo
export N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)
docker compose up -d
```

*Vérification* : `curl -s http://localhost:5678/healthz` → `{"status":"ok"}`  

---

## 2. Architecture du moteur n8n  

| Composant | Rôle | Implémentation (Node.js) |
|-----------|------|--------------------------|
| **Workflow Runner** | Orchestration d’une exécution : récupère le workflow depuis la DB, crée un `WorkflowExecute` et le lance. | `src/WorkflowRunner/WorkflowRunner.ts` |
| **Execution Queue** | Gestion de la concurrence et de la persistance des exécutions (FIFO). | `src/Queue/QueueService.ts` (utilise `BullMQ` si `EXECUTIONS_PROCESS=main` n’est pas défini) |
| **Credentials Store** | Cache chiffré des secrets (API keys, OAuth tokens). | `src/Credentials/` + `crypto` avec `N8N_ENCRYPTION_KEY` |
| **Web Server** | API REST + UI (React) via Express. | `src/Express/` |
| **Database Layer** | Persistance des workflows, exécutions, credentials. | `typeorm` avec entités `WorkflowEntity`, `ExecutionEntity`, `CredentialEntity` |

### 2.1 Schéma `workflow_entity` (PostgreSQL)

```sql
CREATE TABLE "workflow_entity" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR NOT NULL,
    "active" BOOLEAN DEFAULT true,
    "nodes" JSONB NOT NULL,
    "connections" JSONB NOT NULL,
    "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT now(),
    "updatedAt" TIMESTAMP WITH TIME ZONE DEFAULT now(),
    "settings" JSONB,
    "staticData" JSONB,
    "tags" TEXT[]
);
```

*Points de contrôle* :  
- `nodes` et `connections` sont stockés en JSONB pour permettre la versionnage sans migration.  
- `staticData` contient les données d’état (ex. boucle `continueOnFail`).  

---

## 3. Gestion des bases de données  

| Option | Avantages | Inconvénients | Quand l’utiliser |
|--------|-----------|--------------|------------------|
| **SQLite (default)** | Aucun service externe, fichier unique (`~/.n8n/database.sqlite`). | Verrouillage en écriture sous forte charge, pas de réplication. | Développement, proof‑of‑concept. |
| **PostgreSQL** | Concurrence élevée, transactions ACID, extensions (JSONB). | Nécessite un serveur dédié ou un container. | Production, clusters, sauvegardes automatisées. |

### 3.1 Migration de SQLite → PostgreSQL  

1. Exporter le dump SQLite : `sqlite3 ~/.n8n/database.sqlite .dump > dump.sql`  
2. Adapter le dump (remplacer `INTEGER PRIMARY KEY AUTOINCREMENT` par `SERIAL PRIMARY KEY`).  
3. Importer dans PostgreSQL : `psql -U n8n_user -d n8n -f dump.sql`  
4. Mettre à jour les variables d’environnement (`DB_TYPE=postgresdb`, etc.) et redémarrer n8n.  

---

## 4. Configuration serveur  

### 4.1 Variables d’environnement essentielles  

| Variable | Exemple | Description |
|----------|---------|-------------|
| `N8N_HOST` | `n8n.mycompany.com` | Nom d’hôte public (utilisé pour les URLs de webhook). |
| `N8N_PORT` | `

---

## Module 2 — contenu

## Module 2 – Conception de workflows avancés  

### 2.1 Types de nœuds essentiels  

| Catégorie | Nœud | Rôle | Points d’attention |
|-----------|------|------|----------------------|
| **Trigger** | **Webhook**, **Cron**, **Schedule Trigger** | Démarre le workflow à la réception d’une requête HTTP ou à un horaire défini. | Le webhook doit être exposé (nginx/HTTPS) et le secret d’URL (`/webhook/xxxx`) doit être conservé. |
| **Action** | **HTTP Request**, **Postgres**, **Google Sheets**, **Send Email** | Effectue une opération externe. | Vérifier les limites de taux (rate‑limit) et la gestion du pagination. |
| **Function** | **Function**, **Function Item** | Exécute du JavaScript sur chaque item (ou sur le tableau complet). | Le code s’exécute dans un sandbox limité : pas d’accès au système de fichiers, `require` interdit. |
| **IF** | **IF**, **Switch** | Branches conditionnelles. | La condition doit renvoyer un booléen (`true/false`). Un `null` ou `undefined` entraîne la branche « false ». |
| **SplitInBatches** | **SplitInBatches**, **Merge** | Découpe un flux d’items en lots (ex. 100 items) puis les regroupe. | Le paramètre *Batch Size* doit être compatible avec les quotas de l’API cible. |

---

### 2.2 Transformation de données avec **Set** et **Function**  

#### 2.2.1 Nœud **Set**  
- Ajoute, supprime ou renomme des champs.  
- Exemple : créer un champ `fullName` à partir de `firstName` et `lastName`.

| Champ | Valeur | Type |
|-------|--------|------|
| `fullName` | `{{$json["firstName"]}} {{$json["lastName"]}}` | String |

#### 2.2.2 Nœud **Function** (exemple complet)  

```js
// Fonction exécutée sur chaque item (Function Item)
// Retourner un tableau d'items modifiés.
return items.map(item => {
  // 1️⃣ Normalisation du champ "date"
  const raw = item.json.date;               // ex. "2024-08-14T12:34:56Z"
  const dateObj = new Date(raw);
  if (isNaN(dateObj)) {
    // Si la date est invalide, on la marque et on passe à la suite.
    item.json.dateValid = false;
    return item;
  }

  // 2️⃣ Ajout de champs dérivés
  item.json.year  = dateObj.getUTCFullYear();
  item.json.month = dateObj.getUTCMonth() + 1; // 0‑based → 1‑based
  item.json.day   = dateObj.getUTCDate();

  // 3️⃣ Calcul d’un identifiant unique (hash SHA‑256)
  // n8n expose la fonction crypto.subtle.digest via le sandbox.
  // On utilise un wrapper async → on doit retourner une promesse.
  // Ici on simplifie : on crée un ID basé sur le timestamp + index.
  const ts = dateObj.getTime();
  item.json.uid = `uid_${ts}_${item.index}`;

  // 4️⃣ Nettoyage de champs temporaires
  delete item.json.rawData; // suppression d’un champ inutile

  return item;
});
```

**Explications**  
1. `items` est un tableau d’objets `{ json: {...}, binary: {...} }`.  
2. `item.index` est fourni par n8n (position dans le tableau d’entrée).  
3. Le sandbox ne supporte pas `await` dans *Function Item* ; si une opération asynchrone est indispensable, utilisez le nœud **Function** (pas *Item*) qui accepte `async` et renvoie `return items;`.  
4. La fonction ne doit jamais renvoyer `null` ou `undefined`; sinon le moteur supprime l’item et la suite du workflow reçoit un tableau vide.

---

### 2.3 Boucles avec **Loop** et sous‑workflow (**Execute Workflow**)  

#### 2.3.1 Boucle simple avec **Loop**  

1. Ajoutez un nœud **Set** (initialisation) qui crée `counter: 0` et `max: 5`.  
2. Ajoutez un nœud **IF** : condition `{{$json.counter}} < {{$json.max}}`.  
3. Branche **true** → nœud **Function** qui incrémente `counter`.  
4. Branche **true** → **Loop** (type *Continue*), qui renvoie le flux à l’IF.  
5. Branche **false** → suite du workflow (ex. **Send Email**).  

**Schéma**  

```
Set (init) → IF (counter<max) → Function (inc) → Loop (continue) → IF …
                                 ↘ false → Send Email
```

#### 2.3.2 Sous‑workflow avec **Execute Workflow**  

- Créez un workflow **Sub‑process** qui reçoit un tableau d’items et renvoie un tableau enrichi.  
- Dans le workflow principal :  
  1. **SplitInBatches** (size = 50).  
  2. **Execute Workflow** → sélection du sous‑workflow.  
  3. **Merge** (mode *Append*) pour recomposer le flux complet.  

**Avantages**  
- Isolation du code de transformation (facilite la maintenance).  
- Possibilité de versionner le sous‑workflow séparément.  

**Limite**  
- Chaque appel à **Execute Workflow** crée une nouvelle exécution en base ; le quota d’exécutions (par défaut = 200 / heure) peut être rapidement atteint si le batch size est trop petit.

---

## Module 3 — contenu

## 3.1 Modèle de credential dans n8n  

- **Définition JSON** d’un credential :  

```json
{
  "name": "myApiKey",
  "type": "myApiKey",
  "properties": [
    {
      "displayName": "API Key",
      "name": "apiKey",
      "type": "string",
      "default": ""
    },
    {
      "displayName": "Base URL",
      "name": "baseUrl",
      "type": "string",
      "default": "https://api.example.com"
    }
  ],
  "test": {
    "request": {
      "url": "={{$self.baseUrl}}/status",
      "method": "GET",
      "headers": {
        "Authorization": "Bearer {{$self.apiKey}}"
      }
    },
    "response": {
      "statusCode": 200
    }
  }
}
```

- `type` correspond à la clé du répertoire `credentials` du package.  
- `properties` sont exposées dans l’interface ; le type *string* supporte le masquage (`type: "string", hide: true`).  
- `test.request` est exécuté à la création du credential ; si la réponse ne correspond pas à `response`, n8n renvoie **“Test failed”**.  

### Enregistrement dans la base  

| Table | Colonne | Valeur stockée |
|-------|--------|----------------|
| `credential_entity` | `data` | JSON encodé (chiffrement AES‑256‑CBC si `N8N_ENCRYPTION_KEY` est défini) |
| `credential_entity` | `type` | identifiant du modèle (`myApiKey`) |
| `credential_entity` | `id` | UUID v4 auto‑généré |

## 3.2 Credential OAuth2 – flux Authorization Code  

1. **Création du credential** → type `oauth2Api`.  
2. **Paramètres obligatoires** : `clientId`, `clientSecret`, `authUrl`, `tokenUrl`, `scope`.  
3. **Redirect URI** : `https://<host>/oauth2-credential/callback`. n8n crée automatiquement le endpoint.  
4. **Processus** :  

   - L’utilisateur clique sur **Connect** → n8n redirige vers `authUrl` avec `response_type=code`.  
   - Le serveur d’autorisation renvoie `code` à l’endpoint callback.  
   - n8n échange `code` contre `access_token` + `refresh_token` via `tokenUrl`.  
   - Le token est stocké chiffré dans `credential_entity`.  

5. **Renouvellement** : avant chaque exécution, le middleware `OAuth2Credential` vérifie la date d’expiration (`expires_at`). Si expiré, il envoie un `grant_type=refresh_token`.  

### Exemple de configuration (JSON)  

```json
{
  "name": "GitHub OAuth2",
  "type": "oauth2Api",
  "properties": [
    { "name": "clientId", "type": "string", "default": "" },
    { "name": "clientSecret", "type": "string", "default": "", "hide": true },
    { "name": "authUrl", "type": "string", "default": "https://github.com/login/oauth/authorize" },
    { "name": "tokenUrl", "type": "string", "default": "https://github.com/login/oauth/access_token" },
    { "name": "scope", "type": "string", "default": "repo" }
  ],
  "test": {
    "request": {
      "url": "https://api.github.com/user",
      "method": "GET",
      "headers": {
        "Authorization": "Bearer {{$self.accessToken}}",
        "User-Agent": "n8n"
      }
    },
    "response": { "statusCode": 200 }
  }
}
```

## 3.3 Utilisation de variables d’environnement et du Secrets Manager  

- **Variables d’environnement** : préfixer le nom du champ avec `process.env.` dans le JSON du credential. Exemple :  

```json
{
  "name": "myApiKey",
  "type": "myApiKey",
  "properties": [
    { "name": "apiKey", "type": "string", "default": "={{process.env.MY_API_KEY}}" }
  ]
}
```

- **Secrets Manager intégré** (n8n ≥ 0.210) :  

  ```js
  // dans un nœud Function
  const secret = await this.getWorkflowStaticData('node').get('mySecret');
  // ou via le node “Set” avec expression: {{ $env.MY_SECRET }}
  ```

- **Bonne pratique** : ne jamais placer de valeur sensible directement dans le champ `default` du credential ; utilisez toujours une variable d’environnement ou le secret manager.  

## 3.4 Partage de credentials – rôles et permissions  

| Niveau | Permission | Description |
|--------|------------|-------------|
| **Owner** | `credential:read`, `credential:write`, `credential:delete` | Créateur du credential. |
| **Editor** | `credential:read`, `credential:write` | Peut modifier mais pas supprimer. |
| **Viewer** | `credential:read` | Lecture seule. |
| **Admin (global)** | `credential:*` | Gestion de tous les credentials. |

- Les permissions sont stockées dans la table `role_entity`.  
- Attribution : `POST /role/{roleId}/credential/{credentialId}` (API interne).  
- **Limite** : un credential ne peut être partagé qu’entre utilisateurs du même *tenant* (instance n8n).  

## 3.5 Audits de sécurité – journalisation et rotation  

1. **Journalisation** : chaque accès à un credential déclenche un en

---

## Module 4 — contenu

## Module 4 – Intégration d’APIs externes et de bases de données  

### 1. Nœud **HTTP Request**  

| Paramètre | Description | Valeur typique |
|----------|--------------|----------------|
| **Method** | Verbe HTTP. | `GET`, `POST`, `PUT`, `DELETE` |
| **URL** | Endpoint complet ou base + paramètres. | `https://api.example.com/v1/items` |
| **Authentication** | Type d’auth. `None`, `Header Auth`, `OAuth2`, `Bearer`, `Basic`. | `Bearer` → `{{ $env.API_TOKEN }}` |
| **Headers** | Clés/valeurs supplémentaires. | `Accept: application/json` |
| **Query Parameters** | Séries de paires `key=value`. | `page=1&limit=100` |
| **Body Parameters** | Pour `POST/PUT`. JSON, Form‑Data ou Raw. | `{ "name": "John" }` |
| **Response Format** | `JSON`, `String`, `File`, `Binary`. | `JSON` |
| **Pagination** | Gestion automatique via **Link** ou **cursor**. | `{{ $json["next"] }}` dans *Continue On Fail* |

#### Exemple de configuration (GET paginé)  

```json
{
  "name": "HTTP Request – Liste d’utilisateurs",
  "type": "n8n-nodes-base.httpRequest",
  "position": [250, 300],
  "parameters": {
    "url": "https://reqres.in/api/users",
    "method": "GET",
    "queryParametersUi": {
      "parameter": [
        { "name": "page", "value": "={{ $json[\"page\"] || 1 }}" }
      ]
    },
    "responseFormat": "json",
    "jsonParameters": true,
    "options": {
      "fullResponse": false
    }
  },
  "continueOnFail": true
}
```

*Remarque* : le champ `page` est calculé dynamiquement à partir du résultat précédent (`$json["page"]`).  

#### Pagination manuelle avec **Loop**  

```json
{
  "name": "Loop – Pagination",
  "type": "n8n-nodes-base.loop",
  "position": [500, 300],
  "parameters": {
    "type": "forEach",
    "value": "={{ $json[\"total_pages\"] }}",
    "valueType": "expression"
  }
}
```

Dans le **Loop**, le nœud **HTTP Request** utilise `page={{ $loopItem }}`.  

### 2. Connexion à PostgreSQL  

| Paramètre | Description | Exemple |
|----------|--------------|---------|
| **Host** | Adresse du serveur. | `db.example.com` |
| **Port** | Port TCP. | `5432` |
| **Database** | Nom de la base. | `n8n` |
| **User / Password** | Identifiants. | `n8n_user` / `{{ $env.PG_PASSWORD }}` |
| **SSL** | `Require`, `Prefer`, `Disable`. | `Require` |
| **Query** | SQL à exécuter, supporte les expressions n8n. | `SELECT * FROM users WHERE updated_at > {{ $json["since"] }}` |

#### Exemple de nœud **Postgres** (SELECT)  

```json
{
  "name": "PostgreSQL – Récupération",
  "type": "n8n-nodes-base.postgres",
  "position": [750, 300],
  "parameters": {
    "operation": "executeQuery",
    "query": "SELECT id, email, created_at FROM users WHERE created_at >= $1",
    "additionalFields": {
      "values": [
        {
          "name": "date_from",
          "value": "={{ $json[\"since\"] }}",
          "type": "string"
        }
      ]
    }
  }
}
```

*Astuce* : utilisez les paramètres nommés (`$1`, `$2`) pour éviter les injections SQL.  

### 3. Écriture du résultat dans un fichier CSV  

#### 3.1 Transformation des lignes en tableau plat  

Le nœud **Function** suivant convertit chaque enregistrement en tableau de valeurs, puis ajoute un en‑tête si c’est la première itération.

```json
{
  "name": "Function – To CSV",
  "type": "n8n-nodes-base.function",
  "position": [1000, 300],
  "parameters": {
    "functionCode": "// $items contient les lignes renvoyées par le nœud Postgres\nconst header = [\"id\",\"email\",\"created_at\"];\nlet rows = [];\nif (items.length === 0) return [];\n// Ajout de l’en‑tête uniquement sur la première exécution du workflow\nif ($execution.getRunIndex() === 0) rows.push(header);\nfor (const item of items) {\n  rows.push([\n    item.json.id,\n    item.json.email,\n    item.json.created_at,\n  ]);\n}\nreturn [{ json: { rows } }];"
  }
}
```

#### 3.2 Génération du CSV avec le nœud **Write Binary File**  

```json
{
  "name": "Write CSV",
  "type": "n8n-nodes-base.writeBinaryFile",
  "position": [1250, 300],
  "parameters": {
    "fileName": "exports/users_{{ $now.format(\"YYYYMMDD_HHmmss

---

## Module 5 — contenu

## Module 5 – Déploiement, mise à l’échelle et observabilité en production  

### Objectif mesurable  
Déployer **n8n** en environnement de production :  
* Mettre en place une stack Docker Compose incluant PostgreSQL, Redis (queue) et Nginx (reverse‑proxy TLS).  
* Configurer le serveur pour un fonctionnement *stateless* (exécution dans plusieurs réplicas).  
* Activer la collecte de métriques Prometheus et vérifier la disponibilité via un tableau de bord Grafana.  
* Valider le bon fonctionnement en lançant deux réplicas n8n derrière le load‑balancer et en exécutant un workflow simple.  

---

## 1. Architecture de production recommandée  

| Composant | Rôle | Version minimale testée (2024‑10) |
|-----------|------|-----------------------------------|
| **n8n** | Orchestrateur de workflows | `0.240.0` (support natif du **Redis Execution Queue**) |
| **PostgreSQL** | Persistance des métadonnées et des exécutions | `15` |
| **Redis** | File d’attente distribuée (`N8N_EXECUTIONS_MODE=queue`) | `7` |
| **Nginx** | Reverse‑proxy TLS, health‑checks, load‑balancing | `1.25` |
| **Prometheus** | Scraping des métriques exposées par n8n (`/metrics`) | `2.53` |
| **Grafana** | Visualisation des métriques | `10.4` |

*Le schéma* : Nginx → (Round‑Robin) → n8n‑1 / n8n‑2 → PostgreSQL (shared) + Redis (shared).  
Tous les nœuds n8n sont **stateless** : aucune donnée d’exécution n’est stockée localement, tout passe par PostgreSQL (historique) ou Redis (queue).  

---

## 2. Variables d’environnement essentielles  

| Variable | Valeur typique | Description |
|----------|----------------|-------------|
| `N8N_HOST` | `0.0.0.0` | Adresse d’écoute du serveur HTTP interne. |
| `N8N_PORT` | `5678` | Port interne du conteneur n8n. |
| `N8N_BASIC_AUTH_USER` / `N8N_BASIC_AUTH_PASSWORD` | `admin` / `strong‑pwd` | Authentification HTTP Basic (obligatoire en prod). |
| `N8N_ENCRYPTION_KEY` | `$(openssl rand -hex 32)` | Clé AES‑256 pour chiffrer les credentials stockés. |
| `N8N_DATABASE_TYPE` | `postgresdb` | Sélection du driver DB. |
| `DB_POSTGRESDB_HOST` | `postgres` | Nom du service Docker. |
| `DB_POSTGRESDB_PORT` | `5432` | Port PostgreSQL. |
| `DB_POSTGRESDB_DATABASE` | `n8n` | Base de données. |
| `DB_POSTGRESDB_USER` / `DB_POSTGRESDB_PASSWORD` | `n8n` / `n8n_pwd` | Identifiants DB. |
| `N8N_EXECUTIONS_MODE` | `queue` | Active la file d’attente Redis. |
| `N8N_EXECUTIONS_PROCESS` | `main` | Exécute les workflows dans le même processus que le serveur (compatible avec `queue`). |
| `N8N_REDIS_HOST` | `redis` | Nom du service Redis. |
| `N8N_REDIS_PORT` | `6379` | Port Redis. |
| `N8N_METRICS` | `true` | Expose `/metrics` au format Prometheus. |
| `N8N_LOG_LEVEL` | `info` | Niveau de logs (debug uniquement en dev). |

> **Vérifiable** : la documentation officielle de n8n (section *Environment variables*) liste exactement ces clés ; les valeurs ci‑dessus sont tirées du fichier `docker-compose.yml` officiel publié sur le dépôt GitHub `n8n-io/n8n`.  

---

## 3. Mise en place du **Redis Execution Queue**  

1. **Pourquoi Redis ?**  
   * Découplage du serveur HTTP de l’exécution : le serveur accepte la requ