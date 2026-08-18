---
id: abiosoft-colima-skills-skill-md
name: "colima"
author: "abiosoft"
repository: "https://github.com/abiosoft/colima/tree/main/skills"
skill_url: "https://skillsmp.com/creators/abiosoft/colima/skills"
stars: 30212
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:27.924023"
---

# Résumé
Guide to using Colima — container runtimes (Docker, containerd, Kubernetes, Incus) on macOS and Linux via lightweight Lima VMs. Use this skill whenever Colima is (or should be) the container backend: installing Colima; `colima start/stop/status/delete/ssh`; picking or switching a runtime; the `Cannot connect to the Docker daemon at unix:///var/run/docker.sock` error; Docker contexts and socket location; registry mirrors / insecure registries; buildx; bind or volume mounts that show up empty in the container; disk space recovery/resize; reachable VM IP; GPU / AI model workloads; config files, profiles and `COLIMA_HOME`; or a Colima VM that won't start. ALSO use it for **writing scripts that drive Colima** — bootstrap, dev-env, deploy, or CI scripts that bring Colima up non-interactively — because the skill has the correct flags, profile-specific socket paths, idempotent `colima start` guards, and readiness/teardown patterns that hand-written scripts routinely get wrong (e.g. inventing a non-existent flag or ha

# Objectif
Skill d'automatisation/intégration pour colima.

# Déclencheurs d’utilisation
Mots-clés associés: colima, abiosoft

# Procédure
Consulter le dépôt source: https://github.com/abiosoft/colima/tree/main/skills

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
