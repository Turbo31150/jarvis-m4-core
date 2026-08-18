# IA pour l'E-commerce & Shopify

> Référence `ia-ecommerce` ·  

## Plan

## Module 1 – Fondamentaux de l’IA appliquée à l’e‑commerce  
**Objectif mesurable** : À l’issue du module, le participant pourra identifier trois cas d’usage IA pertinents pour une boutique Shopify, sélectionner les sources de données correspondantes et formaliser un cahier des charges fonctionnel contenant au moins plusieurs exigences mesurables.  

- Cartographie des processus e‑commerce (acquisition, conversion, fidélisation) où l’IA apporte une valeur ajoutée prouvée (ex. : recommandation produit, prévision de churn).  
- Analyse des données disponibles sur Shopify (produits, commandes, clients) et exigences de conformité RGPD.  
- Méthodologie de définition d’indicateurs de performance (KPIs) IA (précision, taux de conversion, temps de réponse).  
- Sélection de modèles standards (filtrage collaboratif, régression logistique, réseaux de neurones) adaptés aux volumes de données Shopify.  
- Élaboration d’un plan de collecte, de stockage (ex. : Snowflake, BigQuery) et de gouvernance des données.

---

## Module 2 – Architecture et intégration technique avec Shopify  
**Objectif mesurable** : Le participant sera capable de créer, déployer et sécuriser une application privée Shopify qui expose une API REST et une API GraphQL, et d’y connecter un micro‑service IA via webhook en un temps très court.  

- Utilisation de l’API Admin REST et GraphQL de Shopify (authentification OAuth 2.0, pagination, limites de taux).  
- Développement d’une app privée (Node.js ou Python) hébergée sur une plateforme cloud (AWS Lambda, Google Cloud Run).  
- Configuration des webhooks Shopify (order/create, cart/update) pour déclencher des fonctions IA.  
- Gestion des secrets (API keys, JWT) avec HashiCorp Vault ou AWS Secrets Manager.  
- Mise en place d’un pipeline CI/CD (GitHub Actions, Docker) pour le déploiement automatisé de l’app.

---

## Module 3 – Systèmes de recommandation et personnalisation en temps réel  
**Objectif mesurable** : Le participant pourra implémenter un moteur de recommandation produit basé sur le filtrage collaboratif et les embeddings de texte, l’intégrer dans le thème Shopify via Liquid et mesurer une amélioration notable du taux de conversion.

---

## Module 1 — contenu

## 1. Cartographie des processus e‑commerce où l’IA crée de la valeur  

| Processus | Sous‑processus | Impact IA typique | Métrique clé |
|----------|---------------|-------------------|--------------|
| **Acquisition** | Recherche organique, campagnes SEA, email acquisition | **Targeting prédictif** (look‑alike, look‑back) | CTR, CPA, ROAS |
| **Conversion** | Navigation produit, ajout au panier, checkout | **Recommandation produit**, **optimisation du tunnel** (AB‑test dynamique) | Taux de conversion, valeur moyenne du panier (AOV) |
| **Fidélisation** | Programme de points, relance post‑achat, service client | **Score de churn**, **chatbot IA**, **upsell/cross‑sell** | Taux de ré‑achat, LTV, NPS |

> **Note** : chaque case d’usage doit être justifiable par un gain mesurable (ex. amélioration du taux de conversion grâce à la recommandation « People also bought »).

---

## 2. Analyse des données disponibles sur Shopify  

| Table Shopify | Colonnes utiles pour l’IA | Type de donnée | Exemple de requête (REST) |
|---------------|---------------------------|----------------|---------------------------|
| `products` | `id`, `title`, `tags`, `variants.price`, `created_at` | Texte, numérique, temporel | `GET /admin/api/2024-04/products.json?fields=id,title,tags,variants` |
| `customers` | `id`, `email`, `tags`, `orders_count`, `total_spent`, `created_at` | Texte, numérique, temporel | `GET /admin/api/2024-04/customers.json?fields=id,email,orders_count,total_spent` |
| `orders` | `id`, `customer_id`, `line_items`, `total_price`, `created_at`, `financial_status` | Texte, numérique, temporel | `GET /admin/api/2024-04/orders.json?status=any&fields=id,customer_id,total_price,created_at` |

### 2.1 Conformité RGPD  

| Action | Obligation | Implémentation concrète |
|--------|------------|------------------------|
| Consentement | Enregistrement du consentement avant collecte de données personnelles | Stocker le champ `marketing_opt_in` de `customers` et le tracer dans un log immutable (ex. CloudTrail) |
| Droit à l’oubli | Suppression définitive des données à la demande du client | Utiliser l’endpoint `DELETE /admin/api/2024-04/customers/{id}.json` et purger les copies dans le data‑lake (ex. BigQuery) |
| Minimisation | Ne collecter que les attributs nécessaires aux modèles | Faire un **data‑audit** : chaque variable doit être liée à un KPI et à une exigence fonctionnelle. |

