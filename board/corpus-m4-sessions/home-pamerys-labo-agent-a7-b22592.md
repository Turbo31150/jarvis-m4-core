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

[assistant] The pipeline puts `split_code` in a subshell so the variables never escape. Fixing.

[assistant] Diagnostic passes end to end. Now the read-only search, the dry-run, and the write lock.

[assistant] Final verification — a clean run of the default entry point, exactly as a user would call it.

[assistant] Le skill est réparé et prouvé. Résumé avant l'objet structuré.

**État initial** — `/home/pamerys/.claude/skills/cli_skill_notion/run.sh` était un STUB pur : deux `echo` de texte, exit 0, aucun argument lu, aucun travail, aucune journalisation. `SKILL.md` renvoyait vers deux chemins de la machine M1 inexistants sur M4 (`/home/turbo/jarvis/db/cli_history.db`, `/home/turbo/jarvis/action_validation/domino-action-cascade.yaml` — ce dernier n'existe que sur le SSD monté).

**Ce qui a été câblé** — un `driver.sh` réel, adossé à l'infrastructure Notion déjà présente sur M4 (jeton dans `~/.config/jarvis/notion.env` + coffre sops, lanceur MCP `~/jarvis/scripts/mcp_notion.sh`, export `~/.local/bin/jarvis-notion-sync`) : diagnostic en 6 points, recherche en lecture seule, préparation de page en dry-run, journalisation SQLite.

**Bug rencontré et corrigé en cours de route** — `api_get … | split_code` plaçait l'affectation de `RESP_CODE`/`RESP_BODY` dans un sous-shell : sous `set -u` le contrôle n°4 mourait sur `RESP_CODE : variable sans liaison`. Remplacé par `run_api`, qui exécute l'appel dans le shell courant.

**Aucune action sortante mutante** — seuls `GET /v1/users/me` et `POST /v1/search` (non mutant) ont été émis. La création de page est protégée par un double verrou (`--exec` **et** `JARVIS_NOTION_ALLOW_WRITE=1`) ; testée uniquement en refus, code retour 3.

**Point de sécurité signalé, non traité** — `/home/pamerys/jarvis/scripts/jarvis_notion_claude_bridge.py` contient un jeton