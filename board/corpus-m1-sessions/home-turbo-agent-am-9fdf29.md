[assistant] Le PLAN.md est généré localement et reste abstrait (binaire compilé, latence 2ms = hallucinations LLM). Je le traduis en étapes exécutables avec les briques réelles. D'abord, sonder.

[assistant] Tous les backends sont verts, y compris M6. J'inspecte les séries candidates avant d'exécuter.

[assistant] `serie-run.sh` est exactement l'exécuteur fail-safe demandé (retry + dead-letter + continue). Je l'utilise comme moteur de la cascade.