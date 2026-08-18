# IA pour les RH & Recrutement

> Référence `ia-rh` · 59 €

## Plan

## Module 1 – Fondamentaux de l’IA appliquée aux RH  
**Objectif mesurable** : Être capable d’expliquer les concepts clés de l’IA et de choisir le type de modèle (supervisé, non‑supervisé, hybride) adapté à un cas d’usage RH.  
**Notions couvertes**  
- Types de tâches IA en RH : classification, régression, clustering, recommandation.  
- Algorithmes de base (logistic regression, decision trees, k‑means, embeddings) et leurs limites sur des jeux de données RH.  
- Métriques d’évaluation spécifiques (precision/recall pour la sélection de candidats, F1‑score, ROC‑AUC, silhouette score).  
- Biais de données (sample bias, label bias) et impact sur les décisions RH.  
- Pipeline de modélisation (collecte → prétraitement → entraînement → validation) appliqué aux processus RH.


---

## Module 2 – Extraction et prétraitement des données RH  
**Objectif mesurable** : Implémenter un pipeline automatisé en Python pour nettoyer, normaliser et enrichir les CV, profils LinkedIn et bases internes, avec un taux d’erreur de parsing limité.  
**Notions couvertes**  
- Formats de données RH (PDF, DOCX, HTML, JSON) et bibliothèques de parsing (pdfminer.six, python-docx, BeautifulSoup).  
- Techniques de NER (spaCy, HuggingFace Transformers) pour identifier noms, compétences, expériences, dates.  
- Normalisation des taxonomies de compétences (ESCO, O*NET) et mapping sémantique avec des embeddings (FastText, Sentence‑BERT).  
- Gestion des valeurs manquantes et des outliers (imputation, winsorisation).  
- Construction de jeux de données structurés (pandas DataFrames) prêts à l’alimentation de modèles.
---

## Module 3 – Modélisation du sourcing et du matching de candidats  
**Objectif mesurable** : Déployer un modèle de recommandation qui propose les 5 meilleurs candidats pour une offre donnée, avec un NDCG@5 ≥ 0,75 sur un jeu de test réel.  
**Notions couvertes**  
- Représentation vectorielle des postes et des profils (TF‑IDF, embeddings de phrases, modèles de langage pré‑entraînés).  
- Algorithmes de matching (cosine similarity, bilinear models, factorisation matricielle).  
- Modèles de filtrage collaboratif et hybride (content‑based + collaborative).  
- Apprentissage par renforcement pour optimiser le flux de sourcing (reward = taux de réponse).  
- Validation croisée temporelle pour éviter le leakage dans les données de recrutement.


---

## Module 4 – Analyse prédictive de la rétention et de la performance  
**Objectif mesurable** : Construire un modèle de churn prédictif qui identifie les employés à risque de départ avec un recall ≥ 0,80 et un taux de faux positifs < 0,15


---

## Module 1 — contenu

## 1.1 Types de tâches IA en RH  

| Tâche | Description | Exemple d’usage RH |
|------|-------------|--------------------|
| **Classification** | Attribution d’une ou plusieurs étiquettes à une observation. | Sélection de CV : « candidat admissible / non admissible ». |
| **Régression** | Prédiction d’une variable continue. | Estimation du salaire de départ d’un nouveau collaborateur. |
| **Clustering** | Regroupement non supervisé d’observations similaires. | Segmentation de la main‑d’œuvre par profils de compétences. |
| **Recommandation** | Ordonnancement de candidats ou d’offres selon une pertinence. | Système de matching poste‑candidat. |

> **Note technique** : En RH, les jeux de données sont souvent déséquilibrés (ex. : un faible pourcentage de candidatures retenues). Le choix de la tâche influe directement sur les métriques à surveiller.

---

## 1.2 Algorithmes de base et limites  

