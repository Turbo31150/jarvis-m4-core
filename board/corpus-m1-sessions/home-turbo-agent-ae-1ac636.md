[user] Tu implémentes une tâche dans une app Android existante. Réponds en français. Va droit au but : la tâche est petite et complètement spécifiée.

# Contexte

App Android `com.jarvis.dictee` (« Transcription Portable ») dans `/home/turbo/jarvis/apps/s9-dictee`.
Branche git courante : `dictee-ameliorations` — travaille dessus, ne change pas de branche.
Testée sur Galaxy S9, Android 10 (SDK 29). minSdk 24, targetSdk 34.

App de dictée vocale qui écrit le texte à la position du curseur. Deux composants concernés :
- `BulleService` — un `Service` d'overlay affichant une bulle micro flottante par-dessus les autres apps. Démarré par `startService(new Intent(ctx, BulleService.class))`. Il se met lui-même au premier plan (`startForeground`) et s'arrête proprement si l'autorisation d'overlay manque.
- `Reglages` — préférences partagées. Deux méthodes t'intéressent : `bulle()` qui dit si l'utilisateur veut la bulle affichée, et la méthode statique `BulleService.estAffichable(Context)` qui dit si l'autorisation d'affichage par-dessus les autres apps est accordée.

Contraintes du projet, strictes :
- **Java 8**, aucune bibliothèque tierce, build sans Gradle.
- Commentaires, noms et libellés **en français**.
- Les commentaires expliquent le *pourquoi* d'un choix non évident, jamais le *quoi* d'un code lisible. Aucun commentaire décoratif.

# La tâche

## Problème

Aucun `BOOT_COMPLETED` n'est déclaré. Après un redémarrage du téléphone, la bulle a disparu alors que l'utilisateur l'avait activ

[assistant] Receiver enregistré. Je teste les deux sens — d'abord l'état actuel de la préférence.

[assistant] Impossible de déverrouiller le S9 (bouncer sécurisé) et le service n'est pas exporté. Je passe par une copie debuggable hors dépôt pour piloter la préférence.

[assistant] bulle=true actuellement. Je réinstalle l'APK de prod et je teste le sens « réglage actif ».

[assistant] Le shell ne peut pas émettre `BOOT_COMPLETED` (broadcast protégé, uid 2000 refusé) et l'écran est sécurisé. Je monte un banc d'essai dans la copie debuggable qui invoque le vrai receiver avec un vrai intent `BOOT_COMPLETED`.

[assistant] Appareil restauré (pas de `BancEssai`, pas de flag debuggable, overlay `allow`, `bulle=true`). Je relis mon diff.

[assistant] Les deux sens confirmés sur le code final. Je restaure et je vérifie l'APK de prod.

[assistant] **DONE_WITH_CONCERNS**

## Fichiers touchés
- `/home/turbo/jarvis/apps/s9-dictee/src/com/jarvis/dictee/RelanceAuDemarrage.java` (nouveau)
- `/home/turbo/jarvis/apps/s9-dictee/AndroidManifest.xml` (permission `RECEIVE_BOOT_COMPLETED` + `<receiver>`)

`BulleService.java` **non modifié**. SHA : `d39a11c5cec782a55716ebd96d7df447990bc09f` sur `dictee-ameliorations`.

## Build
```
[6/6] zipalign + signature
OK -> /home/turbo/jarvis/apps/s9-dictee/jarvis-dictee.apk
-rw-rw-r-- 1 turbo turbo 41811 août   6 04:00 jarvis-dictee.apk
```
Install : `Success`. Receiver enregistré :
```
android.intent.action.BOOT_COMPLETED:
  a150dcb com.jarvis.dictee/.RelanceAuDemarrage filter 146c5f0
    Action: "android.intent.action.BOOT_COMPLETED"
android.permission.RECEIVE_BOOT_COMPLETED: granted=true
```

## Tests comportementaux — les deux sens observés
```
===== SENS 1 : reglage ACTIF =====      ===== SENS 2 : reglage INACTIF =====
--- bulle : value="true"                --- bulle : value="false"
--- avant : 0                           --- avant : 0
--- apres : 2                           --- apres : 0
```
Le service démarre bien au premier plan (`isForeground=true foregroundId=42`). Troisième cas testé aussi : `bulle=true` + `appops SYSTEM_ALERT_WINDOW deny` → 0 → 0, rien ne démarre.

