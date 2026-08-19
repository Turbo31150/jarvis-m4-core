[user] MISSION : audit LECTURE SEULE d'un dossier téléchargé pour décider quoi installer/adapter dans l'environnement JARVIS live de Rémi. N'ÉCRIS AUCUN fichier, n'installe rien, ne lance aucun script. Ne récupère JAMAIS de valeurs de secrets (mots de passe, tokens, clés API) — signale seulement leur PRÉSENCE.

DOSSIER À AUDITER : /home/rempc/Téléchargements/planning-app-main
(c'est un zip GitHub `-main`. Contient au top-level : bin, .claude, data, docs, .env.rempc, .env.rempc.bak-rempc, .gitignore, n8n, README.md, scripts, skills, systemd)

ENV LIVE de référence à comparer (pour distinguer NOUVEAU vs DÉJÀ PRÉSENT) :
- ~/jarvis (système JARVIS principal)
- ~/.claude/skills , ~/.claude/plugins , ~/.claude/settings.json (hooks)
- systemd user units : `systemctl --user list-unit-files 2>/dev/null` et ~/.config/systemd/user
- crons : `crontab -l 2>/dev/null`
- n8n : conteneur `jarvis-n8n` (docker) — ne t'y connecte pas, note juste que les workflows n8n vivent dans le conteneur

MÉTHODE (garde ton contexte léger, pas de dump brut de gros fichiers) :
1. Lis README.md + comprends le but de l'app en 1-2 phrases.
2. Énumère les ARTEFACTS INSTALLABLES : skills/ (liste noms + 1 ligne chacun), scripts/ (bin/), systemd/ (units), n8n/ (workflows JSON), .claude/ (hooks/agents/commands), .env.rempc (PRÉSENCE de secrets seulement).
3. Pour CHAQUE artefact notable : est-il DÉJÀ présent dans l'env live (compare noms de skills vs ~/.claude/skills, units vs systemctl, etc.) ? → NOUVEAU / DOUBLON / VERSI

[assistant] Let me gather the folder structure and live env in one batch, keeping raw bytes out of context.

[assistant] Good data. Let me nail down a few gaps: .env secret format, full bin listing, exact live-unit collisions, and whether the two skills exist elsewhere live.

[assistant] Two loops hit a shell-preload quirk. Let me rerun those checks plainly and grab the full env key names.

[assistant] I have everything needed. Here is the audit report.

## planning-app-main — ce que c'est
Un "planning de production autonome" JARVIS : agrège ~765 tâches (BACKLOG + SQLite `jarvis_master.db`) en une todolist unifiée, la déroule via une chaîne producer→executor→dominos, et sert un dashboard web temps réel sur le port **:8899**. C'est une extraction/fork d'un sous-système JARVIS packagé pour réinstallation. Les scripts sont conçus **locaux au projet** (`PLANNING_DATA_DIR`, `bin/`), pas `~/jarvis`.

## Artefacts installables
| nom | type | statut | réversible? | 1-ligne |
|---|---|---|---|---|
| jarvis-dominos | skill | NOUVEAU | oui | runner des 154 dominos (chaînes bash) |
| jarvis-planning | skill | VERSION-DIFF (live = `jarvis-planning-cli`) | oui | todolist unifiée dynamique |
| run-planning-app | skill (.claude) | NOUVEAU | oui | lance le widget + smoke test |
| bin/ (23 scripts) | py/sh | NOUVEAU (aucun équiv. `~/jarvis/bin`) | mixte | executor, producer, plan, router, widget… |
| install-hooks.sh + pre-commit | git hook | NOUVEAU | oui | scanner secrets gitleaks (fail-open, local au repo) |
| 9 units systemd (×service+timer) | systemd | TOUS NOUVEAUX | oui (disable) | timers autonomes 5–180 min |
| 5 workflows n8n | JSON | NOUVEAU (à importer) | oui | IMAP/LinkedIn/prospection/NotebookLM |
| .env.rempc | config | — | oui | 8 clés config, **pas de secret** |
| data/*.db | sqlite | NOUVEAU | oui | plans locaux (jarvis_master.db = 0 octet) |

## Nouveau & utile (top 5)
1. *