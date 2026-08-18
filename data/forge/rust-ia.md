# Rust pour l'IA & Performance

> Référence `rust-ia` · 89 €

## Plan

## Module 1 – Fondamentaux de Rust orientés IA  
**Objectif mesurable :** L’apprenant écrit, compile et exécute un programme Rust qui charge et pré‑traite un jeu de données CSV de 1 M d’enregistrements sans fuite de mémoire.  
**Notions couvertes**  
- Système de types, ownership, borrowing et lifetimes appliqués aux structures de données tabulaires.  
- Gestion de la mémoire avec `Vec`, `String`, slices et `Option`/`Result`.  
- Utilisation de `serde` et `csv` pour la désérialisation sécurisée.  
- Traitement parallèle avec `rayon` : map‑reduce sur des collections.  
- Profilage basique avec `cargo bench` et `perf`.

---

## Module 2 – Calculs numériques et algèbre linéaire en Rust  
**Objectif mesurable :** L’apprenant implémente et compare deux algorithmes de multiplication matricielle (naïf et Strassen) sur des matrices 2048×2048, en mesurant le temps d’exécution et l’utilisation de la RAM.  
**Notions couvertes**  
- Types numériques (`f32`, `f64`, `num_traits`) et précision flottante.  
- Bibliothèque `ndarray` : création, slicing, broadcasting.  
- Implémentation de kernels BLAS via `blas-sys` ou `matrixmultiply`.  
- Optimisation cache‑aware et parallélisation (`rayon`, `crossbeam`).  
- Benchmarks avec `criterion` et interprétation des résultats.

---

## Module 3 – Construction de modèles de machine learning basiques  
**Objectif mesurable :** L’apprenant crée, entraîne et évalue un perceptron multicouche (MLP) sur le jeu de données MNIST, atteignant au moins 92 % de précision sur le set de validation.  
**Notions couvertes**  
- Structures de réseaux (`Layer`, `Activation`) et propagation avant/arrière.  
- Calculs de gradients avec `autograd` (ex. `autodiff` crate) ou implémentation manuelle.  
- Optimiseurs (SGD, Adam) et gestion des hyper‑paramètres.  
- Sérialisation du modèle (`bincode`, `serde_json`).  
- Évaluation (accuracy, loss) et visualisation avec `plotters`.

---

## Module 4 – Intégration de bibliothèques IA externes (ONNX, TensorFlow‑Rust)  
**Objectif mesurable :** L’apprenant charge un modèle ONNX pré‑entraîné (ResNet‑18) et l’exécute sur un lot de 10 000 images, en mesurant le débit (images/s) et la consommation GPU/CPU.  
**Notions couvertes**  
- Format ONNX et conversion de modèles (PyTorch → ONNX).  
- Crate `ort` (ONNX Runtime) : session, tensors, inference.  
- Gestion de l’accélération matériel (CUDA, DirectML) via `ort`.  
- Interfaçage avec `tch-rs` (bindings TensorFlow) pour comparaison.  
- Profilage GPU avec `nvprof` et analyse des goulots d’étranglement.

---

## Module 5 – Déploiement, scalabilité et bonnes pratiques de production  
**Objectif mesurable :** L’apprenant containerise une API Rust exposant un endpoint d’inférence, la déploie sur Kubernetes et assure une latence ≤ 30 ms pour 100 req/s avec autoscaling.  
**Notions couvertes**  
- Construction d’une API REST avec `actix-web` ou `warp`.  
- Sérialisation des

---

## Module 1 — contenu

## 1.1 Système de types, ownership, borrowing et lifetimes appliqués aux structures tabulaires  

