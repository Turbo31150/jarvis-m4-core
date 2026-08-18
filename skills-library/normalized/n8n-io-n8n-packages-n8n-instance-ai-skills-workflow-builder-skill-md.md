---
id: n8n-io-n8n-packages-n8n-instance-ai-skills-workflow-builder-skill-md
name: "workflow-builder"
author: "n8n-io"
repository: "https://github.com/n8n-io/n8n/tree/master/packages/@n8n/instance-ai/skills/workflow-builder"
skill_url: "https://skillsmp.com/creators/n8n-io/n8n/packages-n8n-instance-ai-skills-workflow-builder"
stars: 199283
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:09:15.006893"
---

# Résumé
Load before calling build-workflow. Default path for all single-workflow work: new one-off workflows, existing-workflow edits, verification repairs, and workflow-local data tables. Write or edit a workspace source file, run workflow-sdk validate via workspace_execute_command, then call build-workflow with filePath. When the workflow creates or writes Data Tables, load data-table-manager first, then this skill. Do not load planning or create-tasks first. Load planning only when multiple coordinated workflows or shared cross-task data tables require a dependency-aware task graph.

# Objectif
Skill d'automatisation/intégration pour workflow-builder.

# Déclencheurs d’utilisation
Mots-clés associés: workflow-builder, n8n-io

# Procédure
Consulter le dépôt source: https://github.com/n8n-io/n8n/tree/master/packages/@n8n/instance-ai/skills/workflow-builder

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
