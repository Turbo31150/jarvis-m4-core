[user] Rédige la SPEC DE CLÔTURE (markdown, concret, contrats exécutables) du gap suivant pour l'écosystème JARVIS. Respecte impérativement les 4 lois de frontières et le DAG (lis /home/rempc/jarvis/docs/exports/pack-methode-jarvis/01-MATRICE-VECTORIELLE.md avant). Zéro invention hors logique établie. GAP #3 : Gestion inter-process : timeouts, données malformées, propagation d'échecs entre briques CLI chaînées

[assistant] I've read the vectorial matrix. Now let me ground the spec in the real codebase structure so I don't invent anything outside established logic.

[assistant] Let me read the brick wrappers and ops scripts to extract the real I/O contracts (exit codes, JSON, timeouts).

[assistant] Let me read the events lib, the agent/mem CLI heads, and the ops scripts to capture the real envelope/exit-code/timeout conventions.

[assistant] Let me capture the rest of the agent main (exit codes, JSON envelope) and the ops status/doctor conventions.

[assistant] Let me check the drill script and the export prompt style, plus any existing gap closure specs for format consistency.

[assistant] I have everything I need, grounded in the real code. I'll now write the closure spec for GAP #3, canonicalizing the conventions that already exist scattered across `agent/cli.py`, `oc-call.py`, `lib/events.py`, `lib/trust.py`, `ops/doctor.py` and `ops/drill.py` — zero invention, only consolidation into executable contracts.