[user] MISSION : audit LECTURE SEULE d'un dossier téléchargé pour décider quoi installer/adapter dans l'environnement JARVIS live de Rémi. N'ÉCRIS AUCUN fichier, n'installe rien, ne lance aucun script (surtout pas GO.sh). Ne récupère JAMAIS de valeurs de secrets — signale seulement leur PRÉSENCE.

DOSSIER À AUDITER : /home/rempc/Téléchargements/labo-bibliotheque-centrale-main  (29 Mo, ~1242 fichiers, ~189 dossiers)
Top-level connu : BENCH-LLM-MODELS.md, bibliotheque/, BILAN-VITESSE.md, CAHIER-DEMO-SNAKE.md, DEMO-BIBLIO-VS-MODEL.md, .env.rempc, GO.sh, GO.sh.bak-rempc, MEGA-PROMPT-CLAUDE-CODE.md, mirror-systemeio/, n8n-publier-snake-benchmark.json, POST-BROWSEROS-BIBLIO.md, POST-SNAKE-BENCHMARK.md, PROTOCOLE-1.md, README.md, sites-work/, TODOLIST_JARVIS_M1.md

ENV LIVE de référence à comparer (NOUVEAU vs DÉJÀ PRÉSENT) :
- ~/jarvis , ~/.claude/skills , ~/.claude/plugins , ~/.claude/settings.json
- `systemctl --user list-unit-files 2>/dev/null` , ~/.config/systemd/user
- `crontab -l 2>/dev/null`
- n8n workflows vivent dans le conteneur jarvis-n8n (ne t'y connecte pas)

MÉTHODE (contexte léger, pas de dump brut) :
1. Lis README.md + PROTOCOLE-1.md (survol) → but du projet en 1-2 phrases. C'est quoi "bibliotheque centrale" ? un benchmark LLM ? un mirror de site systeme.io ? Clarifie.
2. Explore la STRUCTURE (bibliotheque/, sites-work/, mirror-systemeio/) sans tout lire — comprends ce que chaque grand dossier contient.
3. Énumère ARTEFACTS INSTALLABLES : scripts (GO.sh et co), n8n JSON, év

[assistant] I'll start by loading the context-mode tools, then explore the target folder structure in read-only mode.

[assistant] I'll gather the folder structure, key docs, and compare against the live environment in one batch, keeping raw bytes out of context.

[assistant] Good structure captured. Now let me get the remaining details: full GO.sh actions, the bundled `.claude/skills`, sites-work, mirror-systemeio, n8n JSON, hardcoded paths, and the README/PROTOCOLE narrative.

[assistant] ## labo-bibliotheque-centrale-main — ce que c'est
Un **"biblio-routeur" local-first auto-contenu** (l'app "LABO"). Concept: avant d'exécuter une tâche, on la cherche dans une bibliothèque de "blocs/séries/tasks" et on la route vers le backend le moins cher (ollama/OpenClaw cascade) — exactement l'esprit LOI#1. Ce n'est PAS un mirror de systeme.io ni un simple benchmark: le **snake-bench** (IA Snake BFS+flood-fill, 0 LLM/0 GPU) n'est qu'une démo reproductible "biblio vs model". Construit sur une autre machine (user **`turbo`**, nœud cluster M1), puis téléchargé ici.

## Contenu par grand dossier
- **bibliotheque/ (28 Mo, 1215 f)** : le cœur. `series/` = 209 scripts "domino" 0-token, `lib/` (116), `agents/` (78 catalogues d'agents), `reproductions/` (663 fichiers = logs/plans de runs passés, pas installable), `.claude/skills/` (3 skills), `ecommerce/`, `prospection/`, `vault/`, `modes/`.
- **sites-work/ (304 Ko, 5 f)** : prototypes HTML (jarvis-delmas 125Ko, alkymia-os 110Ko, jarvis-ia-services, passcerfa) + RECAP-DIFFS. Contenu web, pas d'infra.
- **mirror-systemeio/ (40 Ko, 7 f)** : inventaire de sites déployés (live-status.txt, netlify-titles.txt, github-repos.json), pas un vrai mirror.
- **autres** : docs .md + GO.sh + n8n JSON + .env.rempc.

## Artefacts installables
| nom | type | nouveau/doublon | réversible? | 1-ligne |
|---|---|---|---|---|
| bibliotheque/ (209 séries + 78 agents) | app scripts | NOUVEAU | oui (dossier isolé) | router local "biblio-first" |
| .claude/s