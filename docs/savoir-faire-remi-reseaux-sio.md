# Savoir-faire Rémi (DVA) — réseaux sociaux + systeme.io
> Extrait en lecture seule de `rem-linux:/home/rempc/jarvis/scripts/dva/` le 2026-08-14.
> Rien n'a été copié SUR Rémi. Business de référence : domptezvotreargent.com (finance).
> But : répliquer la MÉTHODE pour nos plateformes (Pousseline, jarvis-delmas, systeme.io Franck).

## 1. L'architecture en une phrase
Une seule boucle : **générer (IA locale) → valider (humain via Telegram) → publier (API) →
mesurer (métriques par réseau) → régler (poids des patterns gagnants) → régénérer**.
Aucun post ne part sans validation, aucun réglage ne se fait sans données.

## 2. Les 6 briques par réseau

| Réseau | Génération | Publication | Mesure | Tuning |
|---|---|---|---|---|
| Instagram | `ig-calendar-fill-v2` (calendrier N+1, rotation pondérée piliers/hooks/CTA, 3 posts lun-mer-ven) + `ig-story-hook-gen` | manuel/planifié | `fetch-ig-metrics`, `track-ig-saves-sends` | `ig-tune-from-signals` (dimanche 16h : lit 7 j de signaux, ajuste `ig_winning_patterns.weight`) |
| LinkedIn | `linkedin-daily-pipeline` + posts autopilote | `linkedin-oauth-setup` → `linkedin-api-connect` → `linkedin-api-publish` (API officielle OAuth, pas de scraping) | pipeline-doctor logs | via repurposing |
| X / Reels / multi | `content-repurpose` : **1 post LinkedIn → caption IG + thread X + hook de Reel** (1 seule rédaction, 4 canaux) | — | `analyze-creative-performance` | — |
| WhatsApp commu | `generate-commu-drafts` (draft du jour via LLM local, 1 h avant le créneau) + `wa-communaute-compose` | `wa-communaute-auto` | — | — |
| Email/Newsletter | `generate-email-daily` (LLM local gemma3:27b) | `sio-newsletter-auto` (jeudi 08h30 : thème depuis une table `status='planned'`) | `score-email-subjects`, `funnel-weekly-compare` | `newsletter-auto-replan` (cron 09h) |
| Meta Ads | `create-meta-ads-battle` (A/B) | — | `fetch-meta-ads-metrics`, `check-pixel-meta` | `pause-campaign` |

## 3. La boucle de validation humaine (le vrai secret)
- Un cron pousse chaque brouillon sur **Telegram** (« DRAFT A POSTER — <slot> »).
- `telegram-drafts-handler` (cron toutes les 2 min, 8h-23h) écoute la réponse :
  OK → publie ; modif → régénère. L'humain reste l'éditeur en chef, l'IA fait le volume.
- Nouveau flux = d'abord en **mode OBSERVATION** 2-3 jours (`dsl-acquisition-observe` :
  log seulement, pas de push) avant d'armer les notifications.

## 4. systeme.io — tout par l'API (`api.systeme.io/api`)
- **Contacts** : `fetch-sio-contacts`, `fetch-sio-recent`, `segment-contacts`,
  `backfill-date-inscription`, champ téléphone ajouté par script.
- **Tags** : `sio-list-tags`, `sio-webi-autotagger`, `tag-after-webi`
  (tag automatique post-webinaire → segmentation comportementale).
- **Tunnel** : `fetch-sio-funnel-metrics` + `funnel-weekly-compare` (comparaison hebdo).
- **Newsletter** : `sio-create-newsletter` / `sio-newsletter-auto` avec **gate qualité**
  (voice-lint score ≥ 7 + regex « chiffres sourcés » avant envoi).
- **Conformité/robustesse** : patches GDPR pixel-gate, CMP, retry-submit,
  `watchdog-sio-leak`, `sio-post-webi-validator`.

## 5. Le closing (transformer l'audience en ventes)
- `identify-hot-leads` (cron 08h) : score composite **tags SIO + inscription récente +
  statut pipeline + téléphone renseigné** → TOP 10 classé HOT/WARM/COLD avec
  **action suggérée par lead** (appel, email perso, WhatsApp).
- `detect-inactive-clients`, `track-client-progress`, `webinar-debrief`,
  `generate-attendance-curve` (courbes de présence webinaire).

