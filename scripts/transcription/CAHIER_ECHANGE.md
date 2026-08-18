# Cahier d'échange — Système transcription BDQT (Claire / M4)

Système de qualité-transcription qui relie **Whisper** (dictée), **Wispr Flow** (apprentissage récupéré) et **Perplexity/Comet** (vocabulaire), avec correction en temps réel et apprentissage continu.

## Ce que ça fait
- **Dictée Alt+X** → Whisper turbo/CUDA → texte au curseur, sans hallucination (silence = vide).
- **Post-correction** automatique : tes erreurs connues → forme correcte (emails, lieux, sigles).
- **Apprentissage** : tu ajoutes une correction en 1 commande, effet immédiat.
- **Service HTTP** (:8790) : correction utilisable par n8n / autres apps.

## Bibliothèque actuelle
- 615 corrections · 251 termes (mairie 63, civique 57, tech 57, nom_propre 42, école 32)
- Dataset voix fine-tuning : 242 train / 20 eval / 330 wav (prêt pour GPU ≥8 Go)

---

## TOUTES LES COMMANDES (exemples réels)

### Apprendre une correction (le geste quotidien)
```bash
bdqt-teach "ce qu'il écrit" "ce qu'il faut"     # ex: bdqt-teach "ccas" "CCAS"
bdqt-teach --list 10                             # voir les dernières apprises
bdqt-teach --del "mauvais"                       # supprimer une correction
```
→ effet IMMÉDIAT, pas de redémarrage.

### Corriger un texte existant (retranscription)
```bash
echo "je vais à mont laure voir le ccas" | bdqt_retranscribe.py --diff
# -> je vais à Montlaur voir le CCAS
```

### Corriger via l'API HTTP (n8n / scripts / autres machines)
```bash
curl -s :8790/correct -H "Content-Type: application/json" \
  -d '{"text":"ouvre olama et va à mont laure"}'
# -> {"corrected":"ouvre Ollama et va à Montlaur", ...}
curl -s :8790/health          # état + stats
```

### Importer l'apprentissage Wispr Flow (Windows)
```bash
python3 bdqt_import_flow.py     # depuis l'appli officielle (flow.sqlite)
python3 bdqt_import_wispr.py    # depuis un export JSON
```

### Tester / valider la bibliothèque (multi-scénario)
```bash
python3 bdqt_validate.py        # positifs + négatifs (anti-faux-positifs) → score
python3 bdqt_bench.py           # banc TTS (indicatif, ≠ vraie voix)
```

### Reconstruire / boucle d'apprentissage
```bash
bash bdqt_rebuild.sh            # réimporte corrections + reconstruit lexique + prompts
```

### Voix → dataset → fine-tuning (sur GPU ≥8 Go uniquement)
```bash
python3 bdqt_extract_audio.py                              # extrait ta voix (déjà fait)
pip install torch transformers datasets peft accelerate
python3 bdqt_finetune.py --model openai/whisper-small      # entraîne sur TA voix
```

---

## Exemple concret de bout en bout (ta journée type)
1. Tu dictes (Alt+X) : *« Envoie un mail pro pour la réunion du CCAS à Montlaur »*
2. Whisper entend, la post-correction transforme « mail pro » → ton email, garde CCAS/Montlaur.
3. Whisper se trompe une fois sur un mot → tu fais `bdqt-teach "le mot faux" "le bon"`.
4. La fois d'après, c'est corrigé tout seul. La bibliothèque grossit avec TOI.

## Garde-fous (leçons apprises)
- **Aucun biais Whisper** (initial_prompt/hotwords) : ça faisait halluciner → désactivé.
- **Pas d'import auto en masse** (History/Comet) : trop de bruit → faux positifs. On **cure**.
- `bdqt_validate.py` vérifie qu'aucun mot courant n'est cassé (tests négatifs).
