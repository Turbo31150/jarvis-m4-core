[user] Contexte : le fichier ~/.claude/CLAUDE.md est relu par le modèle à CHAQUE tour de CHAQUE session. Il est devenu énorme (cluster, protocole en 7 étapes, bibliothèque-routeur, tableaux MCP, catalogue de commandes slash). La recommandation convergente de la recherche est un plafond de 1 500 à 2 000 tokens.

Pire : il décrit un parc matériel qui n'existe plus. Le parc RÉEL au 14/08/2026 est uniquement : M4 (la machine locale), M6 (LM Studio en câble direct sur 10.42.0.230:1234) et Rémi (Ollama en Tailscale sur 100.113.121.61:11434). Les machines M1, M2, M5 et OL1 n'existent plus — chaque mention leur coûte des tokens à chaque tour ET induit le modèle en erreur (du temps a réellement été perdu aujourd'hui à router vers ces machines mortes).

Ta mission, en LECTURE ET ANALYSE uniquement — ne modifie AUCUN fichier :
1. Lis ~/.claude/CLAUDE.md et ~/CLAUDE.md et ~/jarvis/CLAUDE.md. Mesure la taille de chacun (mots et estimation de tokens à 1,3 token par mot).
2. Identifie précisément : (a) ce qui doit RESTER — lois de comportement, contraintes matérielles qu'il ne faut jamais réapprendre, règles de sécurité ; (b) ce qui doit PARTIR en skill chargée à la demande — catalogues, tableaux de référence, listes de commandes ; (c) ce qui est MORT et doit disparaître — M1, M2, M5, OL1 et tout ce qui en dépend.
3. Propose un CLAUDE.md cible sous 2 000 tokens, écrit en entier dans ta réponse, prêt à être relu par l'utilisateur.
4. Liste les skills à créer pour accueillir ce qui sort, avec pour c

[assistant] Thermal guard blocked the second command. I have the measurements. Now reading the content.

[assistant] ## 1. Mesures réelles (comptées, pas estimées)

| Fichier | lignes | mots | octets | tokens estimés (×1,3) |
|---|---|---|---|---|
| `/home/pamerys/.claude/CLAUDE.md` | 330 | **2 676** | 24 516 | **≈ 3 479** |
| `/home/pamerys/CLAUDE.md` | 46 | 367 | 2 568 | ≈ 477 |
| `/home/pamerys/jarvis/CLAUDE.md` | 57 | 414 | 3 021 | ≈ 538 |
| **Total** | 433 | **3 457** | 30 105 | **≈ 4 494** |

Charge réelle par tour : **≈ 3 956 tokens** partout dans `~`, **≈ 4 494** quand tu travailles dans `~/jarvis`. Face au plafond recommandé de 1 500–2 000, le seul fichier global fait déjà **1,7 à 2,3 fois le budget total**.

Réserve honnête : `1,3 token/mot` sous-estime CE fichier. Il contient **1 683 caractères `═`** et **40 lignes purement décoratives** pesant **5 073 octets, soit 20,7 % du fichier** — des séparateurs qui ne portent aucune information et coûtent bien plus qu'un mot en tokenisation réelle. `tiktoken` n'est pas installé sur M4, je ne fabrique donc pas de chiffre exact.

### Découpage par section du fichier global

| Lignes | Section | mots | ≈ tokens | Verdict |
|---|---|---|---|---|
| 1-7 | Routeur orchestration client | 55 | 72 | **MORT** |
| 9-35 | État opérationnel M4+M6 | 197 | 256 | **RESTER** (condensé) |
| 37-59 | Protocole obligatoire 7 étapes | 312 | 406 | **SKILL** |
| 61-75 | LOI 1 | 108 | 140 | **RESTER** |
| 76-105 | LOI 2 + cascade + anti-patterns | 279 | 363 | **RESTER** (condensé) |
| 107-121 | Ollama local + cloud | 103 | 134 | **SKILL** (partiel) |
| 123-146 | C