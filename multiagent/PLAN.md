# JARVIS Multi-Agent Transcription Router — Plan d'implémentation
## Objectif
Système d'agents de fond qui intercepte les transcriptions vocales (voice_widget),
détecte les mots-clés/contexte, et distribue automatiquement vers les bons agents M1+M2.

## Architecture
```
voice_widget → transcription → KEYWORD ROUTER → [agent spécialisé M1/M2]
                                    ↓
                    [transcription | cours | trading | code | médical | ...]
```

## Tâches

### TASK-1: Keyword Router (jarvis-router.py)
Fichier: ~/jarvis/multiagent/jarvis-router.py
- Surveille ~/jarvis/subtitles/live.txt (sortie voice_widget)
- Charge keywords.json (dictionnaire thèmes→mots-clés)
- Détecte le thème de la transcription
- Route vers l'agent M1 ou M2 approprié
- Écrit résultat dans ~/jarvis/multiagent/output/

### TASK-2: Keywords config (keywords.json)
Fichier: ~/jarvis/multiagent/keywords.json
- Thèmes: cours, trading, code, recherche, médical, général
- Pour chaque thème: liste de mots-clés FR+EN, modèle cible (M1/M2), prompt système

### TASK-3: Agent Transcription-Compressor (compress-agent.py)
Fichier: ~/jarvis/multiagent/compress-agent.py
- Reçoit texte de transcription (peut être long)
- Compresse/résume via M2 (qwen3.5-9b rapide)
- Retourne texte court optimisé pour coller dans un doc

### TASK-4: Agent Adaptation-Contexte (context-agent.py)
Fichier: ~/jarvis/multiagent/context-agent.py
- Adapte la réponse au contexte enseignant (PAMERYS M4)
- Niveau: collège/lycée (ajustable)
- Ajoute exemples pédagogiques, structure cours

### TASK-5: Service background (jarvis-multiagent.service)
Fichier: /etc/systemd/system/jarvis-multiagent.service
- Lance jarvis-router.py au boot
- Restart automatique si crash
- Log dans ~/jarvis/multiagent/router.log

### TASK-6: CLI commande (jarvis-ask)
Fichier: /usr/local/bin/jarvis-ask
- Interface CLI: jarvis-ask "ma question" [--cours|--code|--trading]
- Route directement vers le bon modèle M1/M2
- Affiche réponse en temps réel
