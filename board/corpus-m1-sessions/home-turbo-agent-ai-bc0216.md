[assistant] L'état constaté correspond exactement à la description : `Type=simple`, `Restart=always`, `RestartSec=10`, `WantedBy=default.target`, service enabled, en boucle `activating (auto-restart)`. Je procède à l'implémentation.

[assistant] Le backup est en place. Je modifie maintenant le service (oneshot, suppression de Restart/RestartSec et du bloc [Install]), puis je crée le timer.

[assistant] Maintenant je crée le timer, puis je désactive le service (il était `enabled` avec un `[Install]` maintenant retiré) et active le timer.

[assistant] Les quatre critères d'acceptation sont validés. J'envoie le rapport complet à l'équipe.

[assistant] La tâche T1 est terminée et le rapport a été envoyé à l'équipe. Résumé pour toi :

Le service `jarvis-multi-bash.service` (M1, `~/.config/systemd/user/`) était bien un one-shot déguisé en daemon (`Type=simple` + `Restart=always` + `RestartSec=10`), redémarré en boucle toutes les ~11 secondes (~5629 restarts constatés). J'ai :

1. Sauvegardé l'unité d'origine dans `jarvis-multi-bash.service.bak-20260802`.
2. Converti le service en `Type=oneshot`, retiré `Restart=`/`RestartSec=` et le bloc `[Install]`, sans toucher au script Python ni au reste.
3. Créé `jarvis-multi-bash.timer` (`OnBootSec=1min`, `OnUnitActiveSec=1min`) qui porte désormais l'`[Install]`.
4. Désactivé le service, activé le timer (`enable --now`), et arrêté le run auto-restart résiduel.

Les quatre critères sont vérifiés par des sorties de commande réelles : le timer est actif avec un `NEXT` à échéance, un déclenchement manuel se termine en `inactive (dead)` avec `status=0/SUCCESS` (plus de `activating (auto-restart)`), le journal montre bien le log « Cycle exécuté avec succès » du run déclenché, et `ActiveState=inactive`/`Result=success`/`NRestarts=0` confirment qu'aucun état résiduel ne subsiste.

[assistant] Maintenant j'applique daemon-reload, déclenche un run manuel, et je vérifie le timer.

[assistant] Les deux corrections de la review qualité ont été appliquées avec succès à `~/.config/systemd/user/jarvis-multi-bash.service` :

1. **`TimeoutStartSec=30`** ajouté dans `[Service]` (convention du dossier, marge de sécurité contre un lock SQLite).
2. **`After=network.target`** retiré (reliquat de template inutile pour ce job local).

Rien d'autre n'a été touché — ni le timer, ni le script Python, ni `AccuracySec`. Après `daemon-reload`, un déclenchement manuel s'est terminé proprement en `inactive (dead)` avec `status=0/SUCCESS`, `TimeoutStartUSec=30s` confirme la prise en compte du nouveau timeout, et le timer `jarvis-multi-bash.timer` reste `enabled` avec un `NEXT` à échéance normale (~1 minute). Le rapport complet a été envoyé au team-lead.