---
id: maziyarpanahi-openmed-skills-pseudonymizing-for-gdpr-skill-md
name: "pseudonymizing-for-gdpr"
author: "maziyarpanahi"
repository: "https://github.com/maziyarpanahi/openmed/tree/master/skills/pseudonymizing-for-gdpr"
skill_url: "https://skillsmp.com/creators/maziyarpanahi/openmed/skills-pseudonymizing-for-gdpr"
stars: 4847
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:23.407893"
---

# Résumé
Apply GDPR-grade pseudonymization to clinical or personal text with OpenMed, keeping a separately-held re-linkage key so the data can be controlled-re-linked later. Use when the user must process EU personal/health data under GDPR, asks for pseudonymization vs anonymization, needs Art. 4(5) / Art. 9 / Recital 26 alignment, wants a reversible mapping/key vault held apart from the data, or needs controlled re-linkage. Covers openmed.deidentify(policy="gdpr_pseudonymization", keep_mapping=True), storing the mapping in a separate key vault, reidentify() for authorized re-linkage, and retention. Pairs after extracting-pii-entities and configuring-privacy-policies.

# Objectif
Skill d'automatisation/intégration pour pseudonymizing-for-gdpr.

# Déclencheurs d’utilisation
Mots-clés associés: pseudonymizing-for-gdpr, maziyarpanahi

# Procédure
Consulter le dépôt source: https://github.com/maziyarpanahi/openmed/tree/master/skills/pseudonymizing-for-gdpr

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
