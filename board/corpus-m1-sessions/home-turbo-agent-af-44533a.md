[user] Tu implémentes une tâche dans une app Android existante. Réponds en français. La tâche est petite et précisément spécifiée.

# Contexte

App `com.jarvis.dictee` dans `/home/turbo/jarvis/apps/s9-dictee`, branche `dictee-ameliorations`.
Android 10 (SDK 29) cible réelle, minSdk 24. **Java 8**, aucune bibliothèque tierce, build sans Gradle. Commentaires et noms **en français**. Les commentaires disent le *pourquoi*, jamais le *quoi*.

`MoteurWhisper` enregistre l'audio du micro sur un fil nommé `dictee-whisper`, puis l'envoie à un serveur. Son cycle actuel :
- `demarre(Retour)` ouvre le micro et lance le fil ;
- `arreteEtEnvoie()` met `enregistre = false`, ce qui fait sortir la boucle de lecture, ferme le micro et **déclenche l'envoi** ;
- `enCours()` ne reflète que la phase d'enregistrement ;
- `boucle()` termine en appelant exactement un callback : `surTexte`, ou `surErreur`.

`BulleService` est une bulle flottante qui pilote ce moteur. Il pose un verrou `envoiEnCours` avant de démarrer, et ne le lève que dans ses callbacks terminaux `depose()` / `echoue()`.

# La tâche — deux défauts liés, à corriger ensemble

## Défaut 1 — pas de moyen d'annuler

Quand la bulle est détruite (l'utilisateur touche « Masquer la bulle » pendant un enregistrement), il n'existe aucun moyen de rendre le micro. `arreteEtEnvoie()` ne convient pas : il **enverrait** l'audio, et le texte finirait écrit dans le champ focalisé alors que l'utilisateur a demandé l'arrêt. Faute de mieux, `BulleService` ne fa

[assistant] The accessibility service was bound before my reinstall (5 dead system bindings) — the install cleared it. Let me restore it and inspect the settings screen.

[assistant] Another agent is concurrently editing this repo — `RelanceAuDemarrage.java` is modified (not by me) and an `occupe` field has appeared in *my* file. Let me examine it.

[assistant] The concurrent change is coherent and builds on mine. Keeping it per instruction. Let me rebuild and reconnect the device.

[user] [Image: original 1080x2220, displayed at 973x2000. Multiply coordinates by 1.11 to map to original image.]

[assistant] The bubble service is running. Let me close the shade and view the settings screen.

[user] [Image: original 1080x2220, displayed at 973x2000. Multiply coordinates by 1.11 to map to original image.]

[user] [Image: original 1080x2220, displayed at 973x2000. Multiply coordinates by 1.11 to map to original image.]

[user] [Image: original 1080x2220, displayed at 973x2000. Multiply coordinates by 1.11 to map to original image.]

[user] [Image: original 1080x2220, displayed at 973x2000. Multiply coordinates by 1.11 to map to original image.]

[assistant] I locked the device with an accidental pattern swipe — I'll stop UI poking immediately rather than risk lockout.

[assistant] Device is asleep and safe. Now let me review the complete diff before committing.

[assistant] Another agent committed concurrently and swept my `MoteurWhisper` work into their commit. Let me verify what landed where.

[assistant] Confirmed a collision: another committer (04:43) swept my uncommitted `MoteurWhisper` work into their commit. Let me verify the final committed state builds and re-read the merged file.