| Concept | Rôle | Exemple minimal |
|--------|------|-----------------|
| **Ownership** | Chaque valeur possède un propriétaire unique; le propriétaire libère la mémoire à la fin de son scope. | `let data = Vec::new(); // data est propriétaire` |
| **Borrowing** | Emprunter une référence (`&T` ou `&mut T`) sans prendre la propriété. Le compilateur vérifie l'absence de conflits d’accès mutable/immutable. | `fn sum(v: &Vec<f64>) -> f64 { v.iter().sum() }` |
| **Lifetimes** | Annotation explicite des durées de vie des références lorsque le compilateur ne peut pas les inférer. | `fn get_first<'a>(slice: &'a [i32]) -> &'a i32 { &slice[0] }` |
| **Slices** | Vue non‑possédante sur une séquence contiguë (`&[T]` ou `&mut [T]`). | `let row: &[f64] = &matrix[i * n..(i+1) * n];` |

### 1.1.1 Structure de ligne CSV  

```rust
use serde::Deserialize;

/// Représente une ligne du CSV « data.csv ».
#[derive(Debug, Deserialize)]
struct Record {
    #[serde(rename = "id")]
    id: u64,
    #[serde(rename = "feature1")]
    f1: f32,
    #[serde(rename = "feature2")]
    f2: f32,
    #[serde(rename = "label")]
    label: u8,
}
```

* `Record` ne possède aucune allocation dynamique : `u64`, `f32`, `u8` sont stockés sur la pile.  
* `serde` utilise uniquement des références temporaires pendant la désérialisation, aucune fuite n’est possible tant que le `Reader` est correctement fermé.

---

## 1.2 Gestion de la mémoire avec `Vec`, `String`, slices et `Option`/`Result`

| Type | Allocation | Usage typique |
|------|------------|---------------|
| `Vec<T>` | Heap, capacité croît par doublement (`Vec::with_capacity`). | Stockage dynamique de lignes. |
| `String` | Heap, UTF‑8. | Lecture de lignes brutes avant parsing. |
| `&[T]` / `&mut [T]` | Aucun heap, pointeur + longueur. | Passage de sous‑tableaux à des fonctions de calcul. |
| `Option<T>` | Aucun heap supplémentaire (enum discriminant). | Valeur éventuelle (`None` = donnée manquante). |
| `Result<T,E>` | Idem. | Propagation d’erreurs (`?` operator). |

### 1.2.1 Lecture et pré‑traitement en flux  

```rust
use std::error::Error;
use std::fs::File;
use std::io::{BufReader, Read};
use csv::ReaderBuilder;

/// Charge le CSV, filtre les lignes où `f1` < 0.0, renvoie un Vec<Record>.
fn load_and_filter(path: &str) -> Result<Vec<Record>, Box<dyn Error>> {
    // 1️⃣ Ouverture du fichier (RAII → fermeture automatique)
    let file = File::open(path)?;
    let mut rdr = ReaderBuilder::new()
        .has_headers(true)
        .from_reader(BufReader::new(file));

    // 2️⃣ Allocation anticipée : on suppose 1 M de lignes → capacité 1 000_000
    let mut records = Vec::with_capacity(1_000_000);

    // 3️⃣ Parcours ligne par ligne, désérialisation incrémentale
    for result in rdr.deserialize() {
        let rec: Record = result?;                // Propagation d’erreur avec `?`
        if rec.f1 >= 0.0 {                         // Filtrage simple
            records.push(rec);                     // `push` ne réalloue que si la capacité est dépassée
        }
    }
    Ok(records)
}
```

* **RAII** garantit la libération du `File` même en cas d’erreur.  
* `Vec::with_capacity` évite les reallocations coûteuses (coût O(1) amorti).  
* Le `for` utilise **borrowing** interne du lecteur : aucune copie du buffer complet n’est faite.  

#### Profilage rapide  

```bash
cargo bench --bench load_csv   # bench défini dans benches/load_csv.rs
perf record -g -- cargo run --release --bin load_csv
perf report
```

* `cargo bench` exécute le benchmark avec `criterion` (voir § 1.4).  
* `perf` montre le temps passé dans `csv::Reader::deserialize` et dans les allocations de `Vec`.

---

## 1.3 Utilisation de `serde` et `csv` pour la désérialisation sécurisée  

