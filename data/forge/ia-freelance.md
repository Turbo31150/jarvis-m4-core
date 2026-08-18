# Freelance IA — Revenus & Services

> Référence `ia-freelance` · 59 €

## Plan

## Module 1 – Positionnement du freelance IA et structuration de l’offre  
**Objectif mesurable** : Être capable de définir, documenter et publier une offre de service IA conforme aux attentes du marché cible (minimum 3 personas identifiés).  
- Analyse des segments de marché IA (automatisation, IA générative, IA décisionnelle).  
- Construction d’un persona client et identification de ses pain points.  
- Rédaction d’une proposition de valeur (UVP) chiffrée (ROI estimé, gains de productivité).  
- Choix du modèle de tarification (jour/horaire, forfait, abonnement) et justification économique.  
- Création d’un “service sheet” standardisé (scope, livrables, SLA).

## Module 2 – Acquisition de clients via canaux digitaux et réseaux professionnels  
**Objectif mesurable** : Générer au moins 5 leads qualifiés en 30 jours grâce à une campagne multicanale documentée.  
- Optimisation du profil LinkedIn (mots‑clés, recommandations, portfolio IA).  
- Mise en place d’une campagne de cold‑mailing (script, séquence, taux d’ouverture cible 25 %).  
- Utilisation de plateformes freelance spécialisées (Upwork, Malt, Toptal) : paramétrage de filtres et réponses automatisées.  
- Création d’un lead magnet technique (ex. notebook Jupyter, étude de cas) et diffusion via newsletter.  
- Suivi CRM simple (Airtable ou HubSpot Free) : pipeline, scoring, taux de conversion.

## Module 3 – Gestion de projet IA et livrables techniques  
**Objectif mesurable** : Piloter un projet IA de bout en bout (définition, prototypage, validation) en respectant un planning de 4 semaines.  
- Méthodologie Agile adaptée aux projets IA (sprints de 1 semaine, Definition of Done).  
- Sélection d’outils de versionnage et de CI/CD (Git, GitHub Actions, DVC).  
- Structuration du code (modularité, tests unitaires, couverture ≥80 %).  
- Documentation reproductible (README, API docs, notebooks).  
- Mise en place d’un système de monitoring des modèles (MLflow, Evidently AI) pour la phase de production.

## Module 4 – Facturation, conformité juridique et protection de la propriété intellectuelle  
**Objectif mesurable** : Émettre une facture conforme (TVA, mentions légales) et sécuriser les livrables par un contrat type en moins de 2 jours ouvrés.  
- Choix du statut juridique (micro‑entreprise, EURL, SASU) et implications fiscales (IR, IS).  
- Modèle de contrat freelance IA (scope, droits d’usage, clause de confidentialité, clause de non‑sollicitation).  
- Gestion de la TVA intra‑UE et des seuils de chiffre d’affaires (ex. 34 800 €).  
- Utilisation d’une solution de facturation en ligne (Facture.net, QuickBooks) avec suivi des paiements.  
- Mise en place d’un accord de licence de modèle (Open‑source vs propriétaire) et dépôt éventuel (Zenodo, GitHub).

## Module 5 – Optimisation du revenu récurrent et montée en gamme des services  
**Objectif mesurable** : Concevoir et lancer un produit SaaS IA ou un

---

## Module 1 — contenu

## Module 1 – Positionnement du freelance IA et structuration de l’offre  

### 1. Analyse des segments de marché IA  

| Segment | Description | Taille du marché (2023) | Principaux cas d’usage |
|--------|-------------|--------------------------|-----------------------|
| Automatisation des processus (RPA + IA) | IA appliquée à la robotisation de tâches répétitives (ex. extraction de données, traitement de factures) | 12 Mds $ (IDC, 2023) | Facturation, onboarding, support ticket |
| IA générative | Modèles capables de créer du texte, des images, du code, de la musique | 8 Mds $ (Gartner, 2023) | Chatbots, création de contenus marketing, prototypage UI |
| IA décisionnelle (ML/Deep Learning) | Modèles prédictifs et prescriptifs pour la prise de décision | 15 Mds $ (Statista, 2023) | Forecasting de ventes, détection de fraude, maintenance prédictive |

**Vérifiabilité** : les chiffres proviennent des rapports IDC, Gartner et Statista publiés en 2023.  

---

### 2. Construction d’un persona client  

