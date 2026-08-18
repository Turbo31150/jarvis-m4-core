---
id: maziyarpanahi-openmed-skills-serving-openmed-rest-api-skill-md
name: "serving-openmed-rest-api"
author: "maziyarpanahi"
repository: "https://github.com/maziyarpanahi/openmed/tree/master/skills/serving-openmed-rest-api"
skill_url: "https://skillsmp.com/creators/maziyarpanahi/openmed/skills-serving-openmed-rest-api"
stars: 4847
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:46.250746"
---

# Résumé
Stand up OpenMed's FastAPI REST service for clinical NER, PII extraction, and de-identification, with health checks, model keep-alive/unload, optional dynamic batching, and no-PHI logging. Use when the user wants to serve OpenMed over HTTP, deploy a de-id/NER REST API, run an inference endpoint for clinical text, add a /analyze or /pii/deidentify route, or containerize OpenMed as a service. Covers the service extra, launching create_app with uvicorn, the real endpoints (/health, /analyze, /pii/extract, /pii/deidentify, /models/loaded, /models/unload), request/response shapes, ServiceRuntime env-var configuration, and self-hosted auth/CORS/TLS notes.

# Objectif
Skill d'automatisation/intégration pour serving-openmed-rest-api.

# Déclencheurs d’utilisation
Mots-clés associés: serving-openmed-rest-api, maziyarpanahi

# Procédure
Consulter le dépôt source: https://github.com/maziyarpanahi/openmed/tree/master/skills/serving-openmed-rest-api

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
