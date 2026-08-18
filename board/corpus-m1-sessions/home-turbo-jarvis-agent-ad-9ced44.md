[user] Subagent implémenteur. Réponds en français. Étape 1 du plan « cartographier et exploiter les ressources JARVIS » : matrice unifiée registre × prompts × skills, interrogeable.

SOURCES RÉELLES (vérifie leur existence, adapte aux chemins réels) :
- Registre maître : ~/jarvis/registry.json (sinon cherche `find ~/jarvis -maxdepth 2 -name 'registry*.json'` — produit par registry_build.py)
- Prompts : ~/prompts/prompts/ (~206 fichiers, 11 catégories) + /home/turbo/Workspaces/jarvis-linux/config/prompt-library.json (~694 entrées annoncées — prends ce qui existe)
- Skills : ~/.claude/skills/*/SKILL.md (~463) + ~/jarvis/.claude/skills/*/SKILL.md (~53)

TÂCHE :
1. Crée `~/jarvis/bin/matrice-ressources.py` (stdlib seule) qui construit dans `~/jarvis/data/matrice_ressources.db` (SQLite) : table `ressources(id, type TEXT CHECK(type IN ('registre','prompt','skill')), nom, chemin, description, mots_cles)` + table FTS5 `ressources_fts` (tokenizer unicode61 remove_diacritics 2, comme le board) synchronisée par triggers. Extraction : nom + description (frontmatter/1re ligne) + mots-clés simples (mots significatifs du nom et de la description, minuscules, sans stoplist FR/EN basique).
2. Mode `build` (reconstruit, idempotent — DROP/CREATE ou INSERT OR REPLACE par (type,chemin)), mode `search <mots>` (requête FTS, top 15, format TSV nom/type/chemin), mode `stats` (compte par type).
3. Exécute `build` réellement, puis `stats`, puis 2 recherches de contrôle : `search backup sql` et `search publica

[assistant] No prior "matrice-search"/"matrice-rebuild" block, good, no dedup collision expected. Now writing the script.

[assistant] Good, syntax is fine after the formatter pass. Now let's run build, stats, and the two control searches.

[assistant] Both control searches are relevant and mix types correctly (registre/skill/prompt). Now let's create the biblio TSV entry and merge into BLOCS-INDEX.tsv.

[assistant] Merge succeeded, no duplicates, count matches (226144 + 2 = 226146). Final verification of DB integrity and file listing.

[assistant] Étape 1 terminée et validée.

**Statut** : réussi. Base construite, intègre (`PRAGMA integrity_check` = ok), searches de contrôle pertinentes et mixtes.

**Fichiers**
- `/home/turbo/jarvis/bin/matrice-ressources.py` — script stdlib (build/search/stats), exécutable
- `/home/turbo/jarvis/data/matrice_ressources.db` — SQLite + FTS5 (`unicode61 remove_diacritics 2`, triggers ai/ad/au comme `board_schema.sql`)
- `/home/turbo/labo/bibliotheque/lib/matrice-blocs.tsv` — 2 blocs 🟢, fusionnés dans `BLOCS-INDEX.tsv` (226144→226146 lignes, dédup vérifié avant fusion)

**Sources réelles utilisées**
- registre : `~/jarvis/orchestrator/registry.json` (670 entrées déclarées, 669 insérées — 1 collision `UNIQUE(type,chemin)`, source dupliquée entre deux entrées `kind` différents sur le même fichier)
- prompt : `/home/turbo/Workspaces/jarvis-linux/config/prompt-library.json` (694 entrées, titre+chemin+catégorie)
- skill : `~/.claude/skills/*/SKILL.md` (460) + `~/jarvis/.claude/skills/*/SKILL.md` (60) = 547 (frontmatter `name`/`description` extrait par regex, sans PyYAML)

**Stats par type** : prompt 694 · registre 669 · skill 547 · total 1910

**Extraits recherche `backup sql`** (mixte registre/skill) :
```
run-jarvis-sql-backup   registre  .../agents/run-jarvis-sql-backup.md
run-jarvis-backup-multi-db skill  .../skills/run-jarvis-backup-multi-db/SKILL.md
run-jarvis-n8n-backup   skill     .../skills/run-jarvis-n8n-backup/SKILL.md
run-backup-control      skill     .../skills/run-backup-control/S