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

[assistant] The skill "works" but that's the trap — it hit the local (stale) pile. Let me compare with the real tour stack.

[assistant] Confirmed: two entirely different stacks. Let me check the guard hook and the logging schema, plus a reference repaired skill.

[assistant] I have the full picture and the house style. Let me back up, then write the repaired driver.

[assistant] Both failure paths degrade cleanly instead of falling back to the stale pile. Let me verify the journalisation.

[assistant] All paths journalise. One flaw though: the `stats` row (id 20) logged `fail` with empty detail — `head -6` closed the pipe, killing the script via SIGPIPE before it recorded success. Let me set the outcome *before* printing.