1. **Collecte de données**  
   - Entretiens de 30 min avec 5 prospects du segment ciblé.  
   - Analyse des posts LinkedIn et des offres d’emploi pour identifier les compétences manquantes.  

2. **Template de persona**  

| Champ | Exemple (PME du retail) |
|------|------------------------|
| **Nom** | Léa Martin |
| **Fonction** | Responsable transformation digitale |
| **Taille de l’entreprise** | 45 salariés, CA 12 M€ |
| **Pain points** | - Temps de traitement des retours produit > 48 h <br> - Aucun modèle de prévision des ventes, décisions basées sur l’intuition |
| **Objectifs** | - Réduire le délai de traitement des retours de 30 % <br> - Augmenter la précision du forecast à 95 % |
| **Critères de décision** | ROI < 6 mois, solution “plug‑and‑play”, conformité RGPD |
| **Canaux de recherche** | LinkedIn, newsletters spécialisées, recommandations de partenaires IT |

---

### 3. Rédaction d’une proposition de valeur (UVP) chiffrée  

#### 3.1 Méthode de calcul du ROI  

\[
\text{ROI (\%)} = \frac{\text{Gain net annuel}}{\text{Coût total du projet}} \times 100
\]

- **Gain net annuel** = économies de temps × coût horaire moyen + revenus additionnels générés.  
- **Coût total du projet** = honoraires + licences éventuelles + frais d’infrastructure.

#### 3.2 Exemple d’UVP pour le persona ci‑dessus  

> **“Nous réduisons le délai de traitement des retours de 30 % (gain estimé = 15 h / mois × 45 €/h = 675 €/mois). En 6 mois, le ROI dépasse 120 %.”**  

| Élément | Valeur |
|--------|--------|
| **Coût projet** | 12 000 € (4 semaines, 150 €/h, 80 h) |
| **Gain net annuel** | 8 100 € (675 €/mois × 12) |
| **ROI** | 67 % sur la première année, 134 % en 2 ans |

---

### 4. Choix du modèle de tarification  

| Modèle | Calcul | Avantages | Inconvénients |
|--------|--------|-----------|---------------|
| **Jour/horaire** | 150 €/h × heures réelles | Transparence, facile à justifier | Risque de “budget creep”, perception de coûts élevés |
| **Forfait** | Prix fixe = estimation + marge (ex. 12 000 €) | Prévisibilité pour le client, meilleure marge | Nécessite une définition précise du périmètre |
| **Abonnement (MRR)** | 1 500 €/mois (maintenance + évolution) | Revenus récurrents, fidélisation | Nécessite un produit ou service évolutif (ex. monitoring IA) |

**Justification économique** : pour un projet de 4 semaines, le forfait minimise le risque de dépassement de budget (source : *Harvard Business Review, “Pricing Professional Services”, 2022*). L’abonnement devient pertinent dès que le modèle est mis en production et nécessite du monitoring continu.

---

### 5. Création d’un “service sheet” standardisé  

```markdown
# Service Sheet – IA – [Nom du service]

**Scope**  
- Analyse des besoins (1 j)  
- Conception du modèle (2 j)  
- Développement & tests (5 j)  
- Déploiement & monitoring (2 j)

**Livrables**  
- Rapport d’analyse (PDF)  
- Notebook Jupyter avec code commenté (Python 3.10)  
- API REST (FastAPI) dockerisée  
- Dashboard de suivi (Streamlit)  

**SLA**  
- Temps de réponse support : ≤ 4 h (heure ouvrée)  
- Disponibilité du service en prod : 99,5 % (excl. maintenance planifiée)  

**Tarification**

---

## Module 2 — contenu

## 2.1 Optimisation du profil LinkedIn  

| Élément | Action concrète | Vérification |
|---------|-----------------|--------------|
| **Mots‑clé** | Ajoutez dans le titre : `Freelance IA • Machine Learning • LLM • MLOps • Automatisation des processus`. Dans le résumé, répétez les 5‑7 mots‑clé les plus recherchés (ex. *deep learning, NLP, computer vision, data pipelines, model monitoring*). | Utilisez l’outil de recherche LinkedIn : tapez chaque mot‑clé, notez le nombre de résultats. Un profil contenant le même mot‑clé dans le titre ou le résumé apparaît dans les 10 % premiers résultats. |
| **Recommandations** | Sollicitez 2 à 3 recommandations ciblées : 1 client (ex. “mise en production d’un modèle de prévision de ventes”) et 1 collègue technique (ex. “qualité du code, tests unitaires > 80 %”). | Vérifiez la présence du badge “Recommendation” et le nombre de caractères ≥ 150. |
| **Portfolio IA** | Créez une section “Featured” contenant : <br>• lien vers un notebook Jupyter hébergé sur GitHub (ex. `https://github.com/username/forecasting-demo/blob/main/forecast.ipynb`) <br>• article Medium décrivant le projet, avec métriques chiffrées (ex. *réduction du temps de traitement de 70 %*) <br>• capture d’écran d’un tableau de bord MLflow. | Ouvrez chaque lien : le notebook doit s’afficher sans erreur, l’article doit contenir un tableau de métriques. |
| **URL personnalisée** | `linkedin.com/in/nom-prenom-IA`. | Testez l’URL dans un navigateur privé. |

