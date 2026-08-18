---
id: nvidia-skills-skills-deepstream-sop-skill-md
name: "deepstream-sop"
author: "NVIDIA"
repository: "https://github.com/NVIDIA/skills/tree/main/skills/deepstream-sop"
skill_url: "https://skillsmp.com/creators/nvidia/skills/skills-deepstream-sop"
stars: 2787
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:08:46.251460"
---

# Résumé
Use this skill when building, deploying, evaluating, debugging, or measuring latency for the DeepStream SOP Inference Microservice — a GPU-accelerated FastAPI service that detects whether operators perform assembly-line steps in order via event boundary detection (GEBD) plus VLM classification. Trigger even if the user does not name it: verify operator step sequence, detect missing or out-of-order SOP steps, score factory/work-cell video for procedure compliance, run VLM-based SOP checking on industrial cameras, or call /v1/chat/completions with a file, RTSP, or Basler camera. Also trigger for its internals: SOPVideoProcessor, DeepStream GEBD model (e.g. DDM) via Triton CAPI, nvds_custom_postprocess, Cosmos Reason 1/2 vLLM, SSE streaming, Kafka NvProto/JSON output, Basler/Pylon camera + emulation, Docker compose, chunk-level latency. Do NOT trigger for generic DeepStream pipelines, object detection/tracking, NIM imports, or video summarization.

# Objectif
Skill d'automatisation/intégration pour deepstream-sop.

# Déclencheurs d’utilisation
Mots-clés associés: deepstream-sop, NVIDIA

# Procédure
Consulter le dépôt source: https://github.com/NVIDIA/skills/tree/main/skills/deepstream-sop

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
