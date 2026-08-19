[assistant] Charge 27.9 sur M6 (11 Go RAM, 9 Go de swap consommé) + un service `m6-server-watch` en échec. Je creuse.

[assistant] Diagnostic clair : **saturation mémoire** (pression `full avg60=53%` → la machine est bloquée la moitié du temps en I/O swap). Tout est en D-state. C'est l'incident connu. Je regarde l'outil de relief et le service en échec.

[assistant] Compris — je répare, puis transfert + upgrade M4. Le service en échec dit justement « lien câble direct M6↔M4 absent ». Je vérifie le lien.

[assistant] M4 est joignable via Tailscale (`100.124.121.16`, idle) mais le **câble direct `enp3s0` est DOWN**. Je vérifie le porteur physique et je cherche l'outil de relief.

[assistant] **Le câble direct est physiquement débranché** (`Link detected: no`) — ça n'est pas réparable en logiciel. Mais M4 répond via Tailscale, donc le transfert passera par là. Je lance le relief mémoire et je sonde M4 en parallèle.

[assistant] Relief efficace : 1,5 → 4,1 Go libres, swap 9 → 4,8 Go, pression 44 → 32 %. Maintenant M4 : je sonde l'accès et je lis le dispositif de transfert existant.

[assistant] Pas d'entrée `m4` dans la config SSH — d'où l'échec (l'agent propose 6 clés, M4 coupe). Je teste les accès et je lis le dispositif de transfert existant.

[assistant] Accès trouvé : **`pamerys@pamerys-m4` avec la clé `jarvis_cluster`**. Je le rends permanent dans la config SSH, puis j'inventorie M4.

[assistant] Il existait déjà une entrée `m4` pointant sur le câble mort. Je lis la fin du fichier.

[assistant] L'ancien bloc code en dur l'IP du câble mort. Je le corrige pour basculer sur Tailscale, et je supprime le doublon que je viens d'ajouter.

[assistant] Pas de doublon (l'ajout avait été court-circuité). J'ajoute juste l'alias câble et je valide l'accès.

[assistant] M4 est sain : 12 cœurs, 15 Go, load 1,55 — contre load 27 sur M6. Je lis le dispositif de transfert déjà en place.

[assistant] Architecture claire : M6 sert ses ressources à M4 par le câble — câble mort, donc toute la couche d'exposition boucle en échec. Je pose le plan.

[assistant] M4 : Ubuntu 24.04.4, sudo sans mot de passe, **29 mises à jour** dont le pilote NVIDIA (595.71→595.84) et le noyau (6.17→7.0.0-29, celui que M6 tourne déjà). Je lance l'upgrade en arrière-plan pendant que je répare le crash-loop.

[assistant] Je répare : le script doit basculer sur Tailscale quand le câble est absent, et ne plus échouer quand aucune voie n'existe.

[assistant] Maintenant `action_up`, pour qu'il ne sorte plus en erreur quand aucune voie n'existe.

[assistant] Reste à initialiser `VOIE` (le script est en `set -u`) et à faire lire l'IP aux relais.

[assistant] Repli Tailscale opérationnel, exit 0. Test décisif : est-ce que M4 les atteint réellement ?

[assistant] Les 7 services sont joignables depuis M4. Je remets le timer et je vérifie qu'il ne tombe plus en échec.

[assistant] `Result=success`, plus aucun service en échec. Je clos la réparation et je regarde l'upgrade M4.

[assistant] Upgrade réussi : noyau 7.0.0-29 installé, GRUB régénéré, **redémarrage requis**. Je vérifie l'état post-upgrade.

[assistant] GPU M4 inutilisable jusqu'au reboot (NVML mismatch, attendu), et **une session tmux active à 7 panes + une session graphique**. Je regarde ce qui tourne avant de parler de redémarrage.

[assistant] M4 fait déjà tourner une pile JARVIS (hub `18800`, n8n, ollama, gateway OpenClaw) — et `18800` est justement **hors service sur M6**. Le transfert documenté (config MCP vers M4) prend tout son sens. Je vérifie l'état.

[assistant] La config MCP posée sur M4 date du 15 août et pointe sur l'IP du câble mort. Je vérifie l'ampleur.

[assistant] Deux vraies cassures sur M4 : **13 références à l'IP du câble mort**, et surtout `Host m6` qui pointe sur **`127.0.0.1`** (config recopiée telle quelle — M4 croit que M6 c'est lui-même). Je teste d'abord si M4 peut joindre M6 en SSH.

[assistant] `ssh m6` depuis M4 atteint enfin M6. Je régénère la config MCP sur la bonne IP et je contrôle ce qui est réellement lançable.

[assistant] 9 serveurs générés, plus aucune référence morte. 4 sont écartés à cause du dossier verrouillé root — le point non résolu du README. Je tente la correction.

[assistant] Découverte : le dossier est **vide**. La correction annoncée dans le README (`chown`) n'aurait rien réglé — ce ne sont pas les droits, c'est le contenu qui a disparu. Je cherche où sont réellement ces serveurs.