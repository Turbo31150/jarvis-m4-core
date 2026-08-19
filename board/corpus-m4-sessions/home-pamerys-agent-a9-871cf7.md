[user] Tu es l'agent PACKAGE-LIVRABLES. Objectif : créer sur M4 un dossier par produit vendable, chacun prêt à zipper et envoyer (Gumroad/systeme.io). Écriture locale de fichiers de livraison + manifeste Notion.

⚠️ SÉCURITÉ ABSOLUE — un livrable client ne doit JAMAIS contenir de secret/PII :
- Avant de copier un fichier, vérifie qu'il ne contient pas de secret/token/clé/mot de passe/PII. Motifs à EXCLURE ou NEUTRALISER ([SECRET]) : API_KEY, TOKEN, BEARER, PASSWORD, sk-, ntn_, ghp_, .env, *.key, *.pem, keys.txt, chemins /home absolus personnels, emails/tel perso, données élèves/clients.
- N'inclus AUCUN : *.env, *.db, secrets*, certs/, credentials, node_modules, .git.
- Si un script contient un chemin/secret perso, remplace par un placeholder générique.

DESTINATION : /home/pamerys/jarvis/livrables/<slug>/ (crée l'arbo). Un sous-dossier par produit.

PRODUITS À PACKAGER (ceux qui ont du CONTENU RÉEL) — pour chacun : copie les fichiers réels (scrubbés), + écris README.md (présentation + installation + usage), + FICHE-VENTE.md (reprends la fiche de vente si elle existe dans Notion), + LICENSE.txt (propriétaire, usage sous licence) :
1. jarvis-domino-engine (moteur dominos) — fichiers depuis ~/jarvis (bin/dominos, domino-compile.py, séries d'exemple) SCRUBBÉS
2. cloud-router-8 — ~/jarvis/scripts/cloud-router-8.py + doc CLOUD-ROUTER-8.md
3. repurpose 1→4 — ~/jarvis/scripts/repurpose.sh + doc REPURPOSE-1-4.md
4. n8n-mcp — ~/jarvis/mcp/tools/n8n.py + doc BRANCHER-N8N-MCP.md
5. checkpoint-

[assistant] I'll start by checking which source files actually exist, then package the ones with real content.

[assistant] domino-compile.py doesn't exist; the n8n "Bearer" is just an env-var placeholder (safe). Let me read the remaining scripts and one example domino/series.

[assistant] Scripts are clean (env-based secrets). Let me check n8n workflows for PII and read the doc files.

[assistant] Clean — no secrets/PII (the `@` hits are `@@SUBJTOKEN@@` placeholders, env-var names carry no values). Now let me check Notion for existing sale sheets/prices.

[assistant] There's an existing sales-sheet page. Let me fetch the full sales gamut page to get all prices at once.

[assistant] Only the domino fiche exists in Notion. Now let me write the LICENSE (shared) into all folders, then per-product README and FICHE-VENTE.

[assistant] The `board-souverain-b2b` folder is another agent's (empty, not mine) — leaving it. Now the Notion manifest page.

[assistant] Terminé. Rapport final.

## PACKAGE-LIVRABLES — rapport

**Racine :** `/home/pamerys/jarvis/livrables/`

**9 dossiers produits créés** (le 10e, `board-souverain-b2b`, appartient à un autre agent — vide, laissé intact).

| Produit | Statut | Prix |
|---|---|---|
| jarvis-domino-engine | PRÊT À ZIPPER (runner `bin/dominos` + 3 exemples de séries ; la biblio complète 835 pipelines reste à joindre au packaging final — `domino-compile.py` n'existe pas sur le disque) | 89 € |
| cloud-router-8 | PRÊT À ZIPPER | 39 € (proposé) |
| repurpose 1→4 | PRÊT À ZIPPER | 29 € (proposé) |
| n8n-mcp | PRÊT À ZIPPER | 49 € (proposé) |
| checkpoint-securise | PRÊT À ZIPPER | 19 € (proposé) |
| hooks-gouvernance | PRÊT À ZIPPER (3 hooks + README, pas de FICHE demandée) | 29 € (proposé) |
| stop-cycles-m4 | PRÊT À ZIPPER | 19 € (proposé) |
| pack-n8n-workflows | PRÊT À ZIPPER (5 JSON scrubbés) | 39 € (proposé) |
| formation-ia-locale-souveraine | STRUCTURE SEULE (PROGRAMME.md + A-PRODUIRE.md, vidéos non tournées) | 149 € (proposé) |

Chaque dossier produit contient les fichiers réels scrubbés + `README.md` + `FICHE-VENTE.md` + `LICENSE.txt` (propriétaire). La fiche domino reprend la fiche Notion existante (89 €) ; c'était la seule fiche existante, les autres prix sont proposés (ancrés sur la gamme Gumroad 19-149 €), marqués « à valider par Franck ».

**Aucun secret / PII dans les livrables — vérifié par :**
- lecture intégrale des sources : tous lisent leurs secrets via variables d'environnement (`