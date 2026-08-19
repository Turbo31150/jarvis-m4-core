[assistant] Ta demande est trop ambiguë pour agir sans risque de partir dans la mauvaise direction — je préfère cadrer en une question.

[assistant] Le mode ultra ne peut pas être activé depuis mon côté — c'est un réglage de session que tu déclenches toi-même. Voici les trois leviers :

**1. Ponctuel (une seule demande)**
Mets le mot-clé `ultracode` dans ton prompt :
```
ultracode optimise le moteur de perf contenu
```
→ j'orchestre alors la tâche en workflow multi-agents (fan-out, vérification adversariale, synthèse) au lieu de la traiter seul.

**2. Permanent sur la session**
`/config` → active **Ultracode**. Tant que c'est on, chaque tâche substantielle passe par un workflow par défaut, sans avoir à répéter le mot-clé.

**3. Taille des workflows**
`/config` → **Dynamic workflow size**. Actuellement sur *medium* (< 15 agents par workflow). Passe-le plus haut si tu veux des fan-out plus larges sur `feat/content-perf-engine`.

À noter aussi, distinct d'ultracode : `/code-review ultra` lance une revue multi-agents dans le cloud sur la branche courante — à taper toi-même, je ne peux pas la déclencher.

Dis-moi ce que tu veux attaquer sur `feat/content-perf-engine` avec `ultracode` en préfixe et je lance l'orchestration.

[assistant] Un seul écran actif : **HDMI-0, 1920x1080 @ 50 Hz** (708×398 mm ≈ 32", modes 29.97/25/23.98 Hz → c'est un **téléviseur**, pas un moniteur PC). Je regarde l'historique des reconnexions.

[assistant] **137 reconnexions de la TV en 1611 s de session X** — soit une toutes les ~12 secondes. C'est ça, ton problème. Je mesure en direct pour confirmer que c'est en cours.

[assistant] Confirmé, c'est **actif en ce moment**. Et le motif est très parlant :

```
1440.334 / 1440.384   ← paire à 50 ms
1497.544 / 1497.604   +57 s
1557.660 / 1557.718   +60 s
1617.811 / 1617.863   +60 s
1678.044 / 1678.097   +60 s
```

Des paires régulières **toutes les 60 secondes, réglées comme une horloge**. Un câble défectueux donne des événements erratiques — ça, c'est **quelque chose qui sonde le lien HDMI toutes les minutes**. Je cherche le coupable.

[assistant] **Trouvé.** Premier timer de la liste :

```
jarvis-resolution-guard.timer → toutes les 60 s (LAST 00:36:52, NEXT 00:37:52)
```

Période **identique** à celle des paires de reconnexion HDMI (57–61 s). Le « garde de résolution » est la cause des changements de résolution. Je lis ce qu'il fait.

[assistant] Mécanisme complet identifié. Le script sort en **ligne 11** (`exit 0`, la résolution est déjà bonne) — il ne corrige jamais rien. Mais **ligne 10** il appelle `xrandr` nu, et `xrandr` sans argument déclenche `RRGetScreenResources`, qui **force le serveur X à re-sonder tous les connecteurs et relire l'EDID**. D'où la paire d'événements HDMI toutes les 60 s.

Le garde crée exactement la perturbation qu'il est censé corriger. Je vérifie ça expérimentalement.