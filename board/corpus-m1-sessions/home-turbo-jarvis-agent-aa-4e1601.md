[user] Reviewer de CONFORMITÉ SPEC. Réponds en français, court. Ne modifie RIEN.

SPEC (package ~/Bureau/workflow-gestion, app OMEGA Mairie) : (1) UNE seule instance, sur :8140 — :8141 ne doit plus écouter ; (2) plus aucun lancement en `--workers 2` (uvicorn/gunicorn) sur les chemins réellement utilisés ; (3) kill-switch `OMEGA_SEND_ENABLED` sur le chemin d'envoi sortant : défaut désactivé = no-op journalisé, envoi réel seulement si "1"/"true".

L'implémenteur rapporte : Dockerfile:52-59 CMD --workers 2→1 ; integrations/telegram/alerter.py garde `_send_enabled()` dans `TelegramAlerter._send()` (seul chemin d'envoi câblé, pas de SMTP dans le code) ; docker-compose.isolated.yml était déjà remappé 127.0.0.1:8140 avec --workers 1 (correctif antérieur non commité) ; container omega-mairie-iso rebuild + up, :8140 répond 200, :8141 refuse ; omega-mairie.service systemd disabled.

VÉRIFIE réellement :
1. `ss -tln | grep -E ':814[01]'` → seul :8140 écoute.
2. `curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:8140/api/status` → 200.
3. `grep -rn 'workers' ~/Bureau/workflow-gestion/docker/Dockerfile ~/Bureau/workflow-gestion/docker/*.yml` → plus aucun `--workers 2` actif (commentaires OK).
4. `grep -n 'OMEGA_SEND_ENABLED' ~/Bureau/workflow-gestion/integrations/telegram/alerter.py` → la garde existe ; lis la fonction `_send_enabled` et son appel : défaut bien DÉSACTIVÉ (absence de variable = pas d'envoi), pas l'inverse.
5. Cherche un chemin d'envoi NON gardé : `grep -rn 'req

[assistant] Bon, workers = 1 partout, kill-switch default "0" (désactivé), pas de référence 8141. Vérifions le port du docker-compose.isolated.yml (mapping 127.0.0.1:8140) et le chemin d'appel de `_send_enabled()` dans `_send()`, plus le scan des envois non gardés.

[assistant] ✅ CONFORME

1. Port : `ss -tln` → seul `127.0.0.1:8140` écoute (65535 backlog), rien sur 8141.
2. `curl 127.0.0.1:8140/api/status` → `200`.
3. `--workers` : `docker/Dockerfile:59` = `"1"` ; `docker/docker-compose.isolated.yml:7` = `"1"`. `docker/docker-compose.yml` (stack full, non utilisée pour le widget, port hôte 8080≠8140/8141) n'override pas `--workers` → hérite du défaut Dockerfile = 1 worker. Aucun `--workers 2` actif nulle part.
4. Garde `OMEGA_SEND_ENABLED` : `integrations/telegram/alerter.py:24` `_send_enabled()` retourne `False` par défaut (`os.getenv(..., "0")`), et `_send()` (ligne ~142) l'appelle en tout premier — si désactivé, `logger.info(...); return True` (no-op journalisé), sans toucher httpx. Défaut bien désactivé.
5. Envois sortants : seul `httpx.AsyncClient(...).post(...)` dans `alerter.py:161`, situé après la garde `_send_enabled()` dans la même fonction `_send()` — aucun autre `requests.post`/`urlopen`/`httpx` externe ailleurs dans le repo (grep ne remonte que ce même fichier).
6. `8141` : aucune référence dans `.yml`/`.service`/`.sh` du repo. Seule mention = commentaire explicatif dans `RAPPORT-DEPLOIEMENT-COMPLET.md:26` et `docker/Dockerfile:54` (documentation, pas config active).

Bonus vérifié (hors checklist mais pertinent) : `systemctl --user is-enabled omega-mairie.service` → `disabled` (confirmé) ; `~/.config/systemd/user/omega-mairie.service` ne pose pas de `--workers` (donc défaut uvicorn = 1) et pointe bien sur `--port 8140`. Le container ré