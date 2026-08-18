# React 19 pour Applications IA

> Référence `react-ia` · 59 €

## Plan

## Module 1 : Fondamentaux de React 19 et environnement IA  
**Objectif** : Configurer un projet React 19 compatible avec les bibliothèques d’IA (TensorFlow.js, ONNX Runtime) et maîtriser les nouvelles API de React 19 (concurrent mode, server components).  
- Installation de Node ≥ 18, npm ≥ 9 et création d’une application avec `create-react-app@5` (support React 19).  
- Activation du Concurrent Mode via `<React.StrictMode>` et `createRoot`.  
- Utilisation des Server Components (`.server.jsx`) pour pré‑rendre les charges de modèle.  
- Intégration de TensorFlow.js 4.x et ONNX Runtime 1.16 dans le bundle Webpack.  
- Gestion du cache des modèles avec `CacheStorage` et `IndexedDB`.

## Module 2 : Gestion d’état avancée pour les flux de données IA  
**Objectif** : Implémenter un état partagé fiable (Redux Toolkit 2.0 ou Zustand 4) capable de synchroniser les prédictions en temps réel et de persister les résultats.  
- Architecture du store avec `createSlice` et middleware `rtk-query` pour charger les modèles.  
- Utilisation de `useSyncExternalStore` pour lire un store externe sans re‑render inutile.  
- Mise en place de la persistance avec `redux-persist` et `localForage`.  
- Gestion des flux asynchrones via `createAsyncThunk` et `AbortController`.  
- Sélection optimisée des données avec `createSelector` et mémoïsation.

## Module 3 : Optimisation du rendu des visualisations IA  
**Objectif** : Concevoir des composants graphiques (charts, canvases) qui affichent des résultats de modèle sans dégrader le FPS en dessous de 55 fps sur un écran 1080p.  
- Utilisation de `react-three-fiber` (r3f 7) pour le rendu WebGL 3D des tenseurs.  
- Implémentation de `useFrame` et du `drei` pour le contrôle du cycle de rendu.  
- Découpage des calculs lourds avec les Web Workers (`workerize-loader`).  
- Application du `Suspense` + `lazy` pour le chargement différé des visualisations.  
- Profilage avec React DevTools Profiler et Chrome Performance.

## Module 4 : Sécurité, confidentialité et conformité des applications IA  
**Objectif** : Appliquer les bonnes pratiques de sécurité (CSP, sanitisation) et garantir la conformité RGPD lors du traitement de données utilisateur côté client.  
- Configuration de Content Security Policy via `helmet` et meta‑tags.  
- Validation et nettoyage des entrées avec `DOMPurify` avant l’inférence.  
- Chiffrement des données sensibles en transit avec `Web Crypto API`.  
- Implémentation du consentement explicite et du droit à l’oubli via `localForage` purge.  
- Audit de dépendances avec `npm audit` et mise à jour automatisée (`renovate`).

## Module 5 : Déploiement, monitoring et mise à l’échelle des applications IA React 19  
**Objectif** : Publier une application React 19 IA sur une plateforme cloud (Vercel, Netlify) et mettre en place un monitoring


---

## Module 1 — contenu

## 1.1 Prérequis : Node ≥ 18 & npm ≥ 9  

| Outil | Version minimale | Vérification |
|-------|-------------------|--------------|
| **Node** | 18.0.0 | `node -v` |
| **npm** | 9.0.0 | `npm -v` |

> **Note** : Node 18 intègre le moteur V8 10.2 qui supporte les API `CacheStorage` et `Web Crypto` utilisées plus loin.

---

## 1.2 Création du projet avec **create‑react‑app@5**  

```bash
# 1. Crée le répertoire
mkdir react19-ia && cd react19-ia

# 2. Initialise le projet avec CRA 5 (compatible React 19)
npx create-react-app@5 . --template cra-template-pwa

# 3. Vérifie la version de React installée
npm list react
# > react@19.x.x
```

*CRA 5* utilise Webpack 5, ce qui permet d’ajouter des loaders personnalisés (ex. `workerize-loader`) sans éjecter.

