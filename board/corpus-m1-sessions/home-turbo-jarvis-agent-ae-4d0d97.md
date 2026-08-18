[user] Tu construis un générateur de **CLI à trous** — des gabarits de commandes paramétrés qu'un LLM remplit ensuite, quel que soit le modèle. Tu ne connais rien de la conversation qui précède. Stdlib Python uniquement, aucune dépendance externe.

## L'idée

L'utilisateur a des années d'historique : commandes shell, sessions d'agent, navigation. Beaucoup de ces commandes sont **la même intention avec des valeurs différentes** — même squelette, arguments qui changent. Aujourd'hui elles sont stockées une par une, en dur, non réutilisables.

Il veut qu'elles deviennent des **gabarits à trous** : le squelette est figé et éprouvé, les valeurs variables deviennent des paramètres nommés qu'un LLM remplit au moment de l'usage. On ne redécouvre jamais la forme d'une commande, on ne remplit que ses valeurs.

Exemple de ce qui doit sortir — le gabarit, pas la commande :
```
sqlite3 "file:{db}?mode=ro" "SELECT {colonnes} FROM {table} LIMIT {n};"
   params : db (chemin) · colonnes · table · n (entier, defaut 10)
   vu 14 fois · danger 🟢 · mots-cles : sqlite lecture requete
```

## Les matières premières (lis-les avant d'écrire)

| Fichier | Contenu |
|---|---|
| `/home/turbo/jarvis/data/histo/shell.md` | commandes bash récurrentes, format `- [Nx] \`commande\`` |
| `/home/turbo/jarvis/data/histo/sessions.md` | 940 commandes extraites de 32 180 messages d'agent, même format |
| `/home/turbo/jarvis/data/histo/navigation.md` | historique de navigation (URL + titres) |
| `/home/turbo/jarvis/data/reg

[assistant] The histo files are small; the real corpus is `registre_actions.db`. Let me inspect both.

[assistant] Corpus understood: `registre_actions.db` (85 765 actions) is BLOCS-INDEX already ingested, with metadata. Let me check a few structural details, then write the generator.

[assistant] Two calibration issues: the ratio metric rejects the spec's own canonical example, and path naming mislabels `/var/log/syslog` as `dossier`. Fixing both.

[assistant] Every parameter got a default, which makes `remplir`'s refusal path unreachable — a "most frequent" value that occurs once isn't a frequency. Tightening the default rule.

[assistant] Terminé.

## 1. Fichiers créés

- `/home/turbo/jarvis/bin/cli-gabarits.py`
- `/home/turbo/jarvis/.claude/skills/gabarits/SKILL.md`
- base : `/home/turbo/jarvis/data/gabarits.db`

Aucun fichier existant modifié — md5 de `registre_actions.db`, `BLOCS-INDEX.tsv` et `data/histo/*.md` vérifiés identiques après build. `build` relancé deux fois → `754/9984/1139` à l'identique (idempotent).

## 2. Sortie réelle de `build` puis `stats`

```
=== BUILD TERMINE ===
commandes lues            : 91244
commandes exploitables    : 57124  (ont passe les filtres de forme)
commandes absorbees       : 9984  (17.5 % des exploitables : le reste ne generalise pas)
gabarits retenus          : 754
rejets (80961 au total) :
  singleton_non_generalisant     46771
  prose                          19392
  trop_long                       5937
  commentaire                     5391
  pas_assez_de_litteral           1818
  deja_gabarit_source             1312
  trop_de_trous                    121
  mot_cle_shell                     99
  aucun_trou                        70
  trop_court                        28
  markdown                          22
```

`stats` (extrait) : 654 🟢 / 30 🟠 / 70 🔴 · 673 stricts / 81 souples · 1 139 params dont **714 sans défaut** · littéral moyen 83 %.

## 3. Trois gabarits représentatifs

| # | squelette | params |
|---|---|---|
| 471 | `sqlite3 'file:{db}?mode=ro&immutable={n}' "SELECT {colonnes} FROM {table} ORDER BY ts DESC LIMIT {n_b}"` | db (déf. `/home/turbo/jarvis/cowor