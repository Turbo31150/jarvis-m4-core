[assistant] Diff obtenu. Je vérifie maintenant le fichier complet, le périmètre des fichiers touchés, et l'état du service.

[assistant] Diff propre et circonscrit. Je lance maintenant les contre-tests réels sur le service actif.

[assistant] Le service tourne, syntaxe OK, embeddings confirmés hors hub. Je passe aux contre-tests HTTP.

[assistant] Le POST normal répond 200 mais en 72 s (fallback ollama/gemma3:4b — le hub est chargé). Je teste l'abandon et le cas sans message user.

[assistant] Aucun crash sur les cas phash limites. Je vérifie les lignes jsonl produites, puis le test d'abandon.

[assistant] Le fichier est vu comme binaire par grep (piège connu). Je reprends avec `grep -a`.

[assistant] Test critique maintenant : abandon client à 3 s, puis requête normale immédiate.

[assistant] Abandon parfaitement traité (client_gone ms:3003, slot rendu — la requête suivante prend lmstudio-m1 en tried:0). Reste le 429 : je vérifie d'abord la cascade réelle.

[assistant] Classification `overloaded` exacte sur 28 cas réels. Test live du 429 avec ses en-têtes.

[assistant] 429 conforme. Je vérifie l'état du sémaphore après la vague (fuite de slot ?) et les client_gone en file.

[assistant] Dernière vérification : test unitaire isolé du cas « entrée annulée en tête de file » (non couvert en live).

[assistant] Dernier point : le périmètre exact des fichiers touchés dans la fenêtre du chantier.