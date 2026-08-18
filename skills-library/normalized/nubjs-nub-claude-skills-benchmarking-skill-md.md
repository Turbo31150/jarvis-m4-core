---
id: nubjs-nub-claude-skills-benchmarking-skill-md
name: "benchmarking"
author: "nubjs"
repository: "https://github.com/nubjs/nub/tree/main/.claude/skills/benchmarking"
skill_url: "https://skillsmp.com/creators/nubjs/nub/claude-skills-benchmarking"
stars: 3767
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:30.558896"
---

# Résumé
Comparative install-benchmarking methodology for nub vs npm/pnpm/bun — cold/warm protocol, genuine-cold cache isolation, load-robust measurement, and the anti-juicing honesty bar. Invoke (via the Skill tool) whenever you need to benchmark `nub install` against another package manager, produce or update the homepage/blog install numbers, or verify a perf claim before it ships. Encodes the hard-won gotchas: time setup OUTSIDE the measurement (hyperfine `--prepare`), the cache lives on DISK so env-var isolation is NOT trustworthy (bun ignores `BUN_INSTALL_CACHE_DIR`/`$HOME` — wipe the real path), VERIFY every cold is genuine via an offline-fails check, and only measure wall-clock on a quiet machine (gate on low load) with file counts as a load-independent cross-check. Pairs with `pm-perf-tracing` for the internal Rust phase decomposition.

# Objectif
Skill d'automatisation/intégration pour benchmarking.

# Déclencheurs d’utilisation
Mots-clés associés: benchmarking, nubjs

# Procédure
Consulter le dépôt source: https://github.com/nubjs/nub/tree/main/.claude/skills/benchmarking

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
