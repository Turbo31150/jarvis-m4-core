---
id: k-dense-ai-scientific-agent-skills-skills-arbor-skill-md
name: "arbor"
author: "K-Dense-AI"
repository: "https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/arbor"
skill_url: "https://skillsmp.com/creators/k-dense-ai/scientific-agent-skills/skills-arbor"
stars: 32587
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:08:23.786065"
---

# Résumé
Autonomously improve a real artifact (code, training recipe, agent harness, data pipeline, prompt) against an objective and an evaluator, using Hypothesis Tree Refinement (HTR) from the Arbor paper. Use this whenever someone wants to iteratively optimize something over many experiments without overfitting — e.g. "get my model's eval score up", "improve this agent/harness", "tune this pipeline", "beat the baseline on this benchmark", "run a search over approaches and keep the best", "do an MLE-bench / Kaggle-style optimization", or any long-horizon "make this artifact better and don't just memorize the dev set" task. Trigger it even when the user doesn't say "Arbor" or "hypothesis tree" but describes repeated experiment-and-evaluate loops, branching exploration of competing ideas, or worries about a dev/test gap. Runs Claude itself as the coordinator with subagent executors in isolated git worktrees; for the standalone `arbor` CLI tool see references/arbor-upstream.md.

# Objectif
Skill d'automatisation/intégration pour arbor.

# Déclencheurs d’utilisation
Mots-clés associés: arbor, K-Dense-AI

# Procédure
Consulter le dépôt source: https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/arbor

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
