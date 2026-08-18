# Model Context Protocol (MCP)

> Référence `mcp-protocol` · 79 €

## Plan

## Module 1 – Architecture du Model Context Protocol (MCP)  
**Objectif** : Être capable de dessiner, en UML ou diagramme d’architecture, les trois couches principales du MCP et d’identifier les points d’extension.  
- Structure de la couche de transport (gRPC / HTTP 2)  
- Modèle de sérialisation JSON‑LD vs. Protobuf  
- Gestion des métadonnées de contexte (URI, vocabulaire, version)  

## Module 2 – Modélisation des contextes et des entités  
**Objectif** : Créer et valider un fichier de contexte MCP conforme au schéma JSON‑Schema v2020‑12.  
- Définition des vocabulaires RDF et SKOS intégrés au MCP  
- Mapping entre classes métier et types MCP (type = « entity », « relation »)  
- Validation syntaxique et sémantique avec Ajv ou jsonschema‑tools  

## Module 3 – Implémentation du serveur MCP  
**Objectif** : Déployer une API MCP fonctionnelle (Node.js / Python) et vérifier son comportement via tests d’intégration automatisés.  
- Implémentation du dispatcher de requêtes (router, middleware)  
- Gestion des sessions de contexte (cookies, JWT, OAuth 2.0)  
- Contrôle de la cohérence transactionnelle (optimistic lock, versioning)  

## Module 4 – Consommation du protocole côté client  
**Objectif** : Écrire un SDK client (TypeScript ou Python) capable de créer, lire, mettre à jour et supprimer des entités MCP avec 95 % de couverture de tests unitaires.  
- Construction des payloads selon le schéma de contexte  
- Gestion des erreurs de validation et de négociation de version  
- Caching local des contextes (ETag, If‑None‑Match)  

## Module 5 – Sécurité, performance et gouvernance  
**Objectif** : Auditer une implémentation MCP et proposer trois améliorations mesurables (ex. réduction du temps de latence de 30 %, renforcement du chiffrement, mise en place d’un registre de versions).  
- Chiffrement TLS 1.3 et signatures JWS des messages MCP  
- Limitation de débit et quotas par client (token bucket)  
- Stratégies de versionnage de contexte (semantic versioning, migration scripts)

---

## Module 1 — contenu

## 1.1 Architecture générale du MCP  

Le MCP repose sur trois couches empilées :  

| Couche | Responsabilité | Technologies typiques | Points d’extension |
|--------|-----------------|--------------------------|--------------------|
| **Transport** | Transport fiable, multiplexage, flow‑control | gRPC sur HTTP/2, HTTP/2 + REST, ALPN TLS 1.3 | Intercepteurs (interceptors), plug‑in de transport (WebSocket, QUIC) |
| **Sérialisation** | Codage/décodage des messages, négociation de format | Protobuf 3 (binary), JSON‑LD (textuel) | Encodeurs personnalisés, schémas de conversion (JSON↔Protobuf) |
| **Métadonnées de contexte** | Gestion du vocabulaire, version, URI de contexte | JSON‑LD @context, en‑tête HTTP (`Mcp-Context`, `Mcp-Version`) | Registries de vocabulaire, extensions de versionning, hooks de validation |

```
+----------------------------+   <-- Application (client / serveur)
|  Métadonnées de contexte   |
|  (Mcp-Context, Mcp-Version)|
+------------+---------------+
|   Sérialisation (JSON‑LD   |
|   ↔ Protobuf)              |
+------------+---------------+
|   Transport (gRPC/HTTP2)  |
+----------------------------+
```

*Diagramme UML simplifié (notation de composants)*  

```
[Client] --> (McpTransport) --> (McpSerializer) --> [Server]
[Client] <-- (McpTransport) <-- (McpSerializer) <-- [Server]

McpTransport «interface» 
   + intercept(request, response)
   + negotiateProtocol()

McpSerializer «interface»
   + encode(entity) : Buffer|String
   + decode(payload) : Entity
```

---

## 1.2 Couche de transport  

### 1.2.1 gRPC sur HTTP/2  

* gRPC utilise HTTP/2 en mode binaire, chaque appel est un **stream** identifié par un **stream‑id**.  
* Le **service definition** (fichier `.proto`) décrit les RPC et les messages.  
* Le **interceptor** côté serveur permet d’injecter les métadonnées MCP (`Mcp-Context`, `Mcp-Version`) dans le `metadata` gRPC.  