* `serde` repose sur **derive macros** : le code généré est vérifié à la compilation, aucune réflexion à l’exécution.  
* Le crate `csv` lit en **chunks** de 8 KiB par défaut, minimise les copies grâce à `ByteRecord`.  
* `serde` renvoie `Result<T, csv::Error>` ; l’opérateur `?` convertit automatiquement en `Box<dyn Error>` grâce à `From`.  

### 1.3.1 Gestion des valeurs manquantes  

```rust
#[derive(Debug, Deserialize)]
struct RecordOpt {
    id: u64,
    #[serde(default)]               // Si la colonne est vide → None
    f1: Option<f32>,
    #[serde(default)]
    f2: Option<f32>,
    label: u8,
}
```

* `Option<f32>` évite les **panics** lors de la conversion de chaînes vides.  
* Le champ `#[serde(default)]` injecte `None` lorsqu’une colonne est absente ou vide.

---

## 1.4 Traitement parallèle avec `rayon` : map

---

## Module 2 — contenu

## 2.1 Types numériques et précision flottante  

| Type | Taille | Représentation | Intervalle (approx.) | Usage recommandé |
|------|--------|----------------|----------------------|------------------|
| `f32` | 32 bits | IEEE‑754 simple précision | ±3.4 × 10³⁸, 24 bits de mantisse | Modèles où la précision n’est pas critique (CNN, inference) |
| `f64` | 64 bits | IEEE‑754 double précision | ±1.8 × 10³⁰⁸, 53 bits de mantisse | Calculs scientifiques, entraînement avec petite batch |
| `i32`, `i64` | 32/64 bits | Complément à deux | 2³¹‑1 / 2⁶³‑1 | Indices, dimensions, comptage d’itérations |
| `usize` | 64 bits sur x86‑64 | – | – | Taille de vecteurs, allocations |

> **Vérifiable** : La spécification IEEE‑754 définit les intervalles ci‑dessus; la documentation de `std::primitive` confirme les tailles.

### 2.1.1 `num_traits` pour la généricité  

```rust
use num_traits::{Float, Zero};

fn dot<T: Float>(a: &[T], b: &[T]) -> T {
    a.iter()
        .zip(b.iter())
        .fold(T::zero(), |acc, (&x, &y)| acc + x * y)
}
```

*Le trait `Float` regroupe les méthodes communes (`sqrt`, `abs`, etc.).*  

## 2.2 Manipulation de matrices avec `ndarray`

`ndarray` fournit un tableau N‑dimensional (NDArray) stocké en mémoire contiguë, compatible avec les conventions C (row‑major) et Fortran (column‑major) via le paramètre `ndarray::ArrayBase<S, D>`.

```rust
use ndarray::{Array2, s};

fn main() {
    // 3×3 matrix, row‑major (default)
    let a: Array2<f64> = Array2::from_shape_vec((3, 3),
        vec![1., 2., 3.,
             4., 5., 6.,
             7., 8., 9.]).unwrap();

    // Slicing : on récupère la première colonne
    let col0 = a.slice(s![.., 0]);
    println!("col0 = {:?}", col0);
}
```

*Points de vigilance*  

| Piège | Conséquence | Remède |
|-------|-------------|--------|
| Utiliser `a.t()` (transpose) puis accéder par `a[[i, j]]` crée une vue non‑contiguë. | Accès plus lent, impossible d’appeler BLAS directement. | Copiez avec `a.reversed_axes().to_owned()` ou utilisez `ndarray::linalg::general_mat_mul` qui accepte les vues. |
| Oublier d’appeler `into_shape` après `reshape` si le nombre d’éléments change. | Panic à l’exécution. | Vérifiez `shape.iter().product::<usize>() == a.len()`. |
| Mélanger `usize` et `i64` dans les indices. | Erreur de compilation. | Normalisez sur `usize`. |

## 2.3 Implémentation de kernels BLAS  

### 2.3.1 `matrixmultiply` (pure Rust, SIMD)  

```toml
# Cargo.toml
[dependencies]
matrixmultiply = "0.3"
ndarray = { version = "0.15", features = ["blas"] }
```

```rust
use ndarray::{Array2, ArrayView2, ArrayViewMut2};
use matrixmultiply::sgemm;

/// C = α·A·B + β·C
fn gemm(a: &Array2<f32>, b: &Array2<f32>, c: &mut Array2<f32>,
        alpha: f32, beta: f32) {
    assert_eq!(a.ncols(), b.nrows());
    assert_eq!(a.nrows(), c.nrows());
    assert_eq!(b.ncols(), c.ncols());

    // Convertir en vues compatibles avec `matrixmultiply`
    let a_view: ArrayView2<f32> = a.view();
    let b_view: ArrayView2<f32> = b.view();
    let mut c_view: ArrayViewMut2<f32> = c.view_mut();

    unsafe {
        sgemm(
            a_view.nrows() as i32,
            b_view.ncols() as i32,
            a_view.ncols() as i32,
            alpha,
            a_view.as_ptr(),
            a_view.strides()[0] as i32,
            a_view.strides()[1] as i32,
            b_view.as_ptr(),
            b_view.strides()[0] as i32,
            b_view.strides()[1] as i32,
            beta,
            c_view.as_mut_ptr(),
            c_view.strides()[0] as i32,
            c_view.strides()[1] as i32,
        );
    }
}
```

*Vérifiable* : `matrixmultiply` implémente le même algorithme que le BLAS SGEMM, mais en Rust pur, avec SIMD auto‑détecté (AVX2, SSE4.2) ; la documentation du crate le précise.

### 2.3.2 Utilisation de `blas-sys` (linkage dynamique)  

```toml
[dependencies]
blas-sys = { version = "0.9", features = ["openblas"] }
ndarray = "0

---

## Module 3 — contenu

## 3.1. Architecture d’un perceptron multicouche (MLP)

| Élément | Rôle | Implémentation Rust typique |
|--------|------|-----------------------------|
| **Neuron** | Stocke les poids `w ∈ ℝⁿ` et le biais `b`. | `Array1<f32>` (de `ndarray`) pour les poids, `f32` pour le biais. |
| **Layer** | Ensemble de neurones partageant la même fonction d’activation. | Structure contenant `weights: Array2<f32>` (shape = [neurones, entrées]), `biases: Array1<f32>`, `activation: fn(&Array1<f32>) -> Array1<f32>`. |
| **Network** | Chaîne ordonnée de `Layer`. | `Vec<Layer>`; la propagation s’effectue couche par couche. |
| **Activation** | Fonction non linéaire (ReLU, Sigmoid, Softmax). | Fonctions pures qui opèrent sur `Array1<f32>` et retournent un nouveau tableau. |
| **Loss** | Mesure l’écart entre prédiction et cible (Cross‑entropy, MSE). | Fonction prenant `(pred: &Array1<f32>, target: &Array1<f32>) -> f32`. |
| **Optimiseur** | Met à jour les paramètres à partir des gradients. | Trait `Optimizer` avec méthode `step(&mut self, params: &mut [Array2<f32>], grads: &[Array2<f32>])`. |

### 3.1.1. Propagation avant (forward)

```rust
fn forward(network: &mut [Layer], input: Array1<f32>) -> Vec<Array1<f32>> {
    // Retourne la liste des activations (incluant l’entrée) pour le back‑prop.
    let mut activations = Vec::with_capacity(network.len() + 1);
    activations.push(input.clone());

    let mut x = input;
    for layer in network.iter_mut() {
        // z = W·x + b
        let z = layer.weights.dot(&x) + &layer.biases;
        // a = σ(z)
        x = (layer.activation)(&z);
        activations.push(x.clone());
    }
    activations
}
```

* `dot` de `ndarray` utilise la BLAS si le crate `blas` est activé (ex. `openblas-src`), ce qui donne un gain de 2‑5× sur les matrices > 256×256.  
* Le vecteur `x` est **re‑alloué** à chaque itération ; pour les gros réseaux on préfère ré‑utiliser un buffer pré‑alloué (`Array1<f32>::zeros`) afin d’éviter les allocations temporaires.

### 3.1.2. Propagation arrière (back‑prop)

```rust
fn backward(
    network: &mut [Layer],
    activations: &[Array1<f32>],
    target: &Array1<f32>,
) -> Vec<Array2<f32>> {
    // grads[i] correspond aux gradients de `weights` de la couche i.
    let mut grads = vec![Array2::<f32>::zeros(network[0].weights.dim()); network.len()];
    // dL/da_last = ∂loss/∂a
    let mut delta = cross_entropy_derivative(&activations.last().unwrap(), target);

    for (i, layer) in network.iter_mut().enumerate().rev() {
        // a_{l-1}
        let a_prev = &activations[i];
        // ∂L/∂W = δ·a_{l-1}ᵀ
        grads[i] = delta.clone().insert_axis(Axis(1)).dot(&a_prev.clone().insert_axis(Axis(0)));
        // ∂L/∂b = δ
        layer.biases -= &delta * layer.learning_rate; // mise à jour du biais (facultatif)
        // Propagation du delta vers la couche précédente
        // δ_{l-1} = (Wᵀ·δ) ∘ σ'(z_{l-1})
        let w_t = layer.weights.t(); // vue transposée, aucune copie
        let sigma_prime = (layer.activation_derivative)(&a_prev);
        delta = w_t.dot(&delta) * sigma_prime;
    }
    grads
}
```

* `cross_entropy_derivative` pour la sortie Softmax : `p - y`.  
* `layer.activation_derivative` doit être fourni (ex. dérivée de ReLU : `x.mapv(|v| if v > 0.0 { 1.0 } else { 0.0 })`).  
* La transposition `layer.weights.t()` ne copie pas les données ; c’est une *view* qui partage le même buffer.  

### 3.1.3. Optimiseur SGD simple

```rust
pub struct Sgd {
    pub lr: f32,
}