---

## 3. Méthodologie de définition d’indicateurs de performance (KPIs) IA  

1. **Alignement business** – chaque KPI doit répondre à une question métier (ex. « Quel sera le taux de conversion si on montre X ? »).  
2. **Mesurabilité** – la métrique doit être calculable à partir des logs Shopify ou du data‑warehouse.  
3. **Seuils de succès** – fixer un objectif chiffré (ex. précision ≥ un certain seuil, lift ≥ un certain facteur).  

| KPI IA | Formule | Source de calcul | Objectif typique |
|--------|---------|------------------|------------------|
| Précision du classif. churn | TP / (TP + FP) | Table `customers` + modèle churn | au moins un niveau élevé |
| Lift de recommandation | CVR_rec / CVR_baseline | Sessions + `recommendations` logs | au moins un facteur d’amélioration |
| Temps de réponse API IA | (t₁ - t₀) | Timestamp avant/after appel micro‑service | inférieur à une durée courte |

---

## 4. Sélection de modèles standards adaptés aux volumes Shopify  

| Cas d’usage | Volume de données (exemple) | Modèle recommandé | Pourquoi |
|-------------|-----------------------------|-------------------|----------|
| **Filtrage collaboratif** | plusieurs milliers de produits et dizaines de milliers de clients, centaines de milliers d’interactions | *Matrix Factorization* (ALS) | Scalable en batch, bonnes performances sur matrices clairsemées |
| **Prédiction churn** | plusieurs dizaines de milliers de clients, un an d’historique | *Logistic Regression* ou *XGBoost* | Interprétable, rapide à entraîner, gère variables catégorielles |
| **Analyse de texte (tags, reviews)** | plusieurs centaines de milliers de reviews | *Sentence‑BERT* embeddings + *K‑NN* | Capture les sémantiques, peu de données d’entraînement supplémentaires |
| **Détection d’anomalie de fraude** | plusieurs milliers de transactions par jour | *Isolation Forest* | Non‑paramétrique, détecte outliers sans labels |

> **Rappel** : le choix du modèle doit être justifié par le **coût d’inférence** (latence) et le **budget de calcul** (ex. ressources modestes sur Cloud Run).

---

## 5. Élaboration d’un plan de collecte, de stockage et de gouvernance des données  

### 5.1 Pipeline de collecte (exemple)  

```mermaid
flowchart TD
    A[Shopify Webhooks] -->|order/create| B[Google Cloud Pub/Sub]
    B --> C[Cloud Function (Python)]
    C -->|transform| D[Big
```

---

## Module 2 — contenu

## 2.1. Architecture générale de l’application privée Shopify  

| Élément | Rôle | Technologie recommandée |
|--------|------|--------------------------|
| **Front‑end (Shopify)** | Thème Liquid, appels aux endpoints de l’app via JavaScript (fetch) | Liquid, Ajax API |
| **Back‑end** | API REST + GraphQL, gestion des webhooks, relais vers le micro‑service IA | Node.js ≥ 18 (Express ou Fastify) ou Python 3.11 (FastAPI) |
| **Infrastructure** | Exécution sans serveur, scalabilité, isolation des secrets | AWS Lambda + API Gateway **ou** Google Cloud Run |
| **Stockage des secrets** | API keys Shopify, JWT, URL du micro‑service IA | AWS Secrets Manager, HashiCorp Vault, ou Google Secret Manager |
| **CI/CD** | Build, test, déploiement automatisé | GitHub Actions + Docker (image : node:18‑slim) |
| **Monitoring** | Traces, métriques, alertes sur erreurs 5xx et dépassements de quota | CloudWatch (AWS) ou Stackdriver (GCP) |

> **Note** : la plupart des boutiques utilisent déjà un domaine `myshop.myshopify.com`. L’app privée s’installe dans le tableau de bord **Apps → Develop apps for your store**. Aucun store public n’est requis.

---

## 2.2. Authentification OAuth 2.0 avec Shopify  

1. **Création de l’app**  
   - Dans le tableau de bord Shopify → *Apps → Develop apps* → *Create an app*.  
   - Cochez **Admin API access** → *Read and write* sur les ressources nécessaires (Orders, Products, Customers).  
   - Activez **Storefront API** si vous comptez appeler le GraphQL côté client.  
   - Enregistrez l’**API key** (client_id) et le **API secret key** (client_secret).  

2. **Flux d’obtention du token** (client credentials grant) – recommandé pour les apps privées (pas d’interaction utilisateur) :

```http
POST https://{shop}.myshopify.com/admin/oauth/access_token
Content-Type: application/json

{
  "client_id": "<API_KEY>",
  "client_secret": "<API_SECRET>",
  "grant_type": "client_credentials"
}
```

Réponse :

```json
{
  "access_token": "shpat_XXXXXXXXXXXXXXXXXXXXXXXX",
  "expires_in": 86400,
  "scope": "read_products,write_orders"
}
```

