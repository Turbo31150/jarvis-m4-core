[user] enlevers scette machine deu paramatrétage graphique dir'ctement en shell comme un serveur avec les deux option en gnome hgraphique plante tt le teùmps

[assistant] Je vérifie d'abord l'état réel avant de couper quoi que ce soit (SSH, services graphiques, apps qui dépendent de l'affichage).

[assistant] LM Studio tourne sous `systemd --user` (linger actif) mais avec `DISPLAY=:0` — il mourrait avec GDM. Je sécurise ça avant de couper.

[assistant] M4 identifié : `jarvis-franck-m4`, Ubuntu, Ollama + n8n. Je vérifie le script LM Studio et une voie d'accès à M4.