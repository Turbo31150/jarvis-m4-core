[user] Contexte : le script ~/jarvis/scripts/jarvis-autopublisher.py prétend publier sur LinkedIn, Twitter, Telegram et GitHub. En réalité il ne publie RIEN, et pire, il se déclare toujours en succès. Preuves déjà établies :
- LinkedIn : tente un conteneur docker « jarvis-linkedin-safe » qui n'existe pas, puis un publish.py, puis écrit un simple .txt dans ~/jarvis/content_buffer/ et retourne True.
- Twitter : n'essaie même pas de poster, écrit un .json et retourne True.
- Telegram : le token du coffre renvoie 401 Unauthorized, et le code affiche « OK » même sur sortie vide.
Chaque fonction retourne True inconditionnellement, c'est pourquoi tout test se déclare « 100 % réussi, zéro erreur ».

C'est dangereux : on peut croire que du contenu part sur les réseaux alors que rien ne sort.

Ta mission — corriger l'honnêteté du script, PAS ajouter de vraie publication :
1. Lis ~/jarvis/scripts/jarvis-autopublisher.py en entier.
2. Fais-en une sauvegarde datée.
3. Modifie-le pour que chaque fonction retourne un statut VRAI : succès seulement si la publication a réellement eu lieu, et un statut distinct et explicite « MIS EN FILE » quand le contenu est seulement écrit sur disque. Un canal non câblé doit le DIRE, pas simuler un succès.
4. Le résumé final doit distinguer clairement ce qui est publié de ce qui est en attente, et sortir avec un code non nul si l'utilisateur a demandé une publication qui n'a pas pu avoir lieu.
5. Pour Telegram : vérifie réellement la réponse de l'API et signale le

[assistant] Now let's test. First the honest status view, then the actual publication paths.

[assistant] Le script est corrigé, testé et la sauvegarde datée est en place.

## Fichiers
- Script corrigé : `/home/pamerys/jarvis/scripts/jarvis-autopublisher.py`
- Sauvegarde datée : `/home/pamerys/jarvis/scripts/jarvis-autopublisher.py.bak-20260814-133051`

## Ce que j'ai confirmé avant de toucher au code
| Élément | Réalité mesurée |
|---|---|
| Conteneur `jarvis-linkedin-safe` | **absent** de `docker ps -a` (l'ancien code faisait quand même `docker exec` puis avalait l'exception) |
| `scripts/publish.py` | existe, `browseros-cli` aussi → il **peut** réellement poster sur LinkedIn |
| `scripts/telegram_alert.py` | n'imprime rien sur stdout et sort toujours en 0 → l'ancien `res.stdout.strip() or 'OK'` affichait **« OK » sur sortie vide** |
| Token Telegram | absent de l'environnement, présent dans le coffre sops (`TELEGRAM_TOKEN`) → **HTTP 401 Unauthorized** confirmé en direct |
| `--channel github` | accepté par l'argparse mais **jamais traité** dans `publish_pack` : succès silencieux total |

## Avant / après

**Avant** (rejoué depuis la sauvegarde, canal telegram) :
```
✈️ [Telegram] Diffusion en cours...
   -> Résultat Telegram : [TELEGRAM] No token/chat_id — would send: ...
EXIT_AVANT=0
```
Rien n'est parti, aucun signal d'erreur, code de sortie 0.

**Après**, mêmes conditions :
```
❌ telegram : ÉCHEC — API refusée — HTTP 401 : Unauthorized (identifiants : coffre sops)
   → token révoqué/invalide, régénérer via BotFather puis mettre à jour le coffre
     · tentative : POST api.t