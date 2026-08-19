[user] Tu es l'agent REPARE-SKILLS. Objectif : réparer les skills CASSÉES qui comptent (stubs + chemins M1 morts) pour qu'elles marchent sur M4. Prudence maximale : édits ciblés, réversibles, aucune casse. Aucun secret. Rien publié.

⚠️ NE PAS toucher aux ~430 skills marketplace (filler) — inutile et risqué. Cible UNIQUEMENT :
A) les 2 stubs CLI de Franck : ~/.claude/skills/cli_skill_search/ et ~/.claude/skills/cli_skill_audit/
B) les références de chemins MORTS /home/turbo/* dans les skills/hooks/drivers LOCAUX de Franck (home-grown), à remapper vers /home/pamerys/*.

ÉTAPE 1 — cli_skill_audit : Read ~/.claude/skills/cli_skill_audit/driver.sh. Corrige :
- report dir + DB log : /home/turbo/jarvis/... → /home/pamerys/jarvis/... (crée ~/jarvis/db/ si besoin ; utilise la base cli locale existante ou ~/jarvis/db/cli_history.db).
- scanner secrets : /home/turbo/jarvis/bin/scan-secrets.sh absent (rc=127 = faux ALERT) → remplace par un scan local simple intégré (grep de motifs sk-/ghp_/ntn_/API_KEY/TOKEN sur ~/jarvis, en excluant .git, avec verdict CLEAN/ALERT réel) OU par le vault check. Fais que « secrets: » reflète un vrai scan.
Teste : bash driver.sh doit finir sans erreur DB et donner un verdict secrets réel. Si Bash bloqué par la garde thermique, applique les édits (Write/Edit) et note « à retester ».

ÉTAPE 2 — cli_skill_search : c'est un STUB sans implémentation. Écris un vrai driver.sh minimal et FONCTIONNEL : prend une requête en argument, fait une recherche (priorité : board loc

[assistant] Maintenant je corrige run.sh de l'audit (il pointait vers /home/turbo/alkymia mort).

[assistant] Étape 1 réparée. Maintenant cli_skill_search — driver fonctionnel + SKILL.md honnête.

[assistant] Étape 2 OK. Maintenant Étape 3 — examinons les occurrences /home/turbo dans les hooks exécutables et run.sh des CLI.

[assistant] Tous les hooks sont fail-safe. J'applique les remaps de chemins dans les hooks exécutables et les run.sh CLI.

[assistant] Les test_*.py sont des fixtures de tests (hors scope data/log, risqué). Je vérifie seulement les scripts opérationnels register_*.py et debug_report.py.

[assistant] Reste les run.sh/driver.sh exécutables d'autres CLI home-grown. Je les inspecte.

[assistant] Ce sont des CLI home-grown avec chemins données/log morts. Je remappe leurs exécutables.

[assistant] Les remaps exécutables sont faits. Le reste (SKILL.md doc, _deleted/, test_*.py) est hors scope. Vérification finale.

[assistant] Travail terminé. Rapport concis.

## Rapport REPARE-SKILLS

**cli_skill_audit — RÉPARÉ (testé, WORKING).**
`/home/pamerys/.claude/skills/cli_skill_audit/driver.sh`
- DB log remappée `/home/turbo/…` → `/home/pamerys/jarvis/db/cli_history.db` (dossier créé, `mkdir -p` ajouté).
- TRIGGERS remappé vers `/home/pamerys/jarvis/.claude/…` (fail-safe `-f` inchangé).
- Scanner secrets `/home/turbo/jarvis/bin/scan-secrets.sh` (rc=127 = faux ALERT) remplacé par un **scan local intégré** (grep récursif motifs `sk-/ghp_/gho_/ntn_/xox/AKIA/API_KEY/…_TOKEN` sous `~/jarvis`, exclut `.git`, `node_modules`, `secrets-vault`, `*.bak`). Verdict réel : CLEAN / ALERT(n match) / UNAVAILABLE.
- `run.sh` (qui pointait vers `/home/turbo/alkymia` mort) réécrit pour lancer `driver.sh`.
- **Test réel** : rapport généré, ligne SQL loggée (id 1), verdict secrets réel = `ALERT (60 match)` (surtout placeholders `sk-xxxx` et `API_KEY=` dans le code — verdict honnête à trier).

**cli_skill_search — RENDU FONCTIONNEL (testé, WORKING).**
- `driver.sh` créé : requête → `~/jarvis/board/ask-hub.sh` (hub :18800) → repli `ask-m6.sh` → sinon message clair « déléguer la recherche web à l'agent ». Requête vide = usage + rc 2. Log SQLite partagé.
- `run.sh` réécrit, `SKILL.md` réécrit : tag STUB retiré, chemins M4, comportement honnête (pas de Perplexity).
- **Test** : requête vide → usage rc 2 ; requête réelle → backends locaux absents (aucun tournant), repli propre, loggé `fail` (id 2, comportement fail-safe correct).

*