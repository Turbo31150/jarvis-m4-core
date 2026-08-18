[user] Tu es relecteur de **qualité de code**. Réponds en français. Tu ne modifies aucun fichier — tu juges.

La conformité au cahier des charges a déjà été validée par un autre relecteur : ne la rejuge pas. Ta question est : **ce code est-il bien construit ?**

# Ce qu'il faut relire

Dépôt `/home/turbo/jarvis/apps/s9-dictee`, branche `dictee-ameliorations`.
Plage à relire : `git diff 8ff1aba..29436fd -- src/com/jarvis/dictee/BulleService.java`
Lis aussi le fichier complet `src/com/jarvis/dictee/BulleService.java` et, pour le contexte, `MoteurWhisper.java`, `MoteurNatif.java` et `EcritureService.java`.

# Ce que ce code fait

`BulleService` est une bulle flottante de dictée vocale posée par-dessus les autres applications Android. Un appui déclenche la dictée. Trois chemins possibles :
1. notre clavier maison est actif → on lui délègue tout ;
2. sinon, on dicte sur place avec le moteur choisi dans les réglages (Google natif, ou Whisper sur un serveur distant), et on écrit dans le champ focalisé via le service d'accessibilité ;
3. si aucun champ n'a le focus → repli sur le presse-papiers.

Le changement relu vient d'ajouter le chemin Whisper, jusque-là ignoré.

# Contraintes du projet, à prendre comme acquises

- **Java 8**, aucune bibliothèque tierce, pas de Gradle. Ne propose ni lambda, ni `java.util.function`, ni AndroidX, ni bibliothèque externe.
- Commentaires, noms et libellés **en français**. C'est voulu.
- Pas de tests automatisés dans ce projet : c'est une app Android sans h

[assistant] J'ai lu le diff, le fichier complet, `MoteurWhisper`, `MoteurNatif`, `EcritureService`, plus `DicteeIME` et `Reglages` pour tracer les interactions d'état.

# Relecture qualité — `BulleService.java` (8ff1aba..29436fd)

## Points forts

- **L'extraction de `depose()` / `echoue()` (lignes 249-268) est la bonne décision.** Sans elle, l'ajout du second moteur dupliquait à l'identique le bloc `ui.post` + `peint(false)` + repli presse-papiers. Le résultat : deux callbacks de quatre lignes chacun, qui se lisent d'un coup d'œil.
- **L'ordre des deux tests d'arrêt (lignes 200-201) est juste, et pas par hasard.** Les placer avant la délégation au clavier garantit qu'une dictée démarrée par la bulle sera toujours close par la bulle, même si le clavier devient actif entre-temps. C'est le seul endroit du fichier où le problème de bascule de clavier est correctement traité.
- **Les commentaires de `demarreWhisper()` (232-236) et de `depose()` (245-248) expliquent le pourquoi** — le protocole à deux appuis, et le fait que les retours Whisper arrivent du fil d'enregistrement. Ce sont des informations qu'on ne déduit pas du code.
- **Le javadoc de classe a été corrigé en même temps que le comportement** (lignes 32-36). La documentation ne ment plus, ce qui est rare dans un ajout de fonctionnalité.
- Les deux moteurs sont instanciés une fois dans `onCreate` (76-77), pas à chaque appui : leurs `enCours()` restent interrogeables, ce qui rend `declenche()` possible.

---

## Bloquant

### B1 — `e

[user] The coordinator sent a message while you were working:
L'implémenteur a traité tes trois points. Nouveau commit : `12c1cce0341cb5abe30ea969c71fff1fa9b9e287` (27 insertions / 8 suppressions, `BulleService.java` seul).

Ce qu'il annonce :
1. **B1** — champ `envoiEnCours` écrit uniquement par `BulleService`, posé dans `demarreWhisper()`, levé en tête de `depose()` et `echoue()`, testé **avant** `DicteeIME.disponible()`. `ecoute` redevient purement visuel.
2. **I3** — champ `detruit` posé dans `onDestroy()`, testé dans `depose()` et `echoue()`.
3. **I4** — javadoc de `declenche()` remis en accord avec les cinq gardes et leur ordre.

Vérifie sur pièces, pas sur parole : `git show 12c1cce` puis relis l'état final du fichier.

Les questions qui décident :
- le verrou est-il désormais **inatteignable depuis l'extérieur** ? Retrace qui écrit `envoiEnCours` et qui écrit `ecoute`.
- ton scénario de la voie 1 (IME instancié pendant l'envoi, 3ᵉ appui) est-il vraiment fermé maintenant ?
- la voie 2 (deux fils `dictee-whisper` vivants) l'est-elle aussi ?
- une nouvelle faille a-t-elle été ouverte au passage — par exemple un chemin où `envoiEnCours` reste posé à jamais et gèle la bulle définitivement ?

Les points que tu avais classés Important sans les demander (`surEtat` vides, renommage `dictee`/`whisper`, `Reglages` en champ) ont été écartés sciemment : ne les recompte pas comme bloquants.

Termine par une seule ligne : `APPROUVÉ` ou `À CORRIGER`.

Address this before completing your cur

[assistant] The diff looks right at first glance. Let me read the final state and check the write-sites exhaustively.

[assistant] Let me confirm the two decisive facts: that nothing outside writes the lock, and where `boucle()`'s try boundaries actually sit.

[assistant] Vérification faite sur pièces. Voici le verdict.

# Contre-relecture du commit `12c1cce`

## Les trois points sont réellement traités

**B1 — le verrou est désormais inatteignable depuis l'extérieur.** Vérifié par recensement exhaustif des écritures, pas sur parole :

| Champ | Écrit en | Par qui |
|---|---|---|
| `envoiEnCours` | `250` (true), `264`, `282` (false) | `BulleService` seul |
| `ecoute` | `315`, dans `peint()` | `BulleService` **et** le clavier via `surEtatDictee` (311) |
| `detruit` | `131`, dans `onDestroy()` | `BulleService` seul |

Le `grep -rn` sur tout `src/` ne trouve `envoiEnCours` et `detruit` que dans `BulleService.java` ; le champ est `private`, sans accesseur. `peint()` (314-315) n'écrit plus que `ecoute` — le seul chemin par lequel le clavier atteignait l'état de la bulle ne touche donc plus le verrou. La séparation demandée est effective, pas seulement annoncée.

**Voie 1 fermée.** `if (envoiEnCours) return;` est en `217`, `DicteeIME.disponible()` en `219`. Mon scénario s'arrête à l'étape 4 : le 3ᵉ appui, pendant l'envoi, rend la main en `217` et le clavier n'est jamais sollicité. Plus de composition concurrente au curseur, plus de `peint(false)` éteignant la bulle pendant que le clavier écoute.

**Voie 2 fermée.** `envoiEnCours` couvre désormais **l'enregistrement *et* l'envoi** — de l'entrée dans `demarreWhisper()` (250) jusqu'au callback terminal. Un second `demarreWhisper()` exigerait de franchir `217`. Et `onStartInputView` ne peut plus désarme