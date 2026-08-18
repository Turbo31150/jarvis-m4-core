---
id: elementalsouls-claude-bughunter-skills-hunt-subdomain-skill-md
name: "hunt-subdomain"
author: "elementalsouls"
repository: "https://github.com/elementalsouls/Claude-BugHunter/tree/main/skills/hunt-subdomain"
skill_url: "https://skillsmp.com/creators/elementalsouls/claude-bughunter/skills-hunt-subdomain"
stars: 3288
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:29.692003"
---

# Résumé
Hunting skill for subdomain takeover vulnerabilities. Includes modern provider fingerprints — Microsoft Azure DevOps `cloudapp.azure.com` regional-pool re-issue (1-click OAuth ATO via wildcard `reply_to`, Binary Security), Zendesk help-desk takeover → email interception → password reset chain (0xprial writeup), Vercel `cname.vercel-dns.com` deleted-project takeover, plus general Fastly CDN service re-attach and S3 dangling-bucket cookie-scope techniques. Use when hunting subdomain takeover — emphasis on ATO-chain primitives (OAuth `redirect_uri`, cookie-domain, email DNS).

# Objectif
Skill d'automatisation/intégration pour hunt-subdomain.

# Déclencheurs d’utilisation
Mots-clés associés: hunt-subdomain, elementalsouls

# Procédure
Consulter le dépôt source: https://github.com/elementalsouls/Claude-BugHunter/tree/main/skills/hunt-subdomain

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
