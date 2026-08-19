[user] Subagent implémenteur. Réponds en français. Travaille dans ~/labo/bibliotheque/skillsmp et ~/jarvis/bin.

CONTEXTE : Le pipeline de moisson skillmp (façade ~/jarvis/bin/skillmp-pipeline.py, étages expansion/catalogue/source/site/fr/boucle, root ~/labo/bibliotheque/skillsmp) souffre de TARISSEMENT : les étages `source`, `site`, `expansion` se terminent quand ils n'ont plus de cibles (« TERMINE · 0 a traiter ») et ne redémarrent JAMAIS seuls, même quand l'étage `catalogue` (toujours actif) produit de nouvelles fiches à traiter. Conséquence mesurée : 198k skills mais seulement ~10 % avec code source. Mémoire projet : les sources statiques s'épuisent, il faut des sources dynamiques + dédup (leçon feedback_task_autogen_source_saturation). Il existe déjà un superviseur.log — regarde ce qui existe avant de créer.

TÂCHE :
1. Comprends la façade : lis ~/jarvis/bin/skillmp-pipeline.py (structure, comment start/stop/status marchent, où sont les PID). Regarde ce que fait le superviseur existant s'il y en a un (grep superviseur).
2. Crée `~/jarvis/bin/skillmp-sentinelle.py` (stdlib seule) : toutes les N minutes (défaut 15) : (a) mesure le delta de fiches/URLs nouvelles par étage depuis le dernier tick (état JSON persistant) ; (b) si un étage arrêté a de NOUVELLES cibles à traiter (ex. fiches sans code source apparues depuis son dernier run → relancer `source` ; nouvelles pages créateur → `expansion`), le relance via `skillmp-pipeline.py start <étage>` ; (c) journalise dans `~/labo/biblio

[assistant] Bon, la syntaxe tient après reformatage. Testons maintenant en réel : d'abord `--dry --once`, puis `--once` réel, puis le timer systemd.

[assistant] Maintenant re-testons avec la correction, d'abord un test unitaire rapide de la fonction, puis `--dry --once`.

[assistant] Corrigé : 22 938 nouveaux repos détectés en base absents de `repos-distincts.txt`. Relançons le `--dry --once` complet.

[assistant] Load 8.09, RAM disponible 4.7 Go — sous les seuils (12 / 2 Go), donc le garde-fou laissera passer. Lançons le tick réel.

[assistant] Excellent, le tick réel a fonctionné : sources étendues (repos-distincts.txt 4212→27150, creators.xml 5000→18746, repos.xml 1425→27316) et les 3 étages relancés. Vérifions qu'ils tournent bien maintenant.

[assistant] Les 6 étages sont maintenant tous actifs, et les 3 étages précédemment taris (source, expansion, site) sont bien repartis avec de vraies nouvelles cibles : source 22 938 dépôts à traiter, expansion 13 746 créateurs, site 39 637 pages. Installons maintenant le timer systemd.

[assistant] Le verrou flock fonctionne : une deuxième instance refuse de démarrer. Nettoyage final et vérification de l'état des fichiers.

[assistant] Tous les 6 étages sont actifs, y compris les 3 précédemment taris (expansion, source, site), qui progressent réellement (volume en croissance : source 851774→866315 fichiers en quelques minutes). Tout est en place et vérifié.

## Rapport

**Statut : opérationnel, testé et déployé.**

**Diagnostic confirmé (avant fix) :** `expansion.py`, `github_source.py` et `aspire_site.py` lisent des listes de cibles STATIQUES figées au 2026-08-06 01:03 (`repos-distincts.txt` 4212 lignes, `creators.xml` 5000 entrées, `repos.xml` 1425 entrées) — jamais régénérées malgré `catalogue` (aspire.py, jamais arrêté) qui alimentait en continu `jarvis_master.db` avec de nouveaux repos/auteurs. Le superviseur existant (`superviseur.sh`) ne relance QUE `enrichir_fr.py`, jamais ces 3 étages. Résultat : 204 894 skills mais seulement 21 480 (~10%) avec code source.

**Fichiers créés :**
- `/home/turbo/jarvis/bin/skillmp-sentinelle.py` — sentinelle stdlib pure
- `/home/turbo/.config/systemd/user/skillmp-sentinelle.service` (oneshot)
- `/home/turbo/.config/systemd/user/skillmp-sentinelle.timer` (15 min, `Persistent=true`, activé)

**Logique de la sentinelle** (au-delà du strict "relancer") : avant de décider, elle étend dynamiquement les 3 listes sources depuis `jarvis_master.db` (colonnes `repo`/`repo_url`/`auteur` de `skillsmp_skills`), toujours en AJOUT pur (jamais de troncature) :
- `source` : nouveaux `owner/repo` → append `repos-distincts.txt`
- `expansion` : nouveaux auteurs → insertion `<url><loc>` a