[assistant] Découverte clé : `created_at == updated_at` sur tout l'échantillon. Je cherche les INSERT directs en `done` et je mesure les régimes.

[assistant] Correspondance frappante : 2 076 795 jamais touchées après INSERT ≈ les 2 077 368 sans résultat. Je valide le croisement avec l'extract de l'audit.

[assistant] Le critère est validé (98,1 %). Je cherche les générateurs de masse et je trace une tâche concrète.

[assistant] Le problème est toujours actif : 8 377 `done` créées aujourd'hui. Je trace un cas vivant.

[assistant] `omega-cascade.timer` toutes les 15 min correspond exactement à la cadence. Je remonte au script.

[assistant] J'ai le mécanisme complet, du générateur jusqu'à l'exécuteur. Je rédige le livrable.

[assistant] Livrable écrit : `/home/turbo/jarvis/artifacts/e1-20260806/chantier-faux-done.md`

**24 sites écrivent `done` dans `tasks` ; 21 sans jamais vérifier une production.** Un seul est correct : `labo/bibliotheque/series/prod-loop.sh:50`, qui exige un artefact sur disque (`[ -f "$art" ]`) avant de marquer.

**13 sites n'écrivent pas un statut : ils insèrent la ligne déjà `done`** (linkedin_*, mail_*, `cron_massive_scheduler.sh:8`, `jarvis_full_execution_validator.py:54`). La tâche naît accomplie.

**Les 2 sites qui vérifient vérifient le mauvais signal.** `jarvis-prod-runner.py:269` conditionne sur `returncode == 0`, mais `executors/executor-mail.sh` finit par `|| echo "Génération mail effectuée."` puis `echo RESULT_FILE` — rc=0 structurellement impossible à faire échouer. C'est pourquoi 18 581 fichiers d'erreur ont pu passer `done` pendant 42 jours.

**Parcours tracé — tâche #2100000** (`[LINKEDIN-NETWORK-GROWTH] Invitation envoyée à : Head of Data & Cloud Architecture`) : créée par `linkedin_daily_research_autopilot.py:92-95` qui itère sur une liste codée en dur ; `status='done', score=100` posé dans le `VALUES` de l'INSERT ; `created_at == updated_at` → aucun exécutant ne l'a touchée ; aucune invitation n'est partie. Le script frère `linkedin_growth_network.py:71-83` fait `time.sleep(0.4)` puis écrit `"status": "EXÉCUTÉ_CDP"` sans émettre une seule requête.

**Régimes séparés par `updated_at = created_at`** : 2 076 795 jamais exécutées (96,8 %) · 67 027 exécutées avec artefact ·