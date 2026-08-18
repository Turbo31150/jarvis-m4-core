[user] Tu relis un commit Android, sur deux plans : **conformité au cahier des charges** puis **qualité de code**. Réponds en français. Tu ne modifies aucun fichier.

# Le commit

Dépôt `/home/turbo/jarvis/apps/s9-dictee`, branche `dictee-ameliorations`, commit `8ca10ae5dc2a99a142e1c2b695bb7e98c80fc385`.
`git show 8ca10ae`, puis lis les fichiers complets `src/com/jarvis/dictee/MoteurWhisper.java` et `Reglages.java`.

# Le cahier des charges qui était donné

## Problème
L'adresse du serveur de transcription est figée par le dernier réglage. En débranchant le câble ou en passant en 4G, `127.0.0.1:9744` ne répond plus : la dictée échoue par « M1 injoignable » alors que la voie Tailscale fonctionnerait.

## Attendu
Dans `MoteurWhisper`, si l'envoi vers l'hôte enregistré échoue **parce que le serveur est injoignable** (connexion refusée, hôte inconnu, délai dépassé), essayer les autres entrées de `Reglages.CANDIDATS` dans l'ordre, **une seule fois chacune**. Dès qu'une répond, l'enregistrer comme nouvel hôte courant via `metHote(...)`.

Deux règles décisives :
- **Ne jamais réessayer sur une erreur HTTP du serveur** (4xx, 5xx) : c'est le bon serveur qui refuse ; changer d'hôte masquerait la vraie cause.
- **L'audio est réutilisé tel quel**, jamais réenregistré.
- Ne pas réessayer l'hôte déjà tenté s'il fait partie des candidats.

## Limites
- `MoteurWhisper.java` et un accesseur dans `Reglages.java` si nécessaire. Rien d'autre.
- Pas de sonde périodique, pas de test de santé en arrière-p

[assistant] Now let me check the callers to assess thread/lock implications, and confirm the commit's file scope.

[assistant] Let me verify the IME re-entry guard, to judge whether the extended window is actually reachable.

[assistant] J'ai lu le commit, les deux fichiers complets, et les deux appelants (`DicteeIME`, `BulleService`) pour juger de la portée réelle.

---

## Points forts

- **Le contrat du cahier des charges est tenu à la lettre.** Repli uniquement sur échec de transport, abandon immédiat sur 4xx/5xx (`MoteurWhisper.java:176`), un seul passage sur `CANDIDATS`, hôte déjà tenté sauté (`:167`), `metHote` sur la voie qui répond (`:173`). Périmètre respecté : 2 fichiers, un accesseur ajouté dans `Reglages`.
- **L'audio est réellement réutilisé.** Le même `byte[] wav` est passé par référence à chaque `envoieVers` ; `enveloppeWav` n'est appelé qu'une fois (`:108`). Aucune recopie du WAV, aucun réenregistrement.
- **La classification d'exceptions est techniquement juste** sur les trois cas nommés. `ConnectException` et `NoRouteToHostException` héritent bien de `SocketException` — le test les couvre donc sans les nommer. `SocketTimeoutException` hérite de `InterruptedIOException`, **pas** de `SocketException` ; `UnknownHostException` hérite directement d'`IOException`. Les lister séparément était nécessaire, et c'est fait.
- **La persistance se fait depuis le bon fil.** `metHote` → `SharedPreferences.apply()` est sûr depuis n'importe quel thread, et rend la valeur visible en mémoire immédiatement. Rien à redire.
- **Les commentaires expliquent le pourquoi**, pas le comment (`:148-153`, `:171-172`, `:185-189`). C'est le niveau attendu.

---

## Bloquant

### B1 — Un délai de lecture dépassé n'est pas u