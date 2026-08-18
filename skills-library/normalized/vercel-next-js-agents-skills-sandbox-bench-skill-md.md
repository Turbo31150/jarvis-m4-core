---
id: vercel-next-js-agents-skills-sandbox-bench-skill-md
name: "sandbox-bench"
author: "vercel"
repository: "https://github.com/vercel/next.js/tree/canary/.agents/skills/sandbox-bench"
skill_url: "https://skillsmp.com/creators/vercel/next.js/agents-skills-sandbox-bench"
stars: 141334
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:09:00.312811"
---

# Résumé
Benchmark React or Next.js changes on Vercel Sandbox VMs with paired A/B statistics: react PR/commit vs base, or Next.js PR/commit vs base, measured end-to-end through the bench/render-pipeline app (rps, latency, p95; TTFB, RSS and document/Flight bytes when the Next side captures them) and, for React changes, through the react repo's flight-ssr-bench fixture (Node AND Edge web-streams paths, Fizz and Flight+Fizz). Use whenever the user asks to bench, perf test, or A/B a React PR, a react-server-dom / Flight / vendored React change, or a Next.js PR ("is this PR faster", "does this regress RSC?", "measure the perf impact of <commit>"), even if they don't say "benchmark" — any request to quantify a server-side performance difference between two revisions belongs here. Runs remotely (laptop-free), applies correctness gates before measuring, and reports boot-level confidence intervals.

# Objectif
Skill d'automatisation/intégration pour sandbox-bench.

# Déclencheurs d’utilisation
Mots-clés associés: sandbox-bench, vercel

# Procédure
Consulter le dépôt source: https://github.com/vercel/next.js/tree/canary/.agents/skills/sandbox-bench

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