### Checklist LinkedIn (à cocher)  
- ☐ Titre ≤ 120 caractères, incluant 3 mots‑clé.  
- ☐ Résumé ≤ 2 paragraphes, chaque phrase commence par un mot‑clé.  
- ☐ 3 projets “Featured” avec liens fonctionnels.  
- ☐ 2 recommandations récentes (< 12 mois).  

---

## 2.2 Campagne de cold‑mailing  

### 2.2.1 Architecture de la séquence  

| Étape | Objet (exemple) | Contenu clé | Délai |
|-------|------------------|-------------|-------|
| 1️⃣ | `[Nom] – 2 minutes pour augmenter votre ROI IA` | Hook : chiffre d’impact (ex. *+23 % de productivité*). 150‑200 mots, CTA : demande de 15 min. | J0 |
| 2️⃣ | `Re‑: [Nom] – votre IA en production` | Rappel du premier mail, preuve sociale (client similaire). | J+3 |
| 3️⃣ | `Dernier message – votre projet IA` | Dernier appel à l’action, offre de livrable gratuit (lead magnet). | J+7 |

### 2.2.2 Script de premier mail (plain‑text)  

```
Objet : {{first_name}} – 2 minutes pour augmenter votre ROI IA

Bonjour {{first_name}},

Je suis {{my_name}}, freelance spécialisé en IA appliquée à {{industry}}.  
Chez {{client_similar}} (CA 12 M€), j’ai automatisé le scoring client : le taux de conversion est passé de 3,2 % à 5,9 % en 6 semaines (ROI ≈ +180 %).

Je vous propose un audit gratuit de 15 min pour identifier les gains rapides possibles dans votre chaîne de valeur.

Disponible mardi 15 h ou jeudi 10 h ?  
[Calendly link]

Bonne journée,  
{{my_name}}  
{{my_email}} – {{my_phone}}
```

Variables (`{{ }}`) seront injectées via le script Python (voir §2.2.4).

### 2.2.3 Taux d’ouverture cible  

| Segment | Taux d’ouverture moyen (2023, HubSpot) | Objectif |
|---------|----------------------------------------|----------|
| B2B SaaS | 21 % | ≥ 25 % |
| Services professionnels | 19 % | ≥ 25 % |
| IA/ML | 23 % | ≥ 25 % |

**Moyenne cible** : 25 % → nécessite un objet < 50 caractères, un nom de destinataire réel, et l’utilisation d’un domaine d’envoi authentifié (SPF/DKIM).

### 2.2.4 Exemple de code : envoi automatisé avec Gmail API (Python 3.10)  