| Algorithme | Type (supervisé / non‑supervisé) | Points forts | Limites spécifiques aux RH |
|-----------|--------------------------------|--------------|-----------------------------|
| **Logistic Regression** | Supervisé (classification) | Interprétable (coefficients = poids des variables) | Linéarité : ne capture pas les interactions complexes entre compétences. |
| **Decision Trees** | Supervisé (classification / régression) | Gère variables catégorielles sans encodage, non linéaire | Sur‑apprentissage sur petits jeux de CV, sensibilité aux petites variations de données. |
| **k‑means** | Non‑supervisé (clustering) | Simple, rapide sur jeux de taille moyenne | Supposition de sphéricité des clusters ; mauvaise performance quand les compétences sont représentées par des embeddings de haute dimension. |
| **Embeddings (Word2Vec, Sentence‑BERT)** | Non‑supervisé (représentation) | Capture la sémantique des compétences, robustes au bruit lexical | Nécessitent un corpus suffisamment grand ; les biais du corpus se répercutent dans les vecteurs. |

---

## 1.3 Métriques d’évaluation RH  

| Métrique | Formule | Situation d’usage |
|----------|---------|-------------------|
| **Precision** | TP / (TP + FP) | Importance de ne pas proposer de candidats inadaptés (coût de l’entretien). |
| **Recall** | TP / (TP + FN) | Priorité à ne pas laisser passer de bons candidats (coût d’opportunité). |
| **F1‑score** | 2·(Precision·Recall)/(Precision+Recall) | Équilibre entre précision et rappel, souvent utilisé en sélection de CV. |
| **ROC‑AUC** | Aire sous la courbe ROC | Comparaison de modèles de classification binaire, insensible au déséquilibre de classes. |
| **Silhouette Score** | (b‑a)/max(a,b) où a = cohésion intra‑cluster, b = séparation inter‑cluster | Évaluation de la qualité d’un clustering de profils. |

> **Précision de calcul** : Pour le **Recall** en RH, on considère généralement le « candidat réellement qualifié » comme positif, même si le label a été attribué a posteriori (ex. : embauché après plusieurs mois).  

---

## 1.4 Biais de données et impact RH  

| Biais | Origine | Conséquence possible |
|------|----------|----------------------|
| **Sample bias** | Jeux de données non représentatifs (ex. : uniquement des CV provenant d’une plateforme) | Modèle favorise les profils typiques de cette plateforme, exclut d’autres canaux. |
| **Label bias** | Annotations influencées par des stéréotypes (ex. : évaluations de performance biaisées par le genre) | Le modèle apprend à reproduire les discriminations historiques. |
| **Historical bias** | Processus de recrutement passé déjà biaisé (ex. : sous‑représentation de femmes dans tech) | Même avec des données équilibrées, le modèle reproduit les tendances historiques. |
| **Measurement bias** | Erreurs de parsing (ex. : mauvaise extraction de dates) | Variables erronées entraînent des prédictions incohérentes. |

### Mitigation concrète (pipeline)  

1. **Audit initial** : comparer la distribution des variables clés (genre, âge, niveau d’études) à la population cible.  
2. **Re‑balancement** : sur‑échantillonnage des minorités (SMOTE) ou sous‑échantillonnage des majorités.  
3. **Dé‑biasing des embeddings** : appliquer la méthode *hard debias* (Bolukbasi et al., 2016) sur les vecteurs de compétences.  
4. **Validation croisée stratifiée** sur le label de sélection pour garantir que chaque fold reflète la même proportion de classes.  

---

## 1.5 Pipeline de modélisation appliqué aux RH  

```python
# pipeline_rh.py
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score

# 1. Chargement des données (exemple simplifié)
df = pd.read_csv('candidates.csv')   # colonnes : id, gender, age, degree, years_exp, skill_vector, hired

# 2. Sélection des features et du target
X = df.drop(columns=['id', 'hired'])
y = df['
```
---

## Module 2 — contenu

## 2.1 Formats de données RH et bibliothèques de parsing  

| Format | Bibliothèque Python | Points d’attention |
|--------|----------------------|--------------------|
| PDF (texte) | `pdfminer.six` – `PDFPage`, `PDFResourceManager`, `LAParams`, `PDFPageInterpreter` | Le texte extrait dépend du layout ; les PDF scannés nécessitent OCR (ex. `pytesseract`). |
| PDF (scanné) | `pdf2image` + `pytesseract` | Qualité d’image recommandée, sinon taux d’erreur. |
| DOCX | `python-docx` – `Document` | Les styles (titre, tableau) ne sont pas conservés ; il faut parcourir les paragraphes et les tables séparément. |
| HTML (pages LinkedIn, sites d’emploi) | `BeautifulSoup` (parser `lxml`) | Les pages dynamiques (React/Angular) nécessitent `selenium` ou `playwright` pour rendre le DOM. |
| JSON (APIs internes) | `json` standard | Vérifier la présence de clés obligatoires (`candidate_id`, `experience`). |