#### Exemple de serveur Node.js (gRPC)  

```js
// server.js – gRPC 1.56+, Node.js 20
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');

// 1️⃣ Chargement du .proto
const packageDef = protoLoader.loadSync(
  path.join(__dirname, 'mcp.proto'),
  { keepCase: true, longs: String, enums: String, defaults: true, oneofs: true }
);
const mcpProto = grpc.loadPackageDefinition(packageDef).mcp;

// 2️⃣ Implémentation du service
const serviceImpl = {
  // RPC unary : CreateEntity
  CreateEntity: (call, callback) => {
    // Extraction des métadonnées MCP
    const mcContext = call.metadata.get('mcp-context')[0] || '';
    const mcVersion = call.metadata.get('mcp-version')[0] || '1.0.0';

    // Validation rapide (exemple)
    if (!mcContext.startsWith('http')) {
      return callback({
        code: grpc.status.INVALID_ARGUMENT,
        message: 'Mcp-Context must be a valid URI',
      });
    }

    // Traitement métier (payload déjà décodé en Protobuf)
    const entity = call.request; // { id, type, attributes }

    // Réponse
    callback(null, { status: 'created', id: entity.id });
  },
};

// 3️⃣ Intercepteur global (logging + contrôle d’accès)
function globalInterceptor(options, nextCall) {
  return new grpc.InterceptingCall(nextCall(options), {
    start: function (metadata, listener, next) {
      console.log('→ RPC', options.method_definition.path);
      console.log('Metadata', metadata.getMap());
      next(metadata, {
        onReceiveMessage: (msg) => console.log('← Response', msg),
        onReceiveStatus: (status) => console.log('← Status', status),
      });
    },
  });
}

// 4️⃣ Démarrage du serveur
const server = new grpc.Server();
server.addService(mcpProto.McpService.service, serviceImpl);
server.use(globalInterceptor); // ← point d’extension
const bindAddr = '0.0.0.0:50051';
server.bindAsync(bindAddr, grpc.ServerCredentials.createSsl(
  null, // key/cert can be added here
  null,
  false
), (err, port) => {
  if (err) throw err;
  console.log(`MCP gRPC server listening on ${bindAddr}`);
  server.start();
});
```

*Points clés*  

* `metadata.get('mcp-context')` renvoie un tableau ; on ne garde que le premier élément.  
* L’intercepteur est le **hook** officiel pour ajouter de la journalisation, du tracing ou du contrôle d’accès.  
* TLS 1.3 doit être activé côté serveur (`createSsl` avec certificats).  

### 1.2.2 HTTP/2 + REST (fallback)  

* Le même service peut être exposé via un endpoint HTTP/2 (`/mcp/v1/entities`).  
* Les en‑têtes `Mcp-Context` et `Mcp-Version` sont transmis comme en‑têtes HTTP standards.  
* Le corps du message est **JSON‑LD** ou **Protobuf** encodé en base64 (si binaire).  

#### Exemple d’endpoint Express (Node.js)  

```js
const express = require('express');
const http2 = require('http2');
const bodyParser = require('body-parser');
const app = express();

//

---

## Module 2 — contenu

## 2.1. Principes de base du fichier de contexte MCP  

| Élément | Description | Valeur attendue (exemple) |
|--------|-------------|--------------------------|
| `$id` | URI unique du fichier de contexte. Doit être résolvable (HTTP GET) et stable. | `https://example.com/mcp/context/v1.0.0.json` |
| `$schema` | Référence au méta‑schéma JSON‑Schema 2020‑12. | `https://json-schema.org/draft/2020-12/schema` |
| `@context` | Mapping JSON‑LD vers les vocabulaires RDF/OWL/ SKOS. | `{ "ex": "https://example.com/vocab#", "skos": "http://www.w3.org/2004/02/skos/core#" }` |
| `mcpVersion` | Version sémantique du protocole (MAJOR.MINOR.PATCH). | `"1.2.3"` |
| `definitions` | Schémas réutilisables pour les entités et relations. | *voir 2.2* |
| `entities` | Tableau de définitions d’entités métier (type = `entity`). | *voir 2.2* |
| `relations` | Tableau de définitions de liens (type = `relation`). | *voir 2.2* |

