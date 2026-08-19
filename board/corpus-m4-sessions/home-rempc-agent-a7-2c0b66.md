[user] Tu écris une IMPLÉMENTATION DE RÉFÉRENCE (starter code) qui matérialise les contrats v2 de l'écosystème JARVIS. Lis d'abord /home/rempc/Bureau/franck/ecosysteme/06-CONTRATS-RUNTIME-V2.md et /home/rempc/Bureau/franck/ecosysteme/01-MATRICE-VECTORIELLE.md.

Crée le dossier /home/rempc/Bureau/franck/reference-impl/ et écris-y, en Python **stdlib-only** (aucune dépendance externe), des stubs clairs, commentés, fidèles à la spec :
- `envelope.py` : construction de l'enveloppe I/O JSON unique (`ok/tool/verb/action/schema_version/command_id/data/error/meta`) + helpers `ok_envelope()` / `err_envelope()` ; table des exit codes (0/1/2/3/4/5/124) ; registre `error.code` (E_PROMPT_EMPTY, E_SSRF_BLOCKED, E_POLICY_MISSING, E_ALLOWLIST_DENIED, E_HASH_DRIFT, E_NO_VOICE, …).
- `proc.py` : `run_brick(caller, callee, argv, *, timeout, expect_json, critical)` avec **garde d'adjacence M2** (`assert callee in ADJ[caller]`), timeouts descendants, propagation dégradable/fatale/fail-closed, traitement du stdout malformé comme non-fiable (jamais exec).
- `policy.py` : `validate_action(action, mode)` **déterministe hors-LLM** (schéma typé + policy bornée type/cible/fréquence/plafond) ; en DEGRADED_LOCAL/NO_LLM → privilèges réduits (read-only, human-confirm).
- `test_invariants.py` : assertions pytest-style pour les invariants Σ.1–Σ.6 (unicité frontière, agent feuille, acyclicité, canal d'effet, ingress non fiable, souveraineté) + E1–E5 (enveloppe).
- `README.md` : comment lancer, avertissement « stubs d

[assistant] I'll start by reading both specification files to understand the contracts I need to implement.

[assistant] Both specs are clear. Now I'll create the directory and write the five files faithfully to spec 06 (with the M1/M2 corrections mandated in §9.6).