[user] CONTRAINTES ABSOLUES (le non-respect invalide ton travail) :
- LECTURE SEULE. Tu ne modifies RIEN : pas de kill, pas de systemctl start/stop/restart,
  pas d'écriture, pas de suppression, pas de git push. Tu OBSERVES et tu RECOMMANDES.
- Le disque /media/pamerys/JARVIS-M1 est physiquement FRAGILE (connexion USB défaillante).
  Lecture seule stricte, jamais d'écriture dessus, et évite les scans exhaustifs longs.
- RGPD : /home/pamerys/jarvis/webapp/ecole.db contient des données d'ÉLÈVES RÉELS.
  Ne lis JAMAIS son contenu. Ne recopie aucun nom d'élève ou de famille nulle part.
- Les fichiers .env / secrets* / *.key / *.pem : tu peux lister leurs CHEMINS,
  jamais leur CONTENU. Ne recopie aucun secret dans ton rapport.
- N'utilise pkill/pgrep -f QUE avec des motifs qui ne matchent pas ta propre ligne
  de commande (piège déjà rencontré : le shell se tue lui-même).
- Machines : M4 = cette machine (/home/pamerys). M6 = ssh turbo@10.42.0.230 (répond mais
  TRÈS chargé, load 11 : mets des timeouts courts, n'insiste pas si ça traîne).
  M1 = OFFLINE, seul son disque USB est lisible. Rémi = 100.113.121.61 (Ollama OK, SSH refusé par ACL Tailscale).
- Si une commande échoue ou timeout, dis-le. Ne prétends jamais avoir vérifié ce que tu n'as pas vu.


MISSION — Préparer le lancement de la stack agents (agy, cli, openclaw, LM Studio) sous tmux.

L'utilisatrice veut lancer "tous les agents équipe IA : agy, cli, openclaw, LM Studio via tmux".
Contrainte forte : ses propres notes INTERDISENT

[assistant] I'll investigate read-only, starting with M4 local checks and M6 over SSH with short timeouts.

[assistant] `agy` is an interactive foreground process (STAT `Sl+`, parent = `-bash`). Let me identify what it actually is.

[assistant] `agy` is a 201 MB Go binary built from `google3` (Google's internal build). Let me confirm its identity and check Docker properly.

[assistant] Confirmed: `agy` = **Google Antigravity CLI**. Docker is active with **zero containers**. Now LM Studio and GPU on M6.

[assistant] `lms` **does** exist on M6 at `~/.lmstudio/bin/lms` (just not in the non-interactive PATH). Let me check its state and what's loading the machine.

[assistant] LM Studio server is **not running**; M6's load 12.8 comes from a Deja Dup backup + Chrome + a desktop session, not AI loops. Now openclaw and LM Studio models.

[assistant] Critical finding: M6 already runs permanent autonomous loops. Let me see the full service list.

[assistant] M6 already runs 30 JARVIS services including permanent autonomous loops. Let me check the LMS watchdog and openclaw services.

[assistant] Let me verify how `agy` is attached, the LMS port options, and M6 resource headroom.

[assistant] `agy` runs in a GNOME Terminal tab (pts/1) — it dies if that window closes. Let me check tmux state and what "cli" refers to.

[assistant] Investigation complete. All facts verified read-only over SSH; no service was started, stopped, or modified.