## Réserve — comment j'ai dû tester
**La commande de vérification fournie ne fonctionne pas sur ce S9** : `BOOT_COMPLETED` est un broadcast protégé, refusé au shell adb —
```
Security exception: Permission Denial: not

[user] The coordinator sent a message while you were working:
Revue rendue : **CONFORME** sur le cahier des charges, **À CORRIGER** sur la qualité. Aucun bloquant, deux choses à faire.

Le relecteur a vérifié ta déclaration point par point et elle tient : dépôt propre, manifeste sans `debuggable`, copie de test bien hors dépôt, `RelanceAuDemarrage.java` du banc **identique** à celui livré, appareil restauré (md5 de l'APK installé = celui du dépôt). C'est du bon travail de traçabilité.

## 1. Protège le démarrage du service

`RelanceAuDemarrage.java:28-33` est le **seul démarrage nu du dépôt**. Partout ailleurs le projet enveloppe : `SetupActivity.java:223` fait `try { startService(...) } catch (Throwable ignore) { }`, `BulleService` fait pareil en trois endroits.

Le scénario qui fait mal : `targetSdkVersion="34"`. Sur un appareil Android 14, un service de premier plan de type `microphone` démarré depuis l'arrière-plan est refusé — l'exemption `BOOT_COMPLETED` autorise un FGS, mais pas les types « pendant l'utilisation ». L'exception remonte dans `onReceive`, personne ne l'attrape, et l'utilisateur voit « Transcription Portable s'est arrêtée » **dès l'allumage du téléphone**. Rien sur le S9 en Android 10, mais le boot est l'endroit où un plantage coûte le plus cher.

Deux lignes, motif déjà maison.

## 2. Fais le vrai test — il était à ta portée

Ta justification n'est vraie qu'à moitié : `am broadcast BOOT_COMPLETED` est bien refusé au shell adb, mais **`adb reboot` ne l'est pas**,

[assistant] Le service tourne après un vrai redémarrage. Je consolide la preuve du chemin emprunté.

[assistant] Le logcat révèle deux problèmes : un `START SetupActivity from uid 2000` à 04:39:19 que je n'ai pas émis, et un crash de l'app. J'enquête.

[assistant] L'énigme est résolue : `lastUpdateTime=04:39:58` — **un autre agent a réinstallé l'APK et lancé `SetupActivity` à 04:39:19**, juste avant mon relevé. Pas de crash applicatif (buffer `crash` vide, `am_kill ... stop` = réinstallation). Mon test de reboot est donc pollué : `SetupActivity.onResume()` lance aussi `BulleService`, je ne peux pas attribuer le démarrage à mon receveur. Je commite d'abord la correction pour que l'APK partagé contienne mon code final.

[assistant] `BulleService.java` et `MoteurWhisper.java` sont modifiés par l'autre agent. J'ajoute un commit séparé plutôt qu'un `--amend` — réécrire l'historique pendant qu'un agent concurrent travaille sur la même branche pourrait absorber son commit.

[assistant] Maintenant le vrai test de reboot, propre. Je capture le logcat en continu pour tracer le chemin exact.

[assistant] `BulleService` tourne au premier plan après le redémarrage, **et cette fois aucun `START ... SetupActivity`**. Je vérifie l'APK installé (`lastUpdateTime` a bougé de 18 s après mon install) et l'unicité du chemin.

[assistant] Les md5 correspondent : l'APK installé est bien celui du dépôt, buildé après mon commit. Contrôle final.

[assistant] Les trois points sont traités. **DONE** — le vrai test de reboot passe.

## SHA
- `d39a11c5cec782a55716ebd96d7df447990bc09f` — le receveur (inchangé)
- `e1b2d1e8bb469d16275b593ecfc58cd8b7726791` — **les corrections 1 et 3**, `RelanceAuDemarrage.java` seul (11 ins., 5 sup.)

Commit séparé plutôt qu'un `--amend` : réécrire `HEAD` pendant que l'agent concurrent travaille sur la même branche risquait d'absorber son commit. Il a d'ailleurs commité `fa09391` juste après — l'amend serait tombé dessus.

## Build
```
OK -> /home/turbo/jarvis/apps/s9-dictee/jarvis-dictee.apk
```

## 1 et 3 — corrigés
```java
try {
    // Un receveur de démarrage bénéficie d'une brève tolérance pendant
    // laquelle startService() passerait encore ; startForegroundService()
    // ne dépend, lui, d'aucune fenêtre de temps.
    if (Build.VERSION.SDK_INT >= 26) contexte.startForegroundService(bulle);
    else contexte.startService(bulle);
} catch (Throwable ignore) {
    // Un Android récent peut refuser un service de premier plan de type
    // micro démarré en arrière-plan. Se taire coûte une bulle absente ;
    // laisser filer l'exception coûterait un plantage au rallumage.
}
```

## 2 — le vrai reboot : vous aviez raison, et il a fallu s'y reprendre à deux fois

**Premier `adb reboot`** (04:36) : `BulleService` tournait après le boot — mais le logcat m'a montré que le résultat était **invalide** :
```
04:39:19 ActivityTaskManager: START u0 {cmp=com.jarvis.dictee/.SetupActivity} from uid 2000
04:39: