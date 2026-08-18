# IA pour le Juridique & RGPD

> Référence `ia-juridique` · 69 €

## Plan

## Module 1 : Principes de l’IA et contraintes légales du traitement de données  
**Objectif mesurable** : L’apprenant pourra identifier les bases légales du RGPD applicables à un modèle d’apprentissage automatique et justifier le choix d’une base juridique pour un jeu de données donné.  
**Notions couvertes**  
1. Traitement de données à caractère personnel : définition et catégories (RGPD art. 4).  
2. Bases légales du traitement (consentement, intérêt légitime, exécution d’un contrat, etc.).  
3. Analyse d’impact relative à la protection des données (DPIA) – exigences et livrables.  
4. Principes de minimisation et de limitation de la conservation dans le cycle de vie d’un modèle.  
5. Documentation de conformité (registre des activités de traitement, registre des modèles IA).

---

## Module 2 : Architecture de pipelines de données conformes au RGPD  
**Objectif mesurable** : L’apprenant sera capable de concevoir, coder et tester un pipeline ETL qui intègre le masquage, la pseudonymisation ou l’anonymisation des données conformément aux exigences du RGPD.  
**Notions couvertes**  
1. Techniques de pseudonymisation et d’anonymisation (k‑anonymat, l‑diversité, t‑closeness).  
2. Gestion des consentements via des métadonnées (schema JSON‑LD, Open Consent).  
3. Utilisation de bibliothèques Python : `pandas`, `pyjanitor`, `faker`, `privacy‑preserving‑ml`.  
4. Orchestration sécurisée (Airflow, Prefect) avec chiffrement des flux (TLS, SOPS).  
5. Validation automatisée de conformité (tests unitaires + règle de conformité Scikit‑Learn‑Compliance).

---

## Module 3 : Modélisation explicable et auditabilité des algorithmes juridiques  
**Objectif mesurable** : L’apprenant pourra générer un rapport d’explicabilité (LIME/SHAP) pour un classificateur juridique et le relier aux exigences de transparence du RGPD (art. 13‑14, art. 15).  
**Notions couvertes**  
1. Méthodes d’explicabilité post‑hoc (LIME, SHAP, Anchor).  
2. Enregistrement des hyper‑paramètres, jeux de données et métriques (MLflow, DVC).  
3. Génération de “model cards” et “datasheets for datasets” selon les standards de Google et IBM.  
4. Audits de biais (disparate impact, fairness metrics).  
5. Production d’un “right‑to‑explain” API conforme aux exigences de portabilité (art. 20).

---

## Module 4 : Déploiement sécurisé et gouvernance des modèles IA en environnement juridique  
**Objectif mesurable** : L’apprenant pourra déployer un modèle de classification juridique dans un conteneur Docker certifié ISO 27001 et configurer les contrôles d’accès basés sur les rôles (RBAC) pour les requêtes de données.  
**Notions couvertes**  
1. Conteneurisation sécurisée (Docker, Docker‑Bench‑Security, images signées).  
2. Orchestration avec Kubernetes : NetworkPolicies, Secrets, Service Mesh

---

## Module 1 — contenu

## 1. Traitement de données à caractère personnel – définition et catégories (RGPD art. 4)

| Article | Définition | Exemple appliqué à l’IA juridique |
|---------|------------|-----------------------------------|
| 4(1)   | « données à caractère personnel » = toute information se rapportant à une personne physique identifiée ou identifiable. | Texte d’un jugement contenant le nom, le numéro de dossier, la date de naissance du justiciable. |
| 4(2)   | « traitement » = toute opération ou ensemble d’opérations effectuées sur des données (collecte, stockage, modification, diffusion, etc.). | Extraction de mentions de parties prenantes depuis un corpus de décisions, puis entraînement d’un modèle de classification. |
| 4(3)   | « sensible » = données révélant l’origine raciale ou ethnique, opinions politiques, convictions religieuses, santé, etc. | Décisions portant sur des motifs de discrimination. |

**Implication IA** : chaque étape du pipeline (ingestion → pré‑traitement → entraînement → inférence) constitue un traitement au sens du RGPD. Le responsable du traitement (souvent le cabinet ou l’entreprise) doit donc documenter chaque opération.