```python
# cold_mailer.py
# Fonctionnalités : lecture d'une CSV de prospects, personnalisation, envoi via Gmail API,
# suivi du statut (sent, draft, error) dans une feuille Airtable.

import base64, csv, json, os, time
from email.mime.text import MIMEText
from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests

# ---------- CONFIG ----------
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
SERVICE_ACCOUNT_FILE = "service_account.json"          # compte

---

## Module 3 — contenu

## Module 3 – Gestion de projet IA et livrables techniques  

### 1. Méthodologie Agile adaptée aux projets IA  

| Élément | Description concrète | Exemple d’application (4 semaines) |
|--------|----------------------|------------------------------------|
| **Sprint** | Cycle de travail itératif de 1 semaine (début le lundi, revue le vendredi). | S‑1 : cadrage & définition du problème (data‑sheet, KPI). S‑2 : acquisition & nettoyage des données. S‑3 : prototypage modèle (baseline + itérations). S‑4 : validation, documentation & mise en production. |
| **Backlog** | Liste priorisée de *user stories* fonctionnelles et techniques (ex. “En tant que data‑scientist, je veux un jeu de données nettoyé pour entraîner un modèle de classification”). | Utiliser un tableau Kanban (GitHub Projects) avec colonnes *To‑Do*, *In‑Progress*, *Done*. |
| **Definition of Done (DoD)** | Critères d’acceptation obligatoires pour chaque story : code versionné, tests unitaires ≥ 80 % de couverture, artefacts versionnés (data, modèles), documentation mise à jour, revue de code validée. | Pour la story “Entraîner le modèle baseline” : <br>• notebook `baseline.ipynb` commité <br>• script `train.py` avec tests <br>• modèle sauvegardé via DVC <br>• métriques enregistrées dans `metrics.json`. |
| **Rétrospective** | 15 min chaque fin de sprint pour identifier blocages (ex. lenteur du pipeline DVC) et actions correctives. | Noter “Le job CI dépasse le timeout = 30 min → passer à un runner plus puissant”. |

**Piège fréquent** – *Scope creep* : ajouter des exigences hors backlog pendant le sprint. **Solution** – bloquer les nouvelles stories à la prochaine planification et les prioriser avec le Product Owner.

---

### 2. Outils de versionnage et CI/CD  

| Outil | Rôle | Configuration minimale (exemple) |
|------|------|----------------------------------|
| **Git** | Historique du code source, branches de fonctionnalité. | `git init` → `git remote add origin <url>` |
| **GitHub Actions** | Exécution automatisée de tests, linting, packaging. | ```yaml<br>name: CI<br>on: [push, pull_request]<br>jobs:<br>  test:<br>    runs-on: ubuntu-latest<br>    steps:<br>      - uses: actions/checkout@v3<br>      - name: Set up Python<br>        uses: actions/setup-python@v4<br>        with:<br>          python-version: "3.10"<br>      - name: Install dependencies<br>        run: pip install -r requirements.txt<br>      - name: Run tests<br>        run: pytest --cov=src tests/``` |
| **DVC (Data Version Control)** | Versionnage des jeux de données, modèles, pipelines de transformation. | ```bash<br># Initialiser DVC dans le repo<br>dvc init<br># Ajouter un dataset volumineux (ex. data/raw.csv)<br>dvc add data/raw.csv<br># Commiter le .dvc file<br>git add data/raw.csv.dvc .gitignore<br>git commit -m "Track raw data with DVC"<br># Configurer le remote (ex. S3)<br>dvc remote add -d storage s3://my-bucket/dvc-storage<br>dvc push``` |
| **GitHub Packages / Docker Hub** | Distribution d’artefacts (wheel, image Docker) pour le déploiement. | `docker build -t ghcr.io/<org>/my-ia-service:latest .` puis `docker push ghcr.io/<org>/my-ia-service:latest`. |

**Piège concret** – *Versionner des fichiers binaires lourds avec Git* entraîne un blow‑up du dépôt. **Solution** – stocker uniquement les métadonnées `.dvc` dans Git, les artefacts réels dans un remote (S3, Azure Blob, GCS).  

**Limite technique** – Les runners GitHub Actions gratuits n’ont pas de GPU. Pour les tests de modèles nécessitant CUDA, utilisez un self‑hosted runner ou un service CI dédié (e.g. GitLab CI avec GPU).  

---

### 3. Structuration du code  

