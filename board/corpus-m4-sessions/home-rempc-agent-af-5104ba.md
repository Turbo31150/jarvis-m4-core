[user] MISSION : audit LECTURE SEULE d'un GROS dossier téléchargé (2,5 Go, ~95000 fichiers) pour décider quoi installer/adapter dans l'environnement JARVIS live de Rémi. N'ÉCRIS AUCUN fichier, n'installe rien, ne lance aucun script. Ne récupère JAMAIS de valeurs de secrets — signale seulement leur PRÉSENCE.

DOSSIER À AUDITER : /home/rempc/Téléchargements/jarvis-linux-main
C'est très probablement le REPO GitHub du système JARVIS de Rémi (contient CLAUDE.md, AGENTS.md, core/, infra/, config/, docs/, skills, package.json, pyproject.toml, requirements.txt, etc.). L'ENV LIVE est ~/jarvis. L'enjeu : ce n'est PAS une app à écraser — il faut identifier le DELTA (ce que le repo a et que le live n'a pas, ou versions plus récentes) pour "installer que ce dont Rémi a besoin".

CONTRAINTE PERF : NE PAS récurser dans les gros dossiers lourds (node_modules, .git, data/, assets/, caches, venv, contexte-maximal si volumineux). Utilise `du -sh */ 2>/dev/null` pour repérer le poids, `find` avec -maxdepth, et cible les répertoires de CODE/SKILLS/CONFIG.

ENV LIVE de référence :
- ~/jarvis (compare structure top-level, bin/, skills, scripts, config)
- ~/.claude/skills , ~/.claude/plugins
- Compare versions : `git -C ~/jarvis log -1 2>/dev/null` si repo git ; README/VERSION ; dates de fichiers.

MÉTHODE :
1. Survol : README.md + CLAUDE.md du repo → à quoi sert ce repo, est-ce bien le miroir de ~/jarvis ? En 2-3 phrases.
2. `du -sh /home/rempc/Téléchargements/jarvis-linux-main/*/ ` → carte du poids (où s

[assistant] I'll start by loading the context-mode tools so I can do the heavy filesystem analysis in the sandbox without flooding my context.

[assistant] I'll do the heavy filesystem analysis in the context-mode sandbox to keep raw bytes out of my context. Starting with a survey batch.

[assistant] Repo is a GitHub "main" tarball extraction (not a git repo itself), 2.5G with `src/` = 2.0G. Live `~/jarvis` is a real git repo (last commit 2026-07-12, PR #542). Now let me compute the delta programmatically and break down the heavy `src/`.

[assistant] Critical structural finding: `inRepoNotLive = 0` at top level, and every code dir shows `onlyInRepo=0` — the repo appears to be a **subset** of live (live is a superset with far more files: scripts 193 vs 49, core 52 vs 8, docs 126 vs 50). Let me verify whether repo *content* is newer/older, what the 1.9G `src/jarvis` actually is, and confirm secrets handling.

[assistant] Now the picture is definitive. Let me run one final verification: confirm live also contains `src/jarvis` (so the 1.9G isn't new), confirm the `.env.rempc` secret-file presence in the download, and quantify content drift on shared files via a lightweight diff.

[assistant] Audit complete. The premise inverted under investigation — findings below.

## jarvis-linux-main — ce que c'est (repo vs live ~/jarvis)
Ce n'est **pas un upstream à intégrer** : c'est un **export/snapshot sanitisé de ton propre `~/jarvis` live**, généré le **2026-07-28 07:21** (tarball GitHub "main", décompressé — pas un dépôt git, `git log` vide). Titre README : *"JARVIS OS — Just A Rather Very Intelligent System"*. Preuve : **0 fichier top-level présent dans le repo et absent du live**, et tous les fichiers racine partagés (README, CLAUDE.md, package.json, pyproject.toml, IDENTITY.md…) sont **byte-identiques** (même md5, même taille, même date). Le live est le **sur-ensemble** ; le repo en est un **sous-ensemble strict**.

## Carte du poids (où sont les 2,5 Go)
- `src/` **2,0 Go** → dont `src/jarvis` **1,9 Go** → dont **`src/jarvis/services/data` = 1,3 Go** (données bundlées qui n'auraient jamais dû être packagées) + `src/jarvis/core` 505 Mo.
- `modules/` 84 Mo · `piper/` 49 Mo (voix TTS) · `assets/` 30 Mo · `docs/` 25 Mo · `src/extern/` 97 Mo.
- Le code réel (core, config, scripts, skills) pèse **< 2 Mo**. Les 2,5 Go = **99% data/modèles/audio bundlés**, pas du code.

## Delta repo → live (nouveau dans le repo, absent du live)
| Catégorie | Verdict |
|---|---|
| Top-level nouveau | **0** (repo ⊆ live) |
| skills/ | repo **1** (`jarvis-planning-cli`, identique) vs live **22** |
| bin/ | **absent du repo** ; live=20 |
| core/ | repo=8 ⊂ live=52 (drift = 160 lignes, **toutes 