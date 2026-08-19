[user] Contexte : le disque d'une machine "M1" désormais hors ligne a été rapatrié dans /home/pamerys/m1-recover. Sur les 39 dépôts git qu'il contenait, **trois n'ont AUCUN remote configuré** et portent du travail non commité. Le disque source et cette copie en sont donc les seules traces au monde. C'est un risque de perte définitive.

Les trois dépôts, copiés ici :
  1. /home/pamerys/m1-recover/git/jarvis            (branche feat/content-perf-engine, ~3452 fichiers modifiés non commités)
  2. /home/pamerys/m1-recover/git/jarvis-chat-vault (4 modifications)
  3. /home/pamerys/m1-recover/git/jarvis-zero-token (2 modifications)

Note importante : pour le dépôt `jarvis`, seuls le code et le .git ont été copiés — les répertoires backups/, apps/, data/ et les fichiers .db ont été volontairement exclus du rsync (111 Go au total sur le disque source). Une partie des "modifications" de git status peut donc être constituée de SUPPRESSIONS apparentes dues à cette exclusion, et non de vrai travail. Tu dois impérativement faire la part des deux — c'est le cœur de ta mission.

Ta tâche — AUDIT EN LECTURE SEULE :

Pour chacun des trois dépôts :
1. `git -C <dépôt> log --oneline -15` : de quoi parle l'historique récent ?
2. `git -C <dépôt> status --porcelain` puis compte séparément :
   - les fichiers SUPPRIMÉS (statut D) → très probablement l'artefact de l'exclusion rsync, pas du travail perdu
   - les fichiers MODIFIÉS (M) → du vrai travail non commité
   - les fichiers NON SUIVIS (??) → du vrai 

[assistant] Key finding emerging. Let me verify the rsync-exclusion hypothesis against reality.

[assistant] ## Rectification préalable de deux prémisses

**1. `jarvis` a bien un remote.** `code` → `https://github.com/Turbo31150/jarvis-core.git`. La prémisse « aucun remote » est fausse pour ce dépôt. Mais ça ne le sauve pas : **141 commits locaux ne sont sur aucune ref distante** (96 sur la branche courante seule).

**2. L'exclusion rsync n'a produit quasiment aucun bruit.** `data/` (155 076 fichiers) et `apps/` (429) **sont présents** dans la copie. Seuls `backups/` et les `.db` manquent — et ils n'étaient pas suivis par git, donc ils ne génèrent aucun `D`. Sur 3 452 entrées, il y a **26 suppressions au total (0,7 %)**, et ce sont des répertoires de sortie d'audit (`20260611_audit_PassCerfa_/`, `20260806_Verification_Config_Waves_/`), pas des victimes du rsync. **Il n'y a pas de « part des deux » à faire : c'est du vrai travail à ~99 %.**

---

## 1. `/home/pamerys/m1-recover/git/jarvis` — **CRITIQUE**

| | |
|---|---|
| Branche | `feat/content-perf-engine` (11 branches locales) |
| Dernier commit | **2026-08-06 18:55** |
| Fichiers worktree les plus récents | **2026-08-08 08:12** (il y a 5 jours) |
| Stash | aucun |
| Taille | 29 Go (dont `.git` 4,9 Go) |

**Historique récent** : durcissement sécurité (injection de commande via email, injection de frontmatter dans les skills, identifiants n8n en dur), une série `sonde-doctor` (registre de sondes, injection réversible, verdicts), une série `gpu-bench` (mesure, médiane + IC95 bootstrap, CLI, protocole de bascule de topologie).

**Ce