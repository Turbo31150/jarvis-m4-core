[user] Tu es un subagent implémenteur. Tâche autonome, réponds en français. Travaille UNIQUEMENT dans ~/Bureau/workflow-gestion (et l'état runtime qui s'y rapporte).

CONTEXTE : audit du 2026-07-22 : (a) l'app tourne en DOUBLON sur :8140 et :8141 avec des états séparés (OMEGA Mairie API — la référence est :8140, cf. widget) ; (b) le container/lanceur utilise `--workers 2` ce qui crée des 404 croisés (état en mémoire non partagé entre workers) ; (c) le chemin d'envoi (mails/notifications sortants) n'a PAS de kill-switch.

TÂCHE :
1. Constate l'état réel : `ss -tlnp | grep -E '8140|8141'` ; `grep -rn 'workers\|8141\|8140' ~/Bureau/workflow-gestion --include='*.sh' --include='*.py' --include='*.yml' --include='*.service' --include='Dockerfile*' | head -30`. Trouve le(s) point(s) de lancement (docker-compose, systemd, script).
2. Unifie sur UNE instance :8140 : corrige la config pour que :8141 ne soit plus lancé. Si un process :8141 tourne, arrête-le APRÈS avoir vérifié que :8140 sert (curl santé). Ne casse pas :8140.
3. Passe `--workers 2` → `--workers 1` dans le lanceur (uvicorn/gunicorn).
4. Kill-switch : sur le chemin d'envoi sortant, ajoute une garde lisant l'env `OMEGA_SEND_ENABLED` — envoi réel UNIQUEMENT si la valeur est "1"/"true" ; sinon log + no-op (mode brouillon). Défaut = DÉSACTIVÉ. Modifie le code d'envoi (cherche send/smtp/mail) proprement, en respectant le style du fichier.
5. Si un service/container doit être relancé pour appliquer : relance-le et vérifie par curl que 

[assistant] Good — fire-and-forget, return value ignored downstream. Now implementing the guard in the single choke-point (`TelegramAlerter._send`), plus the Dockerfile worker fix, and confirming everything else.

[assistant] Good, formatter just added a blank line. Now let's find the `_send` method to add the guard.

[assistant] Now let's fix the Dockerfile's default `--workers 2` → `--workers 1`, and verify with a quick Python syntax check.

[assistant] Now let's build and run the canonical isolated instance to verify end-to-end: :8140 responds, :8141 stays dark, workers=1, and the kill-switch actually blocks a send.

[assistant] Kill-switch verified working exactly as intended: default (disabled) short-circuits with the `OMEGA_SEND_ENABLED=0` no-op log; setting `OMEGA_SEND_ENABLED=1` lets it proceed to the real send path (here falling to Telegram stub since no creds are configured). Now clean up the ad-hoc verification and confirm final state.

[assistant] ## Rapport final

**Statut : DONE**

### Constat réel
L'audit du 2026-07-22 décrivait l'état du dernier **commit** (`93b4380`) : le container isolé mappait `:8141`, sans `--workers` explicite (donc héritait de `--workers 2` du Dockerfile), et sans kill-switch d'envoi. Mais la **copie de travail non commitée** contenait déjà un correctif partiel (probablement une session antérieure non finalisée) : `docker/docker-compose.isolated.yml` remappé sur `127.0.0.1:8140`, commande explicite `--workers 1`, et `OMEGA_SEND_ENABLED=0` déclaré en variable d'env — mais **jamais lu par aucun code** (grep confirmé : seul `core/sentinelle/__main__.py` le lisait pour un log, sans rien à gater puisqu'aucun SMTP n'est câblé). Le service systemd `omega-mairie.service` était déjà désactivé/inactif pour éviter le double-traitement.

