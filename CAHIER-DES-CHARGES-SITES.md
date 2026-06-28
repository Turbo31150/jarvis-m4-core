# Cahier des charges — Écosystème de sites Netlify (Franck Delmas)

> Version 1.0 — 2026-06-28 · Périmètre : 9 sites Netlify (team `franckdelmas00`)
> Objectif : diversifier chaque site par **marque → service → secteur → cible**, corriger les
> problèmes de crédibilité, et structurer un entonnoir de vente cohérent à 4 marques.

---

## 0. Décisions actées (par le client)

1. **On garde les 4 marques** — chacune affectée à une **ligne de service et une cible différentes**
   (pas de fusion en une marque unique).
2. **On ne supprime aucun site** — on les **diversifie** : chaque site reçoit des offres distinctes
   (packs d'accompagnement multi-paliers, formations, partage d'écran, intervention système),
   ciblées par secteur d'activité.
3. Livrable : **cahier des charges + deep-research + plan + todolist + protocole** (ce document).

---

## 1. Deep-research marché (France, 2026) — ancrage prix & positionnement

| Donnée | Valeur marché 2026 | Implication pour nous |
|---|---|---|
| TJM consultant IA confirmé | 600–900 €/j (junior 300–500, expert >700) | TJM actuel 550–700 € → **monter à 650–850 €** côté AlkymIA-OS/expert |
| Projet automatisation ponctuel | ~1 500 € | Plancher AutomatIA Starter OK (1 490 €) |
| Médiane projet PME sérieux | 5 000–15 000 € | Cœur de cible AlkymIA-OS Starter/Pro |
| Déploiement full-stack (self-host + monitoring + formation) | jusqu'à 50 000 € | Enterprise 50–80k€ crédible **si preuves réelles** |
| Concurrents FR directs | Hyperstack, Sequance, NoCode Factory (bureau **Toulouse**), agences n8n | Se différencier par **souveraineté on-premise + voix <300ms** |
| Conversion landing **single-CTA** | **13,5 %** vs 10,5 % multi-CTA | Pages de niche 1 problème→1 CTA = priorité |
| Hero clair (vs malin/ambigu) | +35–40 % conversion | Bannir les hero abstraits ("Alchimie numérique") sur les pages d'acquisition |
| −40 % de champs de formulaire | +30–50 % conversion | Formulaires diag : nom + email + 1 champ max |