impl Sgd {
    pub fn step(&self, layers: &mut [Layer], grads: &[Array2<f32>]) {
        for (layer, grad) in layers.iter_mut().zip(grads.iter()) {
            layer.weights -= &(grad * self.lr);
        }
    }
}
```

## 3.2. Gestion des données

---

## Module 4 — contenu

## 4.1. Concepts clés d’ONNX et du runtime `ort`

| Concept | Description vérifiable |
|---------|------------------------|
| **ONNX (Open Neural Network Exchange)** | Format de sérialisation de graphes de calcul. Un fichier `.onnx` contient les nœuds du graphe, les poids (initializers) et les métadonnées (opset, inputs/outputs). |
| **Opset** | Version du catalogue d’opérateurs ONNX. Le runtime `ort` ne supporte que les opsets déclarés dans sa table de compatibilité (ex. 13, 14, 15). |
| **Tensor** | Représentation dense de données dans `ort`. Les dimensions, le type (`f32`, `i64`, …) et le layout (row‑major) sont stricts. |
| **Session** | Objet qui charge le modèle, optimise le graphe et conserve le plan d’exécution. Une session est thread‑safe **pour la lecture** (inférence) mais pas pour la modification du graph. |
| **Execution Provider (EP)** | Backend d’exécution (CPU, CUDA, DirectML, TensorRT…). Le choix se fait au moment de créer la `SessionBuilder`. |
| **OrtEnv** | Environnement global qui doit être créé une fois (singleton) avant toute session. Il gère le logging et les allocations natives. |

### 4.1.1. Cycle de vie typique

1. **Initialiser l’environnement** (`OrtEnv::new()`).
2. **Construire la session** (`SessionBuilder::new(&env).with_model_from_file(path)`).
3. **Préparer les entrées** (`Tensor::from_array(...)` ou `Tensor::from_vec(...)`).
4. **Lancer l’inférence** (`session.run(inputs)`).
5. **Récupérer les sorties** (`output[0].try_extract::<f32>()`).

---

## 4.2. Installation des crates

```toml
# Cargo.toml
[dependencies]
ort = { version = "2.0", features = ["cuda"] }   # active le provider CUDA
ndarray = "0.15"
image = "0.24"
anyhow = "1.0"
```

*Le feature `cuda` compile les bindings CUDA 11 + ; sinon le runtime se limite au provider CPU.*

---

## 4.3. Exemple complet : inference ResNet‑18 ONNX sur un lot de 10 000 images

> **Pré‑requis**  
> - Modèle `resnet18.onnx` exporté depuis PyTorch (`torch.onnx.export`).  
> - Images RGB 224×224 stockées dans `data/` au format JPEG.  
> - GPU avec driver CUDA 11 + et cuDNN installé.

```rust
use anyhow::Result;
use ort::{environment::Environment, session::SessionBuilder, tensor::OrtOwnedTensor, Value};
use ndarray::{Array4, Axis};
use image::io::Reader as ImageReader;
use std::path::Path;
use std::time::Instant;

