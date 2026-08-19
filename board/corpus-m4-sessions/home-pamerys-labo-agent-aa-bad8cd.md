[user] CONTEXTE — Le disque dur USB M1 est monté en LECTURE sur /media/pamerys/JARVIS-M1/home/turbo (rootfs de la machine M1, utilisateur "turbo").
La machine courante est M4, utilisateur "pamerys", HOME=/home/pamerys.
Un premier import a DÉJÀ été fait : ~/.claude/{agents,skills,commands,hooks,plugins}, ~/.mcp.json (30 serveurs),
~/.claude/CLAUDE-M1-PROTOCOLE.md, ~/.claude/cartes-mentales/, ~/bin (38), et 4 fichiers ~/.bash_*.m1 sourcés
par un bloc IMPORT-M1-TERMINAL dans ~/.bashrc.

RÈGLES DURES (non négociables) :
1. Le disque USB /media/pamerys/JARVIS-M1/home/turbo est en LECTURE SEULE — n'y écris JAMAIS.
2. Fusion ADDITIVE uniquement : jamais écraser un fichier M4 existant. Utilise rsync --ignore-existing,
   ou copie vers un nom suffixé .m1 quand le fichier existe déjà des deux côtés.
3. Réécriture de chemins : /home/turbo/ -> /home/pamerys/ SAUF sur les lignes contenant "turbo@"
   (ce sont de vrais chemins distants SSH, les casser casse session-restore).
   Commande de référence : sed -i '/turbo@/! s|/home/turbo/|/home/pamerys/|g' <fichier>
4. SECRETS : jetons/API keys restent dans des fichiers chmod 600 sous ~/. JAMAIS écrire un secret
   dans /home/pamerys/labo (dépôt git). Ne JAMAIS afficher la valeur d'un secret dans ton rapport —
   nomme la variable, pas la valeur.
5. N'active AUCUN service/timer systemd, ne démarre aucun daemon, ne modifie aucun état runtime.
6. Disque à 92% — ne copie pas de cache/ ni d'archive volumineuse. Signale toute copie > 200 Mo au lieu de la f

[assistant] I'll inventory the terminal surface. Let me start by checking what exists on both sides.

[assistant] Now let me extract aliases, exports and functions from both to find what M1 adds.

[assistant] Let me check whether the M1-only aliases are already covered by the previously imported `.m1` files.

[assistant] `~/.ssh/config` on M4 is blocked by permission rules — I'll note that. Continuing with the terminal emulator and binaries.

[assistant] Many entries failed the existence test — they're likely dangling symlinks. Let me verify.