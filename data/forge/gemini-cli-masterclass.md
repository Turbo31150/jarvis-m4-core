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

**Objectif mesurable** : Générer, stocker et renouveler une clé d’API Gemini, puis l’utiliser pour authentifier 100 % des appels CLI sans erreur d’autorisation.  

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
- Gestion des limites de taille de payload (max ≈ 2 MiB) et découpage de documents volumineux.  
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
- Le suffixe date évite les collisions de noms.  

> **Piège** : si la clé est utilisée par d’autres services (ex. : Cloud Run), la suppression prématurée entraîne des échecs d’appel. Toujours vérifier la liste des dépendances avant `--delete-old`.

---

### 2.5. Utilisation d’ADC comme alternative  

```bash
# Installe le SDK Google Cloud (si absent)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Authentifie l’utilisateur et crée des ADC
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform
```

Une fois les ADC créées, Gemini CLI les détecte automatiquement :  

```bash
gemini auth test
# → Si aucune configuration de profil n’est fournie,

---

## Module 3 — contenu

## 3 – Interaction avec les modèles Gemini (prompting, paramètres, streaming)

### 3.1 Syntaxe du fichier de prompt `.gemini.yaml`

| Clé          | Type   | Description                                                                                     |
|--------------|--------|-------------------------------------------------------------------------------------------------|
| `system`     | string | Instructions globales destinées au modèle (ex. rôle, contraintes).                              |
| `user`       | string | Prompt principal de l’utilisateur.                                                             |
| `assistant` | string | Réponse attendue ou exemple de format (facultatif, utile pour le *few‑shot*).                  |
| `temperature`| number| Niveau de stochasticité (0 → déterministe, 2 → plus créatif).                                    |
| `top_p`      | number | Nucleus sampling : probabilité cumulative du vocabulaire retenu (0‑1).                            |
| `max_output_tokens` | int | Nombre maximal de tokens que le modèle peut générer.                                            |
| `stream`     | bool   | `true` active le streaming de la réponse (voir 3.3).                                            |
| `model`      | string | Identifiant complet du modèle (ex. `gemini-1.5-pro`).                                            |

Exemple minimal :

```yaml
# .gemini.yaml
system: |
  Tu es un assistant spécialisé en transformation de texte.
user: |
  Résume le texte suivant en trois phrases :
  {{input}}
temperature: 0.7
top_p: 0.9
max_output_tokens: 512
stream: true
model: gemini-1.5-pro
```

*`{{input}}`* est remplacé automatiquement lorsqu’on utilise l’option `-i` ou `--input` de la CLI.

---

### 3.2 Paramètres de génération

| Paramètre | Valeur autorisée | Effet observable |
|-----------|------------------|-------------------|
| `temperature` | 0 – 2 (pas de décimale obligatoire) | 0 → réponses toujours identiques ; 2 → variabilité maximale. |
| `top_p` | 0 – 1 (exemple : 0.8) | Limite le vocabulaire aux tokens cumulatifs ≤ `top_p`. |
| `max_output_tokens` | 1 – 8192 (selon le modèle) | Coupe la réponse dès que le quota est atteint. |
| `stop_sequences` | tableau de strings | Force l’arrêt dès qu’une séquence apparaît. |

**Règle de combinaison** : si `temperature` > 0, `top_p` est appliqué *après* le softmax ; si `temperature` = 0, le modèle agit en mode « greedy », rendant `top_p` sans effet.

---

### 3.3 Mode streaming

Le streaming transmet chaque token dès qu’il est généré, au lieu d’attendre la fin de la séquence. En CLI :

```bash
gemini prompt -c .gemini.yaml -i texte.txt --stream | jq -r '.candidates[0].output'
```

- `--stream` force le serveur à renvoyer un flux de messages JSON séparés par des sauts de ligne.
- `jq -r` extrait la chaîne de sortie sans les guillemets.
- Le client doit être capable de gérer les fragments incomplets ; `jq` ignore les lignes non‑JSON valides.

**Gestion des erreurs de streaming**  
```bash
# Exemple de boucle Bash robuste
while IFS= read -r line; do
  if echo "$line" | jq . >/dev/null 2>&1; then
    echo "$line" | jq -r '.candidates[0].output' >> result.txt
  else
    echo "Fragment non‑JSON reçu : $line" >&2
  fi
