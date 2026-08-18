---
id: netdata-netdata-agents-skills-project-build-static-binary-skill-md
name: "project-build-static-binary"
author: "netdata"
repository: "https://github.com/netdata/netdata/tree/master/.agents/skills/project-build-static-binary"
skill_url: "https://skillsmp.com/creators/netdata/netdata/agents-skills-project-build-static-binary"
stars: 80011
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:08:27.922368"
---

# Résumé
Build a static, self-extracting Netdata installer (`netdata-<arch>-latest.gz.run`) from this checkout for x86_64, aarch64, armv6l, or armv7l. Use when the user asks to build, produce, package, or test a static binary, makeself installer, `.gz.run` artifact, or "static install" of Netdata; when verifying a PR by deploying it to a Linux machine without a native build toolchain; when reproducing a CI static-builder issue locally. Covers the docker-based build flow under `packaging/makeself/`, mandatory pre-flight checks (submodule init, fresh `netdata/static-builder:v1` image), the 18 ordered jobs the build runs, output artifact layout, the `artifacts/cache/` reuse model, cross-arch QEMU caveats, debug builds, common failures with their fixes, and how to copy/verify the artifact on a target host.

# Objectif
Skill d'automatisation/intégration pour project-build-static-binary.

# Déclencheurs d’utilisation
Mots-clés associés: project-build-static-binary, netdata

# Procédure
Consulter le dépôt source: https://github.com/netdata/netdata/tree/master/.agents/skills/project-build-static-binary

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
