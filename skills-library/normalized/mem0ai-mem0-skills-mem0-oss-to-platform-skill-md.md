---
id: mem0ai-mem0-skills-mem0-oss-to-platform-skill-md
name: "mem0-oss-to-platform"
author: "mem0ai"
repository: "https://github.com/mem0ai/mem0/tree/main/skills/mem0-oss-to-platform"
skill_url: "https://skillsmp.com/creators/mem0ai/mem0/skills-mem0-oss-to-platform"
stars: 62485
verified: false
quality_score: 100
security_score: 20
status: "DANGEROUS"
collected_at: "2026-08-07T17:08:42.719089"
---

# Résumé
Plan and then execute a migration of a project from the mem0 open-source / self-hosted SDK (the local `Memory` class) to the mem0 Platform / hosted / managed SDK (the `MemoryClient` class). Use this whenever a developer wants to move, switch, or migrate their mem0 usage off OSS/self-hosted to the hosted API — e.g. "migrate my mem0 setup to the platform", "switch from self-hosted mem0 to MemoryClient", "use my mem0 API key instead of a local Qdrant", "move mem0 to the cloud/hosted/managed service", or "replace my local mem0 vector store + embedder config with the platform". Applies to Python (`from mem0 import Memory` → `from mem0 import MemoryClient`) and TypeScript/JavaScript (`import { Memory } from "mem0ai/oss"` → `import MemoryClient from "mem0ai"`). Trigger even when the user doesn't say the word "migrate" but clearly wants their existing mem0 integration to run against the hosted platform. It first produces a reviewable migration plan, then executes it after the developer approves. Strictly scoped to th

# Objectif
Skill d'automatisation/intégration pour mem0-oss-to-platform.

# Déclencheurs d’utilisation
Mots-clés associés: mem0-oss-to-platform, mem0ai

# Procédure
Consulter le dépôt source: https://github.com/mem0ai/mem0/tree/main/skills/mem0-oss-to-platform

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