- Le token est **stateless** (JWT signé par Shopify) ; il n’est pas rafraîchi automatiquement. Renouvelez‑le avant l’expiration.  
- **Piège** : ne stockez jamais le `client_secret` dans le code source. Utilisez un secret manager et injectez‑le au runtime (ex. `process.env.SHOPIFY_API_SECRET`).

---

## 2.3. Structure du projet (Node.js)  

```
my-shopify-app/
├─ src/
│  ├─ api/
│  │  ├─ adminRest.js          # wrapper REST
│  │  └─ adminGraphQL.js        # wrapper GraphQL
│  ├─ webhooks/
│  │  └─ orderCreate.js        # handler webhook order/create
│  ├─ services/
│  │  └─ aiClient.js            # appel au micro‑service IA
│  └─ index.js                  # entry point (Express)
├─ .github/
│  └─ workflows/
│     └─ ci-cd.yml              # GitHub Actions
├─ Dockerfile
├─ package.json
└─ README.md
```

---

## 2.4. Exemple complet : webhook `order/create` qui déclenche un micro‑service IA  

> **Objectif** : dès qu’une commande est créée, envoyer le panier (liste d’IDs produits, quantités, client_id) à un service IA qui renvoie une recommandation de cross‑sell. La réponse est stockée dans les métadonnées de la commande via l’API Admin.

### 2.4.1. `src/index.js`

```js
// src/index.js
import express from 'express';
import bodyParser from 'body-parser';
import crypto from 'crypto';
import { handleOrderCreate } from './webhooks/orderCreate.js';
import { getShopifyClient } from './api/adminRest.js';

const app = express();

// Shopify envoie les webhooks en `application/json` + header HMAC
app.use(bodyParser.json({
  verify: (req, res, buf) => {
    const hmacHeader = req.get('X-Shopify-Hmac-Sha256');
    const secret = process.env.SHOPIFY_WEBHOOK_SECRET; // stocké dans Secrets Manager
    const hash = crypto.createHmac('sha256', secret).update(buf).digest('base64');
    if (hash !== hmacHeader) {
      throw new Error('Webhook verification failed');
    }
  }
}));

app.post('/webhooks/order/create', async (req, res) => {
  try {
    await handleOrderCreate(req.body);
    res.status(200).send('OK');
  } catch (e) {
    console.error('Webhook error:', e);
    res.status(500).send('Internal Server Error');
  }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log(`App listening on ${PORT}`));
```

### 2.4.2. `src/webhooks/orderCreate.js`

```js
// src/webhooks/orderCreate.js
import { getShopifyClient } from '../api/adminRest.js';
import { getRecommendation } from '../services/aiClient
```

---

## Module 3 — contenu

## 3.1 Principes théoriques du moteur de recommandation

| Concept | Définition | Formule / Algorithme clé |
|--------|------------|--------------------------|
| **Filtrage collaboratif (CF) – implicite** | Utilise les interactions (vues, ajouts au panier, achats) comme signal de préférence. | `p_ui = 1` si l’utilisateur *u* a interagi avec l’article *i*, sinon `0`. |
| **Factorisation matricielle (MF)** | Approxime la matrice d’interaction `R` (U×I) par le produit de deux matrices de rang *k* : `R ≈ P·Qᵀ`. | `min_{P,Q} Σ_{(u,i)∈K} (p_ui – p_u·q_i)² + λ(‖p_u‖²+‖q_i‖²)` |
| **Embeddings de texte** | Vecteurs dense obtenus à partir du titre / description produit via un modèle pré‑entraîné (ex. `sentence‑transformers/all‑MiniLM‑L6‑v2`). | `e_i = model.encode(text_i)` |
| **Hybridation** | Combine CF (scores de similarité utilisateur‑article) et contenu (similarité texte). | `score_ui = α·CF_ui + (1‑α)·cos(e_u, e_i)` |
| **Top‑N** | Classe les articles par score décroissant et renvoie les premiers. | `rec_u = argsort(score_u)[‑N:]` |

### Pourquoi ces choix pour Shopify ?

* **Volumes** : une boutique moyenne tient dans la RAM d’une petite instance EC2.  
* **Temps réel** : les webhooks (`cart/update`, `order/create`) déclenchent une fonction Lambda qui calcule le top‑5 très rapidement.  
* **Coût** : `implicit` (bibliothèque Cython) et `sentence‑transformers` sont open‑source, aucune licence supplémentaire.

---

## 3.2 Pipeline de données

1. **Extraction** (Shopify Admin API)  
   ```bash
   GET /admin/api/2023-10/orders.json?status=any&fields=id,customer,email,line_items
   GET /admin/api/2023-10/products.json?fields=id,title,body_html,variants
   ```
2. **Transformation**  
   * Crée la table `interactions(user_id, product_id, weight)` où `weight` reflète