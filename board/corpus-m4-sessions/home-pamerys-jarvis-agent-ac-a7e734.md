[user] CONTEXTE: machine M4 (pamerys-m4), uid=1000(pamerys), repo /home/pamerys/jarvis.
REGLE ABSOLUE: LECTURE SEULE. Tu ne modifies AUCUN fichier, tu ne demarres/arretes AUCUN service,
tu ne fais AUCUN git commit. Uniquement: cat, ls, grep, find, head, sed -n, sqlite3 en SELECT, --help.
REGLE DOCKER: la commande 'docker' locale est BLOQUEE par un hook (pile perimee).
Utilise TOUJOURS /home/pamerys/jarvis/bin/jarvis-docker a la place.
REGLE ZERO-HALLUCINATION: chaque affirmation doit citer un chemin de fichier reel + un extrait reel.
Si tu n'as pas verifie, dis "NON VERIFIE". N'invente jamais un nom de script ou une option CLI.
Reponds en francais.

MISSION — VERIFICATION ADVERSARIALE.
Un agent explorateur pretend ceci (axe skills):
  chemin: /home/pamerys/jarvis/bin/skillmp-cascade.sh
  role pretendu: Cascade massive : garde-fous charge/RAM/GPU, lecture du plan, persistance de la todolist dans skillmp_cascade_taches, dispatch par vagues appelant `skillmp install <slug> --cible both`.
  commande pretendue: bash /home/pamerys/jarvis/bin/skillmp-cascade.sh --help
  preuve fournie: L43-49 : resolution du CLI — 'if command -v skillmp ... elif [ -x "$JARVIS/bin/skillmp" ] ... else SKILLMP="python3 $JARVIS/bin/skillmp.py"'. L82 : seuils auto charge>=12, ram>=92%, gpu>=95C.

Ta mission est de REFUTER. Par defaut, considere que c'est FAUX jusqu'a preuve du contraire.
1. Le fichier existe-t-il vraiment ? (ls -la, file)
2. Fait-il vraiment ce qui est pretendu ? Lis-le REELLEMENT (cat / sed -n

[assistant] Now let me verify the critical dependency: does the `skillmp` CLI and its `install ... --cible both` option actually exist?

[assistant] Let me run the claimed command (read-only: `sed -n` + exit) and inspect the DB state.

[assistant] Let me hunt for the hard-coded-fallback / false-success pattern the mission warns about.

[assistant] Verification complete. Every element of the claim checks out against the real file.

**1. Existence** — `/home/pamerys/jarvis/bin/skillmp-cascade.sh` : `-rwxrwxr-x 1 pamerys pamerys 8066 août 18 10:06`, `Bourne-Again shell script, UTF-8 text executable`, 190 lignes.

**2. Role** — les 4 fonctions revendiquees sont toutes presentes et lues reellement :
- Garde-fous L62-86 : `CHARGE=$(cut -d' ' -f1 /proc/loadavg)`, `RAM_PC=$(free | awk '/Mem:/{printf "%d", $3/$2*100}')`, `GPU_T=$(nvidia-smi --query-gpu=temperature.gpu ...)`
- Lecture du plan L89-100 : heredoc python sur `$PLAN` (fichier reel, 82 Mo, present)
- Persistance L123-126 : `CREATE TABLE IF NOT EXISTS skillmp_cascade_taches (...)` — table confirmee en base
- Dispatch par vagues L159-178 : `for v in $(seq 1 "$VAGUE")` + L168 `if $SKILLMP install "$SKILL" --cible both >/dev/null 2>&1;`

**3. Commande** — `--help` est bien un cas du `case` (L36 : `-h|--help) sed -n '2,20p' "$0"; exit 0;;`). Lancee (lecture seule stricte) : sortie conforme, `EXIT=0`.

**4. Chasse au repli code en dur** — le dispatch n'invente pas de succes : `ETAT` derive du code de retour reel. J'ai trouve **un** repli en dur (L71-74 `GPU_T=0` si sonde muette) mais il est **declare explicitement** L76 : `AVERTISSEMENT sonde GPU muette (nvidia-smi HS) : garde-fou thermique INACTIF` — c'est de la transparence, pas une fausse reussite. `nvidia-smi` repond actuellement `48` : le garde-fou est actif.

**Chaine de dependance validee** : `skillmp` absent du PATH