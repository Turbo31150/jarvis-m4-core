[assistant] Le `--list` confirme les 3 succès du jour (n8n, grafana, vaultwarden = 1 montage). Je vérifie le `--dry-run` sur un service encore volatile.

[assistant] Le driver 1 est validé en lecture. J'écris maintenant le second driver, la garde de cascade.

[assistant] Les deux drivers passent en lecture. J'écris les SKILL.md avec les sorties réelles.

[assistant] Les deux skills sont créés, exécutés en lecture et enregistrés partout.

## Ce qui a été créé

**`/home/turbo/.claude/skills/run-swarm-persistance/`** (`SKILL.md` + `driver.sh`) — enveloppe `/home/turbo/jarvis/scripts/swarm-persistance.sh`. Trois modes : `--list` (services Swarm sans volume, lecture seule), `--dry-run <service> <chemin>` (localise et mesure, étapes 1-2 seulement), `--run` (délègue au script réel). Le SKILL.md documente le piège central — monter le volume d'abord masque la base, et un volume préexistant peut être vide (`jarvis_n8n_data` avec un `database.sqlite` de 0 octet) — ainsi que le tableau des 6 étapes et les trois succès du jour (n8n 5,7 Mo `1000:1000`, grafana 50 Mo `472:0`, litellm N/A).

**`/home/turbo/.claude/skills/run-cascade-guard/`** (`SKILL.md` + `driver.sh`) — `--check` compare les trois vues (drop-in systemd, `/proc/<MainPID>/environ`, ligne `[proxy] cascade:` du journal) et lève une alerte rouge si `rem-linux` est en tête ; `--fix` documenté mais non exécuté. Le SKILL.md pose que l'ordre vit dans le drop-in systemd **utilisateur**, pas dans `openclaw.json`, et raconte l'incident du 2026-08-01 (charge 24/8, `llama-server` à 370 % CPU, manager Swarm co-hébergé en `DeadlineExceeded` — donc plus aucun `docker service update` possible).

## Sorties réelles obtenues

`--list` a trouvé **6 services volatiles sur 9** ; les trois à 1 montage sont exactement le travail déjà fait (n8n, grafana, vaultwarden). `--dry-run` sur `jarvis-full-stack_promethe

[assistant] Rapport transmis à `main`.

**Livrables** : `/home/turbo/.claude/skills/run-swarm-persistance/` et `/home/turbo/.claude/skills/run-cascade-guard/`, chacun avec `SKILL.md` + `driver.sh` exécutable.

**Vérifications réelles** : `--list` a trouvé 6 services Swarm volatiles sur 9, les 3 restants étant exactement le travail du jour (n8n, grafana, vaultwarden à 1 montage) ; `--dry-run` sur `jarvis-full-stack_prometheus` a mesuré 450 896 octets, ce qui en fait un quatrième candidat légitime ; `--check` a rendu un verdict vert avec les trois vues concordantes et `lmstudio-m1` en tête. Les sorties intégrales sont collées dans les SKILL.md.

**Enregistrement** : 2 triggers priority 6 dans `skill-triggers.json` (49 au total, JSON revalidé, sauvegarde `.bak.20260801-231056`), et 2 blocs `skill-live` dans `session-20260801-blocs.tsv` puis `BLOCS-INDEX.tsv`, sans doublon.

Deux réserves signalées dans le rapport : `--fix` et `--run` n'ont pas été exécutés conformément à la consigne production, donc `--fix` reste non éprouvé en conditions réelles ; et l'index contient des doublons `session-20260801` antérieurs à mon intervention (17 lignes pour 12 dans la source).