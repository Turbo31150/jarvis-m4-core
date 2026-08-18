# IA No-Code — Make, Zapier, n8n

> Référence `ia-no-code` · 39 €

## Plan

## Module 1 – Architecture des plateformes No‑Code IA  
**Objectif mesurable** : Concevoir et documenter un schéma d’intégration entre au moins deux services IA (ex. OpenAI, Hugging Face) en utilisant Make, Zapier ou n8n.  
- Modélisation des flux de données (entrée, transformation, sortie)  
- Types d’authentification supportés (API‑Key, OAuth 2.0, JWT)  
- Gestion des quotas et limites de taux (rate‑limiting)  
- Sécurisation des secrets (variables d’environnement, vault)  
- Documentation technique (README, diagrammes Mermaid)

## Module 2 – Construction de scénarios multi‑services  
**Objectif mesurable** : Implémenter, tester et publier un scénario complet qui combine trois API externes (ex. extraction texte → analyse sentiment → stockage) sur chaque plateforme.  
- Utilisation des modules HTTP/REST et des connecteurs natifs  
- Mappage et transformation de données (JSONPath, fonctions de texte, filtres)  
- Chaînage conditionnel (branches, filtres, routes)  
- Gestion des erreurs (retry, fallback, notifications)  
- Déploiement versionné (branches, tags, export/import)

## Module 3 – Intégration de modèles IA via des Webhooks  
**Objectif mesurable** : Configurer un webhook bidirectionnel qui déclenche un modèle IA et renvoie la réponse en temps réel, avec suivi des métriques d’appel.  
- Création et sécurisation de webhooks (signature HMAC, IP whitelist)  
- Sérialisation/désérialisation des payloads (JSON, base64)  
- Traitement asynchrone (queues, polling, callbacks)  
- Enregistrement des logs et métriques (duration, status, payload size)  
- Monitoring avec alertes (ex. Zapier → Email, n8n → Slack)

## Module 4 – Extensions de code personnalisé  
**Objectif mesurable** : Ajouter et valider un script JavaScript ou Python dans chaque plateforme pour pré‑traiter ou post‑traiter les données d’un flux IA.  
- Module “Code” de Make, “Code by Zapier”, “Function” de n8n  
- Environnement d’exécution (Node 14+, Python 3.9) et limites (timeout, mémoire)  
- Accès aux variables d’environnement et aux secrets  
- Tests unitaires intégrés (ex. Jest, pytest)  
- Gestion des dépendances (npm, pip) et isolation (virtualenv, Docker)

## Module 5 – Optimisation, scalabilité et gouvernance  
**Objectif mesurable** : Auditer un scénario existant, réduire son temps moyen d’exécution de ≥ 20 % et formaliser une politique de gouvernance des automatisations.  
- Analyse de performance (profilage, métriques d’exécution)  
- Optimisation des appels API (batching, pagination)  
- Mise en place de limites de concurrence (queues, throttling)  
- Contrôle d’accès (RBAC, équipes, permissions)  
- Procédures

---

## Module 1 — contenu

## 1.1 Modélisation des flux de données  

| Étape | Description | Artefact attendu |
|------|-------------|------------------|
| **Entrée** | Point d’entrée du scénario (ex. webhook HTTP, déclencheur planifié, poll d’une API) | `Trigger` (Make: **Watch webhook**, Zapier: **Catch Hook**, n8n: **Webhook**) |
| **Transformation** | Normalisation / enrichissement (extraction de texte, conversion JSON → texte, ajout de métadonnées) | Module **Code** / **Function** ou **Set** (Make) / **Formatter** (Zapier) / **Function** (n8n) |
| **Appel IA** | Envoi du payload à l’API IA (OpenAI, Hugging Face, etc.) | Module **HTTP** ou connecteur natif |
| **Sortie** | Destination finale (base de données, stockage objet, réponse webhook) | **Google Sheets**, **S3**, **Email**, **Return data** (Make) |

> **Diagramme Mermaid** (à placer dans le README)  

