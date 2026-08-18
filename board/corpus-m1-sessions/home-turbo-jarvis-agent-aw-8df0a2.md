[assistant] Confirmons que le service reste actif après le reload, et vérification finale par preuve HTTP.

[assistant] Preuve finale obtenue : 200, JSON avec données réelles (`counts.done: 2 121 092`, `creations.total: 15`, `pending: 3`). Le service est stable, `enabled`, avec `Linger=yes`.

[assistant] ## Compte rendu

**(a) Cause racine du down**
Le service `jarvis-planning-widget.service` lui-même n'a **jamais planté** au sens systemd (aucun `Failed`, aucun `exit-code` non nul sur toute la journée dans le journal). La coupure vue par le team-lead correspondait à l'instabilité générale de la machine : le manager `systemd --user` a été relancé plusieurs fois dans la journée (PID différent à chaque fois : 2276→2514→2523→2502→2521→2498→2475→**2518**), ce qui coupe et redémarre tous les services `--user` d'un coup — cohérent avec l'épisode des 21 reboots dont vous parlez. Depuis ~18:44 (PID manager 2518), plus aucun bounce du manager : la machine est stable. Le service a ensuite continué de tourner normalement, y compris via des redémarrages **volontaires et sains** ("Stopping"→"Stopped"→"Started" en < 1 s) déclenchés toutes les ~15 min par `run-planning-context-capture/driver.sh:185` (comportement existant du pipeline, pas un bug).

Petit bruit annexe sans rapport avec la panne : des `BrokenPipeError` occasionnels dans les logs quand un client (ex. curl avec `--max-time`) coupe la connexion avant la fin de l'écriture — cosmétique, sans impact sur la disponibilité.

**(b) Ce qui a été changé, fichier par fichier**
- `/home/turbo/.config/systemd/user/jarvis-planning-widget.service` : `Restart=always` / `RestartSec=5` → **`Restart=on-failure` / `RestartSec=30`**, conformément à votre consigne (vrai serveur qui tourne en continu ⇒ pas de `Restart=always` agressif). Sauvegarde de 

[assistant] Bien protégé par `if __name__ == "__main__":` — je peux importer le module sans démarrer un second serveur.

[assistant] Maintenant reload + restart pour appliquer le patch code + la nouvelle limite, puis vérification.

[assistant] 35 % effectif confirmé. Vérification par la preuve exacte demandée, à froid puis avec un peu de charge concurrente réaliste.

[assistant] 2,86 s à froid, bien loin des 60 s de blocage. Testons maintenant sous charge concurrente réaliste (plusieurs clients simultanés, comme le bureau + S9 + onglets) pour vérifier l'absence de stampede résiduel.

[assistant] Maintenant relever la CPUQuota à un niveau plus confortable (machine 16 cœurs, marge large) et redémarrer.

[assistant] Vérification avec la même charge de test (8 requêtes concurrentes) puis la preuve exacte demandée.

[assistant] ## Compte rendu — /data débloqué

**Requête coupable identifiée**
Ce n'était pas une requête SQL (toutes chronométrées isolément : 0,1 à 0,2 s, table `tasks` 2,1 M lignes comprise). C'était un **effet combiné** :

1. `cached()` n'avait **aucun verrou**. Quand un cache expire (ex. `frontieres` TTL=120 s, qui lance 2 sous-process `jarvis audit:frontiers` + `jarvis deepsearch health --all`), chaque requête `/data` concurrente qui arrive pendant le calcul **relance le même calcul en double/triple** (cache stampede) au lieu d'attendre le résultat.
2. Le service tournait sous **`CPUQuota=10%`** (durci le 03/08 suite à une fuite CPU antérieure). J'ai mesuré via `cpu.stat` du cgroup : **`nr_throttled`/`nr_periods` = 99,98 %** — le process était throttlé quasiment à chaque période de 100 ms. Combiné au stampede, quelques clients concurrents (bureau + reverse S9 + onglets, refresh 5 s) suffisaient à faire dépasser 60 s par requête → `HTTP 000`.
3. `counts` (GROUP BY sur 2,1 M lignes) et `dom` (scan des contextes pending/running) tournaient **sans cache**, recalculés à chaque appel de chaque requête concurrente.

**Fichiers modifiés**
- `/home/turbo/jarvis/bin/jarvis-planning-widget.py` :
  - `cached()` : ajout d'un verrou par clé (`threading.Lock`, double-checked locking) → une seule requête calcule un cache expiré, les autres attendent le résultat frais au lieu de le relancer.
  - `counts` et `dom` (dans `data()`) : sortis en fonctions `_counts_query()`/`_dom_query()` et passés sous `