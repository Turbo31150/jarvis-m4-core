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

[assistant] Driver works but the system prompt is silently dropped. Let me verify the backends and the `qwen-nothink.sh` contract.

[assistant] Both defects confirmed. Let me test the hub with a proper system+user call before rewriting.

[assistant] M6 chat mode confirms the reasoning-runaway (empty, 50s). Testing the `/v1/completions` + `<think></think>` route with the system merged in.

[assistant] Now the new driver with a real 3-backend cascade and anti-hallucination validation.

[assistant] Now testing the failure paths — the critical part (old version wrote fake content silently).

[assistant] The M6 route works but the model echoes the template first. Let me add a deterministic cleanup.

[assistant] The failure needs a real diagnosis — the driver swallows python stderr. Let me fix that first.

[assistant] M6 output is incomplete (missing Plan/Preuves/CTA). Let me add a structural quality gate so the cascade rejects half-briefs.

[assistant] Now the key cascade proof: hub unreachable, auto mode must fall through to a working backend.

[assistant] Now let me verify the documented onward paths actually exist before writing SKILL.md.

[assistant] The skill is repaired and proven. Summary of what I found and fixed:

**Was broken (verified by execution, not assumption):**
- `run.sh` delegated to `/home/turbo/jarvis/scripts/lm-ask.sh` — M1's home, absent on M4 → `exit 127` every time.
- `driver.sh` called `qwen-nothink.sh "<user>" "<system>" 900`, but that script only reads `$1` and hardcodes `max_tokens: 512`. The Hook/Angle/Plan/Preuves/CTA template never reached the model — the 09:39 brief came out off-format and cut mid-word (`**#Souverain`).
- Worst defect: with the backend down, `qwen-nothink.sh` returns **rc=0** plus a hardcoded marketing sentence, which the driver wrote to disk as the brief and logged `outcome=ok`. Reproduced: `LMS_ENDPOINT=http://127.0.0.1:9 … → rc=0` + fake text.
- Single backend (M6 only), and `--reseau` parsing read `$3` even without the flag.
- SKILL.md claimed "STUB — Implementation pending", pointed at `/home/turbo/jarvis/db/cli_history.db`, and claimed a link to `domino-action-cascade.yaml` chains — that file exists only read-only on the M1 SSD, its engine is absent from M4, and none of its 9 chains reference `topic`/`brief`/`rédige`.

**Now:** inference lives in the driver with a real cascade hub :18800 → M6 :1234 (`/v1/completions` + `<think></think>`, since chat mode returns empty content after 23–51 s on qwen3.5-9b) → Ollama :11434. Output is accepted only if >200 chars and containing `## Hook`, `## Plan`, `## CTA`; otherwise the cascade moves on and, if all fail, exits 1 writing noth