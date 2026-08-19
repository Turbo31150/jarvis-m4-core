[user] AUDIT INTERNE de cohérence. Lis /home/rempc/jarvis/docs/exports/pack-methode-jarvis/01-MATRICE-VECTORIELLE.md, /home/rempc/jarvis/docs/exports/pack-methode-jarvis/02-SKILL.md, /home/rempc/jarvis/docs/exports/pack-methode-jarvis/03-PROMPT-EXPORT.md. Puis probe les vrais contrats via Bash : pour t in media board web publish agent mem => `~/jarvis/bin/jarvis $t --help` (timeout court, head). Vérifie que la matrice M1 (1 seul OWNS par colonne), le DAG M2 (agent=feuille, acyclique) et les vecteurs V (contrats) correspondent AU CODE RÉEL. Liste les incohérences (location/issue/fix) et ce qui manque encore pour être 100% recréable. Donne une confiance /1.

[assistant] I'll read the three method-pack files and probe the real CLI contracts in parallel.

[assistant] Now let me probe `mail`, the meta-launcher itself, and inspect the actual binaries to verify whether the documented delegation edges (M2) and frontiers (M1) are enforced in real code.

[assistant] Let me inspect the actual source of each brick to verify whether the M2 delegation edges and M1 frontiers are enforced in real code (not just doctrine).

[assistant] Let me grep the real source of each brick to verify how they call LLM providers and each other (the load-bearing check for A1/M2).

[assistant] Key signals emerging. Let me verify the load-bearing details: does publish ever touch mem, does web have any cache/mem, does board's "local" voice hit OpenClaw directly, and what mail's real verbs are.

[assistant] Let me check board's `local_voice` and the shared `oc_llm` helper — this determines whether the "local" voice respects A1 (via agent) or hits OpenClaw :3200 directly.

[assistant] Let me confirm `oc_llm`'s actual body (does the local voice truly route through agent, or fall back to direct :3200) to be fair before finalizing.

[assistant] Let me verify two more M2 edges against code: does board actually route web acquisition through `jarvis-web` (A3), and does media call `jarvis-web`? Their own fetchers may bypass the web brick.

[assistant] Let me confirm two edges: board→media (autosource) which may be missing from M2, and whether mail is reachable/`--json` capable (invariant #1).

[assistant] I have everything I need. Compiling the audit verdict.

Core structural verdict (the three things I was asked to verify):
- M1 "1 seul OWNS par colonne" → HOLDS (agent=A1, mem=A2, web=A3, publish=A4; exactly one OWNS each).
- M2 "agent = feuille" → HOLDS (jarvis-agent calls only LLM providers, no brick).
- M2 "acyclique" → HOLDS (no cycles; phantom/missing edges don't introduce any).

The defects are all in the secondary delegation cells and in frontier enforcement (doctrine, not code-enforced). Reporting now.