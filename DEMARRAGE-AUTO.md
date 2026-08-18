# 🔄 DÉMARRAGE AUTOMATIQUE — mémoire longue & préchargement unifié

> Configuration posée le **2026-08-18** sur **M4** (`pamerys-m4`, uid=1000).
> Convention de ce fichier : **tout chiffre porte sa date de mesure**. Sans date,
> un chiffre se périme en silence — l'ancien « 49 317 chunks » a survécu des mois.

---

## 1. Ce qui démarre tout seul

Deux unités **systemd `--user`**. Elles survivent à la déconnexion et au
redémarrage grâce à `Linger=yes` (vérifié : `loginctl show-user pamerys`).

| Unité | Type | État au 18/08 | Rôle |
|---|---|---|---|
| `tdai-sidecar.service` | démon | `enabled` · `active` | Recherche hybride RRF de la mémoire longue sur `127.0.0.1:3250` |
| `jarvis-precharge.timer` | minuterie | `enabled` · `active` | Déclenche le préchargement **au boot (+2 min) puis toutes les heures** |
| `jarvis-precharge.service` | oneshot | `static` · piloté par le timer | La tâche elle-même |

> `static` n'est **pas** une anomalie : ce service n'a pas de section `[Install]`
> parce qu'il n'est jamais lancé seul — c'est le timer qui l'active. Chercher à
> l'`enable` renverrait une erreur et ne servirait à rien.

---

## 2. Chaîne d'exécution du préchargement

`jarvis-precharge.timer` → `jarvis-precharge.service` → `~/jarvis/bin/jarvis-precharge-refresh.sh`

| Étape | Action | Échec = |
|---|---|---|
| **0** | Miroir : resync depuis M1 **si** corpus > `SYNC_MAX_H` **et** M1 joignable | non bloquant, **avertit** |
| **1** | Disque → index local (`precharge.db`) | bloquant |
| **2** | Index → 7 TSV au schéma `bloc` (5 colonnes) | bloquant |
| **3** | TSV → moteur de recherche `bloc` | bloquant |
| **4** | Contrôle de fraîcheur, **journalisé à chaque tick** | non bloquant |

L'étape 4 existe pour une raison précise : sans elle, une panne reste invisible
jusqu'à ce que quelqu'un la cherche. C'est ainsi que le board est resté muet
du 13 au 17/08 sans que personne ne le voie.

Journal complet : `~/jarvis/logs/precharge.log`

---

## 3. Commandes

```bash
jarvis-precharge                  # cycle complet (= ce que fait le timer)
jarvis-precharge fraicheur        # 14 domaines sondés, ~4,5 s ; sort 1 si panne
jarvis-precharge stats            # volumes + fraîcheur du corpus
jarvis-precharge search "<mots>"  # recherche 0-token (OR + bm25)
jarvis-precharge doctor           # dérive index ↔ disque
bloc <mots-clés>                  # recherche unifiée (moteur câblé au hook de prompt)
```

**Périmètre indexé au 18/08 — 1 630 ressources :**
1 007 skills · 258 CLI · 210 agents · 86 MCP · 47 commandes · 15 conteneurs · 7 plugins,
reversés dans `bloc` (**98 878 entrées**, 18/08).

---

## 4. Réglages (variables d'environnement)

| Variable | Défaut | Effet |
|---|---|---|
| `SYNC_MAX_H` | `6` | Âge au-delà duquel le miroir est resynchronisé depuis M1 |
| `M1_HOTE` | `100.112.114.32` | Hôte sondé avant tout resync |
| `JARVIS_PRECHARGE_DB` | `~/jarvis/databases/precharge.db` | Emplacement de l'index |
| `BLOC_LOCAL_DIR` | `~/.claude/bibliotheque/local` | Dépôt des TSV lus par `bloc` |
| `TDAI_SIDECAR_URL` | `http://127.0.0.1:3250` | Endpoint interrogé par le hook mémoire |
| `TDAI_TOUR_ENV` | `/home/rempc/jarvis/.env` | Source de la clé d'embedding, **sur la tour** |