```
project/
│
├─ src/                     # Bibliothèque métier
│   ├─ __init__.py
│   ├─ data/                # Pipeline de chargement / nettoyage
│   │   ├─ __init__.py
│   │   └─ preprocess.py
│   ├─ model/               # Entraînement & inference
│   │   ├─ __init__.py
│   │   └─ trainer.py
│   └─ utils/               # Fonctions utilitaires (logging, metrics)
│       └─ metrics.py
│
├─ tests/                   # Tests unitaires & d’intégration
│   ├─ __init__.py
│

---

## Module 4 — contenu

## 4.1 Choix du statut juridique et implications fiscales  

| Statut | Plafond de chiffre d’affaires (2024) | TVA collectée | Impôt sur le revenu / société | Formalités de création | Points d’attention |
|--------|--------------------------------------|--------------|------------------------------|------------------------|--------------------|
| **Micro‑entreprise** | 176 200 € (services) | Franchise en base de TVA tant que le chiffre d’affaires < 34 800 € (seuil “auto‑entrepreneur”) | IR (BIC/BNC) avec abattement 34 % (minimum 305 €) | Déclaration en ligne (URSSAF) | Pas de récupération de TVA, pas de déduction des charges, limite de protection sociale. |
| **EURL (IR)** | Illimité | TVA normale dès le premier euro facturé | IR sur le bénéfice (régime réel) + prélèvements sociaux 45 % | Rédaction de statuts, immatriculation au RCS, dépôt de capital (≥ 1 €) | Obligation de comptabilité complète, possibilité d’option à l’IS. |
| **SASU** | Illimité | TVA normale | IS (15 % jusqu’à 42 500 € de bénéfice, puis 25 %) + prélèvements sociaux (15,5 % sur dividendes) | Rédaction de statuts, immatriculation, capital minimum 1 € | Flexibilité de gouvernance, coût de création + frais de comptabilité plus élevés. |

**Règle pratique** : Si le prévisionnel de la première année dépasse 30 000 €, privilégier l’EURL ou la SASU pour pouvoir récupérer la TVA sur les achats (cloud, licences, matériel).  

### 4.1.1 Gestion de la TVA intra‑UE  

1. **Numéro de TVA intracommunautaire** : obtenez‑le via le service en ligne de la DGCCRF (ex. FRXX999999999).  
2. **Auto‑facturation** (reverse charge) pour les prestations B2B dans l’UE :  
   - Mention « TVA due par le preneur, article 283‑2 du CGI ».  
   - Pas de TVA sur la facture, mais le client doit l’autoliquider.  
3. **Déclaration** : utilisez le formulaire CA3 mensuel/trim. Le champ “Livraisons intracommunautaires de services” doit être renseigné.  

**Piège** : Omettre la mention « TVA due par le preneur » entraîne une facturation erronée et expose à une redressement de 20 % du montant de TVA.

---

## 4.2 Modèle de contrat freelance IA  

```markdown
# Contrat de prestation de services IA – Version 2024‑08

## 1. Parties
- **Prestataire** : [Nom, prénom, SIREN, adresse, email].
- **Client**   : [Nom de l’entreprise, SIREN, adresse, représentant légal].

## 2. Objet
Développement, entraînement et mise en production d’un modèle de classification d’images (see Annex A) selon les spécifications du Client.

## 3. Périmètre et livrables
| Livrable | Description | Date de livraison | Acceptation |
|----------|-------------|-------------------|-------------|
| D1 | Notebook Jupyter contenant le pipeline de données | J+14 | Signé par le Client |
| D2 | Modèle entraîné (format .pth) + Dockerfile | J+28 | Signé par le Client |
| D3 | Documentation API (OpenAPI 3.0) | J+30 | Signé par le Client |

## 4. Rémunération
- **Tarif forfaitaire** : 8 000 € HT.
- **Modalités** : 30 % à la signature, 40 % à la livraison du D1, 30 % à la livraison du D3.
- **Facturation** : émise sous 5 jours ouvrés, paiement à 30 jours net.

## 5. Droits d’usage
- Le Client obtient une licence **non exclusive, mondiale, perpétuelle** d’utilisation du modèle et du code source.
- Le Prestataire conserve les droits d’exploitation sur le code générique (ex. fonctions de pré‑traitement) et peut le réutiliser dans d’autres projets.

## 6. Confidentialité
- Chaque partie s’engage à ne pas divulguer les informations confidentielles reçues.
- Clause de non‑sollicitation : 12 mois d’interdiction de recruter le personnel de l’autre partie.

## 7. Garantie & maintenance
- Garantie de conformité de 30 jours après acceptation du D3.
- Option de maintenance mensuelle 500 €/mois (non incluse).

## 8. Résiliation
- Résiliation unilatérale possible avec préavis de 15 jours et paiement des prestations déjà réalisées.

## 9. Loi applicable & juridiction
- Droit français, tribunal de commerce de [ville].