```mermaid
flowchart TD
    A[Webhook (Trigger)] --> B[Set / Code (Pré‑traitement)]
    B --> C[HTTP Request (OpenAI)]
    C --> D[Function (Post‑traitement)]
    D --> E[Google Sheets (Enregistrement)]
    D --> F[Webhook Response]
```

---

## 1.2 Types d’authentification supportés  

| Méthode | Implémentation dans chaque plateforme | Points de vigilance |
|---------|----------------------------------------|---------------------|
| **API‑Key** | - Make : Header `Authorization: Bearer {{api_key}}` <br> - Zapier : “Custom Request” → *Headers* <br> - n8n : “HTTP Request” → *Authentication* → *API Key* | Ne jamais hard‑coder la clé dans le corps du workflow ; utilisez les **variables d’environnement** ou le **Credential Store**. |
| **OAuth 2.0** (Authorization Code) | - Make : *OAuth2* → *Connect* (gère le refresh token) <br> - Zapier : *OAuth2* app (déclaré dans le **Developer Platform**) <br> - n8n : *OAuth2* credentials (client‑id/secret, token URL) | Le **redirect URI** doit correspondre exactement à celui enregistré sur le provider (ex. `https://n8n.mycompany.com/rest/oauth2-credential/callback`). |
| **JWT** (Bearer) | - Make : Header `Authorization: Bearer {{jwt}}` (jwt généré préalablement) <br> - Zapier : *Code* → `fetch` avec header <br> - n8n : *HTTP Request* → *Authentication* → *Bearer* | La durée de vie du token doit être gérée : rafraîchir avant expiration ou implémenter un **retry** qui regénère le JWT. |

---

## 1.3 Gestion des quotas et limites de taux (rate‑limiting)  

| Situation | Solution concrète | Exemple (n8n) |
|----------|-------------------|----------------|
| **Limite de 60 req/min** (OpenAI) | Utiliser le **node “Throttle”** (n8n) ou le **“Sleep”** (Make) entre les appels. | ```json { "mode": "rate", "value": 60, "timeUnit": "minute" }``` |
| **Burst de 10 req** autorisé | Configurer un **bucket** avec `capacity:10` et `refillRate:60/min`. | n8n → *Rate Limit* node (v0.225+) |
| **Back‑off exponentiel** en cas de 429 | Ajouter un **Retry** avec `maxAttempts:5`, `delay: 2^{{attempt}} * 1000 ms`. | n8n → *HTTP Request* → *Retry on Failure* |

> **Piège** : les plateformes ne partagent pas les compteurs de quota entre plusieurs scénarios. Si deux scénarios utilisent la même clé API, chaque compteur est indépendant, ce qui peut entraîner un dépassement inattendu. Centralisez la logique de throttling dans un **workflow partagé** (ex. un “gateway” qui reçoit les requêtes et les redistribue).  

---

## 1.4 Sécurisation des secrets  

| Secret | Stockage recommandé | Accès dans le workflow |
|--------|----------------------|-----------------------|
| **API‑Key** | **Make** : *Secrets* (chiffré) <br> **Zapier** : *Environment Variables* (déclarées dans le UI) <br> **n8n** : *Credentials* (type “API Key”) ou *n8n‑cloud secrets* | `{{ $secrets.OPENAI_KEY }}` (Make) <br> `process.env.OPENAI_KEY` (Code by Zapier) <br> `{{$credentials["OpenAI API"].apiKey}}` (n8n) |
| **Client Secret OAuth** | **Vault** externe (HashiCorp, Azure Key Vault) via **HTTP Request** pour récupérer le secret à chaque exécution. | n8n → *HTTP Request* → *Authentication* → *OAuth2* (le client secret reste dans le Credential Store, chiffré). |
| **JWT private key** | **File** stocké dans un répertoire protégé du serveur n8n, accessible uniquement via le compte système. | `fs.readFileSync('/run/secrets/jwt.key')` dans le *Function* node. |

> **Piège** : certaines plateformes (Zapier Free) ne supportent pas les

