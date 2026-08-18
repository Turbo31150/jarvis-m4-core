[user] Mission JARVIS (M1, réponds en français) : lecture massive de GitHub sur le thème « meilleures performances et actions des youtubeurs professionnels » (croissance chaîne, rétention, titres/miniatures, SEO YouTube, cadence, analytics, automation vidéo).

1. Via `gh search repos` + `gh api` (compte connecté) : identifie 10-15 repos à fort signal (awesome-lists, outils analytics YouTube, guides growth, automation shorts/longform). Lis leurs README/docs clés (gh api contents, pas de clone massif).
2. Synthétise en actions concrètes et mesurables de youtubeur pro : hooks 0-3s, structure de rétention, titres/CTR, miniatures, cadence, SEO/tags, analytics à suivre, réutilisation shorts, erreurs classiques.
3. Livrables (écris réellement les fichiers) :
   a. `/home/turbo/jarvis/data/biblio_knowledge/youtube-pro-performances-github.md` — fiche de connaissance structurée avec sources (repo + lien).
   b. `/home/turbo/prompts/prompts/claude-code/youtube-pro-actions.md` — PROMPT réutilisable : « agis comme stratège YouTube pro » avec les règles distillées, format compatible avec la bibliothèque de prompts existante (regarde un fichier voisin pour le format).
   c. `/home/turbo/.claude/skills/cli_skill_youtube/SKILL.md` + `driver.sh` — skill CLI minimal calqué sur `/home/turbo/.claude/skills/cli_skill_audit/` (lis-le comme modèle) : le driver affiche la checklist d'actions et route une question stratégie vers le prompt via `~/jarvis/bin/qwen-nothink.sh` si dispo (0 token API).
4. Ajoute l

[assistant] Démarrage de la mission. Vérification des outils et recherche GitHub en parallèle.

[assistant] Matière suffisante. Lecture des modèles de format (skill audit, prompt voisin, TSV biblio).

[assistant] Mission accomplie. Rapport final.

## Fichiers créés
| Fichier | Contenu |
|---|---|
| `/home/turbo/jarvis/data/biblio_knowledge/youtube-pro-performances-github.md` | Fiche de connaissance : framework 4-goulots, benchmarks chiffrés, modèle ranking 6 tiers, workflow pro, analytics API, automation shorts, 10 anti-patterns, 15 sources (repo + lien) |
| `/home/turbo/prompts/prompts/claude-code/youtube-pro-actions.md` | Prompt réutilisable « stratège YouTube pro » au format bibliothèque (Ce que ça fait / Comment l'utiliser / Effet / bloc ```text), compatible qwen-nothink |
| `/home/turbo/.claude/skills/cli_skill_youtube/SKILL.md` | Skill calqué sur cli_skill_audit (frontmatter, triggers, log SQL) |
| `/home/turbo/.claude/skills/cli_skill_youtube/driver.sh` | Testé OK : mode checklist + mode `ask` routé vers `qwen-nothink.sh` (0 token, fallback propre si LMS down), log dans `skill_invocations` (row 48 vérifié) |
| `~/labo/bibliotheque/lib/youtube-blocs.tsv` | 4 blocs fusionnés dans `BLOCS-INDEX.tsv` avec dédup (41077→41081) |

## Lecture GitHub effectuée
14 README lus via `gh api` (0 clone) : youtube-growth-agent (framework Adam Ivy), youtube-marketing-skills (21 commandes + benchmarks publiés), youtube-seo-skills (ranking 6 tiers), nova-youtube-agent (329★), MoneyPrinterTurbo (101k★), MoneyPrinter, api-samples officiel, analytix, youtube-analytics-bot, youtube-data-first-24, VideoGraphAI, Viral-Faceless-Shorts-Generator, claude-faceless-shorts-creator, awesome-faceless, AI-Content