---

## 2. Bases légales du traitement

| Base juridique | Conditions d’application | Points de vigilance pour l’IA juridique |
|----------------|--------------------------|------------------------------------------|
| **Consentement** (art. 6‑1 a) | Consentement libre, spécifique, éclairé et univoque. | Le consentement doit couvrir *tous* les usages futurs (entraînement, ré‑utilisation, partage). Un consentement « pour la recherche » ne suffit pas si le modèle est commercialisé. |
| **Intérêt légitime** (art. 6‑1 f) | Nécessité d’un test d’équilibre : intérêt du responsable vs. droits/fondements de la personne. | L’intérêt légitime est rarement admis pour des données sensibles sans mesures de mitigation (pseudonymisation, limitation d’accès). |
| **Exécution d’un contrat** (art. 6‑1 b) | Traitement nécessaire à l’exécution d’un contrat auquel la personne est partie. | Utiliser les données d’un contrat client uniquement pour les services prévus dans ce contrat ; pas pour entraîner un modèle externe sans clause supplémentaire. |
| **Obligation légale** (art. 6‑1 c) | Nécessaire au respect d’une obligation juridique. | Conservation obligatoire de certains registres judiciaires (ex. : archives de décisions). |
| **Intérêt public** (art. 6‑1 e) | Autorisé pour des tâches d’intérêt public ou exercice de l’autorité publique. | Les autorités judiciaires peuvent traiter les données sans consentement, mais doivent publier une base juridique claire. |
| **Santé** (art. 9‑2 h) | Traitement nécessaire à des raisons d’intérêt public dans le domaine de la santé. | Rarement pertinent pour le droit, sauf si le modèle porte sur des dossiers médicaux liés à la responsabilité médicale. |

### 2.1. Décision d’une base juridique – démarche pas à pas

1. **Inventaire des données** : identifier chaque attribut (nom, numéro de dossier, texte de jugement, métadonnées).  
2. **Classification** : déterminer si l’attribut est sensible (art. 9).  
3. **Analyse d’usage** : définir les finalités (ex. : classification de type de contentieux).  
4. **Test d’équilibre** (si intérêt légitime) :  
   - **Bénéfice** : amélioration de la productivité juridique, réduction des coûts.  
   - **Risque** : atteinte à la vie privée, discrimination.  
   - **Mesures d’atténuation** : pseudonymisation, accès restreint, audit.  
5. **Documentation** : consigner la base juridique choisie, le test d’équilibre, les mesures de mitigation dans le registre des activités de traitement (ART 30).

---

## 3. Analyse d’impact relative à la protection des données (DPIA)

| Étape | Action concrète | Livrable |
|-------|----------------|----------|
| 1. Décrire le traitement | Diagramme de flux (data‑flow) du pipeline IA. | Diagramme + description textuelle. |
| 2. Identifier les risques | Tableau d’évaluation (probabilité × gravité). | Matrice de risques. |
| 3. Évaluer la nécessité & proportionnalité | Vérifier que chaque donnée est indispensable à la finalité. | Rapport de minimisation. |
| 4. Mesures de mitigation | Pseudonymisation, chiffrement, contrôle d’accès, audit logs. | Plan d’action détaillé. |
| 5. Consultation du DPO | Validation ou recommandation d’ajustement. | Avis du DPO signé. |
| 6. Décision | DPIA approuvée → lancement du projet ; sinon, revoir la conception. | DPIA final signé. |

**Critère de déclenchement** (art. 35) : traitement à grande échelle de catégories de données sensibles ou utilisation de nouvelles technologies (ex. : apprentissage fédéré) → DPIA obligatoire.

---

## 4. Principes de minimisation et de limitation de la conservation

| Principe | Exigence | Implémentation technique |
|----------|----------|---------------------------|
| **Minimisation** | Collecter uniquement ce qui est nécessaire. | Sélection de colonnes, suppression des métadonnées inutiles (`df.drop(columns=[…])`). |
| **Limitation de la conservation** | Définir une durée de rétention (ex. : durée définie après la clôture du dossier). | Job de purge automatisé (Airflow DAG) qui supprime ou archive les enregistrements expirés. |
| **Exactitude** | Garantir la mise à jour ...

