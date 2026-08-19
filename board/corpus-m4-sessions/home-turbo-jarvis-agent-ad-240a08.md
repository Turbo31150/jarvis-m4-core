[user] Contexte : environnement JARVIS fraîchement (re)provisionné — des unit files systemd existent mais les scripts qu'ils référencent (ExecStart=) n'ont jamais été écrits sur cette machine. Tu dois RECONSTRUIRE ces scripts, de façon sûre et non destructive.

Écris exactement ces fichiers (bash, exécutables chmod +x) :

1. `/home/turbo/jarvis/scripts/hub-healthcheck.sh` — vérifie la santé du hub LLM local (curl http://127.0.0.1:1234/v1/models et http://127.0.0.1:18800/v1/models si dispo), log résultat dans `/home/turbo/jarvis/logs/hub-healthcheck.log` avec timestamp, exit 0 toujours (monitoring ne doit jamais faire échouer le service).

2. `/home/turbo/IA/Core/jarvis/scripts/system-crash-guardian.sh` — vérifie `journalctl --user -p err -n 20 --no-pager` et `dmesg | tail -20 | grep -i "oops\|panic"`, log dans `/home/turbo/jarvis/logs/crash-guardian.log`, exit 0 toujours.

3. `/home/turbo/jarvis/.claude/skills/run-jarvis-autoheal/jarvis_autoheal.sh` — liste `systemctl --user --failed`, pour chaque service failed tente `systemctl --user reset-failed <service>` PUIS `systemctl --user restart <service>` seulement si le service n'a pas déjà échoué >3 fois dans les 10 dernières minutes (évite boucle infinie), log dans `/home/turbo/jarvis/logs/autoheal.log`, exit 0.

4. `/home/turbo/jarvis/scripts/kernel-oops-sentinel.sh` — surveille `dmesg` pour "Oops", "BUG:", "kernel panic", log alertes dans `/home/turbo/jarvis/logs/kernel-oops.log`, exit 0.

5. `/home/turbo/jarvis/bin/gpu-circuit-brea

[assistant] Found a bug: autoheal parses `systemctl --user --failed --no-legend` wrong — first column is the bullet "●", not the service name. Fixing.

[assistant] Confirmed — column 2 is the service name. Fixing the awk field and clearing bad state files.

[assistant] Script hung on real restart attempts (some services block). I need to add timeouts to systemctl calls to keep this safe/non-blocking.

[assistant] Also add an overall timeout when testing to avoid a long run given ~40 failed services.

[assistant] Fixed and completed within timeout, exit 0, no hang, no destructive action, anti-loop state tracked correctly per-service now. Cleaning up the leftover backup state dir.

[assistant] That's harmless leftover state (non-destructive, left in place per safety constraints). Final quick re-verify of all six scripts' exit codes together.

[assistant] DONE

Files created (all `chmod +x`, all tested exit 0):
1. `/home/turbo/jarvis/scripts/hub-healthcheck.sh` — curls LM Studio :1234 and chat_proxy :18800 `/v1/models`, logs OK/DOWN with http code to `/home/turbo/jarvis/logs/hub-healthcheck.log`. Test: RC=0, correctly logged LM_STUDIO_1234=OK, CHAT_PROXY_18800=DOWN (proxy not running — expected, non-fatal).
2. `/home/turbo/IA/Core/jarvis/scripts/system-crash-guardian.sh` — checks `journalctl --user -p err -n 20` + `dmesg|grep oops/panic`, logs to `/home/turbo/jarvis/logs/crash-guardian.log`. Test: RC=0, correctly surfaced existing journal errors (jarvis-commander-api.service, jarvis-cowork-dispatcher.service), no kernel oops found.
3. `/home/turbo/jarvis/.claude/skills/run-jarvis-autoheal/jarvis_autoheal.sh` — lists `systemctl --user --failed`, for each does `reset-failed` then `restart` unless already attempted ≥3 times in the last 10 min (timestamp state files under `logs/.autoheal-state/`), logs to `/home/turbo/jarvis/logs/autoheal.log`. Test: RC=0.
   - **Bug found and fixed**: initial `awk '{print $1}'` grabbed the leading `●` bullet character instead of the service name (column 2 of `systemctl --failed --no-legend` output) — fixed to `awk '{print $2}'`.
   - **Second issue found and fixed**: `systemctl restart` calls could hang on some services with no timeout, causing the whole script to hang past 2 minutes — wrapped both `reset-failed` and `restart` in `timeout 10`/`timeout 15`. Re-tested against ~40 real failed servic