---

## Module 2 — contenu

## Module 2 – Construction de scénarios multi‑services  

**Objectif mesurable** : Implémenter, tester et publier un scénario complet qui combine trois API externes (extraction texte → analyse sentiment → stockage) sur chaque plateforme (Make, Zapier, n8n).  

---  

### 1. Architecture du scénario  

| Étape | API | Fonction | Entrée | Sortie |
|------|-----|----------|--------|--------|
| 1️⃣  | **PDF.co** (ou tout service d’OCR) | Extraction texte brut d’un fichier PDF | URL du PDF (ou fichier binaire) | `text` (string) |
| 2️⃣  | **OpenAI / Hugging Face** (sentiment) | Analyse de sentiment (positif, neutre, négatif) | `text` | `{sentiment, score}` |
| 3️⃣  | **Airtable** (ou Google Sheets) | Persistance du résultat | `{text, sentiment, score, timestamp}` | ID de l’enregistrement |

Le flux est **linéaire** : chaque module attend la réponse du précédent. La logique de **retry** et de **fallback** sera détaillée pour chaque plateforme.

---  

## 2. Implémentation sur Make (ancien Integromat)

### 2.1. Schéma visuel (texte)

```
[Watch folder (Google Drive)] → [HTTP – PDF extraction] → [JSON – Parse] → 
[HTTP – Sentiment] → [JSON – Parse] → [Airtable – Create Record] → [Notifier (Slack)]
```

### 2.2. Modules détaillés  

| Module | Paramètres clés | Exemple de configuration |
|--------|----------------|--------------------------|
| **Watch folder** (Google Drive) | *Folder ID*, *File type = PDF* | `Folder ID = 1a2b3c…` |
| **HTTP – PDF extraction** | *Method = POST*, *URL = https://api.pdf.co/v1/pdf/convert/to/text*, *Headers = Authorization: Bearer {{pdfco_key}}*, *Body = {url: {{fileUrl}}}* | Voir code JSON ci‑dessous |
| **JSON – Parse** | *Schema = auto* | N/A |
| **HTTP – Sentiment** | *Method = POST*, *URL = https://api.openai.com/v1/chat/completions*, *Headers = Authorization: Bearer {{openai_key}}*, *Body = {model:"gpt-3.5-turbo", messages:[{role:"user", content:"Analyse le sentiment du texte suivant : {{text}}"}]}* | |
| **JSON – Parse** (sentiment) | *Path = $.choices[0].message.content* → `sentiment` | |
| **Airtable – Create Record** | *Base ID*, *Table name*, *Fields = {Text: {{text}}, Sentiment: {{sentiment}}, Score: {{score}}, Date: {{now}}}* | |
| **Notifier** (Slack) | *Channel*, *Message* | `Nouveau texte analysé : {{sentiment}}` |

### 2.3. Exemple de payload HTTP (PDF extraction)

```json
{
  "url": "{{fileUrl}}",
  "async": false,
  "encrypt": false,
  "profiles": "OCR"
}
```

*Remarque* : le champ `{{fileUrl}}` est injecté par le module « Watch folder ».  

### 2.4. Gestion des erreurs  

| Situation | Action dans Make |
|-----------|------------------|
| 5xx PDF.co (quota) | **Retry** : 3 tentatives, back‑off exponentiel (2 s, 4 s, 8 s) |
| OpenAI renvoie `rate_limit_error` | **Router** → branche *fallback* → envoi d’un e‑mail d’alerte et mise en pause du scénario 1 h |
| Airtable dépasse le taux d’écriture (5 req/s) | **Throttle** : ajouter un module *Sleep* de 200 ms entre chaque création d’enregistrement |

### 2.5. Publication  

1. **Enregistrer le scénario** → *Version 1.0*  
2. **Activer** → *Schedule* : toutes les 5 min ou déclencheur « Watch folder ».  
3. **Export** → *JSON* (pour sauvegarde ou migration).  

---  

## 3. Implémentation sur Zapier  

### 3.1. Architecture du Zap  