---

## 1.3 Activation du **Concurrent Mode**  

React 19 introduit le *Concurrent Root* (aussi appelé *createRoot*). Dans `src/index.jsx` :

```jsx
// src/index.jsx
import React from 'react';
import { createRoot } from 'react-dom/client';   // ← API 19
import App from './App';

// Le mode StrictMode reste recommandé pour détecter les effets secondaires.
const container = document.getElementById('root');
const root = createRoot(container, {
  // enableConcurrentUpdates: true // option par défaut depuis 19
});
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

**Pourquoi ?**  
* `createRoot` active le Scheduler qui orchestre les rendus non bloquants.  
* `React.StrictMode` déclenche les double‑invocations en dev, indispensable pour repérer les effets de bord.

### Piège fréquent  
Ne pas remplacer `ReactDOM.render` par `createRoot` entraîne le fallback au *Legacy Root* : les Suspense / Transition ne fonctionnent pas correctement.

---

## 1.4 **Server Components** (`.server.jsx`)  

React 19 permet de placer du code qui s’exécute uniquement côté serveur (Node ou Edge). Le fichier doit porter l’extension `.server.jsx` et être importé depuis un composant client.

### 1.4.1 Configuration minimale (sans éjection)

CRA 5 accepte les extensions personnalisées via le champ `webpack` du fichier `craco.config.js` (ou `react-app-rewired`). Exemple avec **CRACO** :

```bash
npm install @craco/craco --save-dev
```

`craco.config.js` :

```js
// craco.config.js
module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Ajoute le loader pour les Server Components
      webpackConfig.module.rules.push({
        test: /\.server\.[jt]sx?$/,
        use: [
          {
            loader: require.resolve('babel-loader'),
            options: {
              presets: ['react-app'],
              plugins: ['react-server-dom-webpack/plugin']
            }
          }
        ],
        type: 'javascript/auto',
      });
      return webpackConfig;
    },
  },
};
```

Modifie le script `start` dans `package.json` :

```json
"scripts": {
  "start": "craco start",
  "build": "craco build",
  "test": "craco test"
}
```

### 1.4.2 Exemple de composant serveur qui charge un modèle TensorFlow.js

```tsx
// src/modelLoader.server.jsx
import * as tf from '@tensorflow/tfjs';

// Fonction exécutée côté serveur uniquement
export async function loadModel() {
  // Le modèle est stocké dans le dossier public (ex. /models/mnist/model.json)
  const url = `${process.env.PUBLIC_URL}/models/mnist/model.json`;
  const model = await tf.loadLayersModel(url);
  return model;
}
```

Utilisation côté client :

```tsx
// src/App.jsx
import React, { Suspense } from 'react';
import { loadModel } from './modelLoader.server.jsx';

function ModelInfo({ model }) {
  return (
    <div>
      <h2>Modèle chargé</h2>
      <p>Nombre de couches : {model.layers.length}</p>
    </div>
  );
}

