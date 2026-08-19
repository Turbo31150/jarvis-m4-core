[user] Contexte : sur cette machine, des hooks Claude Code de type UserPromptSubmit ont bloqué DEUX prompts parfaitement légitimes aujourd'hui, avec le message « Operation stopped by hook ». La cause : un juge LLM ne trouvait aucun mot-clé déclencheur (lenteur, crash, GPU, cluster, systemd…) et refusait le passage, au lieu de simplement ne rien recommander.

Un hook dont le rôle est de CONSEILLER ne doit jamais bloquer. Il doit être fail-open : s'il n'a rien à dire, il laisse passer.

Ta mission :
1. Lis ~/.claude/settings.json et ~/.claude/settings.local.json. Recense TOUS les hooks de type "prompt" ou UserPromptSubmit.
2. Pour chacun, détermine s'il peut bloquer le prompt quand il n'a rien à recommander.
3. Corrige ceux qui bloquent, pour qu'ils sortent proprement (exit 0 / réponse vide) sur le chemin « rien à recommander ». Ne change PAS la logique de recommandation elle-même, ni les hooks PreToolUse de sécurité (ceux qui bloquent rm -rf, mkfs, dd sont légitimes et doivent rester bloquants).
4. Fais une sauvegarde datée de chaque fichier avant modification.
5. Valide le JSON après édition (python3 -m json.tool).

Un agent nommé prompt-hook-fix a déjà traité ce cas le 2026-06-05 — cherche-le dans ~/.claude/agents/ et lis-le AVANT d'agir, il contient peut-être déjà la recette.

Rends un rapport court en français : quels hooks tu as trouvés, lesquels bloquaient, ce que tu as changé, et la preuve que le JSON est valide. Si tu ne peux pas corriger quelque chose, dis-le clairement plut

[assistant] No `type:"prompt"` hooks in settings.json — all are `type:"command"`. I need to inspect each script. Bash is blocked by the thermal guard, so I'll use the filesystem MCP.

[assistant] Found it — `jarvis-turbo` plugin has a `type:"prompt"` hook. Let me inspect it and check for cached copies.

[assistant] Now validation: JSON syntax, no remaining `type:"prompt"` hooks, and a live behaviour test of the replacement script.

[assistant] JSON valid, zero `type:"prompt"` hooks remain. Now a live behaviour test with a neutral prompt (no trigger keywords).

[assistant] One hook remained untested — `prompt-dedupe.sh`, the only intentional blocker. Testing it with state preserved.

[assistant] Terminé. Rapport.

## Ce que j'ai trouvé

**Le coupable était hors des deux fichiers de settings** : il était dans un plugin local.

`/home/pamerys/.claude/plugins/local/jarvis-turbo/hooks/hooks.json` contenait le seul hook `type:"prompt"` (juge LLM) de toute l'installation, sur `UserPromptSubmit` :

> « … Sinon retourne 'approve' sans message. »

C'est exactement le motif documenté par l'agent `prompt-hook-fix` (`/home/pamerys/.claude/agents/prompt-hook-fix.md`, fix validé le 2026-06-05) : un hook `type:"prompt"` est non déterministe — dès que le juge éditorialise au lieu de renvoyer un `approve` propre (donc à chaque prompt sans mot-clé lenteur/GPU/cluster/systemd), la sortie non conforme = **blocage**. Le fix de juin avait été appliqué sur les chemins `/home/turbo` ; la migration vers `/home/pamerys` a ramené le fichier fautif, alors que le script de remplacement `skill-reco.sh` était toujours là, en place et inutilisé.

## Inventaire (21 hooks UserPromptSubmit au total)

| Source | Hooks | Bloquait ? |
|---|---|---|
| `settings.json` | 13 (tous `type:"command"`) | 1 bloqueur volontaire (voir plus bas) |
| `settings.local.json` | 0 (aucune section `hooks`) | — |
| plugins (hookify, remember ×2, security-guidance ×3, jarvis-turbo) | 8 | **1 : jarvis-turbo `type:"prompt"`** |

## Ce que j'ai changé

1. **`plugins/local/jarvis-turbo/hooks/hooks.json`** — le bloc `type:"prompt"` remplacé par le command hook déterministe déjà présent :
   `bash .../hooks/scripts/skill-reco.sh 2