---

## Module 2 — contenu

## 2.1 Techniques de pseudonymisation et d’anonymisation  

| Technique | Objectif | Garantie RGPD | Implémentation courante (Python) |
|-----------|----------|----------------|----------------------------------|
| **k‑anonymat** | Chaque combinaison de quasi‑identifiants apparaît au moins un certain nombre de fois. | Réduction du risque de ré‑identification ; requis pour l’anonymisation « dé‑identifiée ». | `sdc.k_anonymity(df, quasi_identifiers, k=…)` (module `sdc‑kit`). |
| **l‑diversité** | Au sein de chaque groupe k‑anonyme, il existe plusieurs valeurs distinctes pour l’attribut sensible. | Empêche l’inférence d’un attribut sensible même si le groupe est identifié. | `sdc.l_diversity(df, quasi_identifiers, sensitive, l=…)`. |
| **t‑closeness** | La distribution de l’attribut sensible dans chaque groupe k‑anonyme ne diffère pas de façon excessive de la distribution globale. | Renforce la protection contre les attaques de distribution. | `sdc.t_closeness(df, quasi_identifiers, sensitive, t=…)`. |
| **Pseudonymisation** | Remplacement d’un identifiant direct par un pseudonyme réversible (ex. hash + sel). | Conformité si la clé de décodage est séparée et sécurisée. | `hashlib.pbkdf2_hmac('sha256', id.encode(), salt, 100_000).hex()`. |
| **Anonymisation** | Suppression ou transformation irréversible des identifiants. | Conformité si le processus est certifié irréversible (ex. suppression totale, bruit différentiel). | `diffprivlib.mechanisms.Laplace(epsilon=…).randomise(value)`. |

### 2.1.1 Choix de la technique  

1. **Nature du jeu de données** – Si le jeu contient uniquement des données d’entreprise (B2B) et aucun identifiant personnel, la pseudonymisation suffit.  
2. **Exigence de ré‑identification** – Si le modèle doit être ré‑entraîné avec les mêmes individus, conservez le mapping dans un coffre‑fort (ex. HashiCorp Vault) et utilisez la pseudonymisation.  
3. **Complexité du traitement** – k‑anonymat + l‑diversité sont simples à implémenter avec `pandas`; t‑closeness nécessite un calcul de distribution plus coûteux.  

---

## 2.2 Gestion des consentements via des métadonnées  

### 2.2.1 Schéma JSON‑LD de consentement  

```json
{
  "@context": "https://schema.org/",
  "@type": "Consent",
  "identifier": "consent-2024-001",
  "dateCreated": "2024-03-15",
  "hasConsent": true,
  "grantedThrough": {
    "@type": "DataProcessingAgreement",
    "name": "Analyse juridique des contrats"
  },
  "purpose": {
    "@type": "MedicalStudy",
    "name": "Modélisation de clauses de responsabilité"
  },
  "subject": {
    "@type": "Person",
    "identifier": "hashed-8f3c2a..."
  }
}
```

*Le champ `subject.identifier` doit contenir le même pseudonyme que celui utilisé dans le pipeline.*  

### 2.2.2 Intégration dans le flux ETL  

```python
def load_consent_metadata(path: str) -> dict:
    """Lit le fichier JSON‑LD et renvoie le dictionnaire."""
    import json, pathlib
    return json.loads(pathlib.Path(path).read_text())

def filter_by_consent(df: pd.DataFrame, consent: dict) -> pd.DataFrame:
    """Ne conserve que les lignes dont le sujet a donné son consentement."""
    if not consent.get("hasConsent"):
        return pd.DataFrame(columns=df.columns)  # rien à garder
    # le pseudonyme est stocké dans consent["subject"]["identifier"]
    allowed_id = consent["subject"]["identifier"]
    return df[df["pseudonym"] == allowed_id]
```

---

## 2.3 Bibliothèques Python utiles