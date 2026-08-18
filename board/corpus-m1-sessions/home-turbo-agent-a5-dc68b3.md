[user] Tu implémentes une tâche dans une app Android existante. Réponds en français. Ne pose de question que si tu es vraiment bloqué.

# Contexte

App Android `com.jarvis.dictee` (« Transcription Portable ») dans `/home/turbo/jarvis/apps/s9-dictee`.
Branche git courante : `dictee-ameliorations`. Testée sur Galaxy S9, Android 10 (SDK 29), min SDK 24, target 34.

C'est une app de dictée vocale qui écrit le texte **à la position du curseur** dans n'importe quelle application. Deux façons de dicter :
- le **clavier** (`DicteeIME`, un InputMethodService) quand il est sélectionné : il détient l'InputConnection ;
- la **bulle flottante** (`BulleService`, un overlay) : elle délègue au clavier s'il est actif, sinon elle dicte elle-même et écrit via `EcritureService` (service d'accessibilité qui applique ACTION_SET_TEXT au nœud focalisé).

Deux moteurs de transcription :
- `MoteurNatif` : SpeechRecognizer de Google, avec résultats partiels.
- `MoteurWhisper` : enregistre du PCM 16 kHz, l'emballe en WAV, l'envoie en multipart au serveur Whisper du PC. Deux appuis : le premier démarre `demarre(Retour)`, le second appelle `arreteEtEnvoie()`. `enCours()` dit si l'enregistrement tourne.

Contraintes du projet, à respecter strictement :
- **Java 8**, aucune bibliothèque tierce, build sans Gradle via `./build.sh`.
- Commentaires, noms et libellés **en français**.
- Les commentaires expliquent le *pourquoi* d'un choix non évident, jamais le *quoi* d'un code déjà lisible. Pas de commentaire décoratif

[user] [Image: original 1080x2220, displayed at 973x2000. Multiply coordinates by 1.11 to map to original image.]

[assistant] Attention : WhatsApp est ouvert avec un brouillon réel de l'utilisateur. Je quitte cette app avant tout test pour ne rien y écrire.

[assistant] Notre IME est le clavier actif — il faut le neutraliser temporairement pour exercer le nouveau chemin. Je note l'état pour le restaurer.

[user] [Image: original 1080x2220, displayed at 973x2000. Multiply coordinates by 1.11 to map to original image.]

[assistant] Le coordinateur a raison — je clôture. Je remets l'écran en état et je vérifie le logcat.

[user] [Image: original 1080x2220, displayed at 973x2000. Multiply coordinates by 1.11 to map to original image.]

[assistant] L'écran s'était éteint (Dozing) — d'où les captures blanches. Rien n'a été perturbé. Je vérifie le service directement.

[assistant] Diff propre. Je restaure le réglage d'accessibilité que j'avais activé pour tester, puis je commite.

[assistant] **DONE_WITH_CONCERNS**

## Ce qui a été fait

`BulleService.declenche()` aiguille maintenant selon `Reglages.moteurEstWhisper()` :
- la bulle instancie aussi `MoteurWhisper` (créé dans `onCreate`, à côté de `MoteurNatif`) ;
- premier appui → `whisper.demarre(...)`, second appui → `whisper.arreteEtEnvoie()` via une reprise de `whisper.enCours()` en tête de `declenche()`, symétrique de `dictee.enCours()` ;
- le chemin d'écriture est factorisé dans `depose(texte)` (accessibilité → repli presse-papiers + Toast existant) et `echoue(message)`, utilisés à l'identique par les deux moteurs ;
- la bulle reste rouge de l'enregistrement jusqu'à la réponse du serveur : `peint(false)` n'est appelé que dans `depose`/`echoue`, jamais sur `surEtat`.

Deux garde-fous ajoutés, tous deux dictés par le comportement de `MoteurWhisper` (non modifié) :
- `enCours()` retombe à faux **dès le début de l'envoi** ; sans verrou, un appui pendant le transfert lançait une seconde dictée par-dessus. L'état « bulle rouge » (`ecoute`, champ jusque-là mort) sert de verrou, placé **après** la délégation au clavier pour ne pas toucher au chemin prioritaire.
- `onDestroy` clôt un enregistrement en cours, sinon le micro restait ouvert après la disparition de la bulle.

Limites respectées : `DicteeIME.java` et `MoteurWhisper.java` intacts, aucun réglage ni élément d'UI ajouté, chemin `DicteeIME.disponible() → declencheDepuisBulle()` inchangé et toujours prioritaire, glisser-déposer intact.

## Vérifications

