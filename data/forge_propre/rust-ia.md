# Rust pour l'IA & Performance

> Référence `rust-ia`

## Plan

## Module 1 – Fondamentaux de Rust orientés IA  
**Objectif mesurable :** L’apprenant écrit, compile et exécute un programme Rust qui charge et pré‑traite un jeu de données CSV sans fuite de mémoire.  
**Notions couvertes**  
- Système de types, ownership, borrowing et lifetimes appliqués aux structures de données tabulaires.  
- Gestion de la mémoire avec `Vec`, `String`, slices et `Option`/`Result`.  
- Utilisation de `serde` et `csv` pour la désérialisation sécurisée.  
- Traitement parallèle avec `rayon` : map‑reduce sur des collections.  
- Profilage basique avec `cargo bench` et `perf`.

---

## Module 2 – Calculs numériques et algèbre linéaire en Rust  
**Objectif mesurable :** L’apprenant implémente et compare deux algorithmes de multiplication matricielle (naïf et Strassen) sur des matrices de grande dimension, en mesurant le temps d’exécution et l’utilisation de la RAM.  
**Notions couvertes**  
- Types numériques (`f32`, `f64`, `num_traits`) et précision flottante.  
- Bibliothèque `ndarray` : création, slicing, broadcasting.  
- Implémentation de kernels BLAS via `blas-sys` ou `matrixmultiply`.  
- Optimisation cache‑aware et parallélisation (`rayon`, `crossbeam`).  
- Benchmarks avec `criterion` et interprétation des résultats.

---

## Module 3 – Construction de modèles de machine learning basiques  
**Objectif mesurable :** L’apprenant crée, entraîne et évalue un perceptron multicouche (MLP) sur le jeu de données MNIST, atteignant une précision satisfaisante sur le set de validation.  
**Notions couvertes**  
- Structures de réseaux (`Layer`, `Activation`) et propagation avant/arrière.  
- Calculs de gradients avec `autograd` (ex. `autodiff` crate) ou implémentation manuelle.  
- Optimiseurs (SGD, Adam) et gestion des hyper‑paramètres.  
- Sérialisation du modèle (`bincode`, `serde_json`).  
- Évaluation (accuracy, loss) et visualisation avec `plotters`.

---

## Module 4 – Intégration de bibliothèques IA externes (ONNX, TensorFlow‑Rust)  
**Objectif mesurable :** L’apprenant charge un modèle ONNX pré‑entraîné (ResNet‑18) et l’exécute sur un lot d’images, en mesurant le débit et la consommation GPU/CPU.  
**Notions couvertes**  
- Format ONNX et conversion de modèles (PyTorch → ONNX).  
- Crate `ort` (ONNX Runtime) : session, tensors, inference.  
- Gestion de l’accélération matériel (CUDA, DirectML) via `ort`.  
- Interfaçage avec `tch-rs` (bindings TensorFlow) pour comparaison.  
- Profilage GPU avec `nvprof` et analyse des goulots d’étranglement.

---

## Module 5 – Déploiement, scalabilité et bonnes pratiques de production  
**Objectif mesurable :** L’apprenant containerise une API Rust exposant un endpoint d’inférence, la déploie sur Kubernetes et assure une latence faible pour un trafic soutenu avec autoscaling.  
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

    // 2️⃣ Allocation anticipée : on suppose un grand nombre de lignes → capacité suffisante
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

* `cargo bench` exécute le benchmark avec `criterion`.  
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