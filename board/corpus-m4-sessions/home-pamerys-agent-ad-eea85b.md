[assistant] Je vais lire les fichiers existants pour comprendre les conventions avant de concevoir le hook.

[assistant] Le garde thermique bloque Bash (CPU 91°C). Comme c'est une tâche read-only de conception, je lis les hooks existants directement avec Read pour respecter les conventions.

[assistant] J'ai les conventions clés. Je regarde aussi `post-tool-use.sh` pour le style d'audit, puis je conçois le hook.

[assistant] J'ai toutes les conventions nécessaires. Voici la conception complète.

## Conception du hook Stop de validation

### Décision de design (importante)

Un hook Stop peut agir de deux façons :
- **`{"decision":"block","reason":"..."}`** → **relance** Claude avec le `reason` en contexte. Puissant (Claude peut vraiment finir le travail) mais **risque de boucle** et **relance du compute** — dangereux ici vu le contexte thermique (CPU déjà à 91°C) et la règle "Hook Stop en boucle → debug".
- **`{"systemMessage":"..."}`** → affiche un avertissement à l'utilisatrice, **sans relancer** Claude. Zéro boucle, zéro compute, thermiquement neutre. C'est déjà le pattern des hooks Stop existants (`settings.json:304`).

Je retiens **`systemMessage` par défaut** (le plus fail-safe et cohérent avec l'écosystème), avec le mode bloquant fourni en option commentée et strictement gardé par `stop_hook_active` (anti-boucle : une seule relance max).

Le hook détecte 3 signaux **0-token, lecture pure** :
1. **Fichiers non commités** — `git status --porcelain` dans le `cwd` si c'est un repo.
2. **Tests échoués récents** — lit `.pytest_cache/v/cache/lastfailed` (pytest y écrit les derniers échecs) — signal fiable sans rien exécuter.
3. **TODO/FIXME introduits** — comptés uniquement dans les fichiers modifiés non commités (bruit minimal).

### Code proposé : `~/.claude/hooks/validate-stop.sh`

```bash
#!/usr/bin/env bash
# validate-stop.sh — hook Stop : validation de fin de tâche (0-token, lecture pure).
#