Le fichier **doit** être valide contre le méta‑schéma JSON‑Schema 2020‑12, et **doit** contenir les métadonnées de contexte (`@context`, `mcpVersion`) en plus des définitions métier.

---

## 2.2. Schéma JSON‑Schema de base du contexte MCP  

```json
{
  "$id": "https://example.com/mcp/context/schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MCP Context Schema",
  "type": "object",
  "required": ["$id", "$schema", "@context", "mcpVersion", "entities"],
  "properties": {
    "$id": { "type": "string", "format": "uri-reference" },
    "$schema": { "type": "string", "format": "uri" },
    "@context": {
      "type": "object",
      "minProperties": 1,
      "additionalProperties": { "type": "string", "format": "uri" }
    },
    "mcpVersion": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"
    },
    "entities": {
      "type": "array",
      "items": { "$ref": "#/$defs/entity" },
      "minItems": 1
    },
    "relations": {
      "type": "array",
      "items": { "$ref": "#/$defs/relation" }
    }
  },
  "$defs": {
    "entity": {
      "type": "object",
      "required": ["type", "name", "properties"],
      "properties": {
        "type": { "const": "entity" },
        "name": { "type": "string", "minLength": 1 },
        "description": { "type": "string" },
        "properties": {
          "type": "object",
          "minProperties": 1,
          "additionalProperties": { "$ref": "#/$defs/property" }
        }
      },
      "additionalProperties": false
    },
    "relation": {
      "type": "object",
      "required": ["type", "name", "source", "target"],
      "properties": {
        "type": { "const": "relation" },
        "name": { "type": "string", "minLength": 1 },
        "description": { "type": "string" },
        "source": { "type": "string", "minLength": 1 },
        "target": { "type": "string", "minLength": 1 },
        "properties": {
          "type": "object",
          "additionalProperties": { "$ref": "#/$defs/property" }
        }
      },
      "additionalProperties": false
    },
    "property": {
      "type": "object",
      "required": ["type", "rdfType"],
      "properties": {
        "type": {
          "enum": ["string", "integer", "number", "boolean", "date", "uri"]
        },
        "rdfType": {
          "type": "string",
          "format": "uri"
        },
        "enum": {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 1
        },
        "pattern": { "type": "string" },
        "minimum": { "type": "number" },
        "maximum": { "type": "number" }
      },
      "additionalProperties": false
    }
  }
}
```

*Points clés*  

* `type` = `"entity"` ou `"relation"` est **verrouillé** (`const`).  
* `rdfType` doit être une URI valide pointant vers un terme RDF (ex. `skos:Concept`).  
* Le champ `properties` d’une entité ne doit pas contenir de clé dupliquée.  
* Le méta‑schéma impose `additionalProperties: false` afin d’éviter les attributs orphelins.

---

## 2.3. Exemple complet de fichier de contexte MCP  

```jsonc
{
  "$id": "https://example.com

---

## Module 3 — contenu

## Module 3 – Implémentation du serveur MCP  

### 3.1 Architecture du serveur  

| Composant | Technologie | Rôle |
|-----------|--------------|------|
| **Transport** | gRPC + HTTP/2 (Node .js `@grpc/grpc-js`) | Sérialisation binaire Protobuf, multiplexage, flux bidirectionnel |
| **Router / Dispatcher** | `express` (HTTP / JSON‑LD) + `grpc` server | Enregistrement des services MCP (`CreateEntity`, `ReadEntity`, `UpdateEntity`, `DeleteEntity`, `Query`) |
| **Middleware** | `express.json()`, `helmet`, `cors`, `morgan` | Validation du corps, sécurité des en‑têtes, logs |
| **Session** | JWT signé HS256 ou RS256, stocké dans le cookie `mcp_session` | Authentification, portée (`sub`, `aud`, `exp`), rafraîchissement via endpoint `/auth/refresh` |
| **Persistance** | PostgreSQL + `sequelize` (ou `typeorm`) | Table `entities` (id PK, type, payload JSONB, version INT, created_at, updated_at) |
| **Contrôle de cohérence** | Optimistic lock (`version` column) + transaction SQL (`BEGIN … COMMIT`) | Détection de conflits d’écriture, rejet avec code 409 |

> **Note** : Le serveur expose **deux points d’entrée** :  
> 1. `grpc://host:50051` (binaire)  
> 2. `https://host/api/v1/` (REST, JSON‑LD) – utile pour les clients qui ne supportent pas gRPC.