1. **Trigger** – *Google Drive – New File in Folder*  
2. **Action** – *Webhooks by Zapier – Custom Request* (PDF extraction)  
3. **Action** – *Code by Zapier – Run JavaScript* (parse OCR JSON)  
4. **Action** – *Webhooks by Zapier – Custom Request* (sentiment)  
5. **Action** – *Code by Zapier – Run Python* (extract sentiment & score)  
6. **Action** – *Airtable – Create Record*  
7. **Action** – *Slack – Send Channel Message*  

### 3.2. Exemple de “Custom Request” pour PDF.co  

| Champ | Valeur |
|------|--------|
| **Method** | `POST` |
| **URL** | `https://api.pdf.co/v1/pdf/convert/to/text` |
| **Headers** | `Authorization: Bearer {{bundle.authData.pdfco_key}}` |
| **Data** | `{ "url": "{{bundle.inputData.file_url}}", "async": false }` |
| **Data Type** | `json` |

### 3.3. Code JavaScript – Nettoyage du texte (étape 3)

---

## Module 3 — contenu

## Module 3 – Intégration de modèles IA via des Webhooks  

### 1. Principes de base des webhooks  

| Élément | Description | Implémentation typique |
|---------|-------------|------------------------|
| **Endpoint** | URL publique (HTTPS) que le service source appellera. | `https://mydomain.com/webhook/receive` (Make), `https://hooks.zapier.com/hooks/catch/123456/abcde/` (Zapier), `https://my.n8n.io/webhook/ai-trigger` (n8n) |
| **Méthode HTTP** | POST obligatoire, parfois GET pour vérification. | `POST` |
| **Payload** | Corps JSON (ou base64) contenant les données d’entrée du modèle IA. | `{ "text": "Quel temps fait‑il ?" }` |
| **Réponse** | Corps JSON renvoyé immédiatement (synchronisation) ou via appel séparé (asynchrone). | `{ "answer": "Il fait 22 °C" }` |
| **Sécurité** | Signature HMAC, secret partagé, IP whitelist, TLS 1.2+. | `X‑Signature: sha256=…` |
| **Statut HTTP** | 2xx = succès, 4xx/5xx = erreur (déclenche retry). | `200 OK` |

---

### 2. Création d’un webhook sécurisé (exemple commun)

#### 2.1. Génération du secret partagé  

```bash
# Linux/macOS
openssl rand -hex 32   # → 64‑character hex string, ex: a1b2c3...
```

Enregistrez ce secret dans le **vault** de la plateforme (Make → Variables d’environnement, Zapier → Secrets, n8n → Credentials).

#### 2.2. Signature HMAC (SHA‑256)

Le service source (ex. OpenAI) doit inclure dans l’en‑tête `X-Signature` :

```
X-Signature: sha256=hex_hmac_sha256(secret, raw_body)
```

**Vérification côté webhook** (Node 14) :

```js
// make/webhook/receive.js  (exemple générique)
const crypto = require('crypto');

module.exports = async (req, res) => {
  const secret = process.env.WEBHOOK_SECRET; // stocké dans le vault
  const signature = req.headers['x-signature']; // ex: "sha256=abcd..."
  if (!signature) return res.status(400).send('Missing signature');

  const rawBody = req.rawBody; // Make expose rawBody, n8n via $request.bodyRaw
  const expected = 'sha256=' + crypto.createHmac('sha256', secret)
                                     .update(rawBody)
                                     .digest('hex');

  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    return res.status(401).send('Invalid signature');
  }

  // Payload OK → passer au traitement IA
  const payload = JSON.parse(rawBody);
  // …
  res.json({ status: 'ok' });
};
```

*Make* : ajoutez un **module “Code”** → collez le script ci‑dessus, activez l’option **“Passer le corps brut”**.  
*Zapier* : utilisez **“Code by Zapier (Node.js)”** ; Zapier fournit `inputData` (déjà parsé) mais pas le corps brut, il faut donc demander au service source d’envoyer la signature dans un champ du JSON et de recalculer la HMAC à partir de ce champ.  
*n8n* : créez un **Webhook** → **“Execute Node”** → insérez le même script dans un **Function** (Node.js) ; `$request.bodyRaw` contient le texte brut.

