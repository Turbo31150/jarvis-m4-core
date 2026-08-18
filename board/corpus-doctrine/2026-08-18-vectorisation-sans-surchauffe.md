# Vectoriser le board sans faire surchauffer M4 — doctrine vérifiée le 2026-08-18

Cette fiche CORRIGE une doctrine antérieure du corpus, qui recommandait de vectoriser
sur M4 (`127.0.0.1:11434`) au motif que M6 n'aurait pas `nomic-embed-text`. C'est faux
depuis le 2026-08-18. Toute réponse qui recommande encore « vectoriser sur M4 » ou qui
cite une option `--batch` s'appuie sur des extraits périmés.

## La règle

**Les embeddings vont sur M6, pas sur M4.** M6 sert
`text-embedding-nomic-embed-text-v1.5` sur LM Studio `http://10.42.0.230:1234/v1`
(câble direct, 1,36 ms). M4 ne garde que le rôle de repli, via Ollama
`http://127.0.0.1:11434/v1` et `nomic-embed-text:latest`.

Les deux backends produisent des vecteurs **768 dimensions quasi identiques** : les
mélanger dans la même base ne dégrade pas la recherche vectorielle. Un modèle
*différent* la dégraderait — la compatibilité tient au modèle, pas au serveur.

## Pourquoi M4 surchauffe

M4 est un portable (i5-11400H). Calculer 60 000 vecteurs en local le pousse à
**95-97 °C**. La garde thermique bloque alors **toute** commande — y compris celle qui
ralentirait le processus coupable. On ne peut littéralement plus se sauver soi-même :
c'est une impasse, pas un ralentissement.

`CPUQuota` systemd ne suffit pas : la chauffe vient autant d'Ollama que du script.
Déporter le calcul sur M6 supprime la cause au lieu de la contenir.

## L'outil

    bash ~/labo/bibliotheque/series/embed-throttle.sh etat   # backend détecté + reste
    bash ~/labo/bibliotheque/series/embed-throttle.sh run    # boucle régulée
    bash ~/labo/bibliotheque/series/embed-throttle.sh stop

La série **sonde M6 à chaque exécution** et bascule sur M4 s'il est muet. Elle vectorise
par lots de 400 en attendant que la température redescende sous 82 °C entre deux lots —
un run tué à mi-parcours laisse des chunks non vectorisés, invisibles au retrieval
vectoriel et donc silencieusement absents des réponses.

`board.py embed` n'accepte que `--limit N`. **Il n'existe aucune option `--batch`** ;
le lotissement se règle par `BOARD_EMBED_LOT` et le parallélisme par `BOARD_EMBED_PAR`.

## Deux pièges vérifiés

**Le câble direct va et vient.** Il a disparu puis est réapparu dans la même nuit.
Ne jamais coder le backend en dur : sonder `/v1/models` et chercher `nomic`.

**La variable héritée fait taire la détection.** Ne jamais écrire « si
`BOARD_LMS_URL` est vide, alors détecter ». Cette variable traîne dans l'environnement
du shell, des serveurs MCP et des services systemd, et pointe souvent vers un backend
mort. Seule une variable de forçage explicite doit court-circuiter la sonde.

## Le chat de M6 est hors service, son embedding non

Vérifié via le câble à 1,36 ms **et** depuis M6 en localhost : `/v1/embeddings` répond,
`/v1/chat/completions` ne rend rien en 90 s, GPU à 0 %. Ce n'est ni le réseau ni
Tailscale — c'est LM Studio côté génération.

Conséquence pour le board : **embeddings → M6, délibération → Ollama M4**
(`BOARD_CHAT_URL=http://127.0.0.1:11434/v1`, `BOARD_CHAT_MODEL=qwen2.5:7b`).