done < <(gemini prompt -c .gemini.yaml -i texte.txt --stream)
```

---

### 3.4 Envoi de plusieurs prompts (batch)

Le champ `batch` accepte un tableau d’objets `prompt`. Chaque objet peut redéfinir `system`, `user`, etc. Exemple :

```yaml
model: gemini-1.5-pro
batch:
  - user: "Écris une fonction Python qui calcule la factorielle."
    temperature: 0.3
    top_p: 0.8
  - user: "Donne un titre accrocheur pour un article sur les énergies renouvelables."
    temperature: 0.9
    top_p: 0.95
```

Invocation :

```bash
gemini batch -c batch.yaml --output batch_results.json
```

Le fichier de sortie contient un tableau `responses`, chaque entrée incluant `output`, `usage` et `finish_reason`.

---

### 3.5 Métadonnées de réponse

Chaque réponse JSON possède :

```json
{
  "candidates": [
    {
      "output": "…",
      "finishReason": "STOP",
      "safetyRatings": [...],
      "tokenCount": {
        "inputTokens": 123,
        "outputTokens": 456,
        "totalTokens": 579
      }
    }
  ],
  "usageMetadata": {
    "totalTokens": 579,
    "promptTokenCount": 123,
    "candidatesTokenCount": 456
  }
}
```

- `inputTokens` : tokens du prompt (incluant le fichier d’entrée).
- `outputTokens` : tokens générés.
- `totalTokens` : somme, utilisée pour la facturation.
- `finishReason` : `STOP`, `MAX_T

---

## Module 4 — contenu

## 4.1 Redirection d’entrée / sortie avec `gemini prompt`

| Option | Description | Exemple |
|--------|-------------|---------|
| `-i <fichier>` | Lit le prompt depuis le fichier indiqué. Si le fichier n’existe pas, la commande échoue avec `ENOENT`. | `gemini prompt -i texte.txt` |
| `-o <fichier>` | Écrit la réponse brute (JSON) dans le fichier. Si le fichier existe, il est écrasé sauf si `--append` est utilisé. | `gemini prompt -o réponse.json` |
| `--stream` | Active le mode streaming : les tokens sont envoyés au fur et à mesure sur `stdout`. Nécessite un traitement de flux (ex. `jq -c`). | `gemini prompt --stream -i prompt.yaml` |
| `--log-file <fichier>` | Enregistre le trafic HTTP complet (requêtes + réponses) au format texte. | `gemini prompt --log-file trace.log …` |

> **Note** : `gemini prompt` accepte le format YAML ou JSON pour le prompt. Le fichier doit être encodé en UTF‑8 sans BOM.

### 4.1.1 Exemple complet (Linux/macOS/WSL)

```bash
#!/usr/bin/env bash
# ------------------------------------------------------------
# Script : transform.sh
# Objectif : lire src.txt, le reformuler en style "bullet list"
#            via le modèle gemini-1.5-flash, écrire le JSON dans out.json
# ------------------------------------------------------------

set -euo pipefail   # arrête le script sur la première erreur

#--- Configuration ------------------------------------------------
PROMPT_FILE=$(mktemp)           # fichier temporaire contenant le prompt
INPUT_FILE="src.txt"            # fichier source (UTF‑8)
OUTPUT_FILE="out.json"          # destination du résultat
MODEL="gemini-1.5-flash"
TEMPERATURE=0.7
TOP_P=0.9
#---------------------------------------------------------------

# Vérifier la présence du fichier d’entrée
if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Erreur : fichier d’entrée $INPUT_FILE introuvable" >&2
  exit 1
fi

# Construire le prompt au format YAML
cat >"$PROMPT_FILE" <<'EOF'
system: |
  Vous êtes un assistant qui reformule du texte en listes à puces.
user: |
  {{input}}
assistant:
  max_output_tokens: 1024
  temperature: {{temperature}}
  top_p: {{top_p}}
EOF

# Remplacer les variables dans le prompt (bash substitution)
sed -i "s|{{input}}|$(sed 's/[&/\]/\\&/g' "$INPUT_FILE")|g" "$PROMPT_FILE"
sed -i "s|{{temperature}}|$TEMPERATURE|g" "$PROMPT_FILE"
sed -i "s|{{top_p}}|$TOP_P|g" "$PROMPT_FILE"

# Exécuter la CLI en mode batch (pas de streaming) et capturer le JSON brut
gemini prompt \
  --model "$MODEL" \
  -i "$PROMPT_FILE" \
  -o "$OUTPUT_FILE" \
  --log-file "transform.log"

# Nettoyage du fichier temporaire
rm -f "$PROMPT_FILE"

echo "Transformation terminée → $OUTPUT_FILE"
```

