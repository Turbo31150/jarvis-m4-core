[user] Tu es relecteur de **conformité au cahier des charges**. Réponds en français. Tu ne modifies aucun fichier — tu juges.

Ta seule question : **le code livré fait-il exactement ce qui était demandé, ni plus, ni moins ?**

Tu ne juges PAS la qualité du code (nommage, structure, élégance) — un autre relecteur s'en charge après toi. Tu juges l'écart entre la demande et la livraison.

# Le commit à relire

Dépôt : `/home/turbo/jarvis/apps/s9-dictee`, branche `dictee-ameliorations`, commit `9e505556af71bdae8871daf8d7d64a7da5d2f1c9`.

Lis-le avec `git show 9e50555` et lis le fichier complet `src/com/jarvis/dictee/BulleService.java` pour juger en contexte.

# Le cahier des charges qui était donné à l'implémenteur

## Problème
`BulleService.declenche()` appelle toujours `MoteurNatif`. Si l'utilisateur a choisi Whisper dans les réglages (`Reglages.moteurEstWhisper()`), la bulle l'ignore **silencieusement** et dicte via Google. Le réglage ment à l'utilisateur.

## Attendu
Quand `Reglages.moteurEstWhisper()` est vrai, la bulle doit enregistrer via `MoteurWhisper` :
- premier appui sur la bulle → démarre l'enregistrement ;
- second appui → clôt l'enregistrement et envoie au serveur.

Le texte obtenu doit emprunter **exactement le même chemin d'écriture** que le moteur natif : `EcritureService.ecrit(texte)`, et si aucun champ n'a le focus, repli sur le presse-papiers avec le Toast déjà en place. Ne pas dupliquer ce chemin — le factoriser.

La bulle doit rester rouge pendant tout l'enregistr

[assistant] J'ai lu le commit, le fichier complet, ainsi que `MoteurWhisper.java`, `DicteeIME.java` et `Reglages.java` pour juger en contexte.

## Vérification des exigences

| Exigence du cahier | État | Preuve |
|---|---|---|
| Aiguillage sur `Reglages.moteurEstWhisper()` | ✅ | `BulleService.java:222-224` |
| 1er appui → démarre l'enregistrement | ✅ | `:223` → `demarreWhisper()` `:241-247` |
| 2e appui → clôt et envoie | ✅ | `:205` `if (whisper.enCours()) { whisper.arreteEtEnvoie(); return; }` |
| Même chemin d'écriture `EcritureService.ecrit()` + repli presse-papiers/Toast | ✅ | `depose()` `:253-265`, appelé par les deux moteurs (`:230` et `:243`) |
| Chemin factorisé, non dupliqué | ✅ | `depose()`/`echoue()` sont les deux seules sorties, le corps du repli est identique à l'ancien |
| Rouge pendant enregistrement **et** envoi, puis or | ✅ | `peint(true)` `:221` avant les deux moteurs ; `peint(false)` uniquement dans `depose()`/`echoue()`, jamais entre `arreteEtEnvoie()` et le callback |
| `DicteeIME.java` et `MoteurWhisper.java` intacts | ✅ | `git show --stat` : 1 seul fichier modifié |
| Aucun réglage / option d'interface ajouté | ✅ | aucun `Reglages.met*` nouveau, aucune vue ajoutée |
| Chemin clavier prioritaire et inchangé | ✅ | `:207` strictement identique à l'original |
| Glisser-déposer non touché | ✅ | `fabriqueBulle()` `:150-189` inchangé au diff |

## Garde-fou légitime (à ne pas compter comme écart)

`BulleService.java:211` — `if (ecoute) return;`. **Ce n'est pas un écart.*

[user] The coordinator sent a message while you were working:
L'implémenteur a corrigé. Nouveau commit sur `dictee-ameliorations` : `29436fd292e8c9f2761dd8a7d1abc1a827ac08dd`.

Il annonce avoir retiré `whisper.arreteEtEnvoie()` et son commentaire de `onDestroy()` — 4 lignes, seul `BulleService.java` touché — et avoir conservé le verrou `if (ecoute) return;` ainsi que la position du test `whisper.enCours()`.

Vérifie-le toi-même plutôt que de le croire : `git show 29436fd`, puis relis l'état final du fichier. L'écart que tu avais relevé est-il bien levé, sans qu'un nouveau soit apparu et sans qu'une exigence déjà satisfaite ait été cassée au passage ?

Termine par une seule ligne : `CONFORME` ou `NON CONFORME`.

Address this before completing your current task.

[assistant] I'll verify the correction myself rather than take the announcement at face value.

[assistant] The diff is exactly the 4 lines announced. Now I verify the final state of the file itself, rather than trusting the diff alone.

[assistant] Vérification faite sur pièces, pas sur parole.

## Ce que le nouveau commit fait réellement

`git show --stat 29436fd` : **1 fichier, 0 insertion, 4 suppressions**. Le diff ne contient qu'un seul hunk, dans `onDestroy()` : les 3 lignes de commentaire et la ligne `if (whisper != null && whisper.enCours()) whisper.arreteEtEnvoie();`. Rien d'autre — aucune insertion, donc aucune possibilité qu'un nouveau code se soit glissé au passage.

État final vérifié dans le fichier lui-même (pas seulement dans le diff) :

- `BulleService.java:121-129` — `onDestroy()` est revenu à l'identique de son état d'avant `9e50555` : `DicteeIME.observe(null)`, retrait de la vue, `bulle = null`, `super.onDestroy()`. L'écart **EN TROP** est bien levé : « Masquer la bulle » n'est plus émetteur.
- `grep` sur tout le fichier : `arreteEtEnvoie` n'apparaît plus qu'à **une seule** ligne, `:201`, c'est-à-dire le second appui dans `declenche()`. Aucune clôture résiduelle ailleurs.
- Cumul `8ff1aba..29436fd` : `1 file changed`. `DicteeIME.java` et `MoteurWhisper.java` restent intacts sur l'ensemble de la branche, pas seulement sur le dernier commit.
- Arbre de travail propre (seul `PLAN.md` non suivi, hors périmètre) : le fichier sur disque est identique au commit relu.

## Non-régression des exigences déjà satisfaites

| Exigence | Ligne finale | État |
|---|---|---|
| Aiguillage sur le réglage | `:218-220` | intact |
| 1er appui démarre | `:219` → `demarreWhisper()` `:237-243` | intact |
| 2e appui clôt et en