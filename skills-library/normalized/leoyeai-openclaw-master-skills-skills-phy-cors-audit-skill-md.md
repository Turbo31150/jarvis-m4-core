---
id: leoyeai-openclaw-master-skills-skills-phy-cors-audit-skill-md
name: "phy-cors-audit"
author: "LeoYeAI"
repository: "https://github.com/LeoYeAI/openclaw-master-skills/tree/main/skills/phy-cors-audit"
skill_url: "https://skillsmp.com/creators/leoyeai/openclaw-master-skills/skills-phy-cors-audit"
stars: 2105
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:46.252406"
---

# Résumé
CORS (Cross-Origin Resource Sharing) misconfiguration auditor. Probes any API endpoint with crafted Origin headers to detect the most dangerous CORS vulnerabilities — reflecting arbitrary Origins (any attacker.com gets CORS approved), Access-Control-Allow-Credentials:true with wildcard ACAO, null-Origin allowed (iframe/file:// bypass), subdomain regex bypasses (evil.myapp.com passes), missing Vary:Origin (CDN cache poisoning), and permissive preflight responses. Also scans source code for insecure CORS middleware patterns (Express/FastAPI/Go/Rails/Django/Spring). Generates correct CORS configuration for your specific stack. Works against any live URL via curl — zero external API. Triggers on "CORS error", "CORS misconfiguration", "Access-Control-Allow-Origin", "cors policy", "preflight", "cors blocked", "/cors-audit".

# Objectif
Skill d'automatisation/intégration pour phy-cors-audit.

# Déclencheurs d’utilisation
Mots-clés associés: phy-cors-audit, LeoYeAI

# Procédure
Consulter le dépôt source: https://github.com/LeoYeAI/openclaw-master-skills/tree/main/skills/phy-cors-audit

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