---

### 3.2 Dispatcher de requêtes (router & middleware)

```js
// server.js – Node.js 20, ECMAScript modules
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import morgan from 'morgan';
import { json } from 'express';
import { verifyJwt, issueJwt } from './auth.js';
import { createEntity, readEntity, updateEntity, deleteEntity } from './handlers.js';
import grpcServer from './grpc-server.js';

const app = express();

// ---------- Middleware global ----------
app.use(helmet());                     // en-têtes de sécurité
app.use(cors({ origin: process.env.CORS_ORIGIN })); // CORS limité
app.use(morgan('combined'));           // logs HTTP
app.use(json({ limit: '2mb' }));       // parsing JSON‑LD, taille max 2 MiB

// ---------- Authentification ----------
app.use(async (req, res, next) => {
  const token = req.cookies?.mcp_session ?? req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Missing token' });
  try {
    req.user = await verifyJwt(token);
    next();
  } catch (e) {
    return res.status(401).json({ error: 'Invalid token' });
  }
});

// ---------- Routes MCP ----------
const router = express.Router();

router.post('/entities', createEntity);          // POST /api/v1/entities
router.get('/entities/:id', readEntity);        // GET  /api/v1/entities/:id
router.patch('/entities/:id', updateEntity);   // PATCH /api/v1/entities/:id
router.delete('/entities/:id', deleteEntity);  // DELETE /api/v1/entities/:id

app.use('/api/v1', router);

// ---------- Error handling ----------
app.use((err, _req, res, _next) => {
  console.error(err);
  const status = err.status ?? 500;
  res.status(status).json({ error: err.message });
});

// ---------- Lancement ----------
const PORT = process.env.PORT ?? 8080;
app.listen(PORT, () => console.log(`REST MCP listening on ${PORT}`));
grpcServer.start(); // démarre le serveur gRPC sur le port 50051
```

#### 3.2.1 Handler d’insertion (exemple complet)

```js
// handlers.js
import { Entity } from './models.js';          // modèle Sequelize
import Ajv from 'ajv';
import schema from './mcp-context-schema.json' assert { type: 'json' };

const ajv = new Ajv({ allErrors: true });
const validate = ajv.compile(schema);

/**
 * POST /entities
 * Corps attendu : JSON‑LD conforme au contexte MCP
 */
export async function createEntity(req, res, next) {
  const payload = req.body;

  // 1️⃣ Validation syntaxique du JSON‑LD
  if (!validate(payload)) {
    const errors = validate.errors.map(e => `${e.instancePath} ${e.message}`).join('; ');
    const err = new Error(`Validation error: ${errors}`);
    err.status = 400;
    return next(err);
  }

  // 2️⃣ Extraction des métadonnées MCP
  const { '@type': type, '@id': id, '@context': context, ...data } = payload;
  if (!type) {
    const err = new Error('Missing @type in payload');
    err.status = 400;
    return next(err);
  }

  // 3️⃣ Insertion atomique + optimistic lock (version = 1)
  try {
    const entity = await Entity.create({
      id: id ?? undefined,               // laisse PostgreSQL générer un UUID si absent
      type,
      context: JSON.stringify(context),   // stockage brut du contexte
      payload: data,
      version: 1,
    });
    res.status(201).json({ '@id': entity.id, version: entity.version });
  } catch (e) {
    if (e.name === 'SequelizeUniqueConstraintError') {
      const err = new Error('Entity already exists');
      err.status = 409;
      return next(err);
    }
    next(e);
  }
}
```

*Points clés*  

* `Ajv` utilise le **JSON‑Schema

---

## Module 4 — contenu

## 4.1 Architecture du SDK client  

| Composant | Rôle | Implémentation typique |
|-----------|------|------------------------|
| **McpClient** | Point d’entrée unique, encapsule l’URL de base, les options d’authentification (JWT ou OAuth 2.0) et le cache d’ETag. | Classe `McpClient` (TS) ou `McpClient` (Python). |
| **RequestBuilder** | Construit le corps JSON‑LD conforme au contexte chargé (vocabulaire, version). | Méthodes `createEntity`, `updateEntity`, etc. |
| **ResponseHandler** | Décode le JSON‑LD, vérifie le champ `@context`, applique la désérialisation vers les modèles métier. | Fonction `parseResponse`. |
| **CacheLayer** | Stocke les contextes (`@context` JSON‑LD) et les ETag associés. Utilise `Map<string, {etag:string, context:any}>`. | Méthodes `getContext`, `setContext`. |
| **ErrorMapper** | Transforme les erreurs HTTP/validation en exceptions métier (`McpValidationError`, `McpConflictError`). | Classe d’erreurs. |