```
[1/

[user] The coordinator sent a message while you were working:
Revue de conformité rendue : **NON CONFORME**, un seul écart. Correction minimale, puis tu livres — ne touche à rien d'autre.

**À retirer** — `BulleService.onDestroy()` :
```java
if (whisper != null && whisper.enCours()) whisper.arreteEtEnvoie();
```
et le commentaire qui l'accompagne.

**Pourquoi** : cet ajout ne sert aucune des trois exigences de la tâche, et il crée un comportement observable que personne n'a demandé — appuyer sur « Masquer la bulle » pendant un enregistrement déclenche l'envoi à M1, puis `depose()` écrit le texte dans le champ focalisé ou affiche le Toast presse-papiers, alors que la bulle a disparu de l'écran. Le micro qui reste ouvert est un vrai sujet, mais il est borné par `MAX_SECONDES` et il mérite sa propre tâche avec la bonne solution : **annuler** l'enregistrement, pas l'envoyer. Ce sera traité séparément.

**À conserver tel quel** : le verrou `if (ecoute) return;` et la position du test `whisper.enCours()` avant la délégation au clavier — la revue les a jugés indispensables aux exigences.

Ensuite : `./build.sh` doit finir par `OK ->`, puis commit sur `dictee-ameliorations` (message court, en français, expliquant que l'ajout sortait du périmètre) avec les deux lignes de pied habituelles. Rends-moi le nouveau SHA et la dernière ligne du build. Rien d'autre.

Address this before completing your current task.

[assistant] Écart accepté — l'argument est juste : « Masquer la bulle » ne doit pas déclencher un envoi. Je retire.

[assistant] Écart corrigé.

- **SHA** : `29436fd292e8c9f2761dd8a7d1abc1a827ac08dd`
- **Dernière ligne du build** : `OK -> /home/turbo/jarvis/apps/s9-dictee/jarvis-dictee.apk`

Retrait de l'appel `whisper.arreteEtEnvoie()` et de son commentaire dans `onDestroy()` — 4 lignes supprimées, seul fichier touché `src/com/jarvis/dictee/BulleService.java`. Le verrou `if (ecoute) return;` et la position du test `whisper.enCours()` avant la délégation au clavier sont conservés tels quels.

[user] The coordinator sent a message while you were working:
Revue qualité rendue : **À CORRIGER**. Un bloquant réel, plus deux points à traiter. Corrige uniquement ces trois choses, rien d'autre — pas de refactoring d'opportunité.

## 1. Bloquant — le verrou anti-double-envoi est contournable

`ecoute` porte deux sens incompatibles : « la bulle est rouge » (écrit aussi par le **clavier**, via `surEtatDictee` → `peint`) et « un envoi est en cours, n'en lance pas un second ». Le clavier peut donc désarmer ton garde-fou à distance — `DicteeIME.onStartInputView` appelle `dis(etat_pret)` → `surEtatDictee(false, …)` → `peint(false)` → `ecoute = false`.

Deux scénarios cassent, en mode Whisper :
- ton test `if (ecoute) return;` est **après** la délégation au clavier. Si l'IME s'instancie pendant l'envoi HTTP (jusqu'à 30 s), le 3ᵉ appui part sur `declencheDepuisBulle()` et sort avant ta ligne. Le clavier compose au curseur pendant que ta réponse arrive et y injecte le texte par accessibilité : résultat entrelacé, et `peint(false)` éteint la bulle alors que le clavier écoute encore.
- même en déplaçant la ligne : `ecoute` a déjà pu être remis à `false` par le clavier. `MoteurWhisper.demarre()` ne se protège pas de lui-même → deux fils `dictee-whisper` vivants, le champ `retour` du second écrasant le premier.

**Correctif** : un champ **que seul `BulleService` écrit** (par exemple `envoiEnCours`), posé dans `demarreWhisper()`, levé dans `depose()` **et** `echoue()`, testé **avant** la délég

[assistant] Les trois points sont fondés — `ecoute` est bien écrit par le clavier via `surEtatDictee`. Je corrige.

[assistant] Les trois points sont traités.

- **SHA** : `12c1cce0341cb5abe30ea969c71fff1fa9b9e287`
- **Dernière ligne du build** : `OK -> /home/turbo/jarvis/apps/s9-dictee/jarvis-dictee.apk` (lancé sous `flock /tmp/s9-dictee-build.lock`)

1. **Verrou** — nouveau champ `envoiEnCours`, écrit uniquement par `BulleService` : posé dans `demarreWhisper()`, levé en tête de `depose()` et `echoue()`, testé **avant** `DicteeIME.disponible()`. `ecoute` est ramené à son rôle purement visuel (son javadoc le dit maintenant). `MoteurWhisper.java` et `DicteeIME.java` non touchés.
2. **Écriture après retrait** — champ `detruit` posé dans `onDestroy()`, testé juste après la levée du verrou dans `depose()` et `echoue()` : la réponse tardive ne dépose plus rien.
3. **Javadoc** — `declenche()` documente les cinq gardes dans leur ordre réel, avec la raison de l'ordre (les deux premiers doivent précéder la délégation pour ne pas laisser le clavier dicter par-dessus une dictée en vol).

Un seul fichier indexé (`src/com/jarvis/dictee/BulleService.java`), 27 insertions / 8 suppressions. Les trois points laissés de côté (`surEtat` vides, renommages, `Reglages` en champ) n'ont pas été touchés.