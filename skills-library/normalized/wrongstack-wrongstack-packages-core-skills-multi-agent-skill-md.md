---
id: wrongstack-wrongstack-packages-core-skills-multi-agent-skill-md
name: "multi-agent"
author: "WrongStack"
repository: "https://github.com/WrongStack/WrongStack/tree/main/packages/core/skills/multi-agent"
skill_url: "https://skillsmp.com/creators/wrongstack/wrongstack/packages-core-skills-multi-agent"
stars: 216
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:25.876738"
---

# Résumé
Use this skill whenever work can be split across multiple AI agents running in
parallel, or when orchestrating leader/worker patterns in WrongStack. Trigger
on the explicit vocabulary — "fan out", "parallel", "delegate", "subagent",
"fleet", "coordinator", "collab_debug", "swarm", "workers" — but more
importantly trigger on the SHAPE of the task, because users rarely name the
pattern: "audit these 40 files", "check every package for X", "run the tests
across the monorepo", "review this PR and the tests and the docs", "refactor
these three modules", "scan the codebase for security issues", "find all the
places that do Y". Any request with a plural target set and repeatable
per-target work is a fan-out candidate. Also use this skill when a delegated
run came back with `budget_exhausted`, when worker results need to be
synthesized into one report, or when deciding whether parallelism is worth it
at all — talking someone out of fanning out is a valid use of this skill.

# Objectif
Skill d'automatisation/intégration pour multi-agent.

# Déclencheurs d’utilisation
Mots-clés associés: multi-agent, WrongStack

# Procédure
Consulter le dépôt source: https://github.com/WrongStack/WrongStack/tree/main/packages/core/skills/multi-agent

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