### Modifications apportées (par moi)
1. `/home/turbo/Bureau/workflow-gestion/docker/Dockerfile:52-59` — durci le `CMD` par défaut `--workers 2` → `--workers 1` (défense en profondeur : ce Dockerfile est aussi utilisé par `docker-compose.yml` — la stack complète — qui n'a pas d'override `command`, donc héritait silencieusement de 2 workers).
2. `/home/turbo/Bureau/workflow-gestion/integrations/telegram/alerter.py:22-24,143-147` — ajouté `_send_enabled()` et l'appel dans `TelegramAlerter._send()`, seul chemin d'envoi sortant réellement câblé dans le code (alertes urgentes `agents/m2_detecteur/agent.py:200` et rapport matinal `api/server.py:355`). Défaut = désactivé → no-o

[user] The coordinator sent a message while you were working:
La review qualité approuve tout sauf un point mineur à corriger dans ~/Bureau/workflow-gestion/integrations/telegram/alerter.py : le no-op kill-switch de `_send()` renvoie `True`, indiscernable d'un envoi réussi. Vérifié : aucun appelant ne lit le retour aujourd'hui (ensure_future sans await), donc tu peux corriger sans risque. Fais : (1) le chemin no-op `OMEGA_SEND_ENABLED=0` renvoie `False` ; (2) docstring explicite sur `_send()` et `send_alert()` : « retour True = requête d'envoi partie sans exception, False = non envoyé (kill-switch ou échec) — ne signifie PAS “délivré” ». Garde le log du mode brouillon. Puis rebuild/redémarre le container omega-mairie-iso et re-vérifie que :8140 répond 200 et que le no-op loggue toujours. Rapport court : diff + preuve.

Address this before completing your current task.

[assistant] Now update the docstring on `send_alert` per the coordinator's request (they specifically named `_send()` and `send_alert()`):

[assistant] All confirmed. Rebuilt, restarted, re-verified.

## Rapport correctif

**Statut : DONE**

### Diff (`integrations/telegram/alerter.py`)
```diff
     async def _send(self, text: str, parse_mode: str = "Markdown") -> bool:
+        """Dispatch a message, gated by the OMEGA_SEND_ENABLED kill-switch.
+
+        Return value semantics: True means the send request went out without
+        raising (or was intentionally not attempted because the app is in
+        stub mode) — it does NOT mean "delivered". False means nothing was
+        sent — either the kill-switch is off (OMEGA_SEND_ENABLED != 1/true)
+        or the real Telegram API call failed. Callers currently fire-and-forget
+        (asyncio.ensure_future without await), so this return value is not
+        read anywhere today — do not rely on it as a delivery signal.
+        """
         if not _send_enabled():
             logger.info("[OMEGA_SEND_ENABLED=0 — mode brouillon, no-op] %s", text[:200])
-            return True
+            return False
```
Plus `send_alert()` docstring (lines ~56-68) updated to spell out the same True/False semantics ("does NOT mean delivered").

### Preuve
- Rebuild + `up -d` : `omega-mairie-iso` recreated, healthy.
- `curl :8140/api/status` → `HTTP 200`, `{"status":"operational",...}`.
- `curl :8141/api/status` → connection refused (unchanged, still dark).
- No-op path re-tested inside the running container: log line `[OMEGA_SEND_ENABLED=0 — mode brouillon, no-op] ...` still fires, and t

[user] The coordinator sent a message while you were working:
Dernier point de la review : dans ~/Bureau/workflow-gestion/integrations/telegram/alerter.py, le chemin `except ImportError` (httpx absent, ~lignes 180-184) renvoie `True` alors que la docstring dit désormais « False = rien n'est parti ». Tranche dans le sens de la cohérence : renvoie `False` dans ce chemin (rien n'a été envoyé), garde le log existant. Pas besoin de rebuild complet du container pour ce cas (httpx est présent dans l'image, chemin mort en prod) — mais vérifie la syntaxe (python3 -m py_compile) et que le container tourne toujours (curl :8140 → 200). Rapport en 3 lignes.

Address this before completing your current task.

[assistant] `except ImportError` at `alerter.py:180-184` now returns `False` (was `True`), matching the docstring's "False = rien n'est parti". Syntax OK (`py_compile` clean); container `omega-mairie-iso` untouched and still serving — `curl :8140/api/status` → `HTTP 200`. No rebuild needed since this path never executes in prod (httpx is bundled in the image).