export default function App() {
  const modelPromise = loadModel(); // Appelé sur le serveur, renvoie un Promise

  return (
    <Suspense fallback={<div>Chargement du modèle…</div>}>
      <React.Suspense
        fallback={<div>Chargement du modèle…</div>}
        // @ts-ignore – React 19 accepte les promesses directement
        children={modelPromise.then((model) => <ModelInfo model={model} />)}
      />
    </Suspense>
  );
}
```

> **Remarque** : Le serveur (Node) exécute `loadModel` pendant le rendu SSR. Le client reçoit le résultat sérialisé (


---

## Module 2 — contenu

## Module 2 : Gestion d’état avancée pour les flux de données IA  

### 2.1. Choix du store : Redux Toolkit 2.0 vs Zustand 4  

| Critère | Redux Toolkit 2.0 | Zustand 4 |
|--------|-------------------|----------|
| Taille bundle (minifié) | ~4 kB (sans RTK‑Query) | ~2 kB |
| API déclarative (slices) | Oui (`createSlice`) | Non, fonction `create` |
| Middleware intégré | `rtk-query`, `serializableCheck` | Aucun, mais `subscribeWithSelector` disponible |
| DevTools | Intégré (`configureStore({ devTools: true })`) | `zustand/middleware` (`devtools`) |
| Persistance native | `redux-persist` (ou `persistReducer`) | `zustand/middleware` (`persist`) |
| TypeScript | Types générés automatiquement (`PayloadAction`) | Types explicites à définir |

**Recommandation** : pour une application IA où les modèles et leurs prédictions sont chargés via des appels réseau, Redux Toolkit + RTK‑Query offre un cache HTTP robuste et une séparation claire entre les données du modèle (static) et les prédictions (dynamiques). Zustand reste pertinent pour des UI très légères ou des prototypes.

---

### 2.2. Architecture du store avec Redux Toolkit  

#### 2.2.1. Installation  

```bash
npm i @reduxjs/toolkit react-redux redux-persist localforage
# RTK‑Query est inclus dans @reduxjs/toolkit
```

#### 2.2.2. Définition du slice « model » (chargement du modèle TensorFlow.js)  

```tsx
// src/store/modelSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import * as tf from '@tensorflow/tfjs';

// Thunk qui charge le modèle depuis IndexedDB ou le réseau
export const loadModel = createAsyncThunk(
  'model/load',
  async (url: string, { rejectWithValue, signal }) => {
    // AbortController géré automatiquement par RTK
    try {
      const model = await tf.loadGraphModel(url, { onProgress: console.log, signal });
      return model;
    } catch (err) {
      return rejectWithValue(err instanceof Error ? err.message : 'unknown error');
    }
  }
);

type ModelState = {
  model: tf.GraphModel | null;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
};

const initialState: ModelState = {
  model: null,
  status: 'idle',
  error: null,
};

export const modelSlice = createSlice({
  name: 'model',
  initialState,
  reducers: {
    // Pas de reducers synchrones ici
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadModel.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(loadModel.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.model = action.payload;
      })
      .addCase(loadModel.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string;
      });
  },
});

export default modelSlice.reducer;
```

#### 2.2.3. Slice « prediction » (flux de prédictions en temps réel)  

```tsx
// src/store/predictionSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Tensor } from '@tensorflow/tfjs';
import type { GraphModel } from '@tensorflow/tfjs';

type PredictionPayload = {
  input: Tensor; // Tensor d’entrée déjà pré‑traité
  result: Tensor; // Tensor de sortie
};

type PredictionState = {
  queue: PredictionPayload[];
  processing: boolean;
  error: string | null;
};

const initialState: PredictionState = {
  queue: [],
  processing: false,
  error: null,
};

// Thunk qui exécute l’inférence; utilise AbortController pour annuler si besoin
export const runInference = createAsyncThunk<
  PredictionPayload,
  { model: GraphModel; input: Tensor },
  { rejectValue: string }
>('prediction/runInference', async ({ model, input }, { rejectWithValue, signal }) => {
  try {
    const result = await model.executeAsync(input, undefined, { signal });
    // `result` peut être Tensor|Tensor[]; on normalise en Tensor
    const tensorResult = Array.isArray(result) ? result[0] as Tensor : (result as Tensor);
    return { input, result: tensorResult };
  } catch (e) {
    return rejectWithValue(e instanceof Error ? e.message : 'unknown error');
  }
});

