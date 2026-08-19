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


MISSION — Libérer M6 et récupérer ses 2 GPU.

Contexte prouvé : M6 (ssh turbo@10.42.0.230) est à load 11-13 en permanence. Ses GPU
(RTX 3080 : 18 Mio utilisés sur 10240 ; RTX 2060 : 2451 sur 12288) sont à 0 % d'utilisation.
Le meilleur maté

[assistant] Load 12.8 on **4 CPU cores** — that's the real crush. Let me get per-service CPU accounting.

[assistant] CPUUsageNSec is unreliable (CPUAccounting off). Let me measure real CPU deltas via cgroup `cpu.stat`.

[assistant] Root cause identified: **I/O pressure at 94%**, CPU pressure only 6%. Let me confirm the disk and check the loops' actual output.

[assistant] SSD but saturated: 6.3 GB DB + 251 MB WAL being copied to the **same disk**. Now the GPU/Ollama side.

[assistant] Major finding: M6 has essentially **no local model** (only qwen2.5:1.5b). Let me map all JARVIS units and the Chrome processes.

[assistant] **61 timers** — that's the real structural problem, not 16 services. Let me quantify the crash loops.

[assistant] 1598 + 1188 + 518 + 371 + 371 + 187 = **~4200 respawns in 95 min**. Let me find why they crash.

[assistant] Confirmed: broken loops. Let me check the failure-handler amplification and the "useful" loops.

[assistant] Ollama **does** offload to the RTX 3080 (29/29 layers). Final checks: LM Studio and Chrome.

[assistant] SSH now times out at the banner — M6 is collapsing under its own load. Let me retry once.