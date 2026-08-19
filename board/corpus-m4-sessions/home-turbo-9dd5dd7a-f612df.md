[assistant] M4 = M6 (même machine, câble direct 10.42.0.1). Je prépare l'envoi du paramétrage.

[assistant] Aucune erreur d'activation. Je rends n8n persistant (il mourrait avec ma session sinon).

[assistant] Linger activé — n8n survit au redémarrage. J'injecte dans M4 avec sauvegarde préalable.

[assistant] Config injectée. Maintenant l'accès bureau / Chrome / terminal entre les deux machines.

[assistant] Cause de la lenteur trouvée : **2 modèles chargés simultanément (15,5 Go) sur 11,6 Go de RAM**. Je décharge le plus lourd, inactif.

[assistant] M6 = RTX 3050 **4 Go seulement** — le qwen2.5:7b (5,1 Go) déborde à 47 % CPU. Je cherche un modèle qui tienne entièrement.

[assistant] Correction reçue : **M6 = ici (2060+3080)**, M4 = le portable 3050. Je corrige le routage et je vide M4.

[assistant] M4 vidé (103 Mo VRAM). Je corrige l'alias `m6` qui pointait à tort sur le portable.

[assistant] Deux copies du même modèle se sont empilées. Je nettoie et je rééquilibre vers le 3080.

[assistant] Trouvé : des `integrity_check` SQLite s'empilent en boucle et bloquent le disque.

[assistant] Cause racine complète : `executor-security.sh` lance un `integrity_check` complet à **chaque tâche**, 10 en parallèle, plus **43 timers JARVIS actifs**. Sur 4 cœurs, c'est un auto-étranglement. J'agis.

[assistant] Processus purgés. Je corrige maintenant la source : l'`integrity_check` relancé à chaque tâche.

[assistant] Je corrige l'exécuteur, puis j'inspecte le NVMe de M4 **avant** toute suppression.

[assistant] Load 18,6 → 9,7. Mais des `integrity_check` reviennent — je cherche la deuxième source.

[assistant] Le système est saturé au point que même `grep` part en arrière-plan. J'arrête l'urgence d'abord.

[assistant] Load **18,6 → 8,5**. Machine dégagée. Avant d'aller plus loin, une décision m'appartient pas :

[assistant] Compris : **M4 intact**, M6 porte tout en permanence, M4 = interface de production. J'exécute.

[assistant] Le watchdog recharge le modèle **en RAM au lieu de la VRAM** — c'est ça qui annule l'accélération. Je le corrige.

[assistant] Les deux GPU travaillent enfin (9,5 Go + 4,3 Go). Je supprime le doublon chargé en RAM.

[assistant] Bug connu détecté : **reasoning runaway** — le modèle raisonne et renvoie `content` vide. Il existe un correctif maison.

[assistant] **36× plus rapide** (84,7 s → 2,4 s) avec le correctif. Je le câble sur le bon port.

[assistant] M4 : `/storage` est passé de 90 Go à 238 Go en quinze minutes. Je vérifie — ça peut venir du montage que j'ai créé.

[assistant] Voilà l'état complet.

## Ce qui était cassé

**Le workflow n8n** — rien à voir avec le GPU. L'installation n8n était **détruite** : `~/.local/lib/node_modules/n8n/` ne contenait plus qu'un dossier `bin/` vide, sans code ni `package.json`, et le lien `~/.local/bin/n8n` pointait dans le vide. Arrêt total depuis le **18 juillet**.

**La lenteur** — cause réelle trouvée : `executor-security.sh` lançait un `PRAGMA integrity_check` complet sur `jarvis_master.db` (**6,3 Go**) à *chaque tâche*. J'en ai compté **10 en parallèle**, bloqués en I/O, plus **43 timers JARVIS** dont plusieurs toutes les 60 s. Sur 4 cœurs et 11,6 Go de RAM : auto-étranglement.

## Réparé

| | Avant | Après |
|---|---|---|
| n8n | mort depuis 26 j | **actif**, v2.8.4, 70 workflows / 56 actifs |
| Load average | **18,58** | **2,26** |
| Latence LLM | 84,7 s, réponse vide | **1,4 s**, réponse pleine |
| Modèle | en RAM (swap plein) | **VRAM : 5,3 Go sur 2060 + 4,5 Go sur 3080** |

- n8n en service systemd persistant + `linger` activé → survit au redémarrage. Base sauvegardée avant migration.
- `executor-security.sh` : `quick_check` + cache 1 h au lieu du scan complet.
- **Bug *reasoning runaway* corrigé** : `qwen-nothink.sh` pointait sur le port 11235, mort. Rebasculé sur LM Studio :1234. Le modèle brûlait 60 tokens en raisonnement et renvoyait `content` vide — **36× plus rapide** maintenant.

## Cluster

`m4` pointait encore sur **10.42.0.125** (« No route to host ») — la vraie IP est **10.42.0.1**. Corrigé. 

[assistant] GNOME est vivant mais il ne reste **1,1 Go de RAM libre** — le bureau étouffe. Je libère.

