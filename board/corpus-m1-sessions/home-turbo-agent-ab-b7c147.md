[assistant] Je démarre par le constat direct sur le lot fautif et la comparaison avec un lot sain.

[assistant] Constat initial intrigant : le `.db` du lot 020022 porte une mtime de **09:00:20**, pas 02:00. Je creuse.

[assistant] Découverte majeure : il y a **deux** lots à 02:00 (`020001` complet et `020022` mort) — et un manifeste vide tout frais à **23:00:56**. Je vérifie si un backup tourne en ce moment avant toute conclusion.

[assistant] Le déclencheur est double : un **timer systemd horaire** ET une **ligne cron à 02:00**. Je lis le script et le journal pour confirmer la collision.

[assistant] Le run de 23:00 vient de finir avec succès à 23:02:51 — son manifeste était vide **parce que je l'ai listé pendant l'exécution**. Point clé pour le verdict. Je vérifie le journal autour de 02:00-09:00.

[assistant] Le journal systemd ne remonte qu'à 11:31 (pas persistant) — je bascule sur le log applicatif du cron, qui lui couvre 02:00.

[assistant] Preuve décisive trouvée : le run `020022` n'a écrit **aucune ligne** dans `backup.log`. Je cherche maintenant ce qui l'a tué et pourquoi les runs de 03:00 à 09:00 manquent.

[assistant] Le syslog couvre bien 02:00–09:00. Je regarde directement les fenêtres critiques.

[assistant] Confirmation du cron à 02:00:01. Je vérifie maintenant qui a produit chaque lot et pourquoi 03:00→09:00 manquent.

[assistant] La preuve est nette : le lot mort est celui du **timer** (démarré 02:00:22), tué par **SIGTERM à 09:00:21** après 7 h. Je cherche qui a envoyé ce signal.

[assistant] Il s'agit d'un **arrêt massif de la session systemd --user** à 09:00:21 (une dizaine de services tués ensemble). Je cherche le déclencheur.

[assistant] Diagnostic terminé. Rien n'a été modifié, supprimé ni relancé.

## Ce qu'il faut savoir d'abord : la prémisse est partiellement fausse

**Il n'y a pas eu de trou de sauvegarde à 02:00.** Le répertoire contient **deux** lots pour cette heure-là, pas un :

| Lot | Lanceur | Sort |
|---|---|---|
| `20260801_020001` | cron (`0 2 * * *`) | **sain** — 5 bases, manifeste de 487 octets, archive `gzip -t` valide |
| `20260801_020022` | timer systemd `jarvis-backup-hourly` | **mort** — manifeste vide, `.db` orphelin de 1,8 Go |

Le lot mort a donc un jumeau intact couvrant la même minute. Le vrai dégât est ailleurs : **les six déclenchements horaires de 03:00 à 08:00 n'ont jamais eu lieu**, parce que le service `oneshot` était encore actif. C'est là que se situent les 7 heures sans snapshot, pas à 02:00.

## Chronologie, avec les preuves

À **02:00:01**, cron lance le script (`CRON[3437197]: (turbo) CMD (bash ~/jarvis/scripts/backup-multi-db.sh ...)`). Vingt-et-une secondes plus tard, à **02:00:22.314**, le timer systemd lance une seconde instance du même script (`systemd[2729]: Starting jarvis-backup-hourly.service`). Une troisième, `jarvis-backup-sql.service`, avait démarré à 02:00:00.312. Trois processus lisent donc simultanément `/home/turbo/jarvis/jarvis_master.db`, qui pèse 1,86 Go et est écrite en continu (WAL actif de 4 Mo, et pas moins de trois tâches cron qui écrivent dedans chaque minute).

Le run du timer tourne alors pendant **sept heures**. Ce n'est pas un blocage en atte

[assistant] Rapport transmis à `main`.

**Le résumé en une phrase** : il n'y a jamais eu de trou de sauvegarde à 02:00 — un lot sain (`020001`, lancé par cron) coexiste avec le lot mort (`020022`, lancé par le timer systemd) ; le vrai dégât, ce sont les six créneaux horaires de 03:00 à 08:00 sautés parce que le run du timer est resté bloqué sept heures avant d'être tué par un SIGTERM à 09:00:21.

Les trois éléments à retenir :

**Cause** — Le cron (`0 2 * * *`) et `jarvis-backup-hourly.timer` lancent le même script à la même minute chaque jour. Trois processus lisaient simultanément `jarvis_master.db` (1,86 Go, écrite en continu), ce qui fait diverger `sqlite3 .backup` : 1h08 de CPU brûlé sur 7 h d'horloge, la copie redémarrant à chaque écriture concurrente. Le kill final vient d'un arrêt massif de la session `systemd --user` qui a emporté une dizaine de services à la fois. Ni OOM, ni reboot, ni suspension, ni disque plein.

**Purge** — 8 fichiers, 3,4 Go (les lots morts du 01/08 et du 31/07, plus deux manifestes vides). Tous libres selon `fuser`, aucun backup en cours. Commande fournie, non exécutée.

**Piège à connaître pour le script miroir** — le script crée son manifeste vide *avant* de copier quoi que ce soit, donc tout lot en cours d'exécution paraît incomplet. Je l'ai vécu en direct : le lot de 23:00 m'est apparu vide à 23:01 et s'est rempli à 23:02:51. Le miroir doit croiser le manifeste avec l'âge du fichier ou l'état du service avant de conclure.