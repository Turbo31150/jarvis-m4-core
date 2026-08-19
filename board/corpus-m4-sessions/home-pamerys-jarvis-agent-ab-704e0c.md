[user] CONTEXTE: machine M4 (pamerys-m4), uid=1000(pamerys), repo /home/pamerys/jarvis.
REGLE ABSOLUE: LECTURE SEULE. Tu ne modifies AUCUN fichier, tu ne demarres/arretes AUCUN service,
tu ne fais AUCUN git commit. Uniquement: cat, ls, grep, find, head, sed -n, sqlite3 en SELECT, --help.
REGLE DOCKER: la commande 'docker' locale est BLOQUEE par un hook (pile perimee).
Utilise TOUJOURS /home/pamerys/jarvis/bin/jarvis-docker a la place.
REGLE ZERO-HALLUCINATION: chaque affirmation doit citer un chemin de fichier reel + un extrait reel.
Si tu n'as pas verifie, dis "NON VERIFIE". N'invente jamais un nom de script ou une option CLI.
Reponds en francais.

MISSION — VERIFICATION ADVERSARIALE.
Un agent explorateur pretend ceci (axe agents):
  chemin: /home/pamerys/.claude/agents/
  role pretendu: Repertoire canonique des agents Claude Code (215 fichiers .md a la racine, 5 sous-dossiers)
  commande pretendue: ls -1 /home/pamerys/.claude/agents/*.md | wc -l
  preuve fournie: 215 ; find /home/pamerys/.claude/agents -name '*.md' -type f | wc -l -> 267 ; sous-dossiers : security(4) testing(4) ops(9) engineering(7) .backup-desc-20260808(28)

Ta mission est de REFUTER. Par defaut, considere que c'est FAUX jusqu'a preuve du contraire.
1. Le fichier existe-t-il vraiment ? (ls -la, file)
2. Fait-il vraiment ce qui est pretendu ? Lis-le REELLEMENT (cat / sed -n). Ne te fie pas au nom.
3. La commande pretendue est-elle valide ? Verifie les options dans le code source
   (cherche argparse/getopts/case).

[assistant] Counts match at first pass. Now let me verify the subdirectories and the actual content of the files.

[assistant] Now the adversarial checks: are all 215 root files really valid agent definitions?

[assistant] All numbers match so far. Final rigor check: are the 24 subdirectory files distinct agents or duplicates?

[assistant] Vérification terminée. Tous les chiffres avancés sont exacts, mais j'ai relevé des nuances importantes sur leur interprétation.