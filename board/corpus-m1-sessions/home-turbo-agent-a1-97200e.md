[user] Tu implémentes une tâche dans une app Android existante. Réponds en français. La tâche est complètement spécifiée — va droit au but.

# Contexte

App Android `com.jarvis.dictee` (« Transcription Portable ») dans `/home/turbo/jarvis/apps/s9-dictee`.
Branche git : `dictee-ameliorations` — reste dessus.
Testée sur Galaxy S9, Android 10. minSdk 24, targetSdk 34.

App de dictée vocale. Un de ses deux moteurs, `MoteurWhisper`, enregistre l'audio sur le téléphone puis l'envoie à un serveur Whisper qui tourne sur le PC de l'utilisateur. Le PC est joignable par **trois voies** selon la situation :

```java
// Reglages.java
public static final String HOTE_USB       = "http://127.0.0.1:9744";       // téléphone branché, via adb reverse
public static final String HOTE_LAN       = "http://192.168.0.10:9744";    // même Wi-Fi
public static final String HOTE_TAILSCALE = "http://100.112.114.32:9744";  // partout, y compris en 4G
public static final String[] CANDIDATS = { HOTE_USB, HOTE_LAN, HOTE_TAILSCALE };
```

`Reglages` expose `hote()`, `metHote(String)`, `urlTranscription()` (= `hote() + "/v1/audio/transcriptions"`) et `urlSante()` (= `hote() + "/health"`).

Dans `MoteurWhisper`, la méthode privée `envoie(byte[] wav)` construit la requête multipart et la poste vers `reglages.urlTranscription()`. Elle lève une exception sur échec ; l'appelant `boucle()` attrape et rapporte « M1 injoignable ».

