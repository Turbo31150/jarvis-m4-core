# cloud-router-8

Routeur round-robin fan-out qui traite une **liste de prompts en parallèle** en
répartissant la charge sur plusieurs clés API Ollama Cloud (une clé par worker).
100 % déporté sur ollama.com → zéro inférence locale, zéro chaleur machine.

## Contenu
```
cloud-router-8.py     # le routeur (stdlib Python uniquement)
CLOUD-ROUTER-8.md     # documentation détaillée
README.md / FICHE-VENTE.md / LICENSE.txt
```

## Installation
Aucune dépendance tierce (stdlib Python 3.11+).
```bash
chmod +x cloud-router-8.py
```
Fournissez vos clés par **variable d'environnement** ou fichier hors-git (jamais
en dur) :
```bash
export OLLAMA_CLOUD_KEYS="cle1,cle2,cle3"      # séparées par virgule/espace/ligne
# ou : ~/.ollama/cloud_keys  (une clé par ligne)
```

## Usage
```bash
# Selftest : 1 mini-appel par clé → qui répond (200/401/429)
python3 cloud-router-8.py --selftest

# Batch parallèle idempotent (reprend là où il s'est arrêté)
python3 cloud-router-8.py --prompts prompts.txt --out results.jsonl --workers 8

# Via stdin
echo -e "prompt A\nprompt B" | python3 cloud-router-8.py --out out.jsonl
```

## Sécurité
- Aucune clé n'est écrite en dur ni affichée : les logs ne montrent que
  l'index de clé (`key#0..N`).
- Rotation automatique : clé morte (401/403) retirée, backoff sur 429/5xx.
- RGPD : ne pas router de données nominatives (voir `CLOUD-ROUTER-8.md`).
