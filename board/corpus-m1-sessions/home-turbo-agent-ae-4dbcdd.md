[user] M2 (192.168.1.26, SSH clé jarvis_cluster) et M5 (192.168.1.113, SSH clé m5_jarvis_ed25519) sont DOWN (ping + SSH timeout confirmés à l'instant). Mission : réveiller TOUTES les machines down.
1. Retrouve les MACs (configs WoL existantes : scripts anydesk-mesh, jarvis-launchers, ~/jarvis scripts, /etc/ethers, leases, arp cache).
2. Envoie les paquets magiques WoL (wakeonlan/etherwake) sur M2 et M5, plusieurs salves.
3. Poll ping puis SSH (jusqu'à ~3 min par nœud).
4. Si un nœud remonte : vérifie ses services LLM (M2 : ollama :11434 ; M5 : ollama) et signale l'état.
5. Si échec WoL : diagnostique (MAC introuvable ? WoL désactivé ?) et dis-le clairement, sans inventer.
Retour : tableau nœud | WoL envoyé | ping | SSH | LLM | verdict.

[assistant] Dernières tentatives : port 7 + vérification Tailscale (au cas où M2/M5 seraient joignables par le tailnet).

[assistant] Résultat final — les deux nœuds ne remontent pas malgré WoL correct.

| Nœud | MAC (source) | WoL envoyé | Ping | SSH | LLM | Verdict |
|---|---|---|---|---|---|---|
| M2 | `00:68:eb:c1:96:3f` (mesh-registry + jarvis_launchers + leases DHCP, concordantes) | Oui — ~10 salves : 192.168.1.255, 255.255.255.255, puis **192.168.0.255** (bon broadcast), ports 9 et 7 | DOWN (~7 min de poll) | DOWN | Non testable (ollama :11434 injoignable) | **Échec WoL — pas de réveil** |
| M5 | `00:68:eb:a5:35:76` (mêmes 3 sources) | Oui — mêmes salves | DOWN | DOWN | Non testable | **Échec WoL — pas de réveil** |

Diagnostic honnête (pas d'invention) :

1. **Découverte importante : le LAN a changé de sous-réseau.** M1 (`enp42s0`, MAC `d8:43:ae:96:e0:40`) est maintenant en **192.168.0.10/24** (GW 192.168.0.1), plus en 192.168.1.85. Les IPs 192.168.1.26/1.113 des runbooks sont obsolètes ; les premières salves vers 192.168.1.255 partaient vers la passerelle et n'atteignaient pas le LAN. J'ai corrigé en broadcastant sur 192.168.0.255 (le seul broadcast qui atteint physiquement le segment) — sans effet.
2. **MACs fiables** : confirmées par 3 sources indépendantes (`/home/turbo/jarvis/.claude/skills/run-anydesk-mesh/mesh-registry.txt`, `/home/turbo/jarvis/.claude/skills/run-jarvis-launchers/jarvis_launchers.sh`, leases DHCP NetworkManager). Le problème n'est pas la MAC.
3. **Scan complet 192.168.0.0/24** : hôtes actifs = .1, .5 (box), .11, .15, .16 — aucun ne porte une MAC `00:68:eb:*`. M2/M5 ne sont su