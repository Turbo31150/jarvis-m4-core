# Hook Stop — validation de fin de tâche (FAIL-SAFE)

**Fichier** : `~/.claude/hooks/stop-validation.sh` (exécutable, 0-token, pur bash)
**Journal** : `~/.claude/hooks/stop-validation.log`
**Backlog** : tâche #16.

## Ce qu'il fait
À la fin de chaque réponse (événement `Stop`), il fait une vérification **légère et non
bloquante** :
- compte les `TODO` ouverts dans `~/.claude/JARVIS_TASKS.md` ;
- repère les fichiers `.py` modifiés depuis < 10 min dans le `cwd`, sans test associé.

S'il y a quelque chose à signaler, il émet un **rappel visible mais non bloquant**
(`systemMessage`) et l'écrit dans le journal. Sinon il se tait (`{}`).

## Garanties fail-safe (aucune boucle possible)
- **`exit 0` garanti** dans tous les cas (erreur, DB absente, `jq` manquant, stdin vide/corrompu) — `trap ... ERR` + voie de sortie unique.
- **Jamais `{"decision":"block"}`** → jamais de « Operation stopped by hook ».
- **Anti-loop #1** : si `stop_hook_active=true` (Claude relancé par un Stop hook), sortie immédiate.
- **Anti-loop #2** : anti-réentrance temporelle (8 s) via `~/.claude/hooks/.stop-validation-state`.
- **0-token** : aucune inférence LLM. (Si un jour une inférence était voulue, la déléguer à `bash ~/jarvis/scripts/lm-ask.sh` — jamais d'appel facturé.)

## Bloc JSON à coller dans `~/.claude/settings.json`
Dans `hooks` → `Stop`, **ajouter un nouvel objet** au tableau (ne remplace aucun hook existant) :

```json
{
  "hooks": [
    {
      "type": "command",
      "command": "bash /home/pamerys/.claude/hooks/stop-validation.sh 2>/dev/null || echo '{}'",
      "timeout": 8,
      "statusMessage": "Validation fin de tâche (non bloquant)...",
      "async": true
    }
  ]
}
```

`"async": true` et `|| echo '{}'` sont des ceintures de sécurité supplémentaires : même
si le script disparaissait ou plantait, le harnais ne reste jamais bloqué.

> `hooks.Stop` est un **tableau de groupes** ; il en contient déjà plusieurs (TTS, handoff,
> protocole…). On y **ajoute** ce groupe, on n'écrase rien.

## Tester
```bash
# Cas nominal (peut afficher un rappel) :
echo '{"stop_hook_active":false,"cwd":"'"$PWD"'"}' | bash ~/.claude/hooks/stop-validation.sh; echo "exit=$?"
# Anti-loop (doit rendre {} exit 0) :
echo '{"stop_hook_active":true}' | bash ~/.claude/hooks/stop-validation.sh; echo "exit=$?"
# Entrée corrompue (doit rendre {} exit 0) :
echo 'xxx' | bash ~/.claude/hooks/stop-validation.sh; echo "exit=$?"
# Journal :
tail ~/.claude/hooks/stop-validation.log
```
Tout doit finir en `exit=0`.

## Désactiver vite (en cas de doute ou de boucle)
1. **Le plus simple** — retirer le droit d'exécution (le `|| echo '{}'` du bloc prend le relais, aucune boucle) :
   ```bash
   chmod -x ~/.claude/hooks/stop-validation.sh
   ```
2. **Neutraliser sans toucher au JSON** — renommer le script :
   ```bash
   mv ~/.claude/hooks/stop-validation.sh ~/.claude/hooks/stop-validation.sh.off
   ```
3. **Retrait propre** — supprimer le groupe ajouté dans `hooks.Stop` de `settings.json`, puis
   `/config` ou relancer une session pour recharger.

> Rappel : ce hook ne peut structurellement pas provoquer de boucle (il ne renvoie jamais
> `block` et sort toujours en `exit 0`). Ces procédures sont là par principe de précaution.