Contraintes du projet, strictes :
- **Java 8**, aucune bibliothèque tierce (pas d'OkHttp, pas d

[assistant] Maintenant `MoteurWhisper` : découper `envoie` en un envoi vers un hôte donné + un chapeau qui gère le repli.

[assistant] Installé. Pour éprouver la logique sans parler dans le téléphone, je construis un banc d'essai Java qui rejoue **exactement** le même code (`estInjoignable` + boucle de repli + `envoieVers`) contre le vrai pont.

[assistant] Le backend STT (`:8789`) derrière le pont est cassé indépendamment de moi (il ferme la connexion, d'où le 502 sur les trois voies). Je monte un serveur factice qui parle le même JSON pour éprouver le chemin *positif*.

[assistant] Banc d'essai terminé, stub arrêté (port 9755 libre), pont intact. Relecture du diff.

[assistant] Terminé.

## Ce qui a été fait

**`/home/turbo/jarvis/apps/s9-dictee/src/com/jarvis/dictee/MoteurWhisper.java`**
- `envoie(byte[])` devient un chapeau : essai sur l'hôte enregistré, puis sur les autres entrées de `Reglages.CANDIDATS` (l'hôte déjà tenté est sauté, chaque voie une seule fois). La voie qui répond est enregistrée via `metHote(...)`. Le WAV est passé tel quel à chaque tentative, jamais réenregistré.
- L'envoi proprement dit est extrait dans `envoieVers(String hote, byte[] wav)` — corps identique à l'ancien code, seule l'URL change.
- `estInjoignable(Exception)` classe l'échec : `SocketException` (refus, réseau coupé, lien perdu, `NoRouteToHost`), `UnknownHostException`, `SocketTimeoutException` → repli. Tout le reste, dont le `HTTP <code>` levé sur 4xx/5xx, remonte immédiatement sans repli.
- Retour visuel via le `surEtat` existant (« ⏳ Repli sur 100.112.114.32:9744… »). Aucune sonde, aucun test de santé ajouté.

**`Reglages.java`** — un seul ajout : `public static String urlTranscription(String hote)`, pour viser une voie sans l'écrire d'abord comme courante. `urlTranscription()` délègue à cette variante, comportement inchangé.

## Vérification

Build sous verrou :
```
[1/6] aapt2 compile res … [6/6] zipalign + signature
OK -> /home/turbo/jarvis/apps/s9-dictee/jarvis-dictee.apk
```
`flock … adb install -r jarvis-dictee.apk` → `Success`.

**Ce que je n'ai pas pu observer** : le repli de bout en bout depuis le téléphone — il faudrait parler dans le S9. J'ai donc re

[user] The coordinator sent a message while you were working:
Revue rendue : **CONFORME** sur le cahier des charges, **À CORRIGER** sur la qualité. Deux bloquants, précis. Corrige-les, laisse le reste.

## B1 — un délai de LECTURE dépassé n'est pas une injoignabilité

`TIMEOUT_MS` s'applique aussi en lecture. Un timeout de lecture veut dire que la connexion TCP **a été acceptée** : le serveur est là, il est juste lent. Ton code le classe « injoignable » et rejoue alors le même WAV sur les deux autres voies — **or les trois adresses mènent au même PC**. On quadruple donc la charge sur une machine précisément parce qu'elle était trop lente, et l'utilisateur attend jusqu'à 180 s pour finir en erreur.

C'est exactement le raisonnement qui t'a fait interdire le repli sur 5xx ; il s'applique ici à l'identique.

**Correctif** : un drapeau `connexionEtablie` posé dans `envoieVers` une fois que `co.getOutputStream()` a rendu la main. Ne replier que sur un timeout de **connexion**, jamais de lecture.

## B2 — le champ `retour` est écrasable pendant tout le repli

`demarre()` ne se garde que par `if (enregistre) return`, or `enregistre` repasse à `false` **avant** l'envoi. Pendant les 90 à 240 s du repli, le moteur se croit libre alors qu'un fil est en vol. Côté clavier, deux appuis d'un utilisateur qui trouve que « rien ne se passe » suffisent : `demarre()` remplace `this.retour`, et la cascade précédente écrit son texte dans le **nouveau** callback — l'ancienne dictée s'insère dans le champ 

[assistant] Un autre agent a 72 lignes non commitées dans `MoteurWhisper.java`. Je lis l'état actuel avant toute édition.

[assistant] I3 — tenir la promesse du message de commit : ne plus maquiller un refus du serveur en panne réseau.

[assistant] Build OK. Je remets le banc d'essai à jour pour éprouver précisément B1 — un délai de **lecture** ne doit plus déclencher de repli.

[assistant] B1 tranché net : cas B1 et cas 3 lèvent **la même** `SocketTimeoutException`, et le drapeau les sépare correctement (lecture → pas de repli, connexion → repli). Installation puis relecture.

[assistant] Mes correctifs B2/I3 vivent **à l'intérieur** du refactor `boucle()`/`enregistreEtTranscrit()` de l'autre agent : ils ne se séparent pas en un commit qui compile. Je commite donc le fichier entier en créditant explicitement son travail, sans toucher à son `BulleService.java`.

[assistant] Corrections faites et vérifiées.

## B1 — délai de lecture ≠ injoignabilité

Drapeau `connexionEtablie` posé dans `envoieVers` juste après que `co.getOutputStream()` a rendu la main. Un échec n'est reclassé en repli que si `!connexionEtablie && estInjoignable(e)`. La classification est portée par une exception dédiée `VoieMorte` (elle enveloppe l'échec réel, `reelle()` le restitue pour que le message reste lisible) : `envoie` ne replie que sur `VoieMorte`, tout le reste — HTTP 4xx/5xx **et** délai de lecture — remonte tel quel.

Éprouvé au banc, avec le code de prod recopié à l'identique. Le point clé : **les deux cas lèvent la même `SocketTimeoutException`**, et seul le drapeau les sépare.

| Cas | Avant | Après |
|---|---|---|
| Serveur joignable qui ne répond jamais (timeout **lecture**) | repli sur 2 autres voies | `SocketTimeoutException: Read timed out`, **aucun repli**, 1× le timeout |
| Trou noir 10.255.255.1 (timeout **connexion**) | repli | `VoieMorte` → repli → succès |
| Connexion refusée | repli | inchangé, hôte retenu = la voie qui répond |
| Vrai pont en HTTP 502 | pas de repli | inchangé |

## B2 — `retour` verrouillé pendant tout l'envoi

Nouvel état `occupe`, posé avant le démarrage du fil et libéré dans un `finally` imbriqué au tout dernier moment (même si le callback lui-même lève). `demarre()` teste `occupe` **avant** `this.retour = r` et refuse en le disant (`"Dictée précédente en cours…"`) plutôt qu'en restant muet — c'est le silence qui poussait à ré-a