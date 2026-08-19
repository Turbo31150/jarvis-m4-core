[user] peut tu lire le mail de franck sur remten341 il a envoye du lourd en reponse a notre mail d hier

[assistant] Lu. Mail de Franck : **uid 484, mercredi 29/07 à 23:37**, en réponse à ton mail AI Act (qui datait du **18/07**, pas d'hier — c'est *sa réponse* qui est d'hier soir).

## Ce qu'il a envoyé

Pas une réponse à ton mail. Un **rapport d'analyse + un brouillon de post LinkedIn** sur une session Claude Code, visiblement produit par une IA à partir de captures d'écran (« Les captures d'écran analysées révèlent… »).

Le contenu :
1. **Récit technique** — une seule commande via un « connecteur reliant l'infrastructure Microsoft au système Jarvis », qui déclenche en autonomie : rapport d'analyse complet (méthodo + erreurs), descriptions vidéo + voix off IA, et analyse d'archi du dépôt `jarvis git:(feat/autoapi-enrichment-ssrf*)`.
2. **Chiffres avancés** — 100+ sous-agents par arborescence (85/101 et 105/108 en double session), pics à **6,7M tokens en < 20 min**, coût **1,29 $ à 2,79 $** par arborescence, attribué au prompt caching d'« Opus 5 ».
3. **Post prêt à publier** — titre « L'illusion de la puissance locale : quand un simple connecteur et UN SEUL prompt déploient plus de 100 agents IA », avec hashtags `#ClaudeCode #Anthropic #Opus5 #AIAgents #DevOps`.

## Lecture

**Le vrai signal : il n'a répondu à rien.** Zéro mot sur l'Art. 50, zéro sur le garde-fou commercial, et surtout **zéro sur « où tu en es côté moteur »** — ta seule question directe. Il est parti sur la vitrine.

**Et l'échéance mord maintenant** : tu lui écrivais « dans ~15 j » pour le 02/08/2026. On est le 30/07 → **

[user] je veut surtout que tu analyses ce qu il fait sur sa machine la performance et qu on reproduise a notre sauce sa mathode , si besoin genere lui un prompte qui balance dans son terminal pour qu il nous donne la recette ( mode emploi ) que tu pourra reproduire pour des sessions hors du commun c est ca l idee

[assistant] Bonne piste — et il y a un truc important à voir avant de lui écrire. Je probe d'abord notre machine pour que le prompt qu'on lui envoie pointe sur des chemins réels, pas inventés.

[assistant] Les captures sont en PJ du mail — `jarvis-mail read` ne les sort pas. Je regarde si le lecteur IMAP sait extraire les pièces jointes.

[assistant] Il n'y a aucun support pièces jointes dans le lecteur IMAP. Je forge l'outil manquant (réutilisable), puis j'extrais.

[assistant] Trouvé : 2 captures + une vidéo `preuve.mp4` (10,9 Mo). Je regarde les captures.

[user] [Image: original 3840x2160, displayed at 2000x1125. Multiply coordinates by 1.92 to map to original image.]

[assistant] Ça change tout — ce n'est pas ce que le mail raconte. Deuxième capture + un probe décisif sur l'identité de ce dépôt.

[user] [Image: original 3840x2160, displayed at 2000x1125. Multiply coordinates by 1.92 to map to original image.]

[assistant] Maintenant j'ai la vraie mécanique — et elle ne ressemble pas au mail. Je vérifie notre écart de config avant d'écrire le prompt d'extraction.

[assistant] Analyse solide maintenant. J'écris le prompt d'extraction, calé sur des chemins que j'ai vérifiés sur notre machine (même layout Claude Code).

[assistant] Il y a aussi `preuve.mp4` (10,9 Mo) — j'en extrais des images clés, ça peut contenir le prompt de départ.

[user] [Image: original 1600x2866, displayed at 1117x2000. Multiply coordinates by 1.43 to map to original image.]

[assistant] Désolé — je creusais parce que le mail racontait n'importe quoi et je refusais de te sortir une recette inventée. C'est bouclé. Voilà le net.

## 1. Ce qu'il fait vraiment (lu sur les captures, pas dans le mail)

Statusline, deux sessions en parallèle, 29/07 15:24→15:28 :

```
[Opus 5 (1M context)] jarvis git:(feat/autoapi-enrichment-ssrf*)  Cost $1,29 → $2,33 → $2,79
Context 43% → 77% → 93% (0k/1,0M)     Usage 19% → 84% (resets in 3h 9m)
bypass permissions on · auto mode on · 3 shells · ←1 agent
deep-research … 85/101 agents done · 15m51s · ↓6.1m tokens · ⚠ Large workflow
deep-research … 105/108 agents done · 19m14s · ↓6.7m tokens · /workflows to stop
```

**La recette tient en 5 briques, toutes locales :**
1. Claude Code CLI, **Opus 5 en fenêtre 1M** (c'est le seul vrai levier matériel du truc)
2. le skill **`deep-research`** qui appelle l'outil **Workflow** → fan-out 101–108 sous-agents
3. **bypass permissions + auto mode** → aucune interruption pendant 20 min
4. **statusline maison** (modèle / branche / coût / contexte / usage / reset)
5. **2 sessions simultanées** sur le même dépôt, + une cascade avec fallback `429 → ChatGPT gpt-5`

**Le mail est faux sur le point central.** Il n'y a aucun « connecteur Microsoft », aucun calcul déporté, aucune « illusion de puissance locale ». C'est Claude Code en local qui tape l'API Anthropic. L'IA à qui il a donné les captures a inventé toute la narration. Si tu publies ce post, c'est ce claim-là qui s'effondre en premier — exactement

[assistant] Go. Je vérifie deux points avant de toucher à la config — dont un où je me suis peut-être trompé.

[assistant] Une correction importante, et je boucle. Grep ciblé + rédaction du mail en parallèle.

[assistant] Config 1M posée (backup `settings.json.bak-1mctx-20260730`). Maintenant le mail.

[assistant] Insert silencieusement perdu — `docker exec` sans `-i` ne transmet pas stdin. Je corrige.

[assistant] Les deux sont faits.

## Mail envoyé ✅
Vérifié au sol : `[Gmail]/Messages envoyés` uid 16, 30/07 10:30, threadé sur son message (`In-Reply-To` correct), PJ `PROMPT-EXTRACTION-RECETTE-SESSION-XXL.md` attachée.

Contenu : le recadrage sur le connecteur Microsoft inventé (avec sa statusline citée noir sur blanc), la correction abonnement-vs-dollars — et je lui ai retourné la punchline vendable à la place : *« 20 minutes de mur de quota pour 6,7M tokens et 108 agents »*, celle-là est incontestable. Puis la demande de recette, la relance moteur, et l'Art. 50 à J-3.

Au passage j'ai dû forger `~/jarvis/scripts/mail/fetch-attachments.py` : notre lecteur IMAP ignorait totalement les pièces jointes, c'est pour ça qu'on ne voyait ni les captures ni la vidéo depuis le début.

## Config ✅ — mais je me suis planté sur un point, et je le dis

**Mon « manque n°1 » n'existait pas.** Je t'ai annoncé que `/deep-research` chez nous tombait sur la méthodo 6 phases et qu'on n'avait pas le harness. Faux : le harness est **dans le binaire `claude`**, les deux skills coexistent en namespaces séparés (`deep-research` vs `jarvis:deep-research`) — et **on a déjà tourné avec**, j'ai retrouvé nos propres `deep-research-wf_*.js` persistés dans 4 sessions, dont une du 9 juillet. J'avais conclu depuis un seul `find` limité à `~/.claude`, sans regarder le binaire ni nos traces d'exécution. C'est noté en post-mortem dans l'atome.

**Le vrai manque, unique :** la fenêtre 1M. Corrigé — `settings.json` : `claude

[assistant] 1M confirmé actif. Je note ça en mémoire et il ne reste qu'à choisir sur quoi on brûle le premier run.

[assistant] **Parité atteinte.** On a exactement sa config : harness `deep-research` + outil Workflow + bypassPermissions + statusline maison + fenêtre 1M. Il ne manque que ses scripts de workflow (demandés par mail) pour comparer les stratégies de fan-out.

Un avertissement avant de tirer : Franck a brûlé **84 % de son quota 5h en 20 minutes**. Un run XXL, c'est ta session de la matinée. Donc autant le pointer sur quelque chose qui rapporte.

[assistant] Bon choix — on instrumente avant d'engager un vrai sujet. Et je vais faire en sorte que le run « à blanc » produise quand même quelque chose d'utile : les 100 agents vont cartographier **notre propre stack**, ce qui nous donne pile la base de comparaison avec Franck.

[assistant] Détail révélateur : **8 cœurs → concurrence plafonnée à 6 agents simultanés** (`min(16, cores-2)`). Les « 108 agents » de Franck sont donc une **file**, pas 108 en parallèle. Ça recadre déjà son récit. Je lance.

[assistant] C'est parti. **Run `wq9kggi58`** en fond.

**Ce qui tourne :** 104 agents de sonde (lecture seule stricte, garde-fou anti-mutation dans chaque prompt), en **pipeline** — chaque anomalie déclarée part immédiatement chez un refuteur adversarial pendant que les autres sondent encore, puis 7 synthèses par groupe et une carte finale. Soit ~115 agents au total, à comparer aux 108 de Franck.

Les 7 groupes sondés : cœur Claude Code (14), serveurs MCP (18), conteneurs Docker (19), Postgres (12), scripts JARVIS (15), plugins/skills (10), système (10), divers (6).

`/workflows` pour suivre en direct.

**À quoi t'attendre :** avec 6 agents concurrents et ~17 vagues, compte **15 à 25 min** — dans le même ordre que ses 19m14s. Le nombre de tokens sera plus bas que ses 6,7M parce que nos agents lisent du disque local au lieu de fetcher du web, mais agents / durée / erreurs seront directement comparables.

Deux choses à la fin :
1. **Les mesures réelles** du run, que je recalculerai depuis le journal (`journal.jsonl`) et le transcript — pas depuis la statusline. C'est notre base de comparaison honnête avec Franck.
2. **Une carte de capacités de la machine** + les anomalies qui ont survécu à la réfutation. Le run « à blanc » sort quand même un livrable exploitable.

Je te préviens quand c'est fini. En attendant, garde un œil sur ton quota : la statusline te dira où tu en es.