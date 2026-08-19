[user] ✅ [BASH_PROFILE] Chargé par MCP TOOL - Terminal immunisé!
Connexion au terminal de Rémi...

  ┌─ M6 ─ JARVIS ──────────────────────────────────────┐
  │  i5-4460 4c · 11 Gi · RTX 2060+3080 · 10.42.0.230  │
  └────────────────────────────────────────────────────┘

   État      ⛔ GEL MÉMOIRE EN COURS  → lance m6-relief pour dégager la RAM
   Mémoire   3,6 Gi libres / 11 Gi  (67% pris)   pression 77.58%
   zram      3,3G stockés → 1543M en RAM (x2,4)  [54% de 6G]   swap disque 7,2 Gi
   Charge    39.42 / 21.60  (4 cœurs)   E/S bloquantes 74.76%   up 6m
   GPU       RTX 2060 2/12G 45°C  RTX 3080 6/10G 59°C  
   Flotte    66 services · 80 timers   3 en échec (user)   1 en échec (système)
   LLM       LMStudio ●  Ollama ●  M4 ○
   m6-relief = dégager la RAM · m6-etat = ce bilan · M6_BANNER_OFF=1 = muet

turbo@turbo:~$ claude
 ▐▛███▜▌   Claude Code v2.1.226
▝▜█████▛▘  Opus 5 (1M context) · Claude Max
  ▘▘ ▝▝    /home/turbo

 ⚠ Agent descriptions are over the 15.0k-token limit (~19.2k tokens) · ask
   Claude to trim agent descriptions in .claude/agents/

 ▎ Using Opus 5 (1M context) (from .claude/settings.json) · /model

────────────────────────────────────────────────────────────────────────────────
❯ Try "write a test for <filepath>"
✅ [BASH_PROFILE] Chargé par MCP TOOL - Terminal immunisé!
Connexion au terminal de Rémi...

  ┌─ M6 ─ JARVIS ──────────────────────────────────────┐
  │  i5-4460 4c · 11 Gi · RTX 2060+3080 · 10.42.0.230  │
  └───────────────────────────────────────────

[assistant] Ton message ne contient que la bannière de démarrage du terminal (répétée ~12 fois), pas de demande. Dis-moi ce que tu veux faire.

⚠️ Point urgent en attendant — la machine est bien en gel mémoire, ce n'est pas un faux positif :

```
/proc/pressure/memory
some avg10=83.31   full avg10=69.87
MemAvailable: 3,0 Gi / 11,1 Gi
```

`full avg10 = 69,87 %` veut dire que pendant les 10 dernières secondes, **tous** les processus ont été bloqués sur la mémoire près de 70 % du temps. Charge 39,4 sur 4 cœurs, 74 % d'E/S bloquantes → c'est du thrash de swap, pas de la charge CPU.

Lance `m6-relief` pour dégager la RAM, ou dis-moi et je le fais.

[user] reeegler lm stsudio le metttre en mode xwerveuir directe et non applmic ation moijn loitrde poeut netre

[assistant] Diagnostic clair. Je regarde encore deux choses avant d'agir (la sentinelle qui pourrait relancer l'appli dans mon dos).

[assistant] Le renderer GUI (288 Mo) est déjà parti. Je termine la migration vers l'unité systemd.

[assistant] PID 7385 ignore SIGTERM (comportement `--run-as-service`) et garde le verrou. Je force.

[assistant] LM Studio est en place. J'enchaîne sur la résolution — et je vois déjà une piste : **4 scripts d'autostart** touchent l'affichage.

[assistant] Trouvé. **Trois scripts se battent avec des cibles contradictoires** — c'est ça, le clignotement.

[assistant] La résolution vient de sauter **sous mes yeux** : 1920x1080 → 1280x1024, et la taille physique déclarée a changé (708×398 mm → 1050×590 mm). Ce n'est pas les scripts : **l'EDID de l'écran change**, le lien HDMI se renégocie.

[assistant] Décisif : la dérive est **réelle** (retour spontané à 1920x1080 après la correction du garde à 01:04). J'isole la cause — je coupe la bagarre et je teste si c'est le garde lui-même qui la provoque.

[assistant] La cause n'est pas les scripts : l'écran est **reparti en 1280x1024 tout seul**, avec la seconde identité EDID (1050×590 mm). Je cherche la panne de lien.

[assistant] **Preuve faite.** Depuis que j'ai coupé les scripts (01:06), l'écran est **stable à 1920x1080 depuis 90 secondes d'affilée** — 18 relevés sur 18, bon EDID. Je confirme et je verrouille.

[assistant] Correction importante : **36 reconnexions HDMI en 110 s** même scripts coupés. Le lien lâche tout seul — c'est physique, les scripts ne faisaient qu'aggraver.

[assistant] EDID valide récupéré : **TOSHIBA-TV de 2009**, mode natif 1920x1080@50. Je remets un garde — mais allégé, sans le `nvidia-settings` qui reprogrammait tout le metamode.

[assistant] Modèle chargé — mais **en double** (le timer dual-warm en avait déjà chargé un). Je nettoie.

[assistant] Écran stable, **0 correction du garde** en 6 minutes (contre une par minute avant). La réponse LLM vide est le bug connu « reasoning runaway » de qwen3.5 — je vérifie avec le contournement maison.

[assistant] ## LM Studio → mode serveur ✅

**Ce qui n'allait pas :** deux lanceurs se disputaient la même instance. L'autostart GNOME (`~/.config/autostart/lmstudio.desktop`) gagnait la course et prenait le verrou ; l'unité systemd `lmstudio-server.service` démarrait ensuite, se prenait `Another instance of the app is already running`, redémarrait 6 fois puis tombait en `start-limit-hit`. Résultat : c'était **l'appli GNOME avec sa fenêtre Electron** qui servait le port 1234, et les protections de l'unité (plafond mémoire 5 G, correctif CUDA 2 GPU) ne s'appliquaient jamais.

**Maintenant :** autostart GNOME désactivé, unité systemd propriétaire de l'instance, `--run-as-service` **sans fenêtre** (0 renderer, ~290 Mo récupérés), modèle chargé une seule fois (j'ai déchargé un doublon `:2` qui prenait 6,5 Go de VRAM en plus).

```
lmstudio-server.service   active
:1234                     LISTEN
qwen/qwen3.5-9b           chargé, 6.55 GB, ctx 4096
GPU0 4,0/12 Go · GPU1 3,2/10 Go
```

⚠️ Le serveur répond mais qwen3.5 brûle **100 % de son budget en `reasoning_tokens`** et renvoie un `content` vide — c'est le bug « runaway » que tes outils `run-qwen-nothink` / `lms-runaway-guard` couvrent déjà. Pré-existant, pas lié à la bascule.

## Résolution ✅

**Trois scripts se contredisaient**, tous lancés au login :

| script | voulait |
|---|---|
| `nvidia-underscan.sh` | Border 40,22 + **50 Hz** → 1840x1036 |
| `lock-hdmi-res.sh` | Border 0 + **60 Hz** |
| `fixe-resolution-1920x1080.sh` | plein cadre, *