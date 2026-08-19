[user] Contexte urgent : ~/.claude/CLAUDE.md vient d'être dégraissé de 2676 à 533 mots. Le contenu retiré référence désormais des skills QUI N'EXISTENT PAS — il est donc inaccessible. Tu dois en créer deux.

La source du contenu retiré est la sauvegarde : ~/.claude/CLAUDE.md.bak-avant-degraissage-20260814-133452 — lis-la en entier d'abord.

Crée DEUX skills dans ~/.claude/skills/ :

1. **jarvis-backends** — récupère de la sauvegarde : la cascade LLM détaillée, la table des modèles Ollama, l'heuristique d'escalade, les scripts lm-ask.sh / qwen-nothink.sh / cascade.py / gemini-ask.sh, le sondage des ports.
2. **jarvis-bibliotheque** — récupère : le méga-prompt bibliothèque-routeur, les 14 sources, le format TSV, comment ranger une nouvelle source, les séries.

ATTENTION — CORRECTIONS OBLIGATOIRES, la sauvegarde contient des informations FAUSSES vérifiées aujourd'hui :
- ~/jarvis/bin/bloc.sh N'EXISTE PAS. Le vrai est ~/labo/bibliotheque/series/bloc.sh — vérifie-le toi-même avant d'écrire.
- ~/jarvis/bin/protocole.sh et ~/jarvis-orchestration/SYSTEM/STARTUP.md N'EXISTENT PAS non plus.
- Le nombre de blocs annoncé est faux et se contredit (44 300 puis 2 579) : la réalité est 18 892. Compte-les toi-même : wc -l sur ~/labo/bibliotheque/lib/BLOCS-INDEX.tsv
- 197 séries annoncées, 250 réelles. Compte-les.
- Les machines M1, M2, M5 et OL1 N'EXISTENT PLUS. Le parc réel est : M4 local, M6 sur 10.42.0.230:1234 (LM Studio, backend par défaut), Rémi sur 100.113.121.61:11434 (Ollama, Tailscale). To

[assistant] Note: the TSV format in the backup is wrong too (4 columns vs 5 real). Let me retry the series listing after the thermal guard.

[assistant] Les deux skills sont créées et vérifiées.

## Créé

```
~/.claude/skills/jarvis-backends/SKILL.md
~/.claude/skills/jarvis-backends/references/scripts.md
~/.claude/skills/jarvis-bibliotheque/SKILL.md
~/.claude/skills/jarvis-bibliotheque/references/sources.md
~/.claude/skills/jarvis-bibliotheque/references/series.md
```

Frontmatter YAML validé (parse `yaml.safe_load`, `name` = nom du dossier, `version: 1.0.0`, description 3ᵉ personne avec ~90 déclencheurs français entre guillemets). Les 15 chemins cités existent tous — contrôlés un par un.

## Corrections apportées à la sauvegarde

| Affirmation de la sauvegarde | Réalité vérifiée |
|---|---|
| `~/jarvis/bin/bloc.sh` | n'existe pas → `~/labo/bibliotheque/series/bloc.sh` |
| `~/jarvis/bin/protocole.sh` | n'existe pas → `~/labo/bibliotheque/series/protocole.sh` (`--full`) |
| `~/jarvis-orchestration/SYSTEM/STARTUP.md` | dossier inexistant — tout le bandeau « routeur orchestration client » supprimé |
| `~/jarvis/bin/cascade-bibliotheques.py` | n'existe pas → `~/labo/moisson_remi_forge/bin/cascade-bibliotheques.py` ; sortie réelle dans `~/labo/bibliotheque/reproductions/<slug>-<horodatage>/plan/`, pas `~/jarvis-linux/contexte-maximal/` |
| 44 300 puis 2 579 blocs | **18 892** (`wc -l` = 18 893 avec l'entête) |
| 197 séries | **250** `.sh` |
| 14 sources | **99** sources distinctes (top réel : `github-jarvisos` 7 469, `script` 5 264, `ocow-script` 1 288…) |
| TSV 4 colonnes `nom source danger bloc` | **5 colonnes** : `bloc_id · sou