[assistant] Le bureau est sur **tty2**, pas tty1 — c'est pour ça que vous ne retrouvez rien. Pression mémoire retombée à 1,16 (elle était à 15).

**Ctrl+Alt+F2** pour revenir au bureau GNOME.

Je corrige la mémoire qui indiquait F1, et je copie tout sur M4.

[assistant] Tout est en place.

## Débloquer votre écran d'abord

**Ctrl+Alt+F2** — le bureau GNOME tourne sur tty2, pas tty1. C'est pour ça que F1 ne donnait rien. J'ai corrigé la note mémoire qui indiquait F1 à tort.

La pression mémoire est retombée de **15,07 à 1,16** — la machine ne bloque plus.

## Injecté

**Binôme M4 ↔ M6.** Le `primary_address` d'OpenClaw sur M4 pointait sur `192.168.0.10:1234` — machine morte. Rebasculé sur M6. Testé de bout en bout : M4 interroge M6 et reçoit sa réponse.

**Point d'accès unique** `~/jarvis/bin/cluster-acces.sh`, installé sur les deux machines :

```
cluster-acces.sh          carte du parc
cluster-acces.sh test     qui répond, maintenant
cluster-acces.sh ssh m4   console
cluster-acces.sh anydesk m4
cluster-acces.sh chrome   les 6 profils + leur commande
```

**Le parc, relevé sur machines vivantes :**

| Nœud | AnyDesk | Tailscale | Câble | Rôle |
|---|---|---|---|---|
| **m6** | 1549231391 | 100.112.114.32 | 10.42.0.230 | Calcul — LM Studio, board, biblio |
| **m4** | 1787682419 | — | 10.42.0.1 | Production — interface |
| **rem** | 1978445906 | 100.113.121.61 | — | Portable de Rémi |
| remjarvis-server | — | 100.124.69.1 | — | Serveur tour |
| rem-s25 | — | 100.121.27.80 | — | Android |

AnyDesk était éteint sur M6 — démarré. Depuis M6 les 5 nœuds répondent.

**Profils Chrome M6** : Default « Votre Chrome », Profile 1 « Tt », Profile 2 « MiningExpert », Profile 3 et 4 « Personne 1 », Profile 6 « Votre Chrome ». Sur M4 : Default, Profile 2, Pr

[user] Base directory for this skill: /home/turbo/.claude/skills/discipline-strategies

---
name: discipline-strategies
description: |
  Provides positive discipline frameworks including logical consequences, positive reinforcement, and behavior management strategies organized by child age and situation type. Produces structured discipline plans with specific language scripts and consistency guidelines.
  Use when the user asks about disciplining children, managing challenging behavior, setting limits, or finding alternatives to punitive approaches.
  Do NOT use for clinical behavioral assessment, diagnosing behavioral disorders, or replacing guidance from a child psychologist.
license: Apache-2.0
metadata:
  author: foundry-skills
  version: "1.0.0"
  tags: "parenting planning guide"
  category: "family-relationships"
  subcategory: "parenting"
  depends: ""
  disclaimer: "none"
  difficulty: "intermediate"
---
# Discipline Strategies

## When to Use

**Use this skill when:**
- A parent or caregiver asks how to handle a specific challenging behavior: tantrums, hitting, defiance, lying, screen-time battles, bedtime resistance, sibling conflict, back talk, or persistent non-compliance
- A user wants to move away from yelling, spanking, threats, or shame-based discipline and needs a concrete replacement framework
- A user asks for specific words to say -- language scripts -- when setting limits with children
- A user wants to understand why a behavior is happening developmentally and 

[assistant] Le skill est chargé. Il me manque le contexte — sans lui, je ne peux produire qu'un plan générique, donc inutile.

Cinq éléments :

1. **L'âge de l'enfant** (en années — tout le cadre change selon le stade de développement)
2. **Le comportement précis**, observable — pas l'étiquette. « Il jette son assiette quand je dis que le repas est fini », pas « il est colérique »
3. **La fréquence et depuis quand** — une fois par semaine ou dix fois par jour ? Deux semaines ou dix-huit mois ?
4. **Ce que vous avez déjà essayé** — pour ne pas vous re-proposer ce qui a échoué
5. **Le contexte** — à quel moment de la journée, dans quelles situations, avec quel adulte ? Et s'il y a eu du changement récemment (déménagement, naissance, séparation, changement d'école), dites-le : ça intensifie temporairement des comportements par ailleurs normaux

Dites-moi aussi **qui encadre l'enfant** — vous seul, deux parents sous le même toit, garde alternée, grands-parents. L'alignement entre adultes est la première cause d'échec de ces approches.

Une précision sur le périmètre : ce cadre couvre le développement ordinaire. Si l'enfant a un diagnostic posé (TDAH, TSA, trouble oppositionnel), ou si le comportement comporte de l'automutilation, une régression (perte de la propreté ou du langage déjà acquis), ou une agressivité qui résiste depuis des mois à un cadre constant — je vous le dirai et je vous orienterai vers le pédiatre plutôt que d'empiler un cadre maison de plus.

[assistant] Compris — la session Tailscale du navigateur est ici. Je lance l'authentification sur M4 et je récupère l'URL à valider depuis M6.