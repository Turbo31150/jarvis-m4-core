[assistant] Le fichier n'expose aucune route `/api/embeddings` — je vérifie l'émetteur réel avant d'éditer.

[assistant] Émetteur identifié : `biblio-vectorize.timer`, pas le hub. Je passe aux modifications du code.

[assistant] Le déclenchement est prématuré : `req.on('close')` se déclenche dès la fin de lecture du body, pas seulement à l'abandon. Je corrige le garde.

[assistant] Test B validé (`ms:2002`, backend ollama). Je vérifie la libération du slot et le format du log.

[assistant] Les trois tests passent. Je vérifie maintenant le 429 sous saturation réelle, et que la génération est bien coupée côté backend.

[assistant] Le 429 fonctionne (9 rejets immédiats en ~2 ms). Je vérifie le corps de la réponse et l'annulation côté backend.

[assistant] DONE. Le hub `/home/turbo/jarvis/scripts/chat_proxy.js` est corrigé, redémarré et vérifié en production (316 → 441 lignes, sauvegarde `chat_proxy.js.bak-20260801-hubfix`).

## Modifications par bloc

**Abandon client (points 1)** — Ajout d'un contexte de requête `makeCtx(req)` (nouveau, ~l. 145-175) porté jusqu'à `callBackend`. Chaque route POST attache deux écouteurs : `req.on('close')` gardé par `!req.complete` et `res.on('close')` gardé par `!res.writableEnded`. Sur abandon, la requête sortante est détruite (`r.destroy()`), le sémaphore est libéré via le garde `released` existant, et une ligne `client_gone` est journalisée avec le temps dépensé. Le `Semaphore` (l. 83-118) accepte désormais un `ctx` : une entrée en file marquée annulée est sautée par `release()`, donc un client parti en attente ne consomme jamais de slot.

Un piège important est apparu au premier essai : `req.on('close')` est émis par Node dès que le corps de la requête est entièrement lu, pas seulement à l'abandon. La première version tuait donc **toutes** les requêtes (`client_gone` avec `ms:0`, curl pendu 120 s). Le garde `!req.complete` corrige cela — c'est `res.on('close')` qui porte le cas réel « client parti pendant la génération ».

**429 distinct du 502 (point 2)** — Les rejets de sémaphore portent un flag `overload`. `route()` (l. 296-346) suit un `overloadOnly` qui reste vrai tant qu'aucun backend n'a été réellement essayé ; la fonction `respondError()` répond alors 429 + `Retry-After: 20`. Le 50

[assistant] Rapport transmis au team-lead. Synthèse de ce qui a été livré :

**Statut DONE.** Le hub `/home/turbo/jarvis/scripts/chat_proxy.js` est corrigé (316 → 441 lignes), sauvegardé en `.bak-20260801-hubfix`, validé par `node --check`, redémarré et actif — aucune exception dans le journal, aucun rollback nécessaire.

Les trois modifications demandées sont en place : libération du slot sur abandon client (avec destruction de la requête sortante et ligne `client_gone` horodatée), réponse `429 + Retry-After: 20` quand tous les backends refusent pour surcharge, et champs `phash` / `client` ajoutés à toutes les lignes du log de cascade sans rien retirer du format existant.

Les trois tests passent avec sorties réelles : requête normale `200` en 0,76 s ; abandon à 2 s produisant `{"event":"client_gone","stage":"inflight","ms":2002}` suivi d'une requête servie en 0,88 s (slot bien rendu) ; `phash` et `client` présents sur toutes les nouvelles lignes. Un test de saturation supplémentaire a prouvé le 429 : 9 requêtes sur 12 rejetées en environ 2 ms au lieu d'attendre 90 s pour un 502.

Deux points méritent ton attention. D'abord un piège rencontré en cours de route : ma première version gardait `req.on('close')` par `!res.writableEnded`, or Node émet cet événement dès que le corps est lu — toutes les requêtes étaient tuées avec `ms:0` et le curl restait pendu 120 s. Le garde correct est `!req.complete`, et c'est `res.on('close')` qui porte le vrai cas d'abandon. Corrigé et revérifié.

Ensuit