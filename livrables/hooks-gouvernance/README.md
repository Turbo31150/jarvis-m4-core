# hooks-gouvernance

Trois hooks Claude Code prêts à l'emploi pour gouverner un poste de travail IA
local : garde thermique, validation de fin de tâche non bloquante, et injection
de contexte SQL avant inférence (0-token). Tous **fail-safe** : en cas d'erreur,
ils laissent toujours passer.

## Contenu
```
hooks/thermal-guard.sh       # PreToolUse : bloque si le CPU dépasse le seuil thermique
hooks/stop-validation.sh     # Stop : rappelle TODO/tests manquants, ne bloque JAMAIS
hooks/cache-board-lookup.sh  # UserPromptSubmit : injecte des extraits SQL FTS5 pertinents
README.md / LICENSE.txt
```

## Installation
Copiez les hooks dans `~/.claude/hooks/` et déclarez-les dans
`~/.claude/settings.json` :
```json
{
  "hooks": {
    "PreToolUse":      [{"hooks":[{"type":"command","command":"~/.claude/hooks/thermal-guard.sh"}]}],
    "Stop":            [{"hooks":[{"type":"command","command":"~/.claude/hooks/stop-validation.sh"}]}],
    "UserPromptSubmit":[{"hooks":[{"type":"command","command":"~/.claude/hooks/cache-board-lookup.sh"}]}]
  }
}
```
`chmod +x hooks/*.sh`.

## Détail des hooks
- **thermal-guard** : lit `/sys/class/thermal`, bloque (exit 2) au-delà du seuil
  (90 °C par défaut, ajustable dans le script). Fail-safe : toute erreur → passe.
- **stop-validation** : rappelle (sans jamais bloquer) les TODO ouverts et les
  `.py` modifiés sans test. Anti-réentrance + respect de `stop_hook_active` :
  aucune boucle « Operation stopped by hook ».
- **cache-board-lookup** : cherche dans une base SQLite FTS5 des extraits
  pertinents au prompt et les injecte en contexte. Lecture seule, 0 inférence.
  Adaptez le chemin `DB=` en tête de script à votre base.

## Sécurité
Aucun secret. Lecture pure de fichiers système / SQLite en lecture seule.