**Sources :** [plateya — TJM consultant IA 2026](https://www.plateya.fr/blog/detail/tarif-consultant-ia-en-2026-guide-complet-fourchettes-et-conseils) · [pricingpro](https://pricingpro.fr/consultant-ia) · [koino — top agences IA FR](https://www.koino.fr/articles/top-10-des-agences-ia-en-france-2026-tarifs-clients-exemples) · [inno-mation — top agences n8n FR](https://inno-mation.com/blog/top-10-agences-ia-and-automatisation-n8n-france-2026-le-classement-complet) · [lafabriquedunet — agences no-code](https://www.lafabriquedunet.fr/agences/pages/agences-nocode) · [causalfunnel — benchmarks conversion B2B SaaS 2026](https://www.causalfunnel.com/blog/b2b-saas-funnel-conversion-benchmarks-2026-data-insights/) · [saashero — landing best practices 2026](https://www.saashero.net/design/enterprise-landing-page-design-2026/)

---

## 2. Architecture des 4 marques (segmentation cible)

| Marque | Positionnement | Cible | Ticket | Sites rattachés |
|---|---|---|---|---|
| **AlkymIA-OS** | Infrastructure IA souveraine on-premise (produit phare) | PME · ESN · industrie | 5 k – 80 k€ | `alkymia-os` (hub), `alkymia-oss` |
| **AutomatIA** | Automatisation métier **par secteur** (no/low-code) | TPE/PME sectorielles | 1,5 k – 3,5 k€ | `automatia` (ex-`euphonious-youtiao`) |
| **JARVIS OS** | Académie / écosystème dev / open-source | Devs · freelances · makers | 39 – 597 € | `jarvis-products` (catalogue), `bespoke-pony` → Academy |
| **Franck Delmas** (nom propre) | Le consultant — services humains directs, entrée de gamme | Particuliers → pros | 19 – 290 € + TJM | `admin-ia`, `agent-sans-coder`, `transcription-ia`, `reparation-ia` |

> ⚠️ **Risque juridique « JARVIS »** : marque Disney/Marvel (Iron Man). Tolérable sur une niche
> dev/open-source confidentielle, **à ne pas pousser en marque grand public**. Plan B de nom :
> *« OpenClaw Academy »* ou *« AlkymIA Academy »*.

### Modèle hub & spokes
```
   Franck Delmas (la personne / l'expert, TJM, partage écran)
        │  caution humaine + entrée de gamme B2C
        ▼
  ┌───────────────┬────────────────┬─────────────────┐
  │ AlkymIA-OS    │ AutomatIA      │ JARVIS Academy  │
  │ (infra PME)   │ (secteurs TPE) │ (formations dev)│
  └───────────────┴────────────────┴─────────────────┘
   spokes B2C (admin-ia, reparation-ia, transcription, agent-sans-coder)
   = 1 page = 1 pub = 1 problème → CTA → marque adéquate
```

---

## 3. Spécification par site (9 fiches)

> Pour chaque site : **objectif · cible/secteur · offre diversifiée (paliers) · CTA principal · corrections**.
> Échelle de paliers commune : **Gratuit (lead) → Guidé/partage écran → Fait-pour-vous → Abonnement/SLA**.

### 3.1 `alkymia-os` — AlkymIA-OS · HUB infra souveraine
- **Objectif** : site mère B2B premium + catalogue + booking.
- **Cible** : PME/ESN/industrie, décideurs technique.
- **Offre (paliers)** : Déploiement Starter 5–15k / Pro 15–50k / Enterprise 50–80k€ · add-ons MCP Toolkit 2–10k · Agent vertical 3–30k · Pipeline voix 100–1500/mois · **Premium** Suivi 149/mois → Pack 349/mois → SLA entreprise · Formation expert live 19h 2400€.
- **CTA** : « Réserver un audit / démo 30 min ».
- **Corrections** : alléger le hero (« Alchimie numérique » trop abstrait → bénéfice concret) ; UNIFIER les chiffres (voir §4) ; retirer faux témoignages.

### 3.2 `alkymia-oss` — AlkymIA-OS · landing acquisition PME
- **Objectif** : page d'acquisition payante (Meta/Google) vers le hub.
- **Cible** : TPE/PME/industrie cherchant « automatiser mon activité ».
- **Offre** : 4 packs 490 / 1490 / 3900 / Industrie-devis + services à la carte (audit 290, infra 190, conseil 150, dépannage 90/h).
- **CTA** : « Audit gratuit 0€ ».
- **Corrections P0** : **bug compteurs hero « 0 agents / 0 chaînes »** → chiffres réels ou retrait ; email `miningexpert31` → `franckdelmas00` ; témoignages Marie L./Pierre R. → requalifier « exemple illustratif ».

### 3.3 `automatia` (ex-`euphonious-youtiao-56dd0d`) — AutomatIA · secteurs
- **Objectif** : automatisation métier déclinée **par secteur**.
- **Cible/secteur** : boutique, industrie, resto/hôtel, immobilier, santé, artisan/PME.
- **Offre** : Starter 1490 / Pro 3490 / Enterprise-devis + à la carte (audit 490, dépannage 190/h, calcul infra, implantation sur site) + **accompagnement mensuel** par secteur.
- **CTA** : « Diagnostic gratuit ».
- **Corrections** : **renommer le slug** `automatia` ; ajouter 1 page/section par secteur (SEO longue traîne) ; preuve sociale réelle ou neutre.

### 3.4 `admin-ia` — Franck Delmas · démarches administratives (B2C)
- **Cible** : particuliers/familles (impôts, CAF, MDPH, permis, carte grise, retraite).
- **Offre (paliers)** : Repérage gratuit → **Guidé partage écran 19€** → Dossier complet 79€ → Suivi annuel 15€/mois.
- **CTA** : « Trouver ma démarche ».
- **Corrections** : ajouter FAQ + bandeau confidentialité (données sensibles) ; preuves/réassurance ; relier à la marque Franck Delmas.

### 3.5 `agent-sans-coder` — Franck Delmas · 1er agent IA (B2C/TPE)
- **Cible** : novices, TPE qui veulent automatiser une tâche répétitive.
- **Offre** : Guide PDF gratuit (lead magnet) → **Séance partage écran 39€** → Agent sur-mesure 290€.
- **CTA** : « Trouver mon agent » / télécharger le guide.
- **Corrections** : capturer l'email du lead magnet ; ajouter cas d'usage par métier ; up-sell vers AutomatIA.

### 3.6 `transcription-ia` (ex-`transcription-ia-jarvis`) — Franck Delmas · transcription
- **Cible** : pros médias, journalistes, cabinets, podcasteurs.
- **Offre** : 5 min offertes → 9€/heure → Pro pipeline 49€/mois (volume illimité, 100% local).
- **CTA** : « Estimer ma transcription ».
- **Corrections** : **renommer slug** (retirer `jarvis`) ; ajouter démo/échantillon ; preuve de précision (WER) honnête.

### 3.7 `reparation-ia` — Franck Delmas · dépannage système (B2C→B2B) ⭐ référence UX
- **Cible** : du particulier novice à l'admin sys (Linux/macOS/Windows).
- **Offre** : Diagnostic gratuit (commande terminal) → **Guidé 29€** → Intervention 89€ → Audit entreprise 290€/poste → Accompagnement 49€/mois.
- **CTA** : « Diagnostic express gratuit ».
- **Corrections** : ✅ déjà le meilleur tunnel — **servir de gabarit** aux autres mono-produits ; ajouter garantie réaliste.

### 3.8 `jarvis-products` — JARVIS OS · catalogue formations + pitches Enterprise
- **Objectif** : boutique formations PDF + pitches commerciaux.
- **Cible** : devs, freelances, décideurs évaluant l'infra.
- **Offre** : 62 formations 39–149€ · Pack 399€ · Pitches Enterprise 29–79€ · Premium dev.
- **CTA** : « Module 1 gratuit » / « Acheter le pack ».
- **Corrections** : démos Loom « sur demande » → **vraies vidéos ou retrait** ; UNIFIER chiffres ; clarifier la frontière avec AlkymIA-OS (formations ici, déploiement là-bas).

### 3.9 `bespoke-pony-491fd1` — → repurposer en **JARVIS Academy** (Claude Code Mastery)
- **Décision** : pas de suppression → **réaffectation**. Devient le site dédié **cohort Claude Code Mastery**.
- **Cible** : devs qui veulent construire leur propre système d'agents.
- **Offre** : Module 1 gratuit → M2 177€ → M3 597€ → Bundle 477€ (Discord, templates, MAJ à vie).
- **CTA** : « Recevoir le Module 1 gratuit ».
- **Corrections** : **renommer slug** `jarvis-academy` ; retirer le doublon de catalogue infra (renvoyer vers AlkymIA-OS) ; chiffres réels (record/benchmark vérifiables).

---

## 4. Corrections transverses (s'appliquent à TOUS les sites)

| # | Problème | Action | Priorité |
|---|---|---|---|
| T1 | Compteurs « 0 agents / 0 chaînes » (`alkymia-oss`) | Chiffres réels OU retrait du bloc | **P0** |
| T2 | Chiffres contradictoires (agents 0/249/900/928/1000 ; GPU 5/6/12) | **1 source unique** de vérité → réplication | **P0** |
| T3 | Emails incohérents (`miningexpert31` vs `franckdelmas00`) | Unifier sur `franckdelmas00@gmail.com` | **P0** |
| T4 | Faux témoignages (Marie L., ESN Paris, CTO…) + « garanti remboursé » | Retirer ou requalifier « exemple illustratif/projection » (risque DGCCRF, art. L121-2) | **P0 (légal)** |
| T5 | Métriques invérifiables (ROI +340%, Sharpe 1.8–2.4, −92%) | Mentionner « estimation/backtest, perf passée ≠ future » ou retirer | **P0 (légal)** |
| T6 | Slugs auto-générés (`euphonious…`, `bespoke…`) | Renommer (§3) | P1 |
| T7 | Mentions légales / CGV / RGPD | Vérifier qu'elles existent et sont réelles sur chaque site | P1 |
| T8 | « JARVIS » (risque marque Disney) | Cantonner à la niche dev ; préparer plan B de nom | P2 |
| T9 | SEO : 3 méga-sites au contenu dupliqué | Différencier le contenu (§3) + canonical/redirections internes | P1 |

---

## 5. Protocole de production (par site, répétable)

```
ÉTAPE 0  Localiser les sources HTML de chaque site (repo local ou export Netlify)
ÉTAPE 1  Appliquer les corrections P0 transverses (T1–T5) — bugs + légal + cohérence chiffres
ÉTAPE 2  Affecter la marque + le positionnement (§2) : hero, nom, couleurs, footer
ÉTAPE 3  Réécrire l'offre en paliers (Gratuit→Guidé→Fait-pour-vous→Abonnement) (§3)
ÉTAPE 4  Diversifier par secteur (AutomatIA) / par démarche (Franck Delmas)
ÉTAPE 5  Optimiser conversion : 1 CTA principal, hero bénéfice, formulaire ≤3 champs
ÉTAPE 6  Renommer le slug Netlify (T6) + vérifier mentions légales (T7)
ÉTAPE 7  Recette : liens, formulaires, mobile, vitesse ; déploiement Netlify
ÉTAPE 8  Tracking : event CTA + source UTM par spoke → mesurer conversion
```

**Règle de délégation (CLAUDE.md LOI #2)** : réécriture de copy/section → `lm-ask.sh` (local) ;
orchestration/archi/validation finale → Opus. Audit visuel/recette → navigateur Chrome.

---

## 6. Todolist priorisée

### P0 — Crédibilité & légal (à faire avant toute pub)
- [ ] T1 Corriger le bug compteurs `alkymia-oss`
- [ ] T2 Définir la source unique de chiffres (agents/GPU/latence) + propager
- [ ] T3 Unifier l'email sur tous les sites
- [ ] T4 Retirer/requalifier les faux témoignages + « garanti remboursé »
- [ ] T5 Encadrer les métriques (mentions « estimation / perf passée ≠ future »)

### P1 — Structure & marques
- [ ] Affecter chaque site à sa marque (§2) — hero, footer, identité
- [ ] Renommer slugs : `automatia`, `transcription-ia`, `jarvis-academy`
- [ ] Repurposer `bespoke-pony` en JARVIS Academy (retirer doublon infra)
- [ ] Diversifier `automatia` par secteur (6 sections/pages)
- [ ] Réécrire les offres en paliers sur les 4 sites Franck Delmas
- [ ] Vérifier mentions légales / CGV / RGPD partout
- [ ] Capturer les emails des lead magnets (admin-ia, agent-sans-coder)

### P2 — Optimisation & croissance
- [ ] Plan B de nom pour « JARVIS » (risque marque)
- [ ] Démos Loom réelles ou retrait (`jarvis-products`)
- [ ] Tracking UTM + events CTA par spoke
- [ ] SEO : contenu différencié + canonical
- [ ] A/B test hero & CTA sur la page la plus trafiquée

---

## 7. KPIs cibles (post-refonte)

| Métrique | Cible |
|---|---|
| Conversion landing de niche (single-CTA) | ≥ 8 % (marché : 13,5 % top) |
| Demande de démo (pages B2B) | 1,5–4 % |
| Cohérence chiffres inter-sites | 100 % (0 contradiction) |
| Sites avec mentions légales valides | 9/9 |
| Faux témoignages restants | 0 |
```