> **Règle de base** : centraliser le parsing dans une fonction `parse_<format>(path) -> dict` qui renvoie toujours le même schéma de sortie (voir 2.3).  

---

## 2.2 Pipeline de prétraitement global  

```
raw_text ──► cleaning (unicode, whitespace) ──► NER extraction ──► taxonomy mapping ──► structured DataFrame
```

1. **Nettoyage**  
   - Normaliser les caractères Unicode (`unicodedata.normalize('NFKC', txt)`).  
   - Supprimer les espaces multiples (`re.sub(r'\s+', ' ', txt)`).  
   - Conserver les sauts de ligne uniquement lorsqu’ils séparent des blocs logiques (ex. expériences).  

2. **Extraction d’entités nommées (NER)**  
   - Modèle de base : `fr_core_news_md` de spaCy.  
   - Fine‑tuning sur un corpus de CV annotés : `spacy train` avec `ner` et `entity_ruler`.  
   - Entités à extraire : `PERSON`, `ORG`, `DATE`, `SKILL`, `EDUCATION`, `CERTIFICATE`.  

3. **Normalisation des compétences**  
   - Taxonomie : **ESCO** (European Skills, Competences, Qualifications).  
   - Embedding : `sentence-transformers/all-MiniLM-L6-v2`.  
   - Algorithme de mapping : recherche du **k‑nearest neighbour** dans l’espace ESCO, puis vote majoritaire sur le libellé.  

4. **Gestion des valeurs manquantes**  
   - `experience_years` : imputation par la médiane par groupe de fonction (`job_title`).  
   - `skills` : si vide, récupérer les mots‑clés du texte brut via TF‑IDF.  

5. **Construction du DataFrame**  

```python
import pandas as pd

def build_dataframe(candidates: list[dict]) -> pd.DataFrame:
    """Retourne un DataFrame avec les colonnes standardisées."""
    rows = []
    for cand in candidates:
        rows.append({
            "candidate_id": cand["id"],
            "full_name": cand["name"],
            "email": cand.get("email"),
            "years_experience": cand.get("experience_years"),
            "skills": ";".join(cand.get("skills_norm", [])),
            "last_job_title": cand.get("last_job_title"),
            "education_level": cand.get("education"),
            "source_file":
---

## Module 3 — contenu

## 3.1 Représentation vectorielle des postes et des profils  

| Source | Technique | Bibliothèque / modèle | Dimensions typiques | Commentaire vérifiable |
|--------|-----------|-----------------------|--------------------|------------------------|
| Texte brut (description de poste, CV) | TF‑IDF (unigrammes + bigrammes) | `sklearn.feature_extraction.text.TfidfVectorizer` | 5 000 – 20 000 (selon vocabulaire) | Reproductible : même corpus → même matrice. |
| Phrase courte (titre, compétence) | Embeddings de phrases | `sentence_transformers.SentenceTransformer('paraphrase‑multilingual‑MSMarco‑v2')` | 768 | Les vecteurs sont normalisés à l’unité (norme = 1) par défaut. |
| Entité sémantique (compétence, métier) | FastText pré‑entraîné sur Wikipedia | `gensim.models.fasttext.load_facebook_vectors` | 300 | FastText gère les mots hors‑vocabulaire via n‑grammes. |
| Profil complet (concatenation de plusieurs champs) | Agrégation pondérée (ex. 0.5 × titre + 0.3 × expérience + 0.2 × compétences) | `numpy` ou `torch` | 768 | La pondération doit être calibrée sur un jeu de validation. |

> **Bon à savoir** : les embeddings de phrases (SBERT) offrent de meilleures performances sur les tâches de similarité sémantique que TF‑IDF, surtout quand les descriptions sont longues et contiennent du vocabulaire métier rare.

### 3.1.1 Pipeline de construction d’embeddings

```python
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

