---
name: stop-cycles-m4
description: >
  Coupe ET désactive les boucles d'inférence autonomes qui saturent le M4
  (RAM + thermique) — elles rechargent les modèles Ollama en boucle et font
  monter le CPU à 95-100°C. Se déclenche quand l'utilisatrice dit « enlève ce
  cycle », « enlève ces cycles », « stoppe les boucles », « coupe les cycles »,
  « board_continuous_loop », « swarm-auto-connect », « le M4 chauffe en boucle »,
  « ça recharge le modèle sans arrêt », « désengorge le M4 », « RAM saturée
  boucle », « boucle d'inférence autonome », « cowork-loop », « domino-loop »,
  « désactive les cycles pour de bon ».
version: "1.0"
---

# stop-cycles-m4 — couper et désactiver les boucles autonomes

Sur le M4 seul (15 Gio RAM, garde thermique 82/90°C), les boucles d'inférence
autonomes sont **interdites** : elles rechargent `gemma3:4b`/`qwen2.5:7b` en
continu → RAM saturée + CPU 95-100°C (cf. mémoires `m4-dispatch-flux-ondemand`
et `m4-surchauffe-overclocking`). Cette skill les coupe **et** neutralise leurs
lanceurs pour qu'elles ne reviennent pas.

## Piège à connaître
Quand le CPU est déjà ≥90°C, la **garde thermique bloque tout Bash de l'agent**.
On ne peut donc pas tuer les boucles via un bash normal — c'est un cercle
vicieux (les boucles chauffent, la chaleur empêche de les tuer). **Solution :
lancer le driver via le préfixe `!`** (shell direct de la session, non filtré
par le hook), ou `sudo`/tty si besoin.

## Usage

```bash
# Diagnostic seul (ne tue rien) :
bash ~/.claude/skills/stop-cycles-m4/driver.sh --dry

# Couper + désactiver (temp < 90°C, bash agent OK) :
bash ~/.claude/skills/stop-cycles-m4/driver.sh
```

Si le CPU est ≥90°C (bash agent bloqué), **coller dans la barre de prompt** :

```
! bash ~/.claude/skills/stop-cycles-m4/driver.sh
```

## Ce que fait le driver (0-token, fail-safe, idempotent)
1. **Coupe** les process de boucle par motif (`board_continuous_loop`,
   `swarm-auto-connect`, `cowork-loop`, `domino-loop`, `*continuous_loop*`…),
   en **protégeant** toujours les apps légitimes (webapp, chat_proxy, mcp,
   Chrome, Claude, Xorg, whisper…).
2. **Désactive** les unités `systemd --user` dont l'ExecStart référence un motif
   (`stop` + `disable`).
3. **Neutralise** les `.desktop` d'autostart concernés (renommés `.disabled`).
4. **Commente** les lignes crontab de boucle (backup `~/.crontab.stop-cycles.bak`).
5. **Décharge** les modèles Ollama que les boucles rechargeaient.
6. Affiche la RAM avant/après. Sortie toujours `exit 0`.

## Garde-fous
- Ne touche jamais aux process protégés (regex `PROTECT` dans le driver).
- Aucun `rm` destructif : l'autostart est **renommé**, le crontab **sauvegardé**.
- Réversible : réactiver une unité = `systemctl --user enable --now <unité>` ;
  restaurer un autostart = retirer le suffixe `.disabled` ; crontab = décommenter.
- À relancer après un `git pull`/réinstall qui remettrait une boucle.
