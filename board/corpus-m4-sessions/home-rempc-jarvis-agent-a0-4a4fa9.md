[user] Tu travailles dans le dépôt /home/rempc/jarvis. Mission EN LECTURE SEULE : ne modifie, ne crée, ne supprime AUCUN fichier. Tu produis un constat, pas un correctif.

CONTEXTE : Rémi vient de demander l'implémentation d'un protocole « MODE AUDIT / DEEP RESEARCH ». Un pre-flight rapide montre que ce protocole semble DÉJÀ implémenté dans `bin/jarvis`. Avant de construire quoi que ce soit, il faut savoir exactement ce qui existe et ce qui manque réellement. Une erreur documentée du dépôt (post-mortem du 2026-08-04) est d'avoir lancé des agents pour un besoin qui n'existait pas, faute de vérification préalable — c'est précisément ce qu'on évite ici.

LE SPEC DEMANDÉ, à confronter au réel. Il décrit 8 sous-commandes :
- `audit:init` — lit une config YAML (profils, modes, mapping agents/outils), charge les plugins/outils selon le profil, construit un contexte JSON partagé
- `audit:scan-local` — scan filesystem (taille, arborescence, langages, fichiers clés), analyse git (branches, fréquence de commit, contributeurs), détection des modules JARVIS présents, check conformité basique. Sort `audit_scan_local.json` + `.md`
- `audit:scan-web` — fetch site client (HTML, sitemap, offres, pricing, mentions légales), scan GitHub, recherche LinkedIn, web search ciblé. Sort `audit_scan_web.json` + `.md`
- `audit:multi-agents` — route le contexte vers des agents spécialisés tech / business / legal(souveraineté) / ops, chacun produisant son rapport intermédiaire
- `audit:report` — fusionne les rapp

[assistant] Key detail spotted: `bin/jarvis` points to `/home/rempc/JARVIS/` (uppercase). Let me verify the actual code.

[assistant] Critical: `bin/jarvis` (12 lines) calls `cli.py`, which delegates back to `~/jarvis/bin/jarvis`. Let me check for recursion.

[assistant] The `M bin/jarvis` in git status is suspicious. Let me check what was overwritten.

[assistant] The real pipeline is the 191-line `bin/jarvis` at HEAD — the working copy has been replaced by a 12-line stub. Let me read the rest.

[assistant] Now the picture is clear. Let me verify the wave inventory and the `simulation` wiring.

[assistant] ## Constat

Le protocole est **déjà implémenté**, mais il est **actuellement cassé par une régression non commitée** — et le code qui s'exécute à la place est précisément la coquille vide fabricante que le dépôt avait déjà identifiée et mise au rebut.

### L'architecture réelle (3 couches, pas 1)

```
bin/jarvis (191 l., bash)  →  claude -p "/mode-audit ..."  →  ~/.claude/commands/mode-audit.md (268 l.)
      ↑ lit config/audit-config.yaml (230 l., SoT)              ↑ le VRAI moteur : un prompt, pas du Python
```

L'audit n'est pas fait par du code Python : `bin/jarvis` est un dispatcher qui valide profil/mode contre le YAML puis lance Claude en headless sur le slash-command `/mode-audit`, qui orchestre les briques existantes (codebase-audit-suite ln-621/623/624, capture-web, jarvis-router, OpenClaw, board). C'est pour ça que les sorties réelles sont substantielles.

### La régression (bloquant #1)

`git status` liste `M bin/jarvis` : **199 lignes supprimées, 10 ajoutées**. Le working copy de `/home/rempc/jarvis/bin/jarvis` n'est plus le pipeline — c'est un stub de 12 lignes :

```bash
# /home/rempc/jarvis/bin/jarvis:9
python3 /home/rempc/JARVIS/audit_engine/cli.py "$COMMAND" "$@"
```

`/home/rempc/JARVIS/` (majuscules) est un répertoire **hors dépôt, non versionné**, et son `cli.py` (218 l.) est la variante de la coquille vide : `audit_report()` écrit une chaîne littérale, `audit_todo()` aussi, `audit_cascade()` idem. Preuve exécutée :

```
$ /home/rempc/jarvis/bin/jarvis au