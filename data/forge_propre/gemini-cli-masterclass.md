# Gemini CLI Masterclass

> Référence `gemini-cli-masterclass` · 59 €

## Plan

## Module 1 – Installation et configuration de l’environnement Gemini CLI  

**Objectif mesurable** : Installer Gemini CLI sur Windows, macOS et Linux, configurer les variables d’environnement et vérifier le bon fonctionnement via la commande `gemini --version`.  

**Notions couvertes**  
- Prérequis système : Node.js ≥ 18, npm ≥ 9, compatibilité OpenSSL.  
- Installation globale (`npm i -g @google/gemini-cli`) et validation du binaire.  
- Configuration du fichier `~/.gemini/config.json` (clé API, région, profil).  
- Gestion des profils multiples avec la commande `gemini profile`.  
- Dépannage des erreurs courantes (permissions, PATH, certificats SSL).

---

## Module 2 – Authentification et gestion des clés d’API  

**Objectif mesurable** : Générer, stocker et renouveler une clé d’API Gemini, puis l’utiliser pour authentifier tous les appels CLI sans erreur d’autorisation.  

**Notions couvertes**  
- Création d’une clé d’API via Google Cloud Console (IAM → Service Accounts).  
- Exportation sécurisée au format JSON et import dans le profil Gemini.  
- Rotation automatique des clés avec la commande `gemini key rotate`.  
- Utilisation de `gcloud auth application-default login` comme alternative OAuth 2.0.  
- Vérification de la portée (scopes) requise pour les modèles de génération et de recherche.

---

## Module 3 – Interaction avec les modèles Gemini (prompting, paramètres, streaming)  

**Objectif mesurable** : Construire et exécuter trois prompts différents (texte, code, multimédia) en ajustant au moins deux paramètres (temperature, top‑p) et récupérer les réponses en mode streaming sans perte de données.  

**Notions couvertes**  
- Syntaxe du fichier de prompt (`.gemini.yaml`) : `system`, `user`, `assistant`.  
- Paramètres de génération : `temperature` (0‑2), `top_p` (0‑1), `max_output_tokens`.  
- Activation du mode streaming (`--stream`) et gestion des événements via `jq`.  
- Utilisation du mode `batch` pour envoyer plusieurs prompts en une seule requête.  
- Analyse des métadonnées de réponse (tokens utilisés, temps de latence).

---

## Module 4 – Gestion des entrées/sorties avancées (fichiers, pipelines, API REST)  

**Objectif mesurable** : Intégrer Gemini CLI dans un pipeline Unix pour lire un fichier source, le transformer via le modèle, et écrire le résultat dans un fichier de sortie, le tout automatisé avec un script Bash fonctionnant sur les trois OS cibles.  

**Notions couvertes**  
- Redirection d’entrée (`gemini prompt -i fichier.txt`) et sortie (`-o result.json`).  
- Utilisation de `stdin`/`stdout` pour chaîner avec `grep`, `sed`, `jq`.  
- Appel de l’API REST Gemini via `curl` en reproduisant exactement les paramètres CLI.  
- Gestion des limites de taille de payload et découpage de documents volumineux.  
- Exportation des logs de session (`--log-file`) et analyse avec `awk`.

---

## Module 5 – Déploiement, automatisation et bonnes pratiques de production  

**Objectif mesurable** : Créer un fichier de

---

## Module 1 — contenu

## Module 1 – Installation et configuration de l’environnement Gemini CLI  

### 1. Prérequis système  

| Composant | Version minimale | Vérification |
|-----------|------------------|--------------|
| **Node.js** | 18.0.0 | `node -v` |
| **npm** | 9.0.0 | `npm -v` |
| **OpenSSL** | 1.1.1 (ou 3.x) – support TLS 1.2+ | `openssl version` |
| **Git** (facultatif) | 2.20+ | `git --version` |

> **Note** : Sur macOS, la version fournie par le système peut être antérieure à 18. Utilisez le gestionnaire `brew` : `brew install node`.  
> Sur Windows, privilégiez l’installeur **LTS** de Node.js ou le package **nvm-windows** pour gérer plusieurs versions.  

### 2. Installation globale du binaire Gemini CLI  

```bash
# Installation unique, valable pour les trois OS
npm i -g @google/gemini-cli
```

