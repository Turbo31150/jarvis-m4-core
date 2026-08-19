[user] CONTEXTE MACHINE (verifie, ne pas re-supposer) :
- Tu es sur M4, hostname pamerys-m4, uid=1000(pamerys), HOME=/home/pamerys.
- /home/turbo N'EXISTE PAS sur M4. C'est le home de la machine M1. Son contenu est
  accessible en LECTURE via le SSD USB monte : /media/pamerys/JARVIS-M1/home/turbo
- /home/rempc N'EXISTE PAS non plus (autre machine).
- INTERDIT : la commande `docker` en local frappe une pile PERIMEE (incident 2026-08-11,
  ecritures silencieusement perdues). Un hook la BLOQUE. Utilise toujours
  /home/pamerys/jarvis/bin/jarvis-docker qui route vers la tour (root@100.124.69.1).
- Journal des skills : /home/pamerys/jarvis/db/cli_history.db, table skill_invocations
  (colonnes : id, session_id, skill_name, invoked_at, trigger_phrase, outcome, feedback_score).
- Backends LLM 0-token disponibles : hub unifie http://127.0.0.1:18800/v1 (modeles logiques
  jarvis-fast / jarvis-auto / jarvis-quality), LM Studio M6 http://10.42.0.230:1234/v1
  (qwen/qwen3.5-9b), Ollama local http://127.0.0.1:11434 (gemma3:4b).
  ATTENTION : LM Studio ne tourne PAS sur 127.0.0.1:1234 de M4 — c'est M6.
- Board d'experts local : /home/pamerys/jarvis/board/board.py (usage : board.py ask <domaine> "<question>").
  Scripts prets : /home/pamerys/jarvis/board/ask-hub.sh et ask-m6.sh.

REGLES ABSOLUES :
1. AUCUNE action sortante reelle. Pas d'envoi de mail, pas de publication LinkedIn /
   Instagram / TikTok / YouTube / Notion, pas d'ordre de trading, pas de push git.
   Si le skill a une fonction de pu

[assistant] The skill appears to have been touched earlier today. I must verify it actually works rather than trust the header comments. Let me run it as-is.

[assistant] The skill runs and exits 0. Now let me probe the edge cases and the sub-commands before concluding.

[assistant] Confirmed: `--domain` without a value hangs in an infinite loop (killed at 8s, exit 124). Let me check the remaining paths and the journal.

[assistant] `--list-domains` works. Now let me test the degraded fallback path with an invalid domain.

[assistant] Found a real defect: a board error message is being reported as a successful answer. Let me confirm the exit codes.

[assistant] Pre-validation costs 5 ms. Let me check the experts table, then back up and patch.

[assistant] Error paths are clean. Now the degraded-fallback branch, isolated in a scratch dir.

[assistant] All three branches behave correctly. Now the nominal proof run on a real domain.

[assistant] Nominal run succeeds with 6 cited sources. Let me verify the journal captured every branch.

[assistant] All branches journal correctly (row 67 is the old false positive, kept as evidence). Now I'll update SKILL.md.

[assistant] The skill is repaired and proven. Final verification passed on every branch.

**What I actually found.** A prior pass that same morning had already fixed the dead `/home/turbo/jarvis/scripts/lm-ask.sh` path, so the skill *appeared* to work. Running it revealed it was still lying in the most dangerous way:

- **False success on an invalid domain.** `board.py ask <domaine-inconnu>` prints `✗ aucun expert pour le domaine` to **stdout** and **exits 0**. The driver served that error string as a genuine board answer, stamped it `via=board/hub:18800 · 0 token`, logged `success`, and returned 0. Row 67 in `cli_history.db` is the preserved evidence of this false positive.
- **Infinite loop on `--domain` with no value.** `shift 2` with a single remaining argument fails without decrementing `$#`, so the parsing loop never terminated — confirmed by a process kill at 8 s (exit 124).
- **Journaling holes.** `--list-domains`, `--help`, and every usage error exited without writing to the database.
- Hardcoded `/home/pamerys/...` paths, now derived from `$HOME` and overridable via `JARVIS_BOARD_DIR`, `JARVIS_CLI_HISTORY_DB`, `JARVIS_HUB_URL`, `JARVIS_HUB_MODEL`.

Fixes: up-front domain validation against `board.db` via SQLite (5 ms, deterministic, 0 token), rejection of `✗`-prefixed board output inside `try_board` so the cascade advances instead of serving an error, an argument-count guard, and a single `log_invocation` function called on every exit path.

**Two upstream defects I did not tou