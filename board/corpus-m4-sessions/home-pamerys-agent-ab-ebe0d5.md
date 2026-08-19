[assistant] Je commence par vérifier ce qui existe réellement côté board local avant de router quoi que ce soit.

[assistant] Board présent (board.py + board.db en miroir, 51 Mo). Backends 0-token disponibles : Ollama local, LM Studio M6 (câble direct), Ollama Rémi. Je regarde l'interface du board.

[assistant] Le board n'a pas de corpus pertinent (10 domaines tous techniques ; les 93 occurrences de « facebook » sont FAISS/Graph API/React). Je lance quand même un `ask` de contrôle et, en parallèle, la cascade locale sur M6.

[assistant] Board en panne (modèle `hermes-2-pro-mistral-7b` absent de M6 → 0 expert répondant). Repli confirmé sur la cascade. Je relance les deux volets manquants.

[assistant] Erreur 400 : le modèle a probablement été évincé sur M6 pendant l'appel du board. Je resonde et je relance.

[assistant] M6 souffre du reasoning-runaway connu (content vide) et met 130 s à répondre. Je bascule sur Ollama Rémi (gemma3:27b), plus adapté à de la rédaction française.

[assistant] gemma3:27b est trop lent (>10 min). Je repars sur M6 qwen3.5-9b, maintenant chaud, avec un budget de tokens suffisant pour absorber le reasoning.