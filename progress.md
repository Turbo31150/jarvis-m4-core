# progress.md — journal de session

## Session 2026-08-18 → 19, M4 (`pamerys-m4`)

### Ce qui a été livré

| Livrable | Chemin | État |
|---|---|---|
| Superposition + vectorisation | `scripts/dispatch_superposition.py` | 141/141 en 535 s, 0 abandon |
| Analyse de superposition | `scripts/analyse_superposition.py` | collapse + template + centroïde |
| Correctif longueur LinkedIn | `scripts/fix_notes_280.py` | 51/51 sous 280 c |
| Index FTS5 des skills | `scripts/index_skills_fts.py` | 40 073 entrées, 12 s |
| Préchargeur enrichi | `scripts/precharge_taches.py` | 0 → 91 % d'appariement |
| Moissonneur multi-sources | `scripts/moisson_multi_source.py` | 257 signaux, idempotent |
| Chaînon cascade manquant | `bin/cascade-massive.sh` | 4 781 tâches en `file_actions` |

### Tables créées ou remplies (`jarvis_master.db`)

`simulation_superposition` (141) · `skills_index` + `skills_index_fts` (40 073) ·
`moisson_signaux` (257) · `file_actions` (4 781) · `plan.preloaded` (12 792 rescannées)

### Vérifications passées

- [x] A1 — 40 073 entrées indexées, recherche « linkedin » remonte les deux racines, 3 ms
- [x] A3 — skill apparié : 0 → 11 684 (91 %), longueur 84 c → 512 c
- [x] B1 — idempotence : second passage, delta = 0
- [x] D1 — préchargement des nouvelles lignes : 11/11 chemins existent réellement
- [x] D2 — dispatch : pending 11 → 2
- [ ] B2 — plafond LinkedIn : non testé, script non écrit
- [ ] C2 — cohérence des clusters : non testée, script non écrit
- [ ] Bout en bout — un signal moissonné n'est pas encore tracé jusqu'à une ligne de file

### Corrections apportées à des fichiers existants

- `~/.claude/skills/cascade-massive/SKILL.md` — deux constats périmés corrigés
  (étape 1 réputée HS mais réparée ; garde-fou GPU réputé inactif mais redevenu actif).
  Sauvegarde : `SKILL.md.bak-20260819`.
- `bin/cascade-massive.sh` — routage séparé entre file d'installation et file d'action,
  après échec mesuré.

### Session du 19/08 — suite (volets E, F, G)

| Livrable | Chemin | État |
|---|---|---|
| Module de parade partagé | `scripts/m6_parade.py` | lève `M6Muet`, jamais de vide silencieux |
| Table ronde corrigée | `~/.local/bin/jarvis-table-ronde` | conclusion au lieu de raisonnement brut |
| Widget cockpit corrigé | `bin/jarvis-planning-widget.py` | faux succès → 502, service redémarré |
| Consensus multi-LLM | `scripts/multi-llm-orchestrate.py` | FAIBLE 0,538 → FORT 1.0 |
| Pagination moisson | `scripts/moisson_multi_source.py` | 428 → 1 855 signaux |
| Garde thermique | `scripts/patterns_marche.py` | repli CPU interdit, arrêt à 85 °C |

**BrowserOS réparé** (panne signalée par Turbo) : figé après 9 h 17. Premier redémarrage en
`setsid` échoué — session Wayland, perte du socket graphique, 0 renderer. Réussi en
préservant `DISPLAY`/`WAYLAND_DISPLAY`/`XDG_RUNTIME_DIR` : 9 renderers + `browseros_server`.

### Reste à faire

1. **B2** — `moisson_linkedin_cdp.py` sur le CDP `:9100`, plafond dur ≤ 40 pages/jour,
   ≥ 20 s entre requêtes, arrêt net si le profil n'est plus authentifié.
2. **C** — superposition par pattern : N interprétations par signal, clustering,
   table `patterns_marche`, rescan borné à 3 tours.
3. **Traçabilité bout en bout** — critère 7 du plan, non vérifié.
4. **Décision utilisateur en attente** — les 26 skills gstack orphelins :
   installer / marquer / retirer.

### Hors périmètre de ce plan, mais toujours ouvert

- `OLLAMA_API_KEY` exposée en clair par une de mes commandes → à révoquer sur ollama.com.
- Giovanna FERRETTI — limite de candidature **21/08/2026**.
- 5 startups non contactées : Univity, Elda Technology, ATEA, IoT Valley, InsightKeeper.
- La vidéo `campagnes/linkedin-toulouse-20260818/video/demo_jarvis_os.mp4` n'est pas
  attachée au post publié.

### Ce que ce travail ne résout pas

La table ronde (11 moteurs) et la grille produit convergent : le facteur décisif d'une
première signature est **l'absence de preuve tangible**, pas la qualité des messages.
Ce plan outille la détection du besoin. Il ne fabrique pas de crédibilité — et il ne
faut pas confondre les deux.
