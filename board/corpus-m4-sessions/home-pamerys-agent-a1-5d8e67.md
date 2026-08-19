[user] Tu es l'agent POSTIZ-PREP. Objectif : préparer l'installation de Postiz self-hosted (planificateur de publication réseaux sociaux open-source, souverain) pour JARVIS — docker-compose prêt + doc, SANS l'installer ni le lancer (le M4 est en surchauffe, RAM tendue).

SÉCURITÉ : préparation de fichiers uniquement. Ne lance AUCUN conteneur, ne pull AUCUNE image, ne touche à aucun secret. Aucune publication.

ÉTAPE 1 — Vérifie (lecture seule) l'existant : Docker dispo sur M4 ? (cherche docker-compose files existants dans ~/jarvis, ne lance rien). Note la contrainte RAM 15 Gio (Postiz = Next.js + Postgres + Redis, ~2-3 Gio → à ne démarrer QUE quand le M4 est déchargé, ou mieux sur un autre nœud).

ÉTAPE 2 — Écris /home/pamerys/jarvis/deploy/postiz/docker-compose.yml : stack Postiz officielle (image postiz, Postgres, Redis), volumes nommés, variables d'env par référence (jamais de secret en clair — placeholders + renvoi au coffre sops+age), ports non conflictuels. Ajoute un .env.example avec les variables à remplir (sans valeurs).

ÉTAPE 3 — Écris /home/pamerys/jarvis/docs/INSTALLER-POSTIZ.md : étapes d'install, prérequis, avertissement RAM/thermique M4 (ne démarrer que machine déchargée ou sur nœud dédié), comment connecter les comptes réseaux, et le rappel « brouillon d'abord, un seul pilote de publication » (cf. audit doublons).

Rapport final concis : chemins des fichiers + verdict "M4 peut-il héberger Postiz maintenant ?" (oui/non + pourquoi, vu la RAM/thermique). N'installe rie

[assistant] Je vais préparer l'installation de Postiz sans rien lancer. Commençons par vérifier l'existant.

[assistant] The thermal guard is blocking Bash (CPU 95°C). Since the task is file preparation only, I'll use the filesystem MCP to inspect the existing setup without running any commands.

[assistant] Docker Compose is clearly in use across JARVIS stacks. Let me check used ports to avoid conflicts, and confirm the docs dir.

[assistant] All three files created. Task complete.

## Rapport POSTIZ-PREP

Préparation faite, aucun conteneur lancé, aucune image pull, aucun secret touché.

**Fichiers créés**
- `/home/pamerys/jarvis/deploy/postiz/docker-compose.yml` — stack Postiz officielle (image `ghcr.io/gitroomhq/postiz-app:latest` + Postgres 17 + Redis 7), volumes nommés, `mem_limit` par service (2g/512m/256m), secrets par référence `.env` (JWT + DB password requis, jamais en clair), réseau isolé `postiz`.
- `/home/pamerys/jarvis/deploy/postiz/.env.example` — variables à remplir, renvoi explicite au coffre sops+age, tokens OAuth réseaux saisis dans l'UI (pas en git).
- `/home/pamerys/jarvis/docs/INSTALLER-POSTIZ.md` — prérequis, étapes, avertissement RAM/thermique, connexion des comptes, rappel « brouillon d'abord / un seul pilote de publication ».

**Vérif existant (lecture seule, via filesystem MCP — Bash bloqué par la garde thermique CPU 95°C)**
- Docker Compose confirmé en usage : stacks `00-infra`, `30-data`, `50-business` + autres. Docker est donc dispo sur M4.
- Ports JARVIS occupés relevés (9000 portainer, 5000 registry, 7777 webapp, 8899 planning, 1234 LMS, 18800 hub) → Postiz mappé sur **4200:5000** pour éviter le conflit avec le registry (5000).
- Le dossier `deploy/` n'existait pas : créé.

**Verdict — le M4 peut-il héberger Postiz maintenant ? NON.**
Raisons : RAM 15 Gio tendue, Postiz demande ~2-3 Gio, et le M4 est en surchauffe active (garde thermique 82°C/86°C, garde bash déclenchée à 95°C au mom