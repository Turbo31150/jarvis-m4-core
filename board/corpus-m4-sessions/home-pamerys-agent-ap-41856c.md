[assistant] Je démarre par sonder l'état réel : comptage board.db, lecture du dispatcher, et santé des trois backends embeddings, en parallèle.

[assistant] Le garde thermique bloque tout Bash : le M4 est à 91-94°C, au-dessus du seuil de 90°C. C'est en soi un signal fort pour la recommandation. Je réessaie les sondes read-only, la température fluctue.

[assistant] 73°C maintenant, sous le seuil. Je lance les sondes essentielles tout de suite dans une seule salve.

[assistant] Bonnes données. Une dernière sonde read-only pendant que la température le permet : cohérence de l'espace vectoriel (modèle/dimension des chunks déjà faits — critique pour une reprise), présence d'un dispatch déjà en cours, et charge M4 instantanée.

[assistant] Recommandation transmise au team-lead. Rien n'a été lancé, aucun fichier modifié — tout en lecture seule.

## Synthèse

**Verdict : relancer maintenant sur Rémi Ollama (nomic-embed-text), 3-4 workers — pas sur M6.**

**Ce qu'il reste (board.db, mode read-only)** : 178 829 chunks à vectoriser sur 264 616 (85 787 faits). Concentré sur deux domaines seulement : `biblio-vivante` (168 002 restant) et `souverainete` (10 823 restant) ; tous les autres domaines sont déjà à zéro.

**Le point qui verrouille le choix du backend** : les 85 787 chunks déjà faits sont tous en **768 dimensions, famille nomic v1.5** (moitié via `nomic-embed-text` Ollama, moitié via `text-embedding-nomic-embed-text-v1.5` LM Studio). J'ai testé Rémi : `nomic-embed-text` renvoie bien 768 dims, donc même espace vectoriel. Il ne faut surtout pas basculer sur `bge-m3` ou `mxbai-embed-large` (présents sur Rémi mais en 1024 dims) qui rendraient l'index incohérent.

**Pourquoi pas M6** : son modèle embed est `not-loaded` et il sert le chat du board (`qwen3.5-9b` en `loading`) sur la même VRAM. Le dernier run M6 échoue d'ailleurs en boucle — le journal `dispatch-embed-m6.log` montre « ABANDON lot de 16 après 6 essais : HTTP Error 400 » à 11h44-11h48. C'est exactement la contention connue : lancer M6 casserait le board chat sans réussir les embeddings.

**Pourquoi Rémi est sûr** : machine séparée (Tailscale, up), donc le chat du board reste vivant sur M6 pendant la vectorisation, et comme le calcul est déporté, le M4 n