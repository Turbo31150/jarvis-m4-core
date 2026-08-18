---
id: mono-skiasharp-agents-skills-security-audit-skill-md
name: "security-audit"
author: "mono"
repository: "https://github.com/mono/SkiaSharp/tree/main/.agents/skills/security-audit"
skill_url: "https://skillsmp.com/creators/mono/skiasharp/agents-skills-security-audit"
stars: 5536
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:29.691223"
---

# Résumé
Audit SkiaSharp's native dependencies for security vulnerabilities and CVEs, including Component Governance (CG) alerts from the SkiaSharp-Native and SkiaSharp Azure DevOps pipelines. Read-only investigation that produces a status report with recommendations.
Use when user asks to: - Audit security issues or CVEs - Check CVE status across dependencies - Find security-related issues and their PR coverage - Get an overview of open vulnerabilities - See what security work is pending - Check Component Governance alerts - Review CG alerts from the native build pipeline
Triggers: "security audit", "audit CVEs", "CVE status", "what security issues are open", "check vulnerability status", "security overview", "what CVEs need fixing", "CG alerts", "component governance", "check container CVEs".
This skill is READ-ONLY. To actually fix issues, use the `native-dependency-update` skill.

# Objectif
Skill d'automatisation/intégration pour security-audit.

# Déclencheurs d’utilisation
Mots-clés associés: security-audit, mono

# Procédure
Consulter le dépôt source: https://github.com/mono/SkiaSharp/tree/main/.agents/skills/security-audit

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