*Annexes* :  
- Annex A – Spécifications fonctionnelles  
- Annex B – Cahier des charges technique
```

### 4.2.1 Clauses critiques  

| Clause | Pourquoi | Conséquence d’une rédaction vague |
|--------|----------|-----------------------------------|
| Droits d’usage | Détermine qui possède le modèle et le code. | Risque de litige sur la réutilisation du modèle ou sur la cession des droits d’exploitation. |
| Confidentialité | Protège les données d’entraînement (ex. données clients). | Violation du RGPD si les données personnelles sont exposées. |
| TVA & mentions

---

## Module 5 — contenu

## 5.1 Principes du revenu récurrent (RRR) appliqués à l’IA  

| Concept | Définition vérifiable | Impact IA |
|---------|----------------------|-----------|
| **Abonnement mensuel/annuel** | Facturation périodique fixe (ex. Stripe `subscription` API) | Garantit un flux de trésorerie prévisible, amortit les coûts d’inférence. |
| **Tarification à l’usage** | Facturation proportionnelle à la consommation (ex. `price_per_call = 0.001 €`) | Permet de monétiser les modèles coûteux (GPU) tout en restant compétitif. |
| **Modèle freemium** | Version limitée (ex. 100 appels/mois) gratuite, débloque les fonctionnalités avancées via abonnement | Accélère l’acquisition de leads qualifiés, crée un effet de réseau. |
| **Upsell / Cross‑sell** | Ajout de modules complémentaires (ex. tableau de bord d’analyse, API de fine‑tuning) | Augmente la valeur vie client (CLV). |

> **Règle de calcul du CLV simplifié**  
> \[
> CLV = \frac{M \times r}{1 + d - r}
> \]  
> où `M` = revenu moyen mensuel par client, `r` = taux de rétention mensuel, `d` = taux d’actualisation mensuel.  

---

## 5.2 Architecture SaaS IA – Choix techniques  

### 5.2.1 Modèle d’hébergement  

| Option | Avantages mesurables | Inconvénients concrets |
|--------|----------------------|------------------------|
| **Multi‑tenant (shared DB, shared compute)** | Utilisation maximale des GPU, coût moyen par client ↓ (ex. 30 % de réduction vs single‑tenant) | Risque de fuite de données entre locataires, nécessite isolation logique (row‑level security). |
| **Single‑tenant (isolé par VPC ou namespace)** | Conformité stricte (RGPD, ISO 27001), facturation à la capacité | Coût fixe plus élevé, sous‑utilisation des ressources. |
| **Serverless (AWS Lambda, Cloud Run)** | Facturation à l’appel, mise à l’échelle instantanée, pas de serveur à gérer | Limite de durée d’exécution (15 min Lambda), coût d’inférence GPU non disponible nativement (requiert EKS GPU). |

### 5.2.2 Stack recommandé (exemple AWS)  

1. **API Gateway** – `Amazon API Gateway` (REST + JWT validation).  
2. **Compute** – `Amazon EKS` avec nœuds GPU (`p3.2xlarge`) pour le modèle, `Fargate` pour les micro‑services sans GPU.  
3. **Stockage modèle** – `Amazon S3` versionné + `AWS SageMaker Model Registry` (facultatif).  
4. **Base de données** – `Amazon Aurora Serverless v2` (PostgreSQL) pour les métadonnées, `DynamoDB` pour le suivi d’usage (low‑latency).  
5. **CI/CD** – `GitHub Actions` → `ECR` → `EKS` (déploiement blue/green).  
6. **Billing** – `Stripe Billing` (subscription + usage‑based).  
7. **Observabilité** – `OpenTelemetry` → `AWS CloudWatch` (traces, métriques), `Prometheus` + `Grafana` pour le monitoring des GPU.  

### 5.2.3 Sécurité & conformité  

* **Authentification** – JWT signé avec RS256, clé publique stockée dans `AWS Secrets Manager`.  
* **Autorisation** – `ABAC` (Attribute‑Based Access Control) via `API Gateway` + `Lambda Authorizer`.  
* **Chiffrement** – S3 SSE‑AES256, RDS TLS 1.2, trafic TLS 1.3 entre services.  
* **GDPR** – Anonymisation des logs (`hash(pii)`) avant stockage dans `DynamoDB`.  

---

## 5.3 Exemple fonctionnel : API IA avec facturation à l’usage  

> **Objectif** : exposer une fonction de classification texte (modèle `distilbert-base-uncased-finetuned-sst-2-english`) via FastAPI, protéger l’accès par JWT, enregistrer chaque appel dans Stripe pour facturation à l’usage.

```python
# file: main.py
"""
FastAPI + HuggingFace + Stripe usage‑based billing
Version : 1.0.0
Auteur : freelance IA
"""

import os
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt  # pyjwt
from