# 1. Chargement des données
jobs  = pd.read_csv('jobs.csv')       # colonnes: job_id, title, description, skills
cvs   = pd.read_csv('cvs.csv')        # colonnes: cv_id, name, headline, experience, skills

# 2. Pré‑traitement texte (lowercase, suppression des caractères spéciaux)
def clean(txt: str) -> str:
    import re
    txt = txt.lower()
    txt = re.sub(r'[^a-z0-9\s]', ' ', txt)
    return ' '.join(txt.split())

for col in ['title','description','skills']:
    jobs[col] = jobs[col].fillna('').apply(clean)
for col in ['headline','experience','skills']:
    cvs[col] = cvs[col].fillna('').apply(clean)

# 3. Embedding de texte long avec SBERT
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')  # 384‑dim

def embed_sentence(series):
    return model.encode(series.tolist(), batch_size=64, show_progress_bar=True)

jobs['vec_desc'] = list(embed_sentence(jobs['description']))
cvs['vec_head'] = list(embed_sentence(cvs['headline']))

# 4. TF‑IDF sur les compétences (liste séparée par ';')
tfidf = TfidfVectorizer(token_pattern=r'[^;]+')
tfidf.fit(jobs['skills'].tolist() + cvs['skills'].tolist())
jobs['vec_skills'] = list(tfidf.transform(jobs['skills']).toarray())
cvs['vec_skills']  = list(tfidf.transform(cvs['skills']).toarray())

# 5. Agrégation pondérée (0.6 desc + 0.4 skills)
def weighted_concat(desc, skills, w_desc=0.6, w_skills=0.4):
    # normalisation L2 avant agrégation
    desc  = normalize([desc])[0]
    skills= normalize([skills])[0]
    return w_desc*desc + w_skills*skills

jobs['vec'] = jobs.apply(lambda r: weighted_concat(r.vec_desc, r.vec_skills), axis=1)
cvs['vec']  = cvs.apply (lambda r: weighted_concat(r.vec_head, r.vec_skills), axis=1)

# 6. Sauvegarde des vecteurs (npz compact)
np.savez_compressed('vectors_jobs.npz', ids=jobs.job_id.values, vecs=np.vstack(jobs.vec.values))
np.savez_compressed('vectors_cvs.npz',  ids=cvs.cv_id.values,  vecs=np.vstack(cvs.vec.values))
```

*Commentaires*  

* `SentenceTransformer` renvoie des vecteurs déjà normalisés (norme ≈ 1).  
* `normalize` de `sklearn` garantit que la pondération ne change pas la norme globale.  
* Le fichier `.npz` permet un chargement O(1) des vecteurs en mémoire pour le service de matching.

---

## 3.2 Algorithmes de matching  

### 3.2.1 Similarity cosine (baseline)

```python
from sklearn.metrics.pairwise import cosine_similarity