- L’option `-g` place le binaire `gemini` dans le répertoire global de npm (`$(npm prefix -g)/bin`).  
- Sous **Windows**, le répertoire est généralement `%AppData%\npm`.  
- Sous **macOS/Linux**, il est `/usr/local/bin` (ou `$HOME/.npm-global/bin` si vous avez redéfini le préfixe).  

#### Vérification de l’installation  

```bash
gemini --version
# Exemple de sortie attendue
# gemini-cli 1.4.2
```

Si la commande n’est pas reconnue :  

1. **PATH** – ajoutez le répertoire contenant `gemini` à votre variable d’environnement `PATH`.  
   - Windows : `setx PATH "%PATH%;%AppData%\npm"` (redémarrez le terminal).  
   - macOS/Linux : `export PATH=$PATH:$(npm bin -g)` (à mettre dans `~/.bashrc` ou `~/.zshrc`).  
2. **Permissions** – sous Linux/macOS, l’erreur `EACCES` indique que le répertoire global n’est pas accessible en écriture. Utilisez :  
   ```bash
   npm config set prefix "$HOME/.npm-global"
   export PATH=$PATH:$HOME/.npm-global/bin
   ```

### 3. Structure du répertoire de configuration  

Par défaut, Gemini CLI lit le fichier JSON suivant :

```
~/.gemini/config.json   (Linux/macOS)
%USERPROFILE%\.gemini\config.json   (Windows)
```

Exemple minimal :

```json
{
  "default_profile": "personal",
  "profiles": {
    "personal": {
      "api_key": "YOUR_API_KEY",
      "region": "us-central1"
    }
  }
}
```

- **`default_profile`** : profil utilisé lorsqu’aucun n’est spécifié.  
- **`profiles`** : dictionnaire de profils nommés. Chaque profil doit contenir au moins `api_key`.  

#### Création du fichier via la CLI  

```bash
# Crée le répertoire s’il n’existe pas et ouvre l’éditeur par défaut
gemini config init
```

Le processus interactif vous demande :  

1. Nom du profil (ex. `personal`).  
2. Clé d’API (copier depuis la console Google Cloud).  
3. Région (ex. `us-central1`).  

Le fichier est sauvegardé avec les permissions `600` (lecture/écriture uniquement pour le propriétaire) ; la CLI le crée automatiquement avec ces permissions sous Unix. Sous Windows, assurez‑vous que le fichier n’est pas partagé en écriture avec d’autres comptes.  

### 4. Gestion des profils multiples  

#### Lister les profils  

```bash
gemini profile list
# > personal (default)
# > work
```

#### Créer un nouveau profil  

```bash
gemini profile add work \
  --api-key=AIzaSyXXXXXXX \
  --region=europe-west1
```

#### Basculer le profil par défaut  

```bash
gemini profile set-default work
```

#### Utiliser un profil sans le définir comme défaut  

```bash
gemini --profile personal prompt -i prompt.txt
```

### 5. Dépannage des erreurs courantes  

| Symptomôme | Cause fréquente | Correction |
|------------|----------------|------------|
| `Error: cannot find module '@google/gemini-cli'` | Installation locale (sans `-g`) ou `npm` corrompu | Ré‑exécuter `npm i -g @google/gemini-cli`; si persiste, nettoyer le cache : `npm cache clean --force` |
| `EACCES: permission denied` lors de l’installation | Répertoire global non accessible (Linux/macOS) | Configurer un préfixe utilisateur (`npm config set prefix "$HOME/.npm-global"`). |
| `SSL certificate problem: self signed certificate` | OpenSSL ne fait pas confiance au certificat du registre npm (proxy d’entreprise) | Exporter la variable `NODE_EXTRA_CA_CERTS=/path/to/ca.pem` ou désactiver le proxy npm (`npm config delete proxy`). |
| `gemini: command not found` | `PATH` ne contient pas le répertoire npm global | Ajouter le répertoire (`npm bin -g`) à `PATH` comme indiqué plus haut. |
| `Invalid API key` | Clé mal copiée (espaces, retours à la ligne) ou profil mal référencé | Ouvrir `~/.gemini/config.json`, vérifier la chaîne exacte, re‑exécuter `gemini config init` si besoin. |

### 6. Exemple complet d’installation et de configuration (Linux/macOS)  

