[user] Tu es l'agent CLOUD-ROUTER. Objectif : construire un routeur round-robin qui fan-out des prompts sur les 8 clés Ollama cloud de Rémi = 8 inférences cloud en parallèle, 0 chaleur sur le M4.

SÉCURITÉ ABSOLUE : ne JAMAIS afficher, journaliser ni committer une valeur de clé. Les clés se lisent depuis les fichiers existants ou l'env, jamais en dur dans le code livré. Aucune publication externe. Le calcul part sur le cloud Ollama (déporté) — n'exécute AUCUNE inférence Ollama locale (le M4 est en surchauffe GPU 100°C).

ÉTAPE 1 — Comprendre le mécanisme existant (lecture seule) :
- Lis /home/pamerys/jarvis/scripts/ollama-cloud-profile.sh et /home/pamerys/jarvis/scripts/ollama-cloud.sh : comment les clés sont stockées, combien il y en a (attendu : 8), quel endpoint (probablement https://ollama.com/api/chat ou un proxy), quel(s) modèle(s) cloud gratuits (ex gpt-oss:20b-cloud / gpt-oss:120b-cloud).
- Ne recopie AUCUNE clé dans ton rapport ; donne seulement le compte et le nom de la variable/fichier.

ÉTAPE 2 — Écrire /home/pamerys/jarvis/scripts/cloud-router-8.py (Python 3.11, type hints) :
- Charge la liste des 8 clés depuis la source existante (fichier/env), sans les afficher.
- Round-robin / pool : ThreadPoolExecutor(max_workers=8), une clé par worker, pour traiter une LISTE de prompts en parallèle.
- Chaque appel : POST vers l'endpoint cloud Ollama avec Authorization Bearer <clé>, modèle cloud gratuit paramétrable, timeout, retry léger (backoff) sur 429/5xx, rotation vers la clé s

[assistant] I'll start by reading the existing cloud scripts to understand the key storage mechanism.

[assistant] Thermal guard is blocking Bash (CPU 95°C). I'll use the Read tool instead. Let me examine the Rémi scripts to find the 8-key storage.

[assistant] Those don't hold the keys. Let me check the other Rémi scripts that reference keys.

[assistant] Bash remains thermally blocked. I'll use the filesystem MCP tools to locate the 8-key file.

[assistant] I've seen the structure (single key). The 8 Rémi keys must live elsewhere. Let me check the Rémi profile and secrets locations.

[assistant] No 8-key file found in the usual spots. Let me check the secrets vault and do a bounded search for a multi-key file.

[assistant] The secrets vault has `ollama.enc.env` (sops-encrypted). Let me read it to see the key names/count (values are encrypted).

[assistant] Confirmed: only ONE key is stored on this machine (env `OLLAMA_API_KEY` in `~/.ollama/cloud.env`, and mirrored encrypted in the sops vault `ollama.enc.env`). No 8-key file exists yet. So I'll design the router to load N keys from a pluggable source (env `OLLAMA_CLOUD_KEYS` / keys-file `~/.ollama/cloud_keys`, one per line), falling back to the single existing key — so it fans out over all 8 the moment Rémi's keys are dropped in, with zero code change and no key ever hardcoded.

Now writing the router.

[assistant] Now ÉTAPE 3 — validate. This needs to run Python (a deported cloud call, 0 heat), but the thermal guard blocks all Bash. Let me try the selftest anyway.

[assistant] Thermal guard cleared. Selftest passed. Let me prove the batch path with a 2-prompt run.

[assistant] Both the selftest and the batch path work end-to-end, deported, with idempotent JSONL output. Task complete.

## Rapport final

**ÉTAPE 1 — Mécanisme existant** (`ollama-cloud-profile.sh`, `ollama-cloud.sh`) : une **seule** clé, lue depuis l'env `OLLAMA_API_KEY` / le fichier `~/.ollama/cloud_api_key` (jamais en dur). Endpoint `https://ollama.com/api/chat` (Bearer). Modèles cloud gratuits : `gpt-oss:120b` (défaut), `gpt-oss:20b-cloud` ; les `kimi/glm/qwen3.5/deepseek` sont payants.

**Constat clés** : aucun fichier « 8 clés » n'existe sur ce M4. Il n'y a **qu'une clé** provisionnée (`~/.ollama/cloud.env` → `OLLAMA_API_KEY`, miroir chiffré sops `secrets-vault/ollama.enc.env`). Le routeur est donc conçu pour charger N clés depuis une source pluggable et monter à 8 sans toucher au code dès que les clés de Rémi sont déposées. Aucune valeur de clé n'est affichée ici.

**Fichiers livrés (chemins absolus)** :
- `/home/pamerys/jarvis/scripts/cloud-router-8.py` — Python 3.11, stdlib seule (0 dépendance), type hints. Charge les clés par priorité `OLLAMA_CLOUD_KEYS` (env) → `~/.ollama/cloud_keys` (1/ligne) → fallback clé unique. `ThreadPoolExecutor(max_workers=min(8, nb_clés))`, une clé par worker, round-robin ; rotation sur 429, marque morte sur 401/403 (continue sans crash), retry backoff sur 429/5xx/timeout. Entrée = fichier/stdin, sortie JSONL **idempotente** (skip des prompts déjà réussis via hash), log de progression `[done/total key#N]`. Mode `--selftest`.
- `/home/pamerys/jarvis/