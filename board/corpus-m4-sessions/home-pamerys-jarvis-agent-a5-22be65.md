[user] CONTEXTE: machine M4 (pamerys-m4), uid=1000(pamerys), repo /home/pamerys/jarvis.
REGLE ABSOLUE: LECTURE SEULE. Tu ne modifies AUCUN fichier, tu ne demarres/arretes AUCUN service,
tu ne fais AUCUN git commit. Uniquement: cat, ls, grep, find, head, sed -n, sqlite3 en SELECT, --help.
REGLE DOCKER: la commande 'docker' locale est BLOQUEE par un hook (pile perimee).
Utilise TOUJOURS /home/pamerys/jarvis/bin/jarvis-docker a la place.
REGLE ZERO-HALLUCINATION: chaque affirmation doit citer un chemin de fichier reel + un extrait reel.
Si tu n'as pas verifie, dis "NON VERIFIE". N'invente jamais un nom de script ou une option CLI.
Reponds en francais.

MISSION — VERIFICATION ADVERSARIALE.
Un agent explorateur pretend ceci (axe boot-containers):
  chemin: /home/pamerys/jarvis/bin/jarvis-docker
  role pretendu: Point d'acces UNIQUE aux conteneurs. Route toute commande docker vers la tour par SSH, avec echappement printf %q argument par argument.
  commande pretendue: /home/pamerys/jarvis/bin/jarvis-docker ps -a   (ou: jarvis-docker service ls / stack ls / node ls / inspect ...)
  preuve fournie: Lignes 14 et 27 : 'TOUR="${JARVIS_TOUR_HOST:-root@100.124.69.1}"' puis 'exec ssh -o BatchMode=yes -o ConnectTimeout=8 "$TOUR" "$remote"'. Sans argument il sort en code 2 avec 'usage: jarvis-docker <commande docker...> / route vers root@100.124.69.1 (pile JARVIS reelle)'. Idempotent (pur passe-plat, aucun etat local). Present dans le PATH : command -v jarvis-docker => /home/pamerys/.local/bin/jarv

[assistant] I'll verify the claims about `/home/pamerys/jarvis/bin/jarvis-docker` adversarially.

[assistant] Source matches the claimed lines exactly. Now let me verify the hook, the settings.json declaration, and the SSH alias.

[assistant] Hook and settings line 100 confirmed. Now the SSH alias and a live read-only test.

[assistant] Usage/exit-code 2 confirmed verbatim. Now the decisive test: does the passthrough actually work?

[assistant] Live passthrough works and returns real containers. Let me verify the other claimed subcommands and hunt for the hardcoded-fallback trap.

[assistant] Let me properly verify exit-code propagation (my last measurement was masked by the pipe) and the systemd claim.

[assistant] Every attempt at refutation failed. Verification summary:

**1. Existence** — `/home/pamerys/jarvis/bin/jarvis-docker`, 887 octets, 27 lignes, `Bourne-Again shell script, UTF-8 text executable`, mode `-rwxrwxr-x`.

**2. Contenu réel** — les deux lignes citées sont exactes au caractère près :
- ligne 14 : `TOUR="${JARVIS_TOUR_HOST:-root@100.124.69.1}"`
- ligne 27 : `exec ssh -o BatchMode=yes -o ConnectTimeout=8 "$TOUR" "$remote"`
- lignes 22-25 : boucle `for arg in "$@"; do remote+=" $(printf '%q' "$arg")"; done` — l'échappement argument par argument est bien là.

**3. Sans argument** — reproduit en live : `usage: jarvis-docker <commande docker...>` / `route vers root@100.124.69.1 (pile JARVIS réelle)`, `EXIT=2`. Exact.

**4. Commandes prétendues** — testées en lecture seule, toutes réelles :
- `ps -a` → 29 conteneurs (`jarvis-postgres`, `jarvis-openclaw`, `jarvis-cowork`…)
- `service ls` → 9 services répliqués, `node ls` → 2 nœuds (`serveurremjarvis` Leader, `rem-linux` Reachable), `stack ls` → 3 stacks
- Intégrité du quoting prouvée : `ps --format '{{.Names}}'` arrive intact et renvoie les noms.

**5. Chasse au repli codé en dur / fausse réussite — NÉGATIF.** C'est le point que je cherchais le plus à faire tomber. Aucun `||`, aucune valeur de secours, aucun `echo` de résultat simulé dans les 27 lignes. Les codes de sortie remontent honnêtement :
- `zzz-inexistant` → **1** avec l'erreur distante réelle `docker: unknown command`
- `inspect conteneur-qui-nexiste-pas` → **1**
- 