---

### 3. Sérialisation / désérialisation  

| Format | Cas d’usage | Exemple de conversion |
|--------|------------|-----------------------|
| **JSON** | Données textuelles, structures simples | `JSON.stringify({ text: "Bonjour" })` |
| **Base64** | Envoi de fichiers binaires (images, audio) | `Buffer.from(binary).toString('base64')` |
| **Multipart/form‑data** | Upload de fichiers volumineux (limite > 5 Mo) | `form-data` lib (Node) ou `requests` (Python) |

**Exemple : envoi d’une image à un modèle de classification (Make)**  

```js
// Code module – Make
const fs = require('fs');
const path = '/tmp/image.jpg';
const base64 = fs.readFileSync(path, { encoding: 'base64' });

return {
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ image: base64 })
};
```

Le modèle IA (ex. Hugging Face) attend `image` en base64, renvoie `{ label: "cat", confidence: 0.97 }`.

---

### 4. Traitement asynchrone  

| Situation | Technique | Implémentation concrète |
|-----------|------------|------------------------|
| **Longue exécution (> 5 s)** | Retour immédiat `202 Accepted` + URL de polling | Le webhook renvoie `{ "job_id": "1234", "status_url": "https://my.api/job/1234" }`. Le client interroge `status_url` toutes les 2 s. |
| **Callback** | Le service IA appelle un second webhook lorsqu’il a fini | Créez deux webhooks : **trigger** (receives request) → **callback** (receives result). Stockez `job_id` dans un store (Make → Data Store, n8n → Workflow Data). |
| **Queue** | Utilisez un service de file (RabbitMQ, SQS) entre le webhook

---

## Module 4 — contenu

## Module 4 – Extensions de code personnalisé  

### 1. Pourquoi injecter du code ?  
- **Pré‑traitement** : nettoyer, enrichir ou normaliser les données avant l’appel IA.  
- **Post‑traitement** : filtrer les réponses, extraire des champs, appliquer une logique métier.  
- **Contournement** : exploiter une fonctionnalité non exposée par le connecteur natif (ex. calcul de vecteur, décodage base64).  

### 2. Environnements d’exécution  

| Plateforme | Langage(s) supporté(s) | Version runtime | Timeout max | Mémoire maximale |
|------------|------------------------|----------------|------------|------------------|
| **Make**   | JavaScript (Node)      | Node 14 (LTS)  | 30 s       | 256 Mo            |
| **Zapier** | JavaScript (Node)      | Node 14        | 10 s       | 128 Mo            |
| **n8n**    | JavaScript (Node) **ou** Python | Node 18 / Python 3.9 | 60 s (Node) / 120 s (Python) | 512 Mo (Node) / 256 Mo (Python) |

> **Note** : les limites sont appliquées par exécution. Un flux qui invoque le même code plusieurs fois cumule les temps d’exécution.

### 3. Gestion des secrets et variables d’environnement  

| Plateforme | Stockage des secrets | Accès depuis le code |
|------------|----------------------|----------------------|
| **Make**   | *Secrets* (chiffrés) via le tableau “Variables” → type “Secret”. | `process.env.MY_SECRET` |
| **Zapier** | *Environment Variables* (dans le tableau “Authentication”). | `process.env.MY_SECRET` |
| **n8n**    | *Credentials* (type “API Key”, “OAuth2”, etc.) ou *Environment Variables* du serveur. | `process.env.MY_SECRET` (Node) ou `os.getenv('MY_SECRET')` (Python) |

**Bonne pratique** : ne jamais hard‑coder de clés dans le code source. Utiliser toujours le mécanisme de secret de la plateforme.

### 4. Modules de code  

#### 4.1 Make – Module “Code” (JavaScript)  

