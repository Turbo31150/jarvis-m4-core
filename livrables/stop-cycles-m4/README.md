# stop-cycles-m4

Skill + driver qui **coupe et désactive** les boucles d'inférence autonomes qui
saturent une machine (RAM + thermique) — celles qui rechargent des modèles
Ollama en boucle et font monter le CPU. 0-token, fail-safe, idempotent.

## Contenu
```
driver.sh    # coupe les process, désactive systemd --user, neutralise autostart, crontab
SKILL.md     # définition de la skill (déclencheurs)
README.md / FICHE-VENTE.md / LICENSE.txt
```

## Installation
```bash
chmod +x driver.sh
```
Comme skill Claude Code : copiez le dossier dans `~/.claude/skills/stop-cycles-m4/`.

## Usage
```bash
bash driver.sh          # coupe + désactive, montre la RAM avant/après
bash driver.sh --dry    # montre ce qui tournerait, ne tue rien
```
Le driver agit sur des motifs de boucles connus (`cowork-loop`, `domino-loop`,
`swarm-auto-connect`, `*continuous_loop`, `*autonomous_loop`…) et **protège** les
apps légitimes (navigateur, Claude, services système, webapp, audio, whisper).
Il stoppe/désactive aussi les unités systemd --user, neutralise les autostart
XDG concernés, commente les lignes crontab (backup) et décharge les modèles
Ollama résidents.

## Sécurité
N'agit que sur des motifs de boucles autonomes ; liste de protection explicite
pour ne jamais toucher aux applications de l'utilisateur. Mode `--dry` pour
inspecter avant d'agir.
