# Installer Postiz (self-hosted) — JARVIS OS

Postiz est un planificateur de publication réseaux sociaux **open-source et
souverain** (Next.js + Postgres + Redis, tout-en-un via Docker). Il remplace
les outils SaaS type Buffer/Hootsuite, sans cloud, conforme à la logique
local-first / EU AI Act.

> Préparation faite le 2026-08-14. **Rien n'a été installé ni lancé** : les
> fichiers sont prêts, l'installation est manuelle et volontairement différée.

---

## ⚠️ Avertissement RAM / thermique (M4)

Le M4 a **15 Gio de RAM** et est actuellement **en surchauffe** (garde thermique
82 °C, coupure 86 °C ; garde bash déclenchée à 95 °C au moment de la préparation).

Postiz consomme **~2 à 3 Gio de RAM** (image applicative jusqu'à 2 Gio +
Postgres ~512 Mo + Redis ~256 Mo) et pousse le CPU/IO au démarrage.

**Ne PAS démarrer Postiz sur le M4 tant que :**
- la RAM libre est < 4 Gio, **ou**
- la température CPU dépasse ~80 °C, **ou**
- des boucles d'inférence tournent (cf. `stop-cycles-m4`).

**Recommandé** : héberger Postiz sur un **nœud dédié** (M6, ou un petit VPS/LXC),
et n'y accéder depuis le M4 que via le navigateur. Sinon, le lancer uniquement
**machine déchargée** (aucun modèle chargé, pas de génération en cours).

Garde-fous déjà posés dans le compose : `mem_limit` par service (2g / 512m / 256m).

---

## Prérequis

- Docker + plugin Compose (déjà présents : la stack JARVIS tourne en Compose/Swarm).
  - Vérifier une fois le M4 refroidi : `docker compose version`.
- ~3 Gio de RAM libre et ~2 Gio de disque pour les images + volumes.
- Ports libres : Postiz est exposé sur **4200** (hôte) → 5000 (conteneur).
  Choisi pour éviter les conflits JARVIS : 9000 portainer · 5000 registry ·
  7777 webapp · 8899 planning · 1234 LMS · 18800 hub.

---

## Étapes d'installation

1. Aller dans le dossier de déploiement :
   ```bash
   cd ~/jarvis/deploy/postiz
   ```

2. Créer le fichier d'environnement à partir du modèle :
   ```bash
   cp .env.example .env
   ```

3. Renseigner les secrets dans `.env` — **jamais en clair dans git** :
   - `POSTIZ_JWT_SECRET` : `openssl rand -hex 32`
   - `POSTIZ_DB_PASSWORD` : mot de passe Postgres fort
   - Stocker ces valeurs dans le **coffre sops+age** (`~/jarvis/secrets-vault`) ;
     `.env` reste hors git (gitignoré).
   - Adapter les URLs (`POSTIZ_MAIN_URL`, etc.) si accès via IP LAN ou domaine
     (ex. `http://10.42.0.230:4200` si hébergé sur M6).

4. Vérifier l'état thermique/RAM AVANT de lancer (voir avertissement ci-dessus).

5. Démarrer la stack :
   ```bash
   docker compose up -d
   docker compose logs -f postiz    # suivre l'init (migrations Postgres au 1er run)
   ```

6. Ouvrir l'UI : `http://<host>:4200`, créer le **compte admin** (1er inscrit).

7. **Fermer l'inscription publique** ensuite :
   `POSTIZ_DISABLE_REGISTRATION=true` dans `.env`, puis `docker compose up -d`.

Arrêt : `docker compose down` (les volumes nommés conservent les données).

---

## Connecter les comptes réseaux sociaux

Les connexions se font **dans l'UI Postiz** (Settings → Channels / Add channel),
pas dans les fichiers de config :

- OAuth par plateforme (X/Twitter, LinkedIn, Instagram, Facebook, Mastodon,
  Bluesky, Threads, TikTok, YouTube…). Chaque plateforme peut exiger une app
  développeur (client id/secret) à saisir via les variables Postiz correspondantes.
- Les tokens sont **chiffrés en base** par Postiz — ne jamais les mettre dans
  `.env` versionné.
- Pour un usage multi-comptes, créer une organisation puis rattacher chaque canal.

---

## Rappel gouvernance : brouillon d'abord, un seul pilote de publication

Cohérent avec l'audit doublons (éviter deux systèmes qui publient en parallèle) :

- **Draft-first** : toute publication passe d'abord en **brouillon**, relue,
  avant planification/envoi. Ne jamais auto-publier sans validation humaine.
- **Un seul pilote de publication** à la fois. Si Mirra (ou un autre connecteur
  social JARVIS) publie déjà, Postiz reste en **planification/brouillon** et ne
  double pas l'envoi — sinon risque de posts en double sur les comptes.
- Décider explicitement qui est la source de vérité de publication avant
  d'activer l'envoi automatique dans Postiz.

---

## Fichiers

- `~/jarvis/deploy/postiz/docker-compose.yml` — stack (postiz + postgres + redis)
- `~/jarvis/deploy/postiz/.env.example` — variables à remplir (secrets → coffre)
- `~/jarvis/docs/INSTALLER-POSTIZ.md` — ce guide