```js
// ------------------------------------------------------------
// Make – Module Code : Nettoyage du texte avant l’appel OpenAI
// ------------------------------------------------------------
// Entrées :  $input.text (string)
// Sorties :  $output.cleaned (string)
// ------------------------------------------------------------

/**
 * Supprime les caractères de contrôle et normalise les espaces.
 * @param {string} raw
 * @returns {string}
 */
function cleanText(raw) {
  // 1️⃣ Retirer les caractères non imprimables (Unicode Cc)
  const printable = raw.replace(/[\u0000-\u001F\u007F-\u009F]/g, '');
  // 2️⃣ Normaliser les espaces multiples
  const normalized = printable.replace(/\s+/g, ' ').trim();
  // 3️⃣ Convertir les guillemets typographiques en ASCII
  return normalized
    .replace(/[«»]/g, '"')
    .replace(/[‘’]/g, "'");
}

// ------------------------------------------------------------
// Exécution du module
// ------------------------------------------------------------
if (typeof $input === 'undefined' || typeof $input.text !== 'string') {
  throw new Error('Paramètre "text" manquant ou non string');
}
$output.cleaned = cleanText($input.text);
```

**Points d’attention**  
- Le module ne possède pas de `require` ; seules les APIs natives de Node sont autorisées.  
- Le résultat doit être assigné à `$output.<nom>` ; sinon la donnée ne sera pas propagée.  
- Le timeout de 30 s inclut le temps d’initialisation du sandbox ; gardez le code léger.

#### 4.2 Zapier – “Code by Zapier” (JavaScript)  

```js
// ------------------------------------------------------------
// Zapier – Code by Zapier : Extraction d’entités nommées
// ------------------------------------------------------------
// InputData (déclaré dans l’interface Zapier) :
//   text : string
// ------------------------------------------------------------

const compromise = require('compromise'); // bibliothèque intégrée à Zapier

// 1️⃣ Normaliser le texte (même fonction que dans Make)
function normalize(str) {
  return str.replace(/[\u0000-\u001F\u007F-\u009F]/g, '')
            .replace(/\s+/g, ' ')
            .trim();
}

// 2️⃣ Analyse avec compromise
function extractEntities(str) {
  const doc = compromise(str);
  return {
    persons: doc.people().out('array'),
    organizations: doc.organizations().out('array'),
    dates: doc.dates().out('array')
  };
}

// ------------------------------------------------------------
// Corps de la fonction Zapier
// ------------------------------------------------------------
if (!inputData.text) {
  throw new Error('Le champ "text" est requis');
}
const cleaned = normalize(inputData.text);
const entities = extractEntities(cleaned);

// Retourner les valeurs que Zapier pourra mapper
return {
  cleaned_text: cleaned,
  persons: entities.persons.join(', '),
  organizations: entities.organizations.join(', '),
  dates: entities.dates.join(', ')
};
```

**Pièges courants**  
- Zapier ne permet pas d’installer des paquets externes à la volée ; seules les dépendances listées dans la documentation sont disponibles.  
- La taille du payload de retour est limitée à **100 KB**. Si vous devez renvoyer de gros objets, sérialisez‑les en base64 ou stockez‑les dans un service externe (ex. S3) et renvoyez l’URL.  
- Le timeout de 10 s est strict ; évitez les boucles lourdes ou les appels réseau (utilisez les modules HTTP natifs de Zapier à la place).

#### 4.3 n8n –

---

## Module 5 — contenu

## 5.1 Analyse de performance  

| Métrique | Source | Outil de mesure | Commentaire |
|----------|--------|----------------|-------------|
| **duration** | `node` (Make), `execution_time` (Zapier), `run.time` (n8n) | Logs d’exécution, tableau de bord interne | Temps total du scénario (inclut latence réseau). |
| **latence API** | Header `x-response-time` ou mesure du temps entre `request.start` et `request.end` | `console.time()` (JS) ou `time.time()` (Python) | Permet d’isoler les appels les plus lents. |
| **taux d’erreur** | `status` HTTP, `error` field du module | Dashboard d’erreurs, webhook `error` de Zapier | Un taux > 2 % indique besoin de retry ou de fallback. |
| **quota consommé** | Header `x-ratelimit-remaining` ou compteur interne | Tableau de bord API (OpenAI, HuggingFace) | Vérifier que le scénario ne dépasse pas les limites contractuelles. |

