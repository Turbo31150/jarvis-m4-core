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
  chemin: /home/pamerys/jarvis/bin/jarvis-cockpit.sh
  role pretendu: Ouvre les CLI de l'ecosysteme (agy, openclaw, gemini, veille board) comme fenetres tmux d'une session existante. Outil d'interface, PAS un demarreur de services.
  commande pretendue: /home/pamerys/jarvis/bin/jarvis-cockpit.sh          # monte les fenetres manquantes
/home/pamerys/jarvis/bin/jarvis-cockpit.sh --status # sonde uniquement, n'ouvre rien
  preuve fournie: Idempotence EXPLICITE, fonction ouvre() lignes 46-54 : 'if tmux list-windows -t "$SESSION" -F "#W" | grep -qx "$nom"; then echo "  $nom : deja ouverte"; return; fi'. Commentaire l.44-45 : 'On ne recree pas ce qui existe deja : relancer le cockpit deux fois ne doit pas empiler des doublons.' Exige une session tmux

[assistant] Script read in full. Now let me verify the peripheral claims: absence from PATH, systemd, and the aliases.

[assistant] Key detail found: the `cockpit` alias points elsewhere. Let me verify the vault and the board query the script embeds.

[assistant] Let me check the last adversarial angle: does it start services indirectly (openclaw bare command), and confirm no docker/systemctl.

[assistant] Vérification complète terminée. Tous les éléments du rapport sont confirmés par lecture réelle du code.

**Fichier** : `/home/pamerys/jarvis/bin/jarvis-cockpit.sh` — existe, `-rwxrwxr-x`, 2756 octets, 83 lignes, `Bourne-Again shell script`.

**Vérifications ligne par ligne (toutes exactes)** :
- l.14 : `SESSION="${JARVIS_COCKPIT_SESSION:-claude-code}"` — variable et défaut confirmés.
- l.39-42 : `if ! tmux has-session -t "$SESSION" ... echo "Session tmux '$SESSION' absente. Rien ouvert." >&2 ; exit 1` — confirmé.
- l.44-45 : commentaire cité au mot près (« On ne recrée pas ce qui existe déjà : relancer le cockpit deux fois ne doit pas empiler des doublons. »).
- l.46-54 : `ouvre()` avec le garde `tmux list-windows -t "$SESSION" -F '#W' 2>/dev/null | grep -qx "$nom"` → `echo "  $nom : déjà ouverte"; return`. Idempotence réelle (le rapport citait `-F "#W"` en doubles quotes et omettait `2>/dev/null` : paraphrase, sémantiquement identique).
- l.58-59, 66, 76-78 : les 4 fenêtres agy / openclaw / gemini / board.
- l.62-73 : `sops -d "$VAULT" > "$ENVF"` avec `ENVF=/dev/shm/.jarvis-cockpit-$$` sous `umask 077`, puis `rm -f`.

**PAS un démarreur de services** — réfutation tentée et échouée : `grep -nEi "docker|systemctl|service |daemon|compose|podman|nohup|disown"` sur le fichier retourne **rc=1, zéro occurrence**. Les seules commandes externes sont `tmux`, `sops`, `timeout`, `grep`, `rm`, `sqlite3`, `watch`. `openclaw` est invoqué nu (`openclaw --help` montre que le démon est un sou