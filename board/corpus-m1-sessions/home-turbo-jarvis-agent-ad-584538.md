[assistant] Maintenant j'implémente le fix : instrumenter le vrai chemin de dispatch (`execute_script` / `dispatch`) pour écrire dans `agent_dispatch_log` de la bonne base (`/home/turbo/jarvis-cowork/etoile.db`, celle qui contient réellement `cowork_cycle_log`).

[assistant] Maintenant j'instrumente `dispatch()` pour appeler `log_agent_dispatch()` à chaque exécution réelle de script.

[assistant] Bien, le format correspond dans cette base. Testons le vrai flux `dispatch(execute=True)` en direct pour prouver l'écriture.

[assistant] Le script a réellement été exécuté (échec attendu, `--once` n'est pas un flag reconnu par `gpu_optimizer.py`, mais peu importe pour la preuve). Vérifions que la ligne a bien été insérée dans `agent_dispatch_log`.

[assistant] Le service existe déjà avec `Restart=on-failure` (pas `always`), donc un simple restart est sûr et respecte la contrainte. Je redémarre pour que le correctif soit actif en production.

[assistant] Preuve end-to-end confirmée : la mission déposée dans `inbox/` a été traitée par le vrai service systemd (`jarvis-cowork-dispatcher.service`, PID redémarré) et a produit une ligne réelle en base (id=2). Nettoyage du fichier de test dans `outbox/`.

[assistant] ## Résumé pour toi

**Cause réelle (hypothèse b confirmée)** : le daemon systemd `jarvis-cowork-dispatcher.service` (`/home/turbo/jarvis-cowork/src/cowork_dispatcher.py --daemon`) est le seul processus qui dispatche vraiment des scripts, mais sa fonction `dispatch()` n'écrivait jamais dans `agent_dispatch_log`. Le code d'INSERT existait ailleurs (`dev/dispatch_quality_tracker.py`, `dev/resilient_dispatcher.py`, `dev/multi_strategy_dispatcher.py`) mais ces scripts ne sont appelés par personne en prod.

**Piège annexe évité** : `core/unified.py` (`UnifiedMemoryStore`) ne connaît pas `/home/turbo/jarvis-cowork/etoile.db` (la base canonique) — un fix naïf aurait écrit dans une autre copie d'etoile.db.

**Correctif** : ajout de `log_agent_dispatch()` dans `/home/turbo/jarvis-cowork/src/cowork_dispatcher.py`, écrivant dans `agent_dispatch_log` via `resolve_db_with_table()` (même résolveur que `cowork_engine.py`, garantit la base canonique). `dispatch()` appelle cette fonction à chaque exécution réelle de script. Service redémarré (unit existante, `Restart=on-failure` inchangé).

**Preuve** : test bout-en-bout réel (mission déposée dans `src/inbox/`, traitée par le service en <30s) → `SELECT COUNT(*) FROM agent_dispatch_log` passe de 0 à 2, avec une ligne réelle horodatée, latence et message d'erreur capturés.

Fichier modifié : `/home/turbo/jarvis-cowork/src/cowork_dispatcher.py` (base concernée : `/home/turbo/jarvis-cowork/etoile.db`). Compte-rendu détaillé déjà envoyé à team-lead