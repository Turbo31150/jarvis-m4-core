# Vibe Coding 2026

> Référence `vibe-coding` · 39 €

## Plan

## Module 1 : Prompt Engineering avancé  
**Objectif mesurable** : À l’issue de ce module, le participant sera capable de concevoir, tester et itérer des prompts capables de générer des réponses avec une précision sémantique élevée sur un jeu de validation de cent requêtes.  

**Notions couvertes**  
1. Structure syntaxique des prompts (système, utilisateur, assistant) et impact sur le modèle.  
2. Techniques de few‑shot et chain‑of‑thought pour guider le raisonnement.  
3. Méthodes de contrôle de la température, top‑p et présence‑penalty pour la diversité et la cohérence.  
4. Analyse de la sortie : métriques BLEU, ROUGE, et évaluation humaine calibrée.  
5. Boucles d’optimisation automatisées (prompt‑tuning via API).

---

## Module 2 : Modélisation de données pour LLMs  
**Objectif mesurable** : Le participant pourra préparer un corpus de taille adaptée, le nettoyer, le tokeniser et le charger dans un pipeline d’entraînement, en respectant un taux d’erreur très faible.  

**Notions couvertes**  
1. Nettoyage de texte (déduplication, normalisation Unicode, filtrage de toxicité).  
2. Tokenisation byte‑pair encoding (BPE) et comparaison avec WordPiece.  
3. Construction de jeux d’entraînement/validation/test équilibrés.  
4. Gestion des biais de distribution (stratification, rééchantillonnage).  
5. Utilisation de `datasets` de Hugging Face et de `DataCollator`.

---

## Module 3 : Fine‑tuning et adaptation de modèles pré‑entraînés  
**Objectif mesurable** : Le participant sera capable de fine‑tuner un modèle de grande taille sur un domaine spécifique en un temps raisonnable, avec une perte de validation faible.  

**Notions couvertes**  
1. Sélection de l’architecture (GPT‑Neo, LLaMA, Falcon) et du checkpoint.  
2. Paramètres d’entraînement (learning‑rate, batch size, gradient accumulation).  
3. Techniques de LoRA (Low‑Rank Adaptation) et QLoRA pour réduire la consommation mémoire.  
4. Gestion des checkpoints et reprise d’entraînement (DeepSpeed, ZeRO‑3).  
5. Évaluation post‑entraînement (perplexité, exact‑match, métriques de tâche).

---

## Module 4 : Intégration d’IA générative dans des applications backend  
**Objectif mesurable** : Le participant pourra exposer une API REST sécurisée qui interroge un LLM fine‑tuned, avec une latence moyenne très courte pour un nombre modéré de tokens, et implémenter une politique de quota.  

**Notions couvertes**  
1. Déploiement de modèles via `transformers` + `FastAPI` ou `Flask`.  
2. Optimisation d’inférence (ONNX, TensorRT, quantisation int8).  
3. Authentification OAuth2, gestion de tokens d’accès et limites de requêtes.  
4. Mise en cache des réponses (Redis) et stratégies de rafraîchissement.  
5. Monitoring (Prometheus, Grafana) et logs

---

## Module 1 — contenu

## Module 1 – Prompt Engineering avancé  

### 1. Structure syntaxique des messages  

| Niveau | Rôle | Exemple de champ | Influence sur le modèle |
|--------|------|------------------|--------------------------|
| Système | `system` | `"You are a helpful assistant that always returns JSON."` | Définit le comportement global, la tonalité et les contraintes de format. |
| Utilisateur | `user` | `"Explique la différence entre BPE et WordPiece en 2 phrases."` | Pose la question ou la tâche. Le modèle se base sur le contexte fourni. |
| Assistant | `assistant` | `"Sure, here is the answer …"` | Utilisé pour le few‑shot (exemples de réponses attendues). |

**Bonnes pratiques**  
- Le message `system` doit être concis.  
- Chaque exemple `user`/`assistant` doit être complet : ne laissez pas de champs vides, sinon le modèle peut générer des réponses hors‑format.  
- Placez les contraintes de format (ex. `JSON`, `XML`) dans le `system` ou le premier `user` pour que le modèle les mémorise dès le départ.  

### 2. Few‑shot & Chain‑of‑thought (CoT)  

#### 2.1 Few‑shot  
```python
messages = [
    {"role": "system", "content": "You are a French tutor. Answer in French only."},
    {"role": "user",   "content": "Comment dit‑on 'apple' en français ?"},
    {"role": "assistant", "content": "Pomme"},
    {"role": "user",   "content": "Comment dit‑on 'computer' en français ?"},
    {"role": "assistant", "content": "Ordinateur"},
    # Prompt réel
    {"role": "user",   "content": "Comment dit‑on 'library' en français ?"}
]
```
- **Pourquoi ça marche** : le modèle infère le schéma *question → réponse courte* à partir des deux exemples.  
- **Limite** : chaque exemple consomme du contexte ; pour des modèles avec une fenêtre de contexte limitée, on ne peut pas dépasser un nombre d’exemples avant d’impacter la longueur de la requête.

#### 2.2 Chain‑of‑thought  
```python
prompt = """Résous le problème suivant en détaillant chaque étape :

Quel est le résultat de (23 × 7) + (15 ÷ 3) ?

Réponse :"""
```
- **Effet** : le modèle génère un raisonnement explicite, ce qui augmente la précision sur les tâches de calcul ou de logique.  
- **Paramètre clé** : `temperature` doit être modéré pour éviter des digressions inutiles.

