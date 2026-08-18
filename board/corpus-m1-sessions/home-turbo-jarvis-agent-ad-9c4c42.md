[assistant] Le service est masqué délibérément (symlink → /dev/null, daté du 29 mars). Je cherche l'unité d'origine et le motif du masquage.

[assistant] Les sauvegardes de l'unité sont vides (0 octet) — donc déjà masquée au moment des snapshots. Je cherche l'origine et le motif.

[assistant] Masquage antérieur à toute sauvegarde : aucune copie de l'unité originale n'existe. Je cherche le contexte du 29 mars et les mécanismes de remplacement.

[assistant] Découverte importante. Je vérifie le remplaçant conteneurisé et le check post-boot.

[assistant] Je localise le check post-boot exact qui produit le message « ✗ Domino Engine FAIL ».

[assistant] Diagnostic complet. Dernière vérification : santé du vrai moteur domino et cohérence de l'invariant.

[assistant] Diagnostic terminé. **Je n'ai rien modifié et n'ai pas démarré le service** — la cause n'est pas un chemin mort, et le démarrer aurait cassé un invariant critique.

## Cause racine

`jarvis-domino-engine.service` est **masqué volontairement** : `/etc/systemd/system/jarvis-domino-engine.service` est un symlink vers `/dev/null`, daté du **29 mars 04:01**. Il n'y a donc aucun ExecStart, aucun journal (`journalctl` : « No entries »), et aucun fichier d'unité récupérable — les 4 copies de sauvegarde trouvées (Timeshift, pre-incident, snapshots) sont **elles aussi le symlink vers `/dev/null`**, le masquage étant antérieur à toutes.

Le point décisif est une **contradiction interne entre deux scripts de boot du même dossier** :

| Fichier | Ligne | Attend |
|---|---|---|
| `/home/turbo/Workspaces/jarvis-linux/infra/scripts/boot/jarvis-boot-layers.py` | 70 | `("Domino engine MASKED", lambda: _svc_masked("jarvis-domino-engine"))` — couche 4 ORCHESTRATOR, `critical: True` |
| `/home/turbo/Workspaces/jarvis-linux/infra/scripts/boot/jarvis-boot-sequencer.sh` | 426 | `sudo systemctl start jarvis-domino-engine … \|\| log "  ✗ Domino Engine FAIL"` |

L'état masqué **est l'état de santé attendu**, vérifié comme invariant critique. Le sequencer, lui, essaie de le démarrer : échec garanti, message « ✗ Domino Engine FAIL ».

Le même verdict vaut pour `jarvis-feeder` (masqué, même check ligne 71) et `jarvis-domino.service` (masqué lui aussi).

## Le moteur domino tourne déjà

La fonction a migré