*Points d’attention*  

* `sed` utilise des séparateurs `|` pour éviter d’interférer avec les `/` du texte source.  
* Le fichier temporaire est créé avec `mktemp` afin d’éviter les collisions de noms.  
* `set -euo pipefail` garantit que toute erreur (y compris une variable non définie) interrompt le script, ce qui évite les résultats partiels.  

---

## 4.2 Chaînage avec `stdin` / `stdout`

```bash
# Exemple d’une chaîne Unix qui filtre les lignes contenant « error »,
# les envoie à Gemini pour reformulation, puis extrait le texte final.
grep -i "error" serveur.log |
  gemini prompt -i - --stream \
    --model gemini-1.5-pro \
    --temperature 0.3 \
    --top_p 0.8 |
  jq -r '.candidates[0].content.parts[0].text'
```

*Explications*  

* `-i -` indique à `gemini` de lire le prompt depuis `stdin`.  
* `--stream` transmet chaque token dès réception, ce qui évite le buffering du processus.  
* `jq -r` extrait le champ texte brut du JSON de réponse.  

### 4.2.1 Gestion des caractères spéciaux

Lorsque le prompt contient des guillemets, des apostrophes ou des backticks, il faut les échapper **avant** de les passer à `gemini`. Exemple :

```bash
printf '%s\n' "Voici le code : \`console.log(\"Hello\")\`" |
  gemini prompt -i - --model gemini-1.5-flash --temperature 0.0
```

Le backtick est interprété par le shell, donc on le préserve en le plaçant entre guillemets simples (`'...'`) ou en l’échappant (`\``).

---

## 4.3 Appel direct de l’API REST via `curl`

Le même résultat que `gemini prompt` peut être obtenu avec `curl`. Cela est utile lorsqu’on veut intégrer Gemini dans un environnement où la CLI n’est pas disponible (ex. CI Docker minimal).

