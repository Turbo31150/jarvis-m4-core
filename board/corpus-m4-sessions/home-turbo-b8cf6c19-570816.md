[user] '/home/turbo/Bureau/jarvis-claude-local.desktop' '/home/turbo/Bureau/jarvis-shell-rem.desktop' '/home/turbo/Bureau/jarvis-shell-rem-linux.desktop' '/home/turbo/Bureau/jarvis-anydesk-REM.desktop' lenvoyis sur m4

[assistant] **Fait — les 4 lanceurs sont sur M4, et le réseau local Bluetooth M6↔M4 est monté.**

**1. Transfert des .desktop → `/home/pamerys/Bureau/`**

| Fichier | État |
|---|---|
| `jarvis-claude-local.desktop` | ✅ copié |
| `jarvis-shell-rem.desktop` | ✅ copié |
| `jarvis-shell-rem-linux.desktop` | ✅ copié |
| `jarvis-anydesk-REM.desktop` | ✅ copié |

Adaptations faites pour qu'ils fonctionnent réellement sur M4 :
- dépendance manquante copiée : `~/.local/share/jarvis-launchers/anydesk-REM.sh` (appelée par 2 des lanceurs),
- chemins réécrits `/home/turbo/` → `/home/pamerys/` (le piège d'injection connu),
- `chmod +x` + `gio metadata::trusted` pour qu'ils soient cliquables sans avertissement GNOME.

Les alias SSH `rem`, `rem-linux`, `rem-desktop` et la clé `rem_jarvis_ed25519` étaient déjà présents sur M4 → les terminaux Rémi marchent tels quels. Seule réserve : `jarvis-claude-local.desktop` pointe sur le Smart Router `127.0.0.1:9765`, qui est un service **local à M6** — sur M4 il faudra soit y lancer un routeur, soit pointer sur celui de M6.

**2. Réseau local Bluetooth**

Le câble direct (`enp3s0`) est débranché et le relay Tailscale « par » timeoutait (`Connection timed out during banner exchange`). J'ai monté un PAN Bluetooth :

- M4 = serveur NAP, bridge `pan0` → **172.20.0.1**
- M6 = client, `bnep0` → **172.20.0.2**
- ping 3/3, ~78 ms — SSH validé : `ssh m4-bt` (alias ajouté dans `~/.ssh/config`)

Ta route par défaut est intacte : elle passe toujours par le partage de connexio

[user] Base directory for this skill: /home/turbo/.claude/skills/remplir-bibliotheque

# Bibliothèque Vivante Infinie — remplissage 0-token

Porté du pattern « banque annuelle » de M4 : remplissage par lots, idempotent,
anti-surchauffe GPU, cache SQL, todoliste dynamique qui se régénère toute seule.

Moteur : **LM Studio M1 `:1234`** (qwen3.5-9b) prioritaire → fallback `jarvis_dispatcher.ask()` (Ollama).
Cœur : `~/jarvis/cli/biblio_filler.py`.

## 1. Voir l'avancement
```bash
python3 ~/jarvis/cli/biblio_filler.py --status
```

## 2. Remplir un lot maintenant (à la demande)
```bash
bash ~/.claude/skills/remplir-bibliotheque/scripts/remplir.sh 6      # 6 items
```

## 3. Remplissage perpétuel (daemon)
```bash
systemctl --user status  biblio-filler.service     # état
systemctl --user start   biblio-filler.service     # lancer l'infini
systemctl --user stop    biblio-filler.service     # arrêter
journalctl --user -u biblio-filler.service -f      # suivre en direct
```
Le daemon boucle : lot de 3 toutes les 90 s, pause si GPU ≥ 84 °C, auto-alimente la
todoliste quand elle se vide.

## 4. Où va le contenu
| Type | Destination |
|---|---|
| Commandes | Postgres `cmdlib` (container `jv-infra-biblio-db`) + `Documents/Commande_Directe_Bibliotheque/command_list.md` (section « 🌱 Bibliothèque vivante ») |
| Fiches connaissance | SQLite `jarvis_master.db` table `biblio_knowledge` + `~/jarvis/data/biblio_knowledge/*.md` |
| Todoliste | `jarvis_master.db` table `biblio_topics` |
| Cache 0-token | `