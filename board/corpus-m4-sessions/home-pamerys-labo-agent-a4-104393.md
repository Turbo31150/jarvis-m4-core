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

[assistant] Two parsing bugs to fix (NVML version and the systemd bullet marker). Let me confirm the raw formats.

[assistant] Now let me prove the `--strict` exit path and the degraded fallbacks, using a scratchpad copy (production file untouched).

[assistant] Le skill est réparé et prouvé. Résumé des causes réelles trouvées :

- **Section disque totalement absente** alors que la description promettait « CPU/RAM/GPU/disk ».
- **GPU : message mensonger.** `nvidia-smi` échoue avec `Failed to initialize NVML: Driver/library version mismatch` et le script affichait `no nvidia-smi` — alors que `/usr/bin/nvidia-smi` existe. Vraie cause diagnostiquée : module noyau NVRM `595.71.05` vs bibliothèque NVML `595.84`.
- **Journalisation inexistante**, et SKILL.md la déclarait vers `/home/turbo/jarvis/db/cli_history.db` — chemin de M1, inexistant sur M4.
- **Références mortes** : `/home/turbo/jarvis/action_validation/domino-action-cascade.yaml` (présent uniquement sur le miroir SSD, jamais utilisé par le code) et agent `system-health-monitor` jamais appelé, lui-même dépendant de `~/Workspaces/jarvis-linux/scripts/jarvis-flow-check.sh` absent de M4 et de `docker ps` local interdit.
- **Deux bugs d'analyse** introduits puis corrigés en séance : NVML lue depuis `libnvidia-ml.so.1` (retournait « 1 ») et nom d'unité systemd lu comme `*` à cause de la puce « ● ».

Fichiers : `/home/pamerys/.claude/skills/cli_skill_health/run.sh`, `/home/pamerys/.claude/skills/cli_skill_health/driver.sh` (nouveau moteur), `/home/pamerys/.claude/skills/cli_skill_health/SKILL.md`. Sauvegardes `.bak-20260818-094053` conservées. Les conteneurs passent exclusivement par `/home/pamerys/jarvis/bin/jarvis-docker` — aucun `docker` local, aucune action sortante, aucune écriture 