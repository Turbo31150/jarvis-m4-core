---
id: stirling-tools-stirling-pdf-claude-skills-ui-before-after-skill-md
name: "ui-before-after"
author: "Stirling-Tools"
repository: "https://github.com/Stirling-Tools/Stirling-PDF/tree/main/.claude/skills/ui-before-after"
skill_url: "https://skillsmp.com/creators/stirling-tools/stirling-pdf/claude-skills-ui-before-after"
stars: 88793
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:53.019326"
---

# Résumé
Analyse a branch or PR and automatically capture before/after screenshots of every UI surface its changes touch, then pixel-diff the pairs to surface what actually changed and assemble PR-ready before/after montage images. Generic and diff-driven: it derives the capture targets from the diff (changed tools/routes → URLs) instead of hand-listing screens, captures "before" from the base branch and "after" from the head, then keeps only the views that visually differ. Each comparison is auto-cropped to the region that actually changed (the bounding box of differing pixels), falling back to the full page only when the change spans most of it. Use for before/after shots, a visual diff of a branch/PR, "screenshots for the PR description", "show what changed in the UI", or a side-by-side of UI changes. Takes a PR number/URL (resolved via gh) or a branch; defaults to the current branch vs its base. Flags: --scope <selector>, --base <ref|merge-base>, --theme light|dark|both, --all (capture every route, not just change

# Objectif
Skill d'automatisation/intégration pour ui-before-after.

# Déclencheurs d’utilisation
Mots-clés associés: ui-before-after, Stirling-Tools

# Procédure
Consulter le dépôt source: https://github.com/Stirling-Tools/Stirling-PDF/tree/main/.claude/skills/ui-before-after

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