**Profilage dans chaque plateforme**

*Make* – Ajoutez un module **“Tools → Set variable”** avant et après chaque appel HTTP et exportez les valeurs dans un tableau Google Sheet ou un webhook Slack.  

*Zapier* – Utilisez le champ **“Performance”** du log d’exécution (visible dans le tableau de bord) ou ajoutez un **“Code by Zapier”** qui écrit `performance.now()` dans un champ de sortie.  

*n8n* – Activez le **“Execution Mode → Debug”** et consultez le champ `runData` qui contient `startedAt` / `finishedAt` pour chaque nœud.

---

## 5.2 Optimisation des appels API  

### 5.2.1 Batching (groupage)  

Beaucoup d’API acceptent un tableau d’objets en entrée (ex. OpenAI `chat/completions` avec plusieurs `messages`). Envoyer un lot réduit le nombre de handshakes TCP/TLS et le temps de round‑trip.

**Exemple (n8n – fonction JavaScript) :**  

```js
// n8n Function node : batch 10 prompts into a single OpenAI request
const BATCH_SIZE = 10;

// entrée : array de strings `items[0].json.prompt`
const prompts = $items().map(i => i.json.prompt);

// découpages en lots
function chunk(arr, size) {
  const out = [];
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
  return out;
}

const batches = chunk(prompts, BATCH_SIZE);

// préparer les requêtes HTTP (utilisation du node HTTP Request en mode "Execute Once")
return batches.map(batch => ({
  json: {
    model: "gpt-3.5-turbo",
    messages: batch.map(p => ({ role: "user", content: p })),
    // OpenAI accepte un tableau `messages`; chaque message est traité séquentiellement.
  },
}));
```

*Déploiement* : Connectez le **Function** à un **HTTP Request** configuré en **“Execute Once”**. Le résultat renvoie un tableau de réponses, que vous re‑décomposez avec un second **Function** (`batch.map(r => r.choices)`).

### 5.2.2 Pagination efficace  

Lorsque l’API impose une pagination (`limit/offset` ou `cursor`), récupérez le maximum d’items par appel (souvent 100 – 1000). Implémentez un **loop** avec un compteur de page et arrêtez‑le dès que `has_more === false` ou que le nombre d’items atteint le besoin.

```js
// Zapier Code (Node) – pagination OpenAI fine‑tuning models
const fetchAll = async (url, token) => {
  let page = "";
  const all = [];
  while (true) {
    const resp = await fetch(`${url}?page=${page}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const { data, next_page } = await resp.json();
    all.push(...data);
    if (!next_page) break;
    page = next_page;
  }
  return all;
};
```

### 5.2.3 Caching des réponses immuables  

Pour les appels dont le résultat ne dépend que d’un identifiant (ex. `GET /documents/:id`), stockez la réponse dans un **key‑value store** (Redis, Airtable, Google Sheet) et réutilisez‑la pendant la durée de vie du cache (TTL = 15 min, par ex.).  

- **Make** : module **“Data Store → Get/Set”**.  
- **Zapier** : **“Storage by Zapier”** (clé‑valeur).  
- **n8n** : nœud **“Redis”** ou **“Set”** dans le **“Workflow Data”**.

---

## 5.3 Limites de concurrence (throttling, queues)  

| Situation | Technique | Implémentation |
|-----------|-----------|----------------|
| API limite à 60 req/min | **Token bucket** | n8n : `Wait` node + expression `Math.max(0, (Date.now() - $json.lastCall) - 1000)` |
| Plusieurs scénarios parallèles | **Queue** (FIFO) | Make : **“Queue”** module (beta) ; Zapier : **“Delay Until”** + **“Storage”** pour pointer le prochain slot ; n8n