Le SDK expose une API **CRUD** : `create`, `read`, `update`, `delete`. Chaque méthode renvoie une `Promise<T>` (TS) ou un objet (Python) et lève une exception en cas d’erreur HTTP ≥ 400.

---

## 4.2 Construction des payloads  

### 4.2.1 Règles de sérialisation JSON‑LD  

* Le champ racine **`@context`** doit être un URI ou un objet contenant les mappings (`@vocab`, `@base`).  
* Chaque entité possède un **`@type`** (`"entity"` ou `"relation"`).  
* Les identifiants sont exprimés avec **`@id`** au format IRI complet ou compact (`prefix:local`).  
* Les propriétés métier sont déclarées sans préfixe si `@vocab` pointe vers le vocabulaire du contexte.  

> **Référence** : [JSON‑LD 1.1 Specification § 3.1](https://www.w3.org/TR/json-ld11/#the-context).  

### 4.2.2 Exemple de payload (TypeScript)  

```ts
// src/payload.ts
/**
 * Construit le corps JSON‑LD d’une entité « Product ».
 * @param data  objet métier contenant les champs business.
 * @param ctx   URI du contexte (ex. "https://example.com/mcp/v1/context.jsonld").
 * @returns     objet prêt à être sérialisé avec JSON.stringify().
 */
export function buildProductPayload(
  data: {
    id?: string;          // optionnel : si absent, le serveur génère un @id
    name: string;
    price: number;
    category: string;     // valeur du vocabulaire SKOS (ex. "skos:Concept")
  },
  ctx: string = "https://example.com/mcp/v1/context.jsonld"
) {
  const payload: any = {
    "@context": ctx,
    "@type": "entity",               // MCP requiert le type « entity »
    "name": data.name,
    "price": data.price,
    "category": data.category,
  };

  // Ajout de l'identifiant s'il est fourni
  if (data.id) payload["@id"] = data.id;

  // Exemple de mapping explicite (utile si le contexte ne définit pas @vocab)
  // payload["@context"] = {
  //   "@vocab": "https://example.com/vocab#",
  //   "category": { "@id": "skos:Concept", "@type": "@id" }
  // };

  return payload;
}
```

**Utilisation**  

```ts
import { McpClient } from "./client";
import { buildProductPayload } from "./payload";

const client = new McpClient({
  baseUrl: "https://api.example.com/mcp",
  authToken: "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
});

async function createProduct() {
  const payload = buildProductPayload({
    name: "Chaise ergonomique",
    price: 129.99,
    category: "skos:OfficeFurniture"
  });

  const created = await client.create("Product", payload);
  console.log("Created @id:", created["@id"]);
}
```

Le SDK envoie le payload avec l’en‑tête `Content-Type: application/ld+json` (conforme à la spécification MCP v2).  

---

## 4.3 Gestion des erreurs de validation et de négociation de version  

| Code HTTP | Situation | Action du SDK |
|-----------|-----------|---------------|
| **400**   | JSON‑LD non conforme (`@context` manquant, type inconnu). | Lève `McpValidationError` contenant le tableau `errors` retourné par le serveur. |
| **409**   | Conflit de version (`If-Match` ne correspond pas). | Lève `McpConflictError` avec le champ `currentVersion`. |
| **415**   | `Content-Type` non supporté. | Lève `McpUnsupportedMediaTypeError`. |
| **422**

---

## Module 5 — contenu

## Module 5 – Sécurité, performance et gouvernance

### 5.1 Chiffrement TLS 1.3 et signatures JWS des messages MCP  

#### 5.1.1 TLS 1.3 obligatoire  
- **Vérifiable** : RFC 8446 spécifie TLS 1.3. La plupart des serveurs modernes (nginx ≥ 1.13.0, Node ≥ 12, Python ≥ 3.7) le supportent nativement.  
- **Configuration nginx** (exemple minimal) :  

```nginx
server {
    listen 443 ssl http2;
    ssl_protocols TLSv1.3;
    ssl_ciphers TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256;
    ssl_prefer_server_ciphers on;
    ssl_certificate     /etc/ssl/certs/mcp.crt;
    ssl_certificate_key /etc/ssl/private/mcp.key;
    # HSTS (30 jours)
    add_header Strict-Transport-Security "max-age=2592000; includeSubDomains" always;
}
```

- **Piège** : désactiver `ssl_prefer_server_ciphers` force le client à choisir la suite de chiffrement, ce qui peut réintroduire des suites faibles (ex. RSA‑PKCS1).  

#### 5.1.2 Signatures JWS (JSON Web Signature) des payloads  

- **Standard** : RFC 7515. Utilise un algorithme asymétrique (ex. `RS256`) ou symétrique (`HS256`).  
- **Schéma de message MCP** : chaque message doit contenir un champ `jws` contenant le token signé, et le corps réel dans `payload`.  

```json
{
  "jws": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
  ,"payload": {
    "@context": "https://example.com/mcp/context/v1",
    "type": "entity",
    "id": "urn:uuid:123e4567-e89b-12d3-a456-426614174000",
    "attributes": { "name": "Alice" }
  }
}
```

#### 5.1.3 Exemple Node.js – génération et vérification JWS  

```js
// mcp-jws.js – dépendances: npm i jsonwebtoken node-forge
const fs = require('fs');
const jwt = require('jsonwebtoken');

// Chargement des clés PEM (RSA 2048 bits, générées avec openssl)
const privateKey = fs.readFileSync('keys/private.pem');
const publicKey  = fs.readFileSync('keys/public.pem');

/**
 * Signe un payload MCP.
 * @param {Object} payload - Le corps MCP (déjà validé contre le JSON‑Schema)
 * @returns {string} JWS compact
 */
function signMcpPayload(payload) {
  // Header JWS explicite pour éviter les algos par défaut
  const header = { alg: 'RS256', typ: 'JWT' };
  // jwt.sign() encode le header + payload puis signe
  return jwt.sign(payload, privateKey, { algorithm: 'RS256', header });
}

/**
 * Vérifie un JWS et retourne le payload décodé.
 * @param {string} token - JWS compact
 * @throws {Error} si la signature échoue ou si le token est expiré
 * @returns {Object} payload décodé
 */
function verifyMcpJws(token) {
  // jwt.verify() lève une exception en cas d'échec
  return jwt.verify(token, publicKey, { algorithms: ['RS256'] });
}

/* ------------------- usage ------------------- */
const mcpPayload = {
  "@context": "https://example.com/mcp/context/v1",
  type: "entity",
  id: "urn:uuid:123e4567-e89b-12d3-a456-426614174000",
  attributes: { name: "Alice" }
};

const jws = signMcpPayload(mcpPayload);
console.log('JWS:', jws);

const decoded = verifyMcpJws(jws);
console.log('Decoded payload:', decoded);
```

- **Pièges**  
  1. **Expiration** : `jsonwebtoken` ajoute `exp` uniquement si fourni. Omettre `exp` rend le token valable indéfiniment → risque de relecture.  
  2. **Algorithme de fallback** : si l’en‑tête `alg` est manipulé, `jwt.verify` accepte par défaut tout algorithme listé dans `algorithms`. Restreindre explicitement évite les attaques « alg:none ».  
  3. **Clé publique compromise** : rotation de clé doit être planifiée (ex. every 90 jours) et les anciens tokens invalidés via une liste de révocation (CRL ou OCSP).  

### 5.2 Limitation de débit et quotas par client (token bucket)

#### 5.2.1 Algorithme de base  
- **Formule** : chaque client possède un « bucket » de capacité `C` (tokens). Un token est consommé par requête. Le bucket se remplit à un taux `R` (tokens/s). Si le bucket est vide, la requête est rejetée (`429 Too Many Requests`).  
- **Implémentation** (Python / FastAPI) :  

```python
# rate_limiter.py – dépendance: pip install fastapi uvicorn redis
import time
import redis
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()
r = redis.Redis(host='localhost', port=6379, db=0)

# Paramètres du bucket (exemple : 100 req/min → R=1.666 token/s, C=100)
RATE = 1.666
CAPACITY = 100
TOKEN_KEY = "rate:{client_id}"

def get_client_id(request: Request) -> str:
    # Priorité au JWT sub, sinon IP
    auth = request.headers.get("Authorization")