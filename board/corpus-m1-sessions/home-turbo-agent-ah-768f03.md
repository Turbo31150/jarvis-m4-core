[assistant] Je commence par lire le proxy en entier, puis j'attaque le journal et les clients.

[assistant] Diagnostic terminé. Voici le rapport.

## Ce que montre la mesure

La saturation n'est pas un défaut du hub : c'est un écart d'échelle entre ce que les clients envoient et ce que le hub accepte. **Le hub tolère 5 requêtes simultanées ; `jarvis-prod-runner.py` en lance 12 à lui seul, toutes les 15 minutes.** Le message `surcharge (file d'attente active)` est le hub qui refuse la 6ᵉ à la 9ᵉ requête — 74 % des échecs sont des rejets en moins de 0,5 s, sans qu'aucun backend n'ait été sollicité.

## Carte de la gestion de charge (`/home/turbo/jarvis/scripts/chat_proxy.js`)

| Mécanisme | Lignes | Valeur |
|---|---|---|
| Classe `Semaphore` | 79-105 | par backend, jamais globale |
| Limite LM Studio | 111-112 | **1** simultanée |
| Limite `ollama` / `rem-linux` | 113-117 | **2** simultanées |
| Limite par défaut (cloud, gemini) | 110 | 999 |
| File d'attente | 90-92 | **1 seule** requête en attente, la suivante est rejetée |
| Message de rejet | 131 | `${b.name} surcharge (file d'attente active)` |
| Timeout socket | 161 | 90 000 ms **par backend**, cumulatif sur la cascade |
| Timeout d'attente en file | — | **aucun** : un client en file attend indéfiniment |
| Retrait des clients partis | — | **aucun** : ni `req.on('close')`, ni `aborted` (seuls `'data'`/`'end'` sont écoutés, l. 255-256 et 282-283) |
| Cache / dédoublonnage | — | **aucun** (0 occurrence de « cache » dans le fichier) |
| Code retour en surcharge | 272, 293 | `502` — indiscernable d'une panne réelle, donc les clien

[assistant] Rapport L13 transmis à `main` via SendMessage.

**Résumé de ce qui a été envoyé :** le hub `:18800` tolère 5 requêtes simultanées (1 pour LM Studio, 2 pour Ollama, 2 pour rem-linux, plus 1 en file chacun), tandis que `jarvis-prod-runner.py` en lance 12 à lui seul toutes les 15 minutes (`MAX_PARALLEL = 12`, ligne 52). C'est l'origine directe du message `surcharge (file d'attente active)` (`chat_proxy.js:131`) : 74 % des échecs sont des rejets en moins de 0,5 s, sans qu'aucun backend n'ait été sollicité.

Deux chiffres qui cadrent le gaspillage : 14,6 h de génération par jour sont livrées après le timeout client de 90 s (soit 32 % du temps de service produit pour personne, faute de détection d'abandon dans le proxy), et le temps de service cumulé atteint 46,2 h sur une journée de 24 h.

Le correctif le plus rentable est d'une ligne — ramener `MAX_PARALLEL` à 3 — sans toucher au hub. Vient ensuite l'ajout d'un `req.on('close')` et d'un code 429 distinct du 502, puis, une fois le log instrumenté avec un hash de prompt, un éventuel cache court (les tâches sont dupliquées à 91 %).

Aucun fichier modifié, aucun service redémarré. La tâche #15 (L13) reste `pending` — les propositions attendent l'arbitrage de `main`.