### 3. Contrôle de la génération  

| Paramètre | Valeur typique | Impact |
|----------|----------------|--------|
| `temperature` |  | Plus bas → sortie déterministe, plus haut → diversité. |
| `top_p` (nucleus) |  | Couper la distribution à la probabilité cumulée. |
| `presence_penalty` |  | Décourage la répétition de tokens déjà vus dans le contexte. |
| `frequency_penalty` |  | Décourage la sur‑utilisation d’un même token. |

**Exemple d’appel API (OpenAI)**  
```python
import openai

response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=messages,
    temperature=0.3,
    top_p=0.95,
    presence_penalty=0.2,
    frequency_penalty=0.0,
    max_tokens=150,
)
print(response["choices"][0]["message"]["content"])
```
- `max_tokens` doit être fixé en fonction du budget de latence : 150 tokens ≈ 0.12 s sur GPU A100.

### 4. Analyse de la sortie  

#### 4.1 Métriques automatiques  
- **BLEU** : compare n‑grammes de la réponse générée à une ou plusieurs références.  
- **ROUGE‑L** : mesure la longueur de la plus longue sous‑séquence commune.  
- **Exact‑match (EM)** : 1 si la réponse est identique à la référence, 0 sinon.  

```python
from nltk.translate.bleu_score import sentence_bleu
from rouge_score import rouge_scorer

ref = ["Pomme"]
hyp = ["pomme"]  # case‑insensitive

bleu = sentence_bleu([ref], hyp, weights=(1, 0, 0, 0))
scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
rouge = scorer.score(' '.join(ref), ' '.join(hyp))['rougeL'].fmeasure

print(f"BLEU={bleu:.3f}  ROUGE‑L={rouge:.3f}")
```
- **Limite** : ces scores ne capturent pas toujours la pertinence sémantique (ex. synonymes).  

#### 4.2 Évaluation humaine calibrée  
1. **Échelle 0‑5** : 0 = hors‑sujet, 5 = parfaitement conforme.  
2. **Guidelines** : préciser la prise en compte du format (JSON valide, respect du ton, etc.).  
3. **Inter‑annotateur** : calculer le coefficient de corrélation de Krippendorff requis élevé.  

### 5. Boucles d’optimisation automatisées

---

## Module 2 — contenu

## Module 2 : Modélisation de données pour LLMs  

### 2.1 Nettoyage de texte  

| Étape | Action | Outils / Méthodes | Vérifiabilité |
|------|--------|-------------------|----------------|
| Déduplication | Suppression de lignes ou documents identiques (hash MD5 ou SHA‑256) | `pandas.DataFrame.drop_duplicates`, `set` Python | Le nombre d’entrées avant/après doit diminuer ou rester identique |
| Normalisation Unicode | Convertir toutes les chaînes en forme NFC (canonical composition) | `unicodedata.normalize('NFC', txt)` | `unicodedata.is_normalized('NFC', txt)` renvoie `True` |
| Nettoyage de ponctuation & espaces | Supprimer espaces multiples, normaliser les apostrophes, remplacer les tirets typographiques | Regex `re.sub(r'\s+', ' ', txt)`, `re.sub(r'[‘’´`]', "'", txt)` | Comparaison avant/après montre le nombre de caractères remplacés |
| Filtrage de toxicité | Éliminer les phrases contenant des mots de la liste de toxicité (ex. `detoxify` ou `Perspective API`) | `detoxify.Detoxify(model="original")` → `score['toxicity'] > 0.7` | Le taux de détection doit être mesurable sur un sous‑ensemble annoté |
| Normalisation des URLs & emails | Remplacer par des tokens `<URL>` / `<EMAIL>` | Regex `re.sub(r'https?://\S+', '<URL>', txt)` | Le nombre de remplacements doit correspondre au nombre d’occurrences détectées |

#### Exemple de pipeline de nettoyage (Python 3.10)

```python
import re
import hashlib
import unicodedata
from pathlib import Path
import pandas as pd
from detoxify import Detoxify

# 1️⃣ Chargement du corpus brut (un fichier texte par ligne)
raw_path = Path("data/raw_corpus.txt")
df = pd.read_csv(raw_path, sep="\n", header=None, names=["text"])

# 2️⃣ Déduplication (hash MD5)
df["hash"] = df["text"].apply(lambda x: hashlib.md5(x.encode("utf-8")).hexdigest())
df = df.drop_duplicates(subset="hash").drop(columns="hash")

# 3️⃣ Normalisation Unicode (NFC)
df["text"] = df["text"].apply(lambda x: unicodedata.normalize("NFC", x))

# 4️⃣ Nettoyage de ponctuation & espaces
def clean_spaces(txt: str) -> str:
    txt = re.sub(r"[‘’´`]", "'", txt)          # apostrophes typographiques
    txt = re.sub(r"[“”«»]", '"', txt)         # guillemets typographiques
    txt = re.sub(r"\s+", " ", txt)            # espaces multiples
    return txt.strip()
df["text"] = df["text"].apply(clean_spaces)

# 5️⃣ Filtrage de toxicité (seuil 0.7)
detox = Detoxify(model="original")
def is_toxic(txt: str) -> bool:
    scores = detox.predict(txt)
    return scores["toxicity"] > 0.7
df = df[~df["text"].apply(is_toxic)]

# 6️⃣ Masquage URLs et emails
url_pat = re.compile(r"https?://\S+|www\.\