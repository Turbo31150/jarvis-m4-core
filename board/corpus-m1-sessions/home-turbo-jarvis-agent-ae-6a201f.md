[assistant] LM Studio est bien en écoute sur 1234 (pid 13733) et deux `llama-server` chargent Qwen3.5-9B. Je teste la réponse réelle.

[assistant] LMS répond 200 : c'était bien du warmup, pas une panne. Je vérifie l'inférence réelle et le hub.

[assistant] `content` vide = budget de tokens trop court (piège connu). Je refais avec un budget correct, et je sonde le routage du hub modèle par modèle.

[assistant] LMS génère (393 tokens de reasoning avant le contenu — runaway connu de qwen3.5). Je sonde maintenant chaque modèle annoncé par le hub.

[assistant] LMS vient de retomber (000 à 17:40 alors qu'il répondait 200 à 17:34). Ce n'est donc pas qu'un warmup — il y a un flap. Je creuse.

[assistant] LM Studio a crashé sur une exception Node non rattrapée (`ERR_INVALID_ARG_TYPE`, argument `path`). Je localise le lanceur pour le relancer proprement.

[assistant] Je relance LM Studio avec exactement la commande documentée de l'autostart (bind 127.0.0.1 conservé).