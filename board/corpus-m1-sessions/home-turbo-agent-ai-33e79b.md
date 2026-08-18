[assistant] Je démarre par la cartographie en lecture seule des producteurs de la ferme, comme demandé.

[assistant] Le service est reparti proprement avec le nouvel environnement effectif. Je surveille un cycle réel et vérifie les latences dans le journal ollama.

[assistant] Le service vient de repartir en pause thermique (GPU 82°C) avant même le premier appel LLM du nouveau cycle. Pour valider sans attendre la pause, je lance un cycle `--once` manuel avec le même environnement que le service patché.

[assistant] J'ai transmis le rapport complet au chef d'équipe. Résumé de ce qui a été fait :

**Cartographie** : sur les 4 producteurs listés, `auto_dynamic_task_producer.py` ne consomme en réalité aucun LLM (simple INSERT SQLite statique) et `jarvis-prod-exec.py`/`mail-draft-producer.py` sont classés QUALITÉ ou passent par le hub sans champ modèle exploitable — je ne les ai pas touchés, conformément aux consignes.

**Root cause découverte** : `biblio_filler.py` (SIMPLE) timait out en boucle vers un nœud M6 mort (`10.42.0.230:18900`, injoignable), ce qui déclenchait un fallback systématique vers `deepseek-r1:7b`/`gpt-oss:20b-cloud` — et j'ai trouvé une **deuxième unité systemd non listée initialement**, `jarvis-biblio-infinite.service` (timer 2 min), avec exactement le même problème.

**Patch appliqué** : deux nouveaux drop-ins systemd (`zzz-zz-t4-qwen15b.conf`) sur ces deux services, routant vers `qwen2.5:1.5b` sur ollama local direct, sans toucher au hub ni aux unités ollama. Backups pris avant, rollback = suppression du fichier.

**Point d'attention (DONE_WITH_CONCERNS)** : le routage est correctement appliqué et vérifié (env effective, services actifs, pas de régression), mais je n'ai pas pu valider le gain de latence attendu — trois tests directs contre ollama avec `qwen2.5:1.5b` ont timeout (jusqu'à 100s sans réponse). J'ai identifié que le serveur ollama tourne avec `-np 1` (un seul slot parallèle) en continu occupé par du trafic `gemma3:4b`, un goulot hors de mon mandat pour ce t