/// Charge une image JPEG, la redimensionne à 224×224, la normalise et la transforme
/// en un tableau `Array4<f32>` de forme (1, 3, 224, 224) (NCHW).
fn load_image(path: &Path) -> Result<Array4<f32>> {
    // 1. Lecture + conversion RGB
    let img = ImageReader::open(path)?.decode()?.to_rgb8();

    // 2. Redimensionnement bilinéaire
    let resized = image::imageops::resize(&img, 224, 224, image::imageops::FilterType::Triangle);

    // 3. Normalisation (ImageNet)
    let mean = [0.485_f32, 0.456, 0.406];
    let std  = [0.229_f32, 0.224, 0.225];

    // 4. Construction du tenseur NCHW
    let mut array = ndarray::Array4::<f32>::zeros((1, 3, 224, 224));
    for (c, (m, s)) in mean.iter().zip(std.iter()).enumerate() {
        for y in 0..224 {
            for x in 0..224 {
                let pixel = resized.get_pixel(x, y)[c] as f32 / 255.0;
                array[[0, c, y, x]] = (pixel - m) / s;
            }
        }
    }
    Ok(array)
}

/// Crée un batch `Array4<f32>` à partir d’un vecteur de chemins d’images.
fn build_batch(paths: &[impl AsRef<Path>]) -> Result<Array4<f32>> {
    // On charge la première image pour connaître la forme.
    let first = load_image(paths[0].as_ref())?;
    let (n, c, h, w) = first.dim();
    let mut batch = ndarray::Array4::<f32>::zeros((paths.len(), c, h, w));

    for (i, p) in paths.iter().enumerate() {
        let img = load_image(p.as_ref())?;
        // `img` a déjà la dimension (1, C, H, W)
        batch.slice_mut(s![i..i+1, .., .., ..])
            .assign(&img.slice(s![0..1, .., .., ..]));
    }
    Ok(batch)
}

