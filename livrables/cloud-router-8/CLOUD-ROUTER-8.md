# CLOUD-ROUTER-8 — fan-out N cles Ollama Cloud (0 chaleur M4)

Routeur round-robin qui traite une **liste de prompts en parallele** en repartissant
la charge sur les **N cles Ollama Cloud de Remi** (cible : 8) — une cle par worker.
Tout part sur `ollama.com` (deporte) : **aucune inference locale**, donc **0 chaleur
sur le M4** (GPU en surchauffe).

Fichier : `~/jarvis/scripts/cloud-router-8.py` (Python 3.11, stdlib seule, 0 dependance).

## 1. Ou sont les cles (jamais en clair, jamais committees)

Le routeur lit les cles dans cet ordre de priorite, **sans jamais les afficher** :

1. `OLLAMA_CLOUD_KEYS` (env) — les 8 cles separees par virgule, espace ou retour ligne.
2. `~/.ollama/cloud_keys` — **une cle par ligne** (`#` = commentaire). `chmod 600`.
3. Fallback single-key (compat scripts existants) : `OLLAMA_API_KEY`, sinon
   `~/.ollama/cloud.env`, sinon `~/.ollama/cloud_api_key`.

### Installer les 8 cles de Remi
```bash
umask 077
printf '%s\n' "$CLE1" "$CLE2" ... "$CLE8" > ~/.ollama/cloud_keys   # une par ligne
chmod 600 ~/.ollama/cloud_keys
```
ou, le temps d'une session, sans fichier :
```bash
export OLLAMA_CLOUD_KEYS="cle1,cle2,cle3,cle4,cle5,cle6,cle7,cle8"
```
Aucune modification de code n'est necessaire : des que les 8 cles sont presentes,
le fan-out passe automatiquement de 1 a 8 workers.

> Etat actuel sur ce M4 : **1 seule cle** est provisionnee (`~/.ollama/cloud.env`,
> `OLLAMA_API_KEY`, mirroir sops `secrets-vault/ollama.enc.env`). Le routeur tourne
> deja avec cette cle ; il montera a 8 des que `~/.ollama/cloud_keys` est rempli.

## 2. Endpoint & modele

- Endpoint : `https://ollama.com/api/chat`, en-tete `Authorization: Bearer <cle>`.
- Modele gratuit par defaut : **`gpt-oss:120b`** (parametrable `--model` / `OLLAMA_CLOUD_MODEL`).
  Autres gratuits connus : `gpt-oss:20b-cloud`. **Payants** (a eviter) : `kimi-k2.*`,
  `glm-*`, `qwen3.5`, `deepseek-*` (subscription).

## 3. Lancer un batch de N prompts

```bash
# 1 prompt par ligne dans prompts.txt -> resultats en JSONL
python3 ~/jarvis/scripts/cloud-router-8.py --prompts prompts.txt --out resultats.jsonl

# via stdin
printf 'Explique la photosynthese\nResume la Revolution francaise\n' \
  | python3 ~/jarvis/scripts/cloud-router-8.py --out resultats.jsonl

# modele / parallelisme explicites
python3 ~/jarvis/scripts/cloud-router-8.py --prompts p.txt --out r.jsonl \
  --model gpt-oss:20b-cloud --workers 8 --timeout 120 --retries 2
```

Sortie : un JSONL (append). Une ligne par prompt :
```json
{"id":"ab12..","idx":0,"ok":true,"key":3,"backend":"ollama-cloud:gpt-oss:120b","prompt":"...","response":"..."}
```
Progression sur stderr : `[done/total] OK key#3 idx=0`.

### Idempotence
La sortie est en `append` et le routeur **saute les prompts deja reussis** (hash du
prompt). Relancer la meme commande = reprend seulement ce qui manque/a echoue.

### Rotation & resilience
- Une cle en **429** => backoff exponentiel puis bascule sur la cle suivante.
- Une cle en **401/403** => marquee **morte**, retiree de la rotation, le run continue.
- Timeout/5xx => retries backoff puis cle suivante. Le batch ne crashe jamais sur une
  cle : un prompt irrattrapable est ecrit avec `"ok": false` + `"error"`.

## 4. Valider les cles (sans charge lourde)

```bash
python3 ~/jarvis/scripts/cloud-router-8.py --selftest
```
Fait **1 mini-appel par cle** (`OK<n>`) et affiche, par index de cle, `200 VIVANTE`,
`401 MORTE` ou `429 RATE-LIMIT`. Termine par `X/8 cle(s) repondent 200`.
Aucune cle n'est jamais affichee. Deporte => 0 chaleur M4.

## 5. Garde-fous

- **Jamais de cle en clair** : ni dans le code, ni dans les logs (seul `key#<index>`
  apparait), ni dans le JSONL de sortie. `~/.ollama/cloud_keys` reste `chmod 600` et
  hors git.
- **RGPD / donnees eleves** : NE PAS router de donnees nominatives (noms d'eleves,
  familles, prospects) vers le cloud Ollama. Anonymiser avant, ou rester sur la
  cascade locale/M6 pour tout contenu personnel.
- **Quota cloud** : les modeles `gpt-oss:*` sont gratuits mais soumis a un quota
  horaire/journalier par cle ; d'ou l'interet des 8 cles (le 429 fait tourner).
- **0 chaleur M4** : ce routeur ne lance aucune inference locale ; il ne fait que des
  requetes HTTP sortantes vers ollama.com. Ne pas le confondre avec `ollama run` local.
