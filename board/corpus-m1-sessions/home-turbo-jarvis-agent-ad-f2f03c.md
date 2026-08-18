[assistant] 100 fichiers recensés. Je croise maintenant avec les services systemd et le crontab pour établir la priorité.

[assistant] Le croisement direct est trop étroit — beaucoup de services passent par des wrappers shell. J'élargis sur deux niveaux.

[assistant] 26 fichiers prioritaires, 74 manuels. J'examine maintenant les motifs de connexion réels.

[assistant] Le recensement a des faux positifs (fichiers qui mentionnent `jarvis_master.db` mais connectent `jarvis_logs.db`). Je vérifie les constantes de chemin.

[assistant] Cible confirmée. J'applique maintenant les correctifs, en commençant par les fichiers les plus simples.

[assistant] Les 20 fichiers prioritaires concernés sont traités. Je vérifie leur syntaxe avant de passer aux 74 restants.

[assistant] Les 20 prioritaires sont valides. Je passe aux 74 restants avec un transformateur AST qui repère précisément les connexions visant cette base.

[assistant] Un défaut : quand un `PRAGMA busy_timeout` faible existe déjà, il reste et écrase le `timeout=`. Je corrige le transformateur.

[assistant] Le rendu est correct. J'identifie les fichiers laissés intacts avant d'appliquer.

[assistant] `bin/jarvis-teams-build.py` était un faux négatif du transformateur (URI construite par f-string). Je le traite à la main.

[assistant] Correctifs appliqués et valides. Je vérifie maintenant les défauts structurels au-delà du timeout.

[assistant] Un dernier contrôle : les transactions qui tiennent le verrou pendant un appel lent.

[assistant] Travail terminé. Voici le rapport.

## Chiffres

| | |
|---|---|
| Recensés | 100 |
| Corrigés | **85** |
| Laissés de côté | 15 |
| Connexions durcies | ~92 |
| Échecs `ast.parse` | 0 |

Aucun script modifié n'a été exécuté, aucun GPU touché, rien commité. Les quatre fichiers déjà corrigés aujourd'hui et les trois de l'agent parallèle sont intacts.

## Prioritaires (service systemd / cron) — 20 traités

26 candidats branchés à un service ou au cron ; 20 visaient réellement la base contendue et ont été corrigés :

`/home/turbo/jarvis/` + `bin/biblio-vectorize.py`, `bin/jarvis-master-routing-daemon.py`, `bin/jarvis-planning-widget.py`, `bin/omega-preload.py`, `bin/omega-todolist.py`, `bin/planning-context-capture.py`, `bin/task-autogen.py`, `cli/biblio_cycle.py`, `cli/cascade.py`, `scripts/build-unit-index.py`, `scripts/continuous_ultra_runner.py`, `scripts/domino_autogen_engine.py`, `scripts/jarvis-prod-runner.py`, `scripts/jarvis-task-auto.py`, `scripts/jarvis-task-recovery.py`, `scripts/linkedin_carousel_publisher.py`, `scripts/linkedin_daily_research_autopilot.py`, `scripts/linkedin_growth_network.py`, `scripts/m6_tampon.py`, `scripts/setup_m6_m1_cable_bridge.py`

Les 6 autres prioritaires écrivent ailleurs (voir plus bas). Les 65 restants — lancés à la main — ont été traités ensuite par un transformateur AST, avec relecture des diffs.

## Les 15 laissés de côté

Tous parce que la connexion ne vise pas la base contendue :

- **Écrivent une autre base** : `bin/dead-letter-q