```bash
#!/usr/bin/env bash

---

## Module 2 — contenu

## Module 2 – Authentification et gestion des clés d’API  

### 2.1. Principes d’authentification de Gemini CLI  

| Niveau | Méthode | Source | Portée (scopes) requise pour les modèles Gemini |
|--------|---------|--------|-----------------------------------------------|
| **Service Account** | Clé JSON (private_key) | Google Cloud Console → IAM → Service Accounts → *Créer une clé* | `https://www.googleapis.com/auth/cloud-platform` (ou plus restrictif : `https://www.googleapis.com/auth/gemini` si disponible) |
| **Application‑default credentials (ADC)** | OAuth 2.0 via `gcloud auth application-default login` | Google Cloud SDK | Identique au service account, dépend des scopes accordés lors du login |
| **User‑account (OAuth)** | Token d’accès stocké dans `~/.gemini/config.json` | `gemini login` (wrapper) | Même scopes que ci‑dessus, mais limité aux API activées pour le compte utilisateur |

Gemini CLI ne supporte que deux formes d’identifiants :  
1. **Clé de service** (fichier JSON) importée dans un profil Gemini.  
2. **ADC** qui repose sur le token généré par `gcloud`.  

> **Vérifiable** : `gemini auth test` renvoie `OK` uniquement si le token présent dans le profil possède le scope `https://www.googleapis.com/auth/cloud-platform`.

---

### 2.2. Création d’une clé d’API Service Account  

1. Ouvrir la console Google Cloud → **IAM & Admin** → **Service Accounts**.  
2. Cliquer sur **Créer un compte de service**.  
   - Nom : `gemini-cli-sa`  
   - ID : `gemini-cli-sa` (automatique)  
   - Description : `Compte de service dédié aux appels Gemini CLI`.  
3. Attribuer le rôle **Vertex AI User** (`roles/aiplatform.user`). Ce rôle inclut le scope `cloud-platform`.  
4. Après création, sélectionner le compte → **Clés** → **Ajouter une clé** → **Créer une clé JSON**.  
   - Le fichier `gemini-cli-sa-xxxx.json` est téléchargé dans le répertoire `~/Downloads`.  

> **Piège** : ne jamais stocker la clé dans un dépôt Git. Utiliser `.gitignore` ou un gestionnaire de secrets (ex. : `git-crypt`, `Vault`).  

---

### 2.3. Importation de la clé dans un profil Gemini  

Le fichier de configuration Gemini se trouve par défaut à `~/.gemini/config.json`. Un **profil** est un objet JSON contenant :  

```json
{
  "default": "prod",
  "profiles": {
    "prod": {
      "api_key_path": "/home/USER/.gemini/keys/gemini-cli-sa-prod.json",
      "region": "us-central1",
      "project_id": "my-gemini-project"
    },
    "dev": {
      "api_key_path": "/home/USER/.gemini/keys/gemini-cli-sa-dev.json",
      "region": "europe-west1",
      "project_id": "my-gemini-dev"
    }
  }
}
```

#### 2.3.1. Commande d’import  

```bash
# Crée le répertoire de stockage des clés (si inexistant)
mkdir -p ~/.gemini/keys

# Copie sécurisée de la clé (chmod 600 pour restreindre l’accès)
cp ~/Downloads/gemini-cli-sa-xxxx.json ~/.gemini/keys/gemini-cli-sa-prod.json
chmod 600 ~/.gemini/keys/gemini-cli-sa-prod.json

# Enregistre le profil « prod » dans la configuration
gemini profile add \
  --name prod \
  --key-file ~/.gemini/keys/gemini-cli-sa-prod.json \
  --region us-central1 \
  --project my-gemini-project
```

Après exécution, `cat ~/.gemini/config.json` doit contenir le bloc `prod` comme ci‑dessus.  

#### 2.3.2. Validation  

```bash
gemini auth test --profile prod
# → Retourne : "Authentication successful (project: my-gemini-project, region: us-central1)"
```

---

### 2.4. Rotation automatique des clés  

Google Cloud recommande de **rotater** les clés de service au moins tous les 90 jours. Gemini CLI propose la commande `gemini key rotate` qui effectue :  

1. Création d’une nouvelle clé JSON.  
2. Mise à jour du profil avec le nouveau chemin.  
3. Suppression (optionnelle) de l’ancienne clé.  

#### 2.4.1. Exemple de rotation  

```bash
# Rotation du profil prod, stockage de la nouvelle clé dans le même répertoire
gemini key rotate \
  --profile prod \
  --output ~/.gemini/keys/gemini-cli-sa-prod-$(date +%Y%m%d).json \
  --delete-old
```

- `--delete-old` supprime la clé précédente après validation.  
- Le suffixe date év