/// Mesure le débit (images/s) d’une session ONNX Runtime.
fn benchmark(session: &ort::session::Session, batch: &Array4<f32>, runs: usize) -> Result<f64> {
    // Convertir le batch en `Value` (

---

## Module 5 — contenu

## 5.1 Architecture de l’API d’inférence  

| Composant | Rôle | Implémentation Rust | Remarque |
|-----------|------|---------------------|----------|
| **HTTP server** | reçoit les requêtes, orchestre le traitement | `actix-web` (v4) ou `warp` (v0.3) | `actix-web` utilise un pool de threads (`actix-rt`) compatible avec les appels bloquants si on les isole avec `web::block`. |
| **Gestion du modèle** | charge le modèle ONNX une fois, le conserve en mémoire partagée | Crate `ort` (v1.12) – `Arc<Session>` | `Session` est thread‑safe (`Send + Sync`). |
| **Sérialisation** | convertit le payload JSON ↔ tensors | `serde` + `serde_json` pour les messages, `ndarray` pour les tensors | La conversion `Vec<f32> → ndarray::Array2<f32>` ne copie pas les données si on utilise `ArrayView`. |
| **Logging & métriques** | trace les temps de latence, erreurs, compte les requêtes | `tracing` + `tracing-subscriber`, `prometheus` | Exporter `/metrics` pour Prometheus. |
| **Health‑check** | permet au orchestrateur de détecter les pods sains | Endpoint `/healthz` renvoie `200 OK` si le `Session` est chargé | Doit être rapide ; ne pas lancer de calculs lourds. |

---

## 5.2 Sérialisation du payload  

```json
// Exemple de requête POST /infer
{
  "batch": [
    [0.0, 0.1, …, 0.255],   // 784 valeurs (MNIST 28×28)
    [0.0, 0.2, …, 0.255]
  ]
}
```

* **Requête** → `Vec<Vec<f32>>` → `Array2<f32>` (shape = (batch, 784)).  
* **Réponse** → `Vec<u8>` (classe prédite) ou `Vec<f32>` (probabilités).  

```rust
#[derive(Deserialize)]
struct InferRequest {
    batch: Vec<Vec<f32>>, // chaque sous‑vecteur = image aplatie
}

#[derive(Serialize)]
struct InferResponse {
    predictions: Vec<u8>, // classe 0‑9
}
```

---

## 5.3 Exemple complet d’API (actix‑web)  

```rust
use actix_web::{post, web, App, HttpResponse, HttpServer, Responder};
use ort::{Environment, SessionBuilder, Value};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use ndarray::Array2;
use tracing::{info, instrument};

/// Payload d’entrée
#[derive(Deserialize)]
struct InferRequest {
    batch: Vec<Vec<f32>>, // (batch, 784)
}

/// Résultat d’inférence
#[derive(Serialize)]
struct InferResponse {
    predictions: Vec<u8>,
}

/// Charge le modèle ONNX une fois au démarrage.
fn load_model() -> Arc<ort::Session> {
    // L’environnement doit être créé une seule fois.
    let env = Environment::builder()
        .with_name("rust-onnx")
        .build()
        .unwrap();

    // Chemin relatif du modèle pré‑compilé.
    let session = SessionBuilder::new(&env)
        .unwrap()
        .with_optimization_level(ort::GraphOptimizationLevel::Basic)
        .unwrap()
        .with_model_from_file("resnet18.onnx")
        .unwrap();

    Arc::new(session)
}

/// Convertit un `Vec<Vec<f32>>` en `ndarray::Array2<f32>` sans copie supplémentaire.
fn to_ndarray(batch: &[Vec<f32>]) -> Array2<f32> {
    let rows = batch.len();
    let cols = batch[0].len();
    // Flatten et créer la vue.
    let flat: Vec<f32> = batch.iter().flat_map(|v| v.iter()).cloned().collect();
    Array2::from_shape_vec((rows, cols), flat).unwrap()
}

/// Handler d’inférence – bloque le calcul dans `web::block` pour ne pas
/// monopoliser le runtime async.
#[post("/infer")]
#[instrument(skip(session, payload))]
async fn infer(
    session: web::Data<Arc<ort::Session>>,
    payload: web::Json<InferRequest>,
) -> impl Responder {
    // Clone du Arc pour le thread de blocage.
    let session = session.clone();
    let batch = payload.batch.clone();

    // Exécution bloquante isolée.
    let result = web::block(move || {
        // 1️⃣ Pré‑traitement
        let input = to_ndarray(&batch);
        let input_tensor = Value::from_array(session.allocator(), input)?;

        // 2️⃣ Inference
        let outputs = session.run(vec![input_tensor])?;
        // ONNX Runtime renvoie un vecteur de `Value`; on attend un seul output.
        let logits = outputs