---

## 5. Vérifier que tout tourne

```bash
systemctl --user status tdai-sidecar.service
systemctl --user list-timers jarvis-precharge.timer
curl -s http://127.0.0.1:3250/health          # {"status":"ok",...}
jarvis-precharge fraicheur                     # tableau des 14 domaines
tail -30 ~/jarvis/logs/precharge.log
```

Test de bout en bout du hook mémoire (ce que Claude Code envoie réellement) :

```bash
echo '{"prompt":"une question de plus de 12 caracteres"}' \
  | python3 ~/.claude/hooks/tdai-preflight-grep.py
```
Attendu : un bloc `# TDAI mémoire pré-flight (top-1 RRF=…)`.
Si `MEMOIRE INJOIGNABLE` apparaît → le sidecar est mort, voir §7.

---

## 6. Ce qui n'est **pas** automatique

- **Quorum Swarm.** 2 managers (`100.124.69.1` + `100.113.121.61`) ⇒ quorum 2/2,
  **zéro tolérance de panne**. Le second est un PC portable (`jarvis-rem-pc-asus`) :
  chaque mise en veille casse le Swarm. Correctif structurel = `docker swarm init
  --force-new-cluster` puis retrait du manager portable. **Irréversible, non exécuté.**
- **Modèles LM Studio.** Après redémarrage, LM Studio ne recharge pas forcément
  tous ses modèles (18/08 : 1 sur 5). Le repli Ollama M4 couvre la cascade 0-token.
- **Moisson SkillsMP.** Les TSV `skillsmp-*` datent du 07-08/08 (301 h au 18/08).
  Aucun moissonneur automatique identifié.

---

## 7. Pièges vérifiés — à ne pas rejouer

- **`jarvis-boot-sequencer` est une simulation** : 0 appel système, 19 `time.sleep`,
  39 `print`. Il annonce « Wave completed » sans rien démarrer. **Ne jamais l'invoquer.**
- **Le « home fantôme »** : `memory_search.py` pointait `/home/rempc/...`, le home de
  la **tour**. Sur M4, `load_key()` levait `FileNotFoundError` et le `fail fast` tuait
  le sidecar au démarrage — sans erreur visible ailleurs que dans le journal du hook.
  Tout outil porté d'une machine à l'autre doit être vérifié sur ce point.
- **Alias SSH trompeurs** : `Host m6` → `100.112.114.32`, que Tailscale nomme
  `jarvis-franck-m1` ; et `Host m1` → `10.42.0.230`, l'adresse que le CLAUDE.md
  attribue à M6. **Un diagnostic passant par ces alias peut viser le mauvais nœud.**
- **`docker` local est bloqué par un hook** (pile périmée, écritures perdues le 11/08).
  Toujours passer par `~/jarvis/bin/jarvis-docker`.
- **`bloc build` fait un `DROP TABLE`** : lancé sans miroir valide, il tronque l'index
  sans prévenir (18/08 : 110 811 → 75 690 entrées, aucun backup n'existait).
  Le miroir `~/m1-sync/bibliotheque-vivante` doit être un **vrai répertoire** — un lien
  symbolique vers `~/labo/bibliotheque` exposerait celle-ci à l'écrasement par `bloc sync`.
- **`stat -c%s` ment sur les bases** : ce sont des liens vers `~/jarvis/databases/`.
  Utiliser `stat -Lc%s`, sinon une base de 6,5 Go est mesurée à 0 Mo.

---

## 8. Désinstaller

```bash
systemctl --user disable --now jarvis-precharge.timer tdai-sidecar.service
rm ~/.config/systemd/user/{jarvis-precharge.service,jarvis-precharge.timer,tdai-sidecar.service}
systemctl --user daemon-reload
rm ~/.local/bin/jarvis-precharge
```
Les TSV `precharge-*.tsv` restent dans `~/.claude/bibliotheque/local/` ; les retirer
puis relancer `bloc build` pour revenir à l'index d'avant.