```bash
#!/usr/bin/env bash
# ------------------------------------------------------------
# Script : curl_gemini.sh
# ------------------------------------------------------------

API_KEY=$(jq -r .api_key ~/.gemini/config.json)
ENDPOINT="https://gener

---

## Module 5 — contenu

## 5.1 Déploiement automatisé avec CI/CD  

| Étape | Action | Commande / fichier | Vérification |
|------|--------|--------------------|--------------|
| **5.1.1** | Créer un *Dockerfile* minimal qui embarque Gemini CLI et le script d’inférence. | ```Dockerfile\nFROM node:20-alpine\n# 1. Installer Gemini CLI (global) \nRUN npm i -g @google/gemini-cli && \\\n    gemini --version\n# 2. Copier le script d’inférence\nCOPY infer.sh /usr/local/bin/infer.sh\nRUN chmod +x /usr/local/bin/infer.sh\n# 3. Définir le point d’entrée\nENTRYPOINT [\"/usr/local/bin/infer.sh\"]\n``` | `docker build -t my-gemini .` → *Successfully built* |
| **5.1.2** | Stocker la clé d’API dans un secret du CI (ex. GitHub Actions `secrets.GEMINI_API_KEY`). | ```yaml\n# .github/workflows/deploy.yml\nname: Build & Deploy\non:\n  push:\n    branches: [ main ]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - name: Set up Node\n        uses: actions/setup-node@v3\n        with:\n          node-version: '20'\n      - name: Build Docker image\n        run: |\n          echo \"$GEMINI_API_KEY\" > gemini_key.json\n          docker build -t ghcr.io/${{ github.repository }}:$(git rev-parse --short HEAD) .\n      - name: Push image\n        uses: docker/login-action@v2\n        with:\n          registry: ghcr.io\n          username: ${{ github.actor }}\n          password: ${{ secrets.GITHUB_TOKEN }}\n      - name: Push image to registry\n        run: |\n          docker push ghcr.io/${{ github.repository }}:$(git rev-parse --short HEAD)\n``` | Après le run, l’image apparaît dans le registre GitHub Container Registry. |
| **5.1.3** | Déployer sur un orchestrateur (ex. Kubernetes) avec un *Deployment* qui monte le secret comme fichier. | ```yaml\n# k8s/deployment.yaml\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: gemini-infer\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: gemini\n  template:\n    metadata:\n      labels:\n        app: gemini\n    spec:\n      containers:\n      - name: gemini\n        image: ghcr.io/owner/repo:{{IMAGE_TAG}}\n        env:\n        - name: GEMINI_CONFIG_PATH\n          value: \"/secrets/config.json\"\n        volumeMounts:\n        - name: gemini-secret\n          mountPath: \"/secrets\"\n          readOnly: true\n      volumes:\n      - name: gemini-secret\n        secret:\n          secretName: gemini-api-key\n``` | `kubectl apply -f k8s/deployment.yaml` → *deployment.apps/gemini-infer created* |
| **5.1.4** | Exposer via un *Service* de type `LoadBalancer` ou `Ingress`. | ```yaml\napiVersion: v1\nkind: Service\nmetadata:\n  name: gemini-svc\nspec:\n  selector:\n    app: gemini\n  ports:\n  - protocol: TCP\n    port: 80\n    targetPort: 8080\n  type: LoadBalancer\n``` | `kubectl get svc gemini-svc` → adresse IP publique disponible. |

### Pourquoi ces étapes sont obligatoires  

* **Dockerfile** garantit le même environnement (Node 20, OpenSSL, Gemini CLI) sur toutes les plateformes.  
* **Secrets CI** évitent que la clé d’API soit écrite dans le dépôt ou les logs.  
* **Kubernetes secret** monte la clé en lecture‑seule, limitant l’exposition au conteneur uniquement.  
* **ReplicaSet** assure la haute disponibilité ; le *LoadBalancer* répartit le trafic.

---

## 5.2 Automatisation du flux de transformation de documents  

```bash
#!/usr/bin/env bash
# infer.sh – script d’inférence utilisé comme ENTRYPOINT du conteneur
# ---------------------------------------------------------------
# 1. Vérifier la présence du fichier de configuration
if [[ ! -f "${GEMINI_CONFIG_PATH:-/secrets/config.json}" ]]; then
  echo "❌ Config file not found at ${GEMINI_CONFIG_PATH}" >&2
  exit 1
fi

# 2. Exporter la configuration pour Gemini CLI (lecture uniquement)
export GEMINI_CONFIG="${GEMINI_CONFIG_PATH}"

# 3. Lire le texte depuis STDIN, le découper en blocs de 1500 tokens
#    (Gemini accepte environ 2 MiB ≈ 3000 tokens, on laisse marge)
MAX_TOKENS=1500
BLOCKS=()
while IFS= read -r -d '' chunk; do
  BLOCKS+=("$chunk")
done < <(gemini tokenize --max-tokens $MAX_TOKENS -i -)

# 4. Boucler sur les blocs, appeler Gemini en streaming et concaténer
RESULT=""
for blk in "${BLOCKS[@]}"; do
  # --stream renvoie chaque token sur une ligne JSON
  RESPONSE=$(echo "$blk" | gemini prompt \
    -m gemini-1.5-pro \
    --temperature 0.7 \
    --top-p 0.9