## 6. La garde de prod
- `production-guardian-urls` : cron 6h/12h/18h/22h, vérifie que les **URLs de vente
  répondent** (la page d'inscription surtout). C'est exactement ce qui nous manque :
  notre `franckdelmas00.systeme.io` est en 404 depuis des jours sans alerte.
- `vigile-check --telegram` : synthèse quotidienne 08h55 vers Telegram.
- `automation-health-check`, `cron-watchdog-inscription`, `prod-snapshot`.
- SEO : `gsc-weekly-diff` (diff hebdo Google Search Console, lundi 09h07).

## 7. Un design system écrit (DESIGN.md « Conversion DNA »)
Charte de conversion figée : fond blanc, navy #003366 + bleu action #149EFC,
boutons pilule, preuve sociale style captures WhatsApp, marquee d'urgence rouge,
et une liste d'**anti-patterns bannis** (dark mode, stock photos, mot « webinaire »).
→ À répliquer : écrire notre propre DESIGN.md par site avant tout contenu.

## 8. Mécanique de publication par réseau (« comment il automatise »)
- **Instagram** : file de posts sur disque (`ig-queue/001-…/reel.mp4 + caption.txt + .ready`),
  cron Lun-Mer-Ven 7h → `ig-auto-publish.sh` : **screener qualité automatique**
  (refuse « lien en bio », exige un CTA « commente/enregistre/dm », caption ≥ 50 car.,
  cadence max 1 post/20 h) → publie via **Graph API Meta** → déplace dans `_published/`
  → notifie Telegram. Un `ig-publish-watchdog.py` surveille le tout.
- **Facebook + Meta Ads** : même **Graph API Meta** (un seul jeton Business) ; serveur
  **MCP meta-ads** pour créer/mesurer/pauser les campagnes A/B depuis l'agent.
- **X** : pas de publication automatisée — moisson/analyse seulement, via
  `api.fxtwitter.com/status/<ID>` (texte intégral + métriques réelles, sans compte).
- **TikTok** : rien chez Rémi — chez nous c'est **Mirra** qui couvre TikTok (+ IG, Threads, YouTube).
- **Mirra bridge** (`integrations/mirr/auto_publish.py`) : liste de sujets → briefs Gemini →
  carousels Mirra → publication « toutes plateformes connectées ». Le multi-réseau, c'est Mirra.
- **WhatsApp / commu** : jamais d'envoi direct — `push-draft.sh <slot>` pousse un texte
  **prêt-à-copier-coller** sur Telegram (slots `whatsapp-sam-10h`, `commu-lundi-wins`…).
  L'humain colle. Zéro risque de ban.

## 9. Mode FORGE & Orfèvrerie (la méthode d'ingestion du savoir)
- **FORGE** = moisson → vérification à la source → distillation. Exemple X : le DOM
  tronque tout → dé-troncature systématique via fxtwitter, publicités écartées,
  et chaque fait non vérifié est marqué comme tel, jamais retenu.
- **Orfèvrerie symbiotique** (bidirectionnel Rémi↔Franck, `watch_and_forge_m6.sh`) :
  boucle qui attend que l'autre nœud soit en ligne (ping Tailscale) puis `rsync`
  **filtré** (que .md/.json/.sh/.py ; exclusions dures : `.env*`, `*.pem`, `*.key`,
  `.git`, historiques persos) vers un **staging** avant élévation dans board.db.
  Principe affiché : « excellence réciproque sans fuite de vie privée ».
- Chez nous : `protocole_orfevrerie_symbiotique.py` (remi-board-kit) fait pareil
  M1→board.db avec la même « confidentialité souterraine ».

## 10. Ordre de réplication chez nous (résumé actionnable)
1. **Guardian d'URLs** (cron 4×/jour sur jarvis-delmas + systeme.io + checkout) — 30 min, aurait détecté le 404.
2. **API systeme.io** : clé API Franck → répliquer fetch-contacts/tags/funnel (coffre age, jamais en clair).
3. **Boucle Telegram de validation** de drafts (on a déjà le bot + telegram_send MCP).
4. **Repurpose 1→4** : un contenu maître par semaine → LinkedIn + IG + X + Reel (Mirra publie déjà IG/Threads/TikTok/YouTube).
5. **Calendrier N+1 pondéré** + boucle de tuning hebdo sur les métriques.
6. **Hot-leads scoring** quand les contacts SIO rentrent.
