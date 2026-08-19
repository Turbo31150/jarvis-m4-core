[assistant] Je commence par cadrer le terrain : lire le code du hub et sonder l'état système avant toute charge.

[assistant] Le mécanisme est clair dans le code. Je prépare le banc de mesure et je vérifie le modèle chargé sur :1234.

[assistant] `--parallel 2` confirmé sur le llama-server de LM Studio, alors que le hub limite `lmstudio*` à 1. Je lance les paliers avec garde thermique.

[assistant] mawk n'a pas `asort` — je corrige l'analyse (les données brutes des paliers 4 et 6 sont déjà écrites).

[assistant] Paliers 4 et 6 sans erreur, mais le p95 explose déjà à 6 (21 s = attente en file). Je continue.

[assistant] À 10 flux : 66 % d'échecs, et ce sont des **502**, pas des 429. Je capture les corps d'erreur pour voir quel backend défaille.

[assistant] Cause identifiée dans les corps d'erreur. Je termine par le palier 16, puis le test décisif direct sur `:1234`.

[assistant] Palier 16 : les deux codes coexistent (429=5, 502=9). `m6-lmstudio` est bien injoignable (connexion refusée). Test décisif maintenant : même montée en charge **directement sur `:1234`**, hub contourné.

[assistant] Direct sur `:1234` : **100 % de succès à 8 et 16 flux**. Le palier 4 direct est suspect (400/500 = chargement JIT du modèle), je le rejoue à chaud et je quantifie le trafic de fond du hub.

[assistant] `Model unloaded.` — les 400 sur `:1234` sont un artefact d'unload LM Studio, pas de concurrence. Je resserre le seuil entre 8 et 10 et je vérifie la reproductibilité.

[assistant] Chantier terminé. GPU redescendus à 75 °C max, charge à 9,8.

**Seuil réel : la rupture est entre 9 et 10 flux simultanés.** 4/6/8/9 → 100 % de succès ; 10 → 33 % de succès (66 % d'échecs), reproduit à l'identique sur deux exécutions. Mais 9 n'est pas exploitable : p95 de 90 s contre 1,3 s à 4 flux — la dégradation utile commence dès 6.

**Premier code d'erreur : 502, à 10 flux — et il est trompeur.** Le corps capturé montre que 4 backends sur 5 disent explicitement « surcharge (file d'attente active) ». C'est un 429 de nature. Mais `m6-lmstudio` est injoignable (connexion refusée sur `10.42.0.230:1234`) et renvoie `socket hang up` ; `chat_proxy.js:331` (`if (!e.overload) overloadOnly = false;`) suffit à requalifier la saturation en panne amont. Le 429 pur n'apparaît qu'à 16 flux, quand m6-lmstudio est lui-même saturé côté sémaphore et refuse avant d'ouvrir une socket.

**Le 429 est émis ligne 350.** Il n'y a ni file globale ni limiteur de débit : un sémaphore par backend, limites codées en dur — `limit = 1` pour `lmstudio*` (ligne 123), `2` pour ollama/rem-linux/m6 (ligne 130), `999` sinon. Capacité = `limit + 1` par backend (ligne 94-96 : refus dès qu'une requête attend déjà). Total 14 nominal, 11 utile, ~9 pour un client isolé une fois le trafic de fond déduit — le code et la mesure concordent.

**Maillon limitant : le hub, pas le backend.** Preuve décisive : `:1234` contourné du hub encaisse **16 flux à 100 % de succès** (p95 26,8 s) pendant que le hub perd 66 % à 10. LM 

[assistant] Ces données permettent de tester une hypothèse que mes mesures ne pouvaient pas trancher seules : le sur-routage vers le backend lent est-il une cause indépendante, ou une conséquence du sémaphore à 1 ? Le champ `errs` du log devrait le dire.

[assistant] La table ingérée ne garde que `ts, via, served, ms, ok, tried, chars` — pas `errs` ni `overloaded`. La causalité est dans le JSONL brut. J'attaque les deux sources en parallèle.

[assistant] Deux résultats majeurs. Je teste maintenant l'hypothèse du team lead sur le choix de destination — car `ms` est mesuré depuis le début de la cascade (`chat_proxy.js:315` puis `:326`), pas depuis l'appel au backend.