export const predictionSlice = createSlice({
  name: 'prediction',
  initialState,
  reducers: {
    enqueue: (state, action: PayloadAction<Tensor>) => {
      state.queue.push({ input: action.payload, result: null as any });
    },
    clear: (state) => {
      state.queue = [];
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(runInference.pending, (state) => {
        state.processing = true;
        state.error = null;
      })
      .addCase(runInference.fulfilled, (state, action) => {
        state.processing = false;
        // Remplace le dernier élément de la queue par le résultat complet
        const lastIndex = state.queue.length - 1;
        if (lastIndex >= 0) {
          state.queue[lastIndex] = action.payload;
        }
      })
      .addCase(runInference.rejected, (state, action) => {
        state.processing = false;
        state.error = action.payload ?? 'Inference failed';
      });
  },
});

export const { enqueue, clear } = predictionSlice.actions;
export default predictionSlice.reducer;
```

#### 2.2.4. Configuration du store avec pers


---

## Module 3 — contenu

## Module 3 : Optimisation du rendu des visualisations IA  

### 1. Architecture du rendu : pourquoi séparer calcul & affichage  

| Concern | Solution React 19 | Impact sur le FPS |
|--------|-------------------|-------------------|
| Calculs tensoriels (matrices 1024×1024) | **Web Worker** (thread dédié) | Aucun blocage du thread UI |
| Chargement asynchrone de modèles / textures | `React.Suspense` + `React.lazy` | Découpage du bundle, rendu différé |
| Mise à jour de la scène 3D à 60 Hz | `react-three-fiber` (r3f) + `useFrame` | Le rendu s’inscrit dans le *requestAnimationFrame* de Three.js, pas de re‑render React inutile |
| Gestion de ressources GPU (géométrie, matériaux) | `drei` (`useGLTF`, `useTexture`) + `dispose` dans `useEffect` cleanup | Libération explicite, évite les fuites VRAM |

---

### 2. Mise en place de **react‑three‑fiber** (r3f 7)  

```bash
npm i three @react-three/fiber @react-three/drei
```

#### 2.1. Canvas de base  

```tsx
// src/App.tsx
import { Canvas } from '@react-three/fiber';
import { Suspense, lazy } from 'react';

// Chargement différé du composant de visualisation
const TensorVis = lazy(() => import('./TensorVis'));

export default function App() {
  return (
    <Canvas
      // Le mode concurrent ne change rien ici, mais on garde createRoot dans index.tsx
      camera={{ position: [0, 0, 5], fov: 60 }}
      gl={{ antialias: true, preserveDrawingBuffer: true }} // utile pour capture d’écran
    >
      {/* Lumières de base */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} intensity={1} />

      {/* Suspense gère le fallback pendant le chargement du modèle */}
      <Suspense fallback={null}>
        <TensorVis />
      </Suspense>
    </Canvas>
  );
}
```

#### 2.2. Composant de visualisation  

```tsx
// src/TensorVis.tsx
import { useRef, useMemo } from 'react';
import { useFrame, extend } from '@react-three/fiber';
import { BoxGeometry, MeshStandardMaterial, InstancedMesh } from 'three';
import { useWorker } from './useWorker'; // hook custom (voir §3.3)

extend({ InstancedMesh });

/**
 * Visualise un tenseur 2‑D (ex. 64×64) comme un champ de cubes dont la hauteur
 * représente la valeur normalisée du tenseur.
 */
export default function TensorVis() {
  // 1️⃣ Récupération du tenseur pré‑calculé (Web Worker)
  const tensor = useWorker('tensorWorker', { size: 64 });

  // 2️⃣ Instanciation d’un InstancedMesh pour éviter 64² appels de render
  const meshRef = useRef<InstancedMesh>(null!);
  const count = tensor?.length ?? 0;

  // 3️⃣ Géométrie et matériau partagés (créés une fois)
  const geometry = useMemo(() => new BoxGeometry(1, 1, 1), []);
  const material = useMemo(() => new MeshStandardMaterial({ color: '#4caf50' }), []);

  // 4️⃣ Mise à jour des matrices d’instance à chaque frame
  useFrame(() => {
    if (!tensor || !meshRef.current) return;

    const dummy = new THREE.Object3D();
    const scale = 0.1; // facteur de réduction pour tenir dans le champ de vision

    for (let i = 0; i < count; i++) {
      const value = tensor[i]; // valeur normalisée [0,1]
      const x = (i % 64) - 32;
      const y = (i / 64) - 32;
      dummy.position.set(x * scale, value * scale, y * scale);
      dummy.scale.set(scale, value * scale, scale);
      dummy.updateMatrix();
      meshRef.current.setMatrixAt(i, dummy.matrix);
    }
    meshRef.current.instanceMatrix.needsUpdate = true;
  });

  // 5️⃣ Retour du mesh instancié
  return (
    <instancedMesh
      ref={meshRef}
      args={[geometry, material, count]}
      castShadow
      receiveShadow
    />
  );
}
```

**Points vérifiables**  

* `InstancedMesh` réduit le nombre d’appels WebGL de `N²` à **1**.  
* `useFrame` est invoqué à chaque tick du `requestAnimationFrame` de Three.js, donc le calcul de la matrice d’instance ne déclenche pas de re‑render React.  
* `Suspense` assure que le `Canvas` ne tente pas de rendre `TensorVis` tant que le worker n’a pas renvoyé le tenseur.

---

### 3. Découpage des calculs lourds avec **Web Workers**  

#### 3.1. Worker de calcul du tenseur  

```js
// src/workers/tensorWorker.js
self.onmessage = async (e) => {
  const { size } = e.data; // ex. 64
  // Simuler un calcul IA (ex. produit de deux matrices aléatoires)
  const tensor = new Float32Array(size * size);
  for (let i = 0; i < tensor.length; i++) {
    // Valeur pseudo‑aléatoire, normalisée
    tensor[i] = Math.random();
  }
  // Transfert du buffer pour éviter copie
  self.postMessage({ tensor }, [tensor.buffer]);
};
```

#### 3.2. Hook `useWorker` (React 19


---

## Module 4 — contenu

## 4.1. Content Security Policy (CSP) côté serveur et côté client  

| Objectif | Action concrète | Vérifiable |
|----------|----------------|------------|
| Interdire l’exécution de scripts non‑autorisés | Utiliser le middleware `helmet` dans le serveur Node (ou le fichier `vercel.json` pour Vercel) | `npm i helmet` → `app.use(helmet.contentSecurityPolicy({ directives: { ... } }))` |
| Autoriser uniquement les ressources nécessaires à TensorFlow.js et ONNX Runtime | Ajouter `script-src 'self' https://cdn.jsdelivr.net` et `worker-src 'self' blob:` | Le navigateur bloque toute requête vers `untrusted.com` dans la console CSP. |

```js
// server.js (Node / Express) – configuration CSP
import express from 'express';
import helmet from 'helmet';
import path from 'path';

const app = express();

app.use(
  helmet.contentSecurityPolicy({
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", 'https://cdn.jsdelivr.net'],
      styleSrc: ["'self'", "'unsafe-inline'"], // React injecte des styles inline
      imgSrc: ["'self'", 'data:'],
      connectSrc: ["'self'", 'https://api.example.com'],
      workerSrc: ["'self'", 'blob:'],
      fontSrc: ["'self'", 'https://fonts.gstatic.com'],
      objectSrc: ["'none'"],
      baseUri: ["'self'"],
    },
  })
);

// Servir le build React
app.use(express.static(path.resolve('build')));
app.get('*', (_, res) => res.sendFile(path.resolve('build/index.html')));

app.listen(3000, () => console.log('🚀 Server listening on :3000'));
```

**Pièges courants**  
- Oublier `worker-src` : les Web Workers créés par TensorFlow.js (`tfjs-backend-webgl`) sont chargés via `blob:`; sans la directive, le worker est bloqué et le modèle ne se charge pas.  
- `'unsafe-inline'` dans `style-src` : nécessaire uniquement si vous utilisez `styled-components` ou des styles injectés par React. Supprimez‑le dès que possible pour réduire la surface d’attaque.  
- CSP appliquée uniquement en production : en mode développement (`npm start`) le serveur de CRA ne passe pas par `helmet`. Utilisez `proxy` ou un serveur de dev qui réplique la même politique.

---

## 4.2. Validation & assainissement des entrées avec **DOMPurify**  

TensorFlow.js accepte des tensors créés à partir de données utilisateur (ex. texte, image). Avant de les convertir, il faut s’assurer que le texte ne contient pas de script HTML qui pourrait être injecté dans le DOM (ex. via `dangerouslySetInnerHTML`).

```tsx
// src/utils/sanitize.ts
import DOMPurify from 'dompurify';

/**
 * Nettoie une chaîne de caractères provenant d’un champ texte.
 * Retourne une chaîne sûre pour tout affichage ou injection.
 */
export function sanitizeInput(raw: string): string {
  // DOMPurify supprime les balises <script>, les attributs on*, etc.
  return DOMPurify.sanitize(raw, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] });
}
```

```tsx
// src/components/TextInput.tsx
import { useState } from 'react';
import { sanitizeInput } from '../utils/sanitize';

export default function TextInput({ onSubmit }: { onSubmit: (clean: string) => void }) {
  const [value, setValue] = useState('');

  const handleSend = () => {
    const clean = sanitizeInput(value);
    onSubmit(clean);
    setValue('');
  };

  return (
    <div>
      <textarea
        value={value}
        onChange={e => setValue(e.target.value)}
        placeholder="Entrez du texte"
      />
      <button onClick={handleSend}>Analyser</button>
    </div>
  );
}
```

**Pièges**  
- `DOMPurify` ne nettoie pas les caractères Unicode dangereux (ex. `\u202E` : RIGHT‑TO‑LEFT OVERRIDE). Activez l’option `SAFE_FOR_TEMPLATES` si vous insérez la chaîne dans un template string.  
- Si vous désactivez `ALLOWED_TAGS` mais laissez `ALLOWED_ATTR`, des attributs comme `style` restent autorisés et peuvent contenir du `url(javascript:…)`.  

---

## 4.3. Chiffrement des données sensibles avec **Web Crypto API**  

Dans un contexte IA client‑side, on peut chiffrer les données avant de les stocker dans `IndexedDB`/`localForage`. Le standard recommandé est **AES‑GCM 256 bits**.

```ts
// src/utils/crypto.ts
const encoder = new TextEncoder();
const decoder = new TextDecoder();

/**
 * Génère une clé symétrique AES‑GCM (256 bits) et la stocke dans IndexedDB.
 * Retourne la clé sous forme d’objet CryptoKey.
 */
export async function generateKey(): Promise<CryptoKey> {
  const key = await crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    true, // extractable = true pour pouvoir sauvegarder la clé
    ['encrypt', 'decrypt']
  );
  // Sauvegarde dans IndexedDB via localForage (exemple simple)
  await import('localforage').then(lf => lf.setItem('aes-key', key));
  return key;
}

/**
 * Chiffre une donnée


---

## Module 5 — contenu

## Module 5 – Déploiement, monitoring et mise à l’échelle d’une application IA sous React 19  

### 5.1 Choix de la plateforme d’hébergement  

| Plateforme | Build supporté | Edge Functions | CDN intégré | Limite de taille du bundle* |
|------------|----------------|----------------|------------|------------------------------|
| **Vercel** | `npm run build` → `dist/` (Next.js ou CRA) | Oui (`api/` ou `vercel.json`) | Oui (global) | 50 Mo (gzip) |
| **Netlify** | `npm run build` → `dist/` | Oui (`netlify/functions/`) | Oui | 100 Mo (gzip) |
| **Cloudflare Pages** | `npm run build` → `dist/` | Workers (`functions/`) | Oui | 25 Mo (gzip) |

\*Le bundle inclut les modèles TensorFlow.js/ONNX pré‑chargés. Si le poids dépasse la limite, il faut servir les modèles depuis un bucket (S3, Cloudflare R2) et les charger à la volée.

### 5.2 Configuration du projet pour le CI/CD  

1. **Fichier `package.json`** – Ajoutez les scripts requis par la plateforme.  

```json
{
  "scripts": {
    "dev": "react-scripts start",
    "build": "react-scripts build",
    "preview": "react-scripts preview",
    "lint": "eslint src/**/*.js src/**/*.jsx",
    "test": "jest"
  },
  "engines": {
    "node": ">=18"
  }
}
```

2. **`.npmrc`** – Bloquez les versions de `react` et `react-dom` pour éviter les ruptures inattendues.  

```ini
save-exact=true
```

3. **`.vercel.json`** (exemple Vercel) – Déclare les réécritures et les fonctions Edge.  

```json
{
  "rewrites": [{ "source": "/api/(.*)", "destination": "/api/$1" }],
  "functions": {
    "api/**/*.js": {
      "runtime": "edge",
      "memory": 128,
      "maxDuration": 5
    }
  },
  "build": {
    "env": {
      "NEXT_PUBLIC_TFJS_MODEL_URL": "https://my-bucket.s3.amazonaws.com/model.json"
    }
  }
}
```

### 5.3 Servir les modèles IA depuis un stockage d’objets  

```js
// src/lib/modelLoader.js
import * as tf from '@tensorflow/tfjs';

// URL du bucket S3 ou Cloudflare R2 – définie en variable d’environnement.
const MODEL_URL = import.meta.env.VITE_TFJS_MODEL_URL;

/**
 * Charge le modèle TensorFlow.js en utilisant le cache du navigateur.
 * Si le modèle est déjà présent dans IndexedDB, il est récupéré sans requête réseau.
 */
export async function loadTfModel() {
  // tf.io.browserIndexedDB() crée un handler de cache persistant.
  const handler = tf.io.browserIndexedDB('my-tfjs-model');

  // Vérifie la présence du modèle dans le cache.
  const models = await tf.io.listModels();
  if (models[handler.path]) {
    console.info('Modèle trouvé dans IndexedDB, chargement direct.');
    return tf.loadLayersModel(handler);
  }

  // Sinon, téléchargement depuis le bucket puis sauvegarde en cache.
  console.info('Téléchargement du modèle depuis le bucket.');
  const model = await tf.loadGraphModel(MODEL_URL, { fromTFHub: false });
  await model.save(handler);
  return model;
}
```

*Points de vigilance*  
- `tf.io.browserIndexedDB` ne fonctionne que sur les contextes **secure origin** (HTTPS).  
- Le bucket doit servir les fichiers avec les en‑têtes `Access-Control-Allow-Origin: *` ou le domaine de l’application.  
- La taille maximale d’un objet stocké dans IndexedDB dépend du navigateur ; chaque navigateur impose ses propres limites, il faut vérifier la capacité disponible.  

### 5.4 Optimisation du bundle pour le edge  

1. **Tree‑shaking** – Importez les sous‑modules de TensorFlow.js au lieu du package complet.  

```js
// Mauvais
import * as tf from '@tensorflow/tfjs';

// Bon
import { loadGraphModel } from '@tensorflow/tfjs-converter';
import { tensor } from '@tensorflow/tfjs-core';
```

2. **Dynamic import** – Chargez le modèle uniquement lorsqu’il est nécessaire.  

```js
// src/components/ModelPredictor.jsx
import React, { Suspense, lazy } from 'react';

const Predictor = lazy(() => import('./Predictor'));

export default function ModelPredictor() {
  return (
    <Suspense fallback={<div>Chargement du modèle…</div>}>
      <Predictor />
    </Suspense>
  );
}
```

3. **Compression** – Activez `compression` dans `vercel.json` ou `netlify.toml`.  

```toml
# netlify.toml
[build]
  publish = "dist"
  command = "npm run build"

[[plugins]]
  package = "@netlify/plugin-nextjs"
```

### 5.5 Monitoring en production  

| Outil | Métrique clé | Implémentation |
|------|--------------|----------------|
| **Vercel Analytics** | TTFB, LCP, CLS | Activé via le tableau de bord, aucune instrumentation code. |
| **Sentry (browser)** | Erreurs JavaScript, traces d’exception | `npm i @sentry/react @sentry/tracing` + wrapper `<Sentry.ErrorBoundary>` |
| **Web Vitals** | `first-input-delay`, `cumulative-layout-shift` | `import { getCLS, getFID, getLCP } from 'web-vitals';` |
| **Custom Metrics (Prometheus via Grafana Cloud)** | Temps de chargement du modèle, utilisation GPU WebGL | `performance.mark('model-start'); … performance.measure('model-load', 'model-start');` |