def top_k_candidates(job_vec, cvs_vecs, cvs_ids, k=5):
    sims = cosine_similarity(job_vec.reshape(1, -1), cvs_vecs).flatten()
    idx  = np.argpartition(-sims, k)[:k]               # k plus grandes valeurs
    top_ids = cvs_ids[idx[np.argsort(-sims[idx])]]    # tri décroissant
    top_sims = sims[idx[np.argsort(-sims[idx])]]
    return list(zip(top_ids, top_s


---

## Module 4 — contenu

## 4.1 Problématique et cadre de modélisation  

| Question métier | « Quels employés risquent de quitter l’entreprise ? » |
|----------------|---------------------------------------------------|
| Variable cible | `attrition` (0 = reste, 1 = part) |
| Horizon prédictif | 6 mois (départ prévu dans les 180 jours suivant la date de snapshot) |
| Contraintes | - Recall élevé <br> - Taux de faux‑positifs (FPR) limité <br> - Modèle exploitable en production (explainability) |
| Données disponibles | - Dossiers RH (date d’entrée, poste, niveau, salaire, localisation) <br> - Historique de performances (scores, évaluations) <br> - Historique de formation (nombre d’heures, type) <br> - Engagement (taux d’ouverture des mails internes, participation aux sondages) <br> - Variables temporelles (ancienneté, temps depuis dernière promotion) |

### 4.1.1 Définition du problème  

Il s’agit d’un **problème de classification binaire** avec un déséquilibre typique : le taux de churn (départs) varie selon les secteurs. Le modèle doit maximiser la capacité à détecter les vrais départs (high recall) tout en limitant les alertes inutiles (low FPR).

---

## 4.2 Pré‑traitement et ingénierie des caractéristiques  

### 4.2.1 Nettoyage de base  

```python
import pandas as pd
import numpy as np

# Lecture du jeu de données
df = pd.read_csv('hr_attrition.csv', parse_dates=['date_embauche', 'date_snapshot'])

# Suppression des colonnes purement identifiantes
df = df.drop(columns=['employee_id', 'email'])

# Gestion des valeurs manquantes
# - Variables numériques : imputation par la médiane
# - Variables catégorielles : imputation par la modalité "Inconnu"
num_cols = df.select_dtypes(include='number').columns
cat_cols = df.select_dtypes(exclude='number').columns

df[num_cols] = df[num_cols].fillna(df[num_cols].median())
df[cat_cols] = df[cat_cols].fillna('Inconnu')
```

### 4.2.2 Création de variables temporelles  

```python
# Ancienneté en années
df['anciennete_annees'] = (df['date_snapshot'] - df['date_embauche']).dt.days / 365.25

# Temps depuis la dernière promotion
df['temps_depuis_dern_promo'] = (df['date_snapshot'] - df['date_derniere_promotion']).dt.days / 30.0
df['temps_depuis_dern_promo'] = df['temps_depuis_dern_promo'].fillna(df['temps_depuis_dern_promo'].median())
```

### 4.2.3 Encodage des variables catégorielles  

* **One‑Hot** pour les variables à faible cardinalité (ex. : `niveau`, `secteur`).  
* **Target Encoding** (ou **Mean Encoding**) pour les variables à forte cardinalité (ex. : `poste`).  

```python
from category_encoders import TargetEncoder

high_card_cols = ['poste']
te = TargetEncoder(cols=high_card_cols)
df = te.fit_transform(df, df['attrition'])
```

### 4.2.4 Gestion du déséquilibre  

- **Sous‑échantillonnage** de la classe majoritaire (`attrition=0`) ou **sur‑échantillonnage** de la classe minoritaire avec SMOTE.  
- **Poids de classe** dans l’algorithme (ex. : `class_weight='balanced'` dans scikit‑learn).

```python
from imblearn.over_sampling import SMOTE

X = df.drop(columns='attrition')
y = df['attrition']

sm = SMOTE(sampling_strategy=0.3, random_state=42)   # une proportion accrue de churn après sur‑échantillonnage
X_res, y_res = sm.fit_resample(X, y)
```

---

## 4.3 Choix du modèle  

| Modèle | Avantages | Inconvénients | Interprétabilité |
|--------|-----------|---------------|------------------|
| **Logistic Regression** | Baseline rapide, coefficients interprétables | Linéarité, performance limitée | Très élevée |
| **Random Forest** | Gère variables mixtes, robuste aux outliers | Moins transparent, plus lourd | Moyenne (feature importance) |
| **Gradient Boosting (XGBoost / LightGBM)** | Meilleure performance sur données tabulaires, contrôle du sur‑apprentissage | Complexité, besoin de tuning | Moyenne (SHAP) |
| **Neural Network (TabNet)** | Capture interactions non linéaires, bonne scalabilité | Nécessite plus de données, moins transparent | Faible (explainability via attention) |

Pour atteindre un recall élevé tout en contrôlant le FPR, on privilégie un **XGBoost** avec réglage du paramètre `scale_pos_weight` et du seuil de décision.

### 4.3.1 Entraînement avec XGBoost  

```python
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import recall_score, confusion_matrix, roc_auc_score

# Séparation temporelle : les snapshots antérieurs servent à l'ent
```
---

## Module 5 — contenu

## Module 5 – Mise en production, suivi et gouvernance des modèles IA RH  

### Objectif mesurable  
Déployer un modèle de matching ou de churn en environnement de production, mettre en place un tableau de bord de monitoring (performance, dérive, biais) et garantir la conformité RGPD et la traçabilité des décisions.  

---

## 5.1 Architecture de déploiement  

| Composant | Rôle | Technologies courantes | Points de contrôle |
|-----------|------|------------------------|--------------------|
| **Modèle entraîné** | Artefact immuable | Pickle, joblib, ONNX, TorchScript | Version : `model_v2024_08_01.pkl` |
| **API d’inférence** | Point d’entrée HTTP | FastAPI, Flask, Django REST, Azure Functions | Authentification OAuth2, limite de débit |
| **Orchestrateur** | Gestion du cycle de vie | Docker, Kubernetes, Airflow (re‑training) | Rolling update, health‑check `/healthz` |
| **Store de logs** | Traçabilité des prédictions | ELK (Elasticsearch‑Logstash‑Kibana), Loki | Log structuré JSON : `{timestamp, user_id, input_hash, score}` |
| **Monitoring métrique** | Détection de dérive & performance | Prometheus + Grafana, Evidently AI | Alertes sur `recall < 0.75` ou `data_drift_score > 0.8` |
| **Gestion des accès** | Confidentialité des données | IAM (AWS IAM, Azure AD), chiffrement TLS | Audit des appels API |

---

## 5.2 Pipeline CI/CD pour les modèles IA  

1. **Build** – Dockerfile qui installe les dépendances (`requirements.txt`), copie le modèle et le code d’API.  
2. **Test** – Unit‑tests (pytest) sur la fonction `predict()`, tests de charge (`locust`) et validation des métriques (`evidently`).  
3. **Publish** – Image Docker poussée vers le registre (ECR, GCR).  
4. **Deploy** – Helm chart ou `kubectl apply` avec `imagePullPolicy: IfNotPresent`.  
5. **Rollback** – Tag `previous` dans le registre, `kubectl rollout undo`.  

*Vérifiable* : chaque étape doit être déclenchée par un commit Git et enregistrée dans le pipeline (GitHub Actions, GitLab CI, Azure Pipelines).

---

## 5.3 Monitoring de la performance et de la dérive  

```python
# file: monitoring.py
import pandas as pd
from evidently.dashboard import Dashboard
from evidently.tabs import DataDriftTab, ClassificationPerformanceTab

def build_dashboard(ref: pd.DataFrame, cur: pd.DataFrame, target: str):
    """
    Crée un tableau de bord Evidently pour la dérive de données et la performance.
    ref  – jeu de référence (ex. données d’entraînement)
    cur  – données réelles en production (ex. dernières 7 jours)
    target – colonne cible (ex. `churn`)
    """
    dashboard = Dashboard(tabs=[DataDriftTab, ClassificationPerformanceTab])
    dashboard.calculate(ref, cur, column_mapping={"target": target})
    return dashboard

# Exemple d’utilisation (dans un job Cron quotidien)
if __name__ == "__main__":
    ref = pd.read_parquet("s3://model-bucket/train_features.parquet")
    cur = pd.read_parquet("s3://model-bucket/prod_features_last7d.parquet")
    dash = build_dashboard(ref, cur, target="churn")
    dash.save("reports/dash_churn.html")
```

*Commentaires*  
- `ref` doit être figé ; aucune mise à jour ne doit être faite sans versionnage.  
- Le score de dérive (`DataDriftTab`) utilise le test KS pour chaque feature ; un **p‑value < 0.05** déclenche une alerte.  
- Le tableau de bord est hébergé en lecture‑seule sur un serveur interne (ex. S3 static site).  

---

## 5.4 Gestion des biais en production  

| Biais | Détection | Correction (post‑hoc) |
|-------|-----------|----------------------|
| **Sample bias** (candidats provenant majoritairement d’un canal) | Distribution du `source_channel` dans le tableau de bord → compare `ref` vs `cur` | Re‑pondération des scores (`weight = 1 / freq(channel)`) |
| **Label bias** (historique de décisions humaines) | Analyse de la courbe ROC par sous‑groupe (genre, âge) | Calibrage isotone par groupe ou apprentissage adversarial |
| **Feedback loop** (candidats sélectionnés → plus de données d’entraînement) | Correlation entre `prediction_score` et `recontact_rate` | Introduire des **exploration** aléatoires (ε‑greedy) dans le moteur de recommandation |

*Piège concret* : ne pas ré‑entraîner le modèle uniquement sur les candidats **acceptés** ; cela renforce le biais de sélection et dégrade la capacité à découvrir de nouveaux profils.

---