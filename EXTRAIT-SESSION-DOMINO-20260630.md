# EXTRAIT SESSION — Neutralisation boucle JARVIS DOMINO

> Date : 2026-06-30 · Machine : M4 (pamerys) · Déclencheur : check autonome `/loop` → alerte RAM 98 %

## Contexte / cause racine
Le moteur **JARVIS DOMINO** + `jarvis-cowork-loop` + `jarvis-cowork-dispatcher`
(services `systemctl --user`) tournaient depuis ~12 h en **boucle de rétroaction** :
FLOW CHECK lit ses propres alertes RAM/CPU → déclenche des chaînes
(`crash-guardian`, `service-auto-repair`, `auto-debug`, `openclaw-router`…)
→ chaque chaîne lance `lm-ask --big` → `curl qwen2.5:7b` sur Ollama CPU **muet**
→ ~22 `lm-ask` empilés → RAM saturée (594 Mi libre, OOM imminent) → nouvelles alertes.

## Série d'actions logiques directes (chronologie réelle)

| # | Action | Commande clé | Résultat |
|---|--------|--------------|----------|
| 1 | Diagnostic RAM + process | `free -h` ; `ps aux --sort=-%mem` | 503 Mi libre, ollama 2,5 Go, 56 match boucle |
| 2 | Identifier les `lm-ask` empilés | `ps -eo pid,ppid,etime,args \| grep lm-ask` | chaînes DOMINO crash-guardian/auto-debug |
| 3 | Sonder la cascade | `timeout 45 lm-ask.sh "test"` → EXIT 124 | cascade locale **muette** |
| 4 | Trouver le maître | parent = `jarvis/domino/service.py` PID 6083, parent `systemd --user` (6024) | service **--user**, pas système |
| 5 | Stop niveau --user | `systemctl --user stop jarvis-domino jarvis-cowork-loop jarvis-cowork-dispatcher` | cgroup nettoyé, enfants tués |
| 6 | **Piège `Restart=`** | stop seul → systemd **respawn** une nouvelle instance (PID 2944281) | « masked active running » |
| 7 | Masquage durable réversible | backup unités → `~/.jarvis-legacy-backup/2026-06-30-boucle-domino/` puis `systemctl --user mask …` | 3 services `masked` |
| 8 | Tuer l'instance déjà lancée | `systemctl --user stop` + `kill -s SIGKILL jarvis-domino` | 0 process réel après ~8 s |
| 9 | Nettoyer l'état failed | `systemctl --user reset-failed jarvis-domino` | 0 service en échec |
| 10 | Logger le playbook | `INSERT INTO commands … entity '90-anti-boucle'` (`~/jarvis/stacks/jarvis-index.db`) | 292 → 294 commandes |

## Garde-fous rencontrés (auto-mode classifier)
- `pkill -9` de masse → **bloqué** (Interfere With Workloads). Solution : `systemctl --user stop` nettoie le cgroup tout seul.
- Déplacement/mask des unités sans autorisation explicite → **bloqué**. Débloqué après validation utilisateur ciblée.

## Séquence qui marche en 1 coup (à réutiliser)
```bash
systemctl --user mask jarvis-domino jarvis-cowork-loop jarvis-cowork-dispatcher
systemctl --user stop jarvis-domino jarvis-cowork-loop jarvis-cowork-dispatcher
systemctl --user kill -s SIGKILL jarvis-domino 2>/dev/null
sleep 8 && pgrep -fc domino/service.py   # doit = 0
systemctl --user reset-failed jarvis-domino
```

## État final vérifié
- domino : `inactive / masked` (ne peut plus redémarrer)
- 0 process boucle, 0 `lm-ask`, 0 service `--user` en échec
- RAM : 594 Mi → **~4 Gi** libre, stable sur 3 vérifications successives

## Réversibilité
`systemctl --user unmask jarvis-domino jarvis-cowork-loop jarvis-cowork-dispatcher`
+ restaurer les `.service` depuis `~/.jarvis-legacy-backup/2026-06-30-boucle-domino/`.

## Liens
- Mémoire : `m4-dispatch-flux-ondemand` (mise à jour), `m4-surchauffe-overclocking`
- Bibliothèque : `jarvis-index.db` table `commands` entity `90-anti-boucle`
