---
id: confident-ai-deepeval-skills-deepeval-otel-skill-md
name: "deepeval-otel"
author: "confident-ai"
repository: "https://github.com/confident-ai/deepeval/tree/main/skills/deepeval-otel"
skill_url: "https://skillsmp.com/creators/confident-ai/deepeval/skills-deepeval-otel"
stars: 17398
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:30:23.406745"
---

# Résumé
Export raw OpenTelemetry traces from an AI application to Confident AI's Observatory. TRIGGER when the user wants to send OpenTelemetry or OTLP traces/spans from an LLM app, agent, RAG pipeline, or chatbot to Confident AI; configure the Confident AI OTLP endpoint; set confident.span.* or confident.trace.* attributes; export AI-app traces to Confident AI without the deepeval Python package; wire an OTLPSpanExporter, OpenTelemetry Collector, or vendor-neutral OTel SDK to Confident AI; or pick the US vs EU Confident AI OTLP endpoint. Language-agnostic — the mechanism is OTLP attribute keys plus an exporter endpoint. DO NOT TRIGGER for building DeepEval pytest eval suites, datasets, goldens, metrics, or deepeval test run (use the `deepeval` skill); for instrumenting with the DeepEval SDK's @observe decorator or framework integrations (use the `deepeval-tracing` skill); or for instrumenting non-AI software such as web servers, CRUD backends, or infrastructure — the confident.* attributes describe AI components (ag

# Objectif
Skill d'automatisation/intégration pour deepeval-otel.

# Déclencheurs d’utilisation
Mots-clés associés: deepeval-otel, confident-ai

# Procédure
Consulter le dépôt source: https://github.com/confident-ai/deepeval/tree/main/skills/deepeval-otel

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
