[user] Tu diagnostiques un problème d'authentification sur la machine `rem-linux` (poste Linux de Rémi, /home/rempc). Réponds en français.

## Le problème

Un serveur Ollama tourne en local sur `http://127.0.0.1:11434`. Il expose 5 modèles :

```
glm-5.2:cloud              756B   (modèle proxié vers https://ollama.com:443)
gemma3:27b                 27.4B  17.4 Go   (poids locaux)
gemma3:4b                  4.3B    3.3 Go   (poids locaux)
qwen3:1.7b                 2.0B    1.4 Go   (poids locaux)
mxbai-embed-large:latest   334M           (embeddings)
```

`glm-5.2:cloud` est un modèle **proxié vers le cloud Ollama** : il ne consomme pas le CPU local. C'est de loin le plus puissant du parc (756 milliards de paramètres). C'est donc celui qui aurait le plus de valeur.

**Mais il est muet.** Un appel `POST /api/chat` avec ce modèle échoue en 0,9 seconde — donc un rejet immédiat, pas un timeout. Les modèles à poids locaux, eux, répondent correctement (`gemma3:4b` répond, quoique lentement : 79 s pour 20 tokens, la machine n'ayant pas de GPU exploitable).

Hypothèse de départ, à confirmer ou infirmer : il manque une clé d'API Ollama Cloud, ou elle a expiré.

## Ta mission

1. Reproduis l'échec et **capture le message d'erreur exact** renvoyé par l'API. Exemple d'appel :
```bash
curl -s http://127.0.0.1:11434/api/chat -d '{"model":"glm-5.2:cloud","stream":false,"messages":[{"role":"user","content":"Dis PRET."}]}'
```
Compare avec le même appel sur `qwen3:1.7b` qui, lui, fonctionne.

2. Dét

[assistant] Key finding: it's a **403 subscription** error, not an auth failure. Let me dig deeper and check the docs.

[assistant] Let me query the docs and run a decisive test: unauthenticated call directly to ollama.com for comparison.

[assistant] Diagnostic terminé. Rapport écrit dans `/home/rempc/bibliotheque-vivante/rapports/diag-ollama-cloud.md`. Aucun autre fichier touché, aucune commande d'authentification exécutée, aucun secret lu.

**L'hypothèse de départ est infirmée. Ce n'est pas un problème de clé.**

## 1. Message d'erreur exact

```
HTTP/1.1 403 Forbidden
Server: Google Frontend
{"error":"this model requires a subscription, upgrade for access: https://ollama.com/upgrade (ref: baf0c9ae-efb2-48d2-a933-9b0a08b27994)"}
```

Reproduit deux fois (403 en 0,14 s et 0,54 s). Le contrôle `qwen3:1.7b` renvoie bien `HTTP=200` en 2,67 s.

Trois éléments prouvent que **l'authentification fonctionne** :
- Le 403 vient d'ollama.com (en-têtes `Google Frontend`, `X-Cloud-Trace-Context`) : la requête a été relayée **et acceptée comme authentifiée**.
- Un appel direct à `https://ollama.com/api/chat` **sans** clé renvoie `401 Unauthorized` — une erreur différente. Idem avec un bearer bidon.
- **`gpt-oss:120b-cloud` répond en HTTP 200 en 1,20 s depuis cette machine**, texte généré.

Cause racine : `glm-5.2:cloud` est classé « **High Usage** » sur sa page officielle. Le plan Free donne accès aux modèles cloud légers ; le plan Pro ($20/mois) donne accès aux « larger, more powerful cloud models ». Le compte est sur Free, glm-5.2 est au-dessus de l'enveloppe. C'est un gate tarifaire, pas une panne.

## 2. Version et lancement

`ollama version is 0.30.6`. Service systemd `ollama.service` (`/etc/systemd/system/ollama.service`, enable