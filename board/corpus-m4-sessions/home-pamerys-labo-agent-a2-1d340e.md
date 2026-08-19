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

[assistant] Le skill sort `exit 0` en ne faisant rien — il ment. Cherchons les vraies sources de données trading.

[assistant] Trouvé : `trading_signals` est une **table** dans `trading_v9.db`, pas un fichier `.db`. Inspectons le contenu réel.

[assistant] Le tableau de bord lit les vraies données. Testons le calculateur TP/SL et le diagnostic.

[assistant] Un libellé est trompeur en SHORT (SL au-dessus mais affiché "-1%"). Corrigeons, puis testons diag et les erreurs.

[assistant] Lecture seule **prouvée** (md5 inchangé, erreur code 8). Mais je détecte un bug : un `JARVIS_TRADING_DB` explicite mais invalide retombe **silencieusement** sur la base par défaut — exactement le faux succès que je corrige. Réparons.

[assistant] Les tables réelles sont vides. Pour **prouver** le rendu des signaux, je crée une base de test dans le scratchpad (sans jamais toucher aux données réelles).

[assistant] Journalisation validée (succès et échecs). Petit ajustement d'accord grammatical, puis SKILL.md.

[assistant] Réparation terminée et prouvée. Base réelle intacte (md5 identique avant/après tous les tests).

**Cause racine** — le skill ne souffrait pas seulement du chemin mort `/home/turbo` : le fichier ciblé n'existait sur **aucune** machine. `trading_signals` est une **table** de `trading_v9.db`, pas une base `.db`. Le test `if [ -f ... ]` échouait donc toujours, affichait `no signals db` et sortait en **code 0** — un faux succès indiscernable d'un vrai pour tout appelant automatisé.

**Vérifications de sûreté effectuées** : la base est ouverte en `file:...?mode=ro`; une tentative d'écriture est rejetée par le moteur (`attempt to write a readonly database`, code 8) et le md5 de `/home/pamerys/jarvis-board/trading_v9.db` est identique avant et après la campagne de tests. Aucune requête réseau, aucun ordre. Le passage d'ordres MEXC reste volontairement non câblé — `run.sh diag` documente la voie sans l'emprunter.

**Limite documentée honnêtement** : aucun credential MEXC n'existe sur M4, donc le PnL de portefeuille *live* via API n'est pas disponible; le skill le signale au lieu de le simuler. Les tables `trading_signals`, `live_positions`, `risk_metrics` de la base vive sont **vides** — j'ai donc validé le rendu sur une base de test peuplée dans le scratchpad pour prouver que l'affichage fonctionne réellement avec des données, sans jamais toucher aux données réelles.