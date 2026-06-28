# Croissance des 9 sites — Ressources MAX + Todolist annuelle dynamique (avec tests/KPI)

> Distribution **éthique** (zéro link-spam, conforme CGU, bon pour le SEO). Chaque item a un
> « test » = critère de validation mesurable. Plan dynamique : ne passer à la phase suivante
> qu'une fois les tests de la phase verts.

## 1. Liste de ressources MAX (canaux légitimes)

### Annuaires / marketplaces freelance (backlinks propres + leads)
- Malt, Codeur.com, Comet, FreelanceRepublik, 404Works, LeHibou (B2B/ESN)
- n8n Experts (experts.n8n.io), Make Partners, Awesome-selfhosted (PR GitHub)
- Product Hunt, BetaList, AlternativeTo, SaaSHub, Indie Hackers Products

### Communautés (apporter de la valeur, lien en contexte/signature)
- Reddit : r/automation, r/selfhosted, r/LocalLLaMA, r/SideProject, r/france, r/entrepreneur
- Discord/Slack : LocalLLaMA, n8n, indie hackers FR, communautés Claude/MCP
- Forums FR : Hardware.fr, Developpez.net, LinuxFr, forums e-commerce (WPFR, PrestaShop)
- Hacker News (Show HN pour AlkymIA-OS / un projet open-source)

### Réseaux (contenu propre, pas de commentaires-spam)
- LinkedIn (profil existant) : 3 posts/semaine, carrousels techniques
- YouTube : TA chaîne — démos AlkymIA-OS, tutos Claude Code (PAS de commentaires sur d'autres)
- X/Threads/TikTok : déjà couverts par Mirra (autopublisher) — réactiver
- GitHub (Turbo31150) : READMEs soignés = vitrine + SEO (60 repos MIT)

### SEO / contenu
- 1 blog par hub (AlkymIA-OS, AutomatIA) : articles de niche par secteur/cible
- Google Business Profile (Toulouse, France) — pour le local B2B
- Référencement annuaires IA : there's-an-ai-for-that, futuretools, aitools.fr

### Partenariats / distribution
- Gumroad (déjà : franckdelmas.gumroad.com) pour les 62 formations
- Affiliation / cross-promo avec d'autres freelances IA FR
- Webinaires / lives avec communautés (n8n FR, NoCode FR)

## 2. Todolist annuelle dynamique (4 trimestres) — avec tests/KPI

### T1 — Fondations & preuve (mois 1-3)
| Tâche | Test (KPI de validation) |
|---|---|
| Déployer les 9 sites corrigés + renommer slugs | 9/9 en ligne, 0 chiffre incohérent, mentions légales OK |
| Compléter SIRET + CGV réelles | Pages légales valides sur 9/9 |
| Google Business Profile + 3 annuaires freelance | Profil vérifié + 3 fiches publiées |
| LinkedIn : 12 posts (3/sem × 4 sem sur 1 mois pilote) | ≥ 1 post > 1000 impressions |
| 1 vidéo démo YouTube (AlkymIA-OS) | Vidéo publiée + intégrée au hero du hub |
| Tracking UTM + events CTA par spoke | Dashboard de conversion fonctionnel |

### T2 — Acquisition (mois 4-6)
| Tâche | Test |
|---|---|
| Lancement Product Hunt (AlkymIA-OS ou AutomatIA) | ≥ Top 10 du jour OU 100 upvotes |
| 8 réponses value-first Reddit/forums/mois | 0 suppression (preuve : non perçu spam) + trafic référent mesurable |
| Inscription n8n Experts + Make Partners | 1 listing accepté |
| 4 articles SEO de niche (1/secteur AutomatIA) | ≥ 1 article indexé top 20 Google sur sa requête |
| Réactiver Mirra (5 réseaux, cron daily) | Publication auto vérifiée 7j/7 |

### T3 — Conversion & optimisation (mois 7-9)
| Tâche | Test |
|---|---|
| A/B test hero + CTA sur la page la plus trafiquée | Variante gagnante ≥ +15 % conversion |
| Upgrade capture leads (mailto → Netlify Forms) | Leads stockés + relançables (0 perdu) |
| Identités visuelles distinctes finalisées (polices) | 4 marques visuellement distinctes, 0 régression layout |
| 1 webinaire/live communauté | ≥ 20 inscrits |
| Cohort Claude Code Mastery — 1ère promo | ≥ 5 ventes Module 2/3 |

### T4 — Échelle & récurrence (mois 10-12)
| Tâche | Test |
|---|---|
| Programme d'affiliation/cross-promo | ≥ 2 partenaires actifs |
| Newsletter (lead magnets → séquence email) | Liste ≥ 200 abonnés, open rate ≥ 30 % |
| Étendre AutomatIA (1 page/secteur dédiée) | 6 pages sectorielles indexées |
| Bilan annuel + réallocation budget pub | ROI par canal calculé, top 3 canaux identifiés |

## 3. Les 5 erreurs à NE PAS faire
1. **Link-spam** forums/YouTube comments → bannissement + pénalité Google (l'inverse de l'objectif).
2. Poster le **même message** partout (duplicate) → filtré comme spam.
3. Négliger les **mentions légales/CGV** → risque DGCCRF + perte de confiance.
4. **Chiffres invérifiables** → un prospect technique vérifie, crédibilité détruite.
5. Tout miser sur **1 canal** → diversifier (annuaires + communautés + SEO + propre contenu).

## 4. Cascade 0-token — à réparer (bloquant pour générer ce type de doc gratuitement)
- `gemini-smart.sh` renvoie « 5000 » pour tout prompt → le wrapper Gemini CLI est cassé (à déboguer : la sortie de la commande `gemini` ne remonte pas).
- M1/M2 (cluster LM) **down** → seul OL1 local reste.
- **RAM à 94 %** → OL1 (Ollama) timeout/lent. Libérer la RAM rétablit le chemin local.
