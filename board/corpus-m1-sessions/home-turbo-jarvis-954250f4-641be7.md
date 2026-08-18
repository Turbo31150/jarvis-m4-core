[user] Base directory for this skill: /home/turbo/jarvis/.claude/skills/run-m6-tampon

# run-m6-tampon

`scripts/m6_tampon.py` encaisse des demandes en texte libre et fait le travail de shell
**ailleurs que sur M1**. M1 porte l'écran, les 4 GPU et l'orchestration ; scorer 7 Mo de TSV et
lancer `df`/`ps`/`uptime` est du CPU pur qui n'a pas à s'exécuter là. **M6 mâche, M1 décide.**

Tout se pilote par **un seul harnais** : `.claude/skills/run-m6-tampon/driver.sh`.
Il existe parce que trois propriétés du tampon sont invisibles dans sa sortie normale et
peuvent casser à chaque édition — le mâchage part-il vraiment sur M6, une ligne d'index forgée
est-elle toujours rejetée, et le tampon respecte-t-il encore la loi A1.

**Tous les chemins ci-dessous sont relatifs à `/home/turbo/jarvis/`.**

## Prérequis

Rien à installer. Vérifié tel quel dans ce conteneur :

```bash
python3 --version          # 3.12.3 — stdlib seule, aucun pip
sqlite3 --version          # présent
ssh -o BatchMode=yes m6 'echo ok'   # -> ok   (ICMP filtré : ne JAMAIS pinger M6)
```

Le driver doit être exécutable :

```bash
chmod +x .claude/skills/run-m6-tampon/driver.sh
```

## Run (chemin agent) — commencer TOUJOURS par le smoke

8 contrôles, **zéro appel LLM**, ~15 s. Sort en 1 si un contrôle échoue.

```bash
bash .claude/skills/run-m6-tampon/driver.sh smoke
```

Sortie obtenue le 2026-07-30 à 00:56 (verbatim, fin de la sortie) — **le contrôle 6 est
rouge, et c'est correct** : il vient de détecter une corruption réelle

[assistant] 8/8 vert, M6 joignable. Je vérifie ce qui existe déjà en automatisation avant de câbler.

[assistant] Drain automatique armé (5 min). Test bout-en-bout : je dépose une demande et je laisse la chaîne la mâcher.