[user] Tâche : sauvegarde LOCALE (jamais GitHub, aucun push) des dépôts git du disque M1 monté.

Contexte disque/espace (garde-fou DUR) :
- Source : /media/pamerys/JARVIS-M1/home/turbo (rootfs M1, read-only conceptuellement — ne rien modifier dessus).
- Cible : /storage (partition locale NVME-FAST). Elle est à 91% pleine, ~35 Go libres SEULEMENT. Vérifie `df -h /storage` AVANT toute écriture et ARRÊTE-toi si moins de 8 Go libres.
- Déjà présent : /storage/m1-recover/git (45G), /storage/m1-recover/git-sans-remote (12G), et /storage/m1-recover/INVENTAIRE-GIT.tsv (303 lignes). NE re-copie PAS ce qui est déjà là.

Il y a ~177 dépôts git (dossiers .git) sous le disque M1.

Objectif : garantir que les dépôts SANS remote (seule copie au monde) sont sauvegardés en git bundle compact, sans dupliquer l'existant.

Étapes :
1. `find /media/pamerys/JARVIS-M1/home/turbo -maxdepth 5 -type d -name .git` → pour chaque, le dépôt = son dossier parent. Pour chacun : récupère `git -C <repo> remote -v` (a-t-il un remote ?) et sa taille.
2. Classe : dépôts SANS remote (priorité absolue) vs AVEC remote (récupérables ailleurs, priorité basse).
3. Croise avec /storage/m1-recover/INVENTAIRE-GIT.tsv et le contenu de /storage/m1-recover/git-sans-remote pour savoir lesquels sont DÉJÀ sauvegardés.
4. Pour chaque dépôt sans-remote NON encore sauvegardé : crée un bundle `git -C <repo> bundle create /storage/m1-recover/git-bundles/<nom-slug>.bundle --all` (crée le dossier). Vérifie l'espace (df) avant chaque bundle 

[assistant] I'll start by checking disk space (the hard guardrail) and surveying the existing state.

[assistant] 35 Go free — above the 8 Go floor. The inventory has 303 lines (header + 302 repos). Let me examine it fully and scan the disk for git repos with their remote status.

[assistant] The inventory shows 96 no-remote, but most are `.npm-new-cache` git-clone temp junk (exclude) and `jarvis` is 118 GB (impossible in 35 GB). Let me do a fresh scan of the disk, checking remotes and sizes, excluding node_modules and npm caches.

[assistant] 292 total, 205 after excluding node_modules/npm-cache. Now let me classify each clean repo by remote status and size.

[assistant] 20 sans-remote repos. Notably `jarvis` (118 GB in inventory) is NOT in this sans-remote list — let me verify its remote status, and check the `.git` size total for the sans-remote set plus what's already backed up in git-sans-remote/.

[assistant] `jarvis` now has remote `jarvis-core.git` — recoverable, correctly excluded. Total sans-remote `.git` = 7.35 GB (dominated by `.gemini/history/turbo` at 7.18 GB). 7 repos already in git-sans-remote/. Let me get the COMPLETE list of what's already backed up there (deeper than maxdepth 3) to avoid re-doing them.

[assistant] All 20 sans-remote repos map exactly to what is already in git-sans-remote/. Let me verify the backups are genuine (non-empty .git with real history) via integrity spot-checks before concluding zero bundles needed.

[assistant] All 20 sans-remote repos are already backed up with intact history (fsck clean). Zero missing, zero to bundle. Since making bundles now would duplicate already-saved repos (forbidden by the guardrail), the correct action is to write the plan documenting full protection. Let me generate the plan file.

[assistant] Terminé. Voici le résumé chiffré final.

## Résultat : tous les dépôts sans-remote sont déjà protégés — 0 bundle nécessaire

**Chiffres :**
- **292** dossiers `.git` trouvés (maxdepth 5) → **87 exclus** (node_modules + caches npm `_cacache`) → **205 dépôts réels**
- **185 AVEC remote** (récupérables ailleurs, priorité basse — non traités)
- **20 SANS remote** (seule copie au monde)
- **20 / 20 déjà sauvegardés** dans `/storage/m1-recover/git-sans-remote/`
- **0 bundlé cette fois**, **0 restant faute d'espace**, **0 non sauvegardé**

**Pourquoi 0 bundle :** chaque dépôt sans-remote a déjà une copie **complète (arbre de travail + historique `.git`)** au chemin identique sous `git-sans-remote/`. Créer des bundles maintenant aurait **dupliqué** l'existant — interdit par le garde-fou. Le dossier `git-bundles/` n'a donc pas été créé.

**Intégrité vérifiée** par sondage `git fsck --connectivity-only` : OK sur les gros (`.gemini/history/turbo` 6,9 G, `jarvis-chat-vault` 3,8 G) comme les petits (`.claude/hooks/qa` 26 commits) — HEAD présents, objets connectés, aucune erreur.

**Garde-fous respectés :**
- Espace `/storage` : 35 G libres, jamais descendu (aucune écriture de sauvegarde) — le seuil 8 G n'a jamais été menacé. Bundler `.gemini/history/turbo` aurait gaspillé ~7 G pour rien.
- Disque M1 : accès **lecture seule** uniquement (`git --git-dir`, `du`) — zéro écriture.
- Aucun push réseau, aucune archive de secrets.

**À noter :** `jarvis` (118 G) apparaissait « sans remote » dans 