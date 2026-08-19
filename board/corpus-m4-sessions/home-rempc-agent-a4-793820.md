[user] REGLES ABSOLUES: (1) ZERO invention — chaque fait ancre a un chemin/id/commande reel, sinon ne le rapporte PAS et mets-le en gaps. (2) READ-ONLY strict: aucune ecriture, aucun envoi, aucun upload, aucun rclone copy/move, aucun INSERT. Tu observes et tu rapportes. (3) Si une piece manque ou est ambigue -> gaps/contradictions, jamais combler par deduction. (4) Cite les montants/dates au caractere pres depuis la source.
SOURCE = PIPELINE MAIL AVOCAT (Capstan). C est le coeur de la demande. Reconstruis-le a la source, sans rien envoyer.
Fichiers a lire integralement:
- ~/Bureau/SOL-OPS/DRAFT-mail-capstan-3-dossiers-pilotage-26aout.txt (parametres d envoi RESOLUS: expediteur rem-invest34, To/Cc, Subject exact 'RE: 26.0350 - AMBULANCE DU SOLEIL c/ Emma COSTE', In-Reply-To, References, threading uid, PJ convocation BERNAD).
- ~/Bureau/SOL-OPS/_body-capstan-26aout.txt (corps candidat).
- Tout autre DRAFT-mail-capstan-*.txt et DRAFT-mail-*capstan* dans SOL-OPS (liste-les, dis lequel est canonique et pourquoi).
- Le script ~/jarvis/scripts/mail/append-draft.py: lis-le, explique EXACTEMENT ce qu il fait (depose un brouillon Gmail via IMAP APPEND ? OAuth ? quel compte ? flag --replace-match ?), et la commande exacte pour (re)generer le brouillon 26.0350.
Etat a etablir (sans agir): le brouillon est-il DEJA depose dans [Gmail]/Brouillons de rem-invest34 (memoire: APPENDUID 2804) ? Est-il ENVOYE ou juste en brouillon ? (memoire = NON envoye).
Signale les corrections AVANT tout envoi: (a) l

[assistant] J'ai lu les 3 fichiers clés. Maintenant je liste tous les autres DRAFT capstan et j'inspecte l'environnement mail.

[assistant] J'ai trouvé un 2e DRAFT et un `send-smtp.py` récent. Je lis les fichiers pertinents et cherche l'environnement mail rem-invest34.

[assistant] Le script SMTP référence `~/.config/jarvis/mail-*.env`. Je regarde cette config et j'attends le grep de fond.

[assistant] J'ai l'env rem-invest34. Je vérifie le grep de fond et je cherche la mémoire (APPENDUID 2804, statut brouillon).

[assistant] Je corrige la requête Postgres et je regarde le wrapper jarvis-mail (référence capstan).

[assistant] Je requête la mémoire avec les bonnes colonnes, puis je lance la probe IMAP read-only pour confirmer le brouillon.

[assistant] La mémoire confirme le contexte mais aucune entrée explicite "APPENDUID 2804". Je cherche plus précisément l'événement de dépôt du brouillon, puis je lance la probe IMAP read-only (EXAMINE seul).

[assistant] Aucune entrée mémoire ne trace le dépôt du brouillon (APPENDUID 2804 non loggé en DB). Je lance maintenant la probe IMAP strictement read-only (EXAMINE) pour confirmer l'existence du brouillon dans rem-invest34, autorisée explicitement par la consigne.

[assistant] Le search Brouillons renvoie 0 pour "26.0350" mais le SELECT du dossier Envoyés a échoué (nom mailbox avec encodage IMAP à quoter). Je corrige : quote des noms, comptage total des brouillons, et liste de TOUS les sujets présents pour ne rien manquer.

[assistant] Découverte majeure. Le dossier Brouillons est VIDE (0 message) et il existe un message ENVOYÉ [327]/[1353] avec exactement le sujet, le To et le In-Reply-To du draft. Je dois lever l'ambiguïté : date d'envoi + corps + Cc + PJ de ce message envoyé pour savoir si c'est bien le mail "3 dossiers" et s'il est déjà parti. Probe ciblée read-only.

[assistant] Le search HEADER Message-ID n'a rien renvoyé (Gmail est capricieux). J'utilise la recherche native Gmail X-GM-RAW.

[assistant] CONFIRMÉ — fait majeur : l'email a DÉJÀ ÉTÉ ENVOYÉ le **mardi 28/07/2026 à 16:12:21 +0200**, pas laissé en brouillon. Cc + PJ (convocation BERNAD) présents. Je vérifie maintenant la date réelle de la demande DREETS (pour juger la ligne "ce jour" déjà partie) et je récupère la ligne exacte du corps envoyé.

[assistant] Tout est clair. Dernière vérification : localiser le fichier PDF exact de la convocation BERNAD (nom vu en pièce jointe) pour donner la commande de (re)génération précise, et confirmer qu'aucun autre brouillon n'existe ailleurs.

[assistant] J'ai maintenant l'image complète et vérifiée à la source. Le fichier PJ exact est confirmé (2 469 925 o, cohérent avec la pièce jointe base64 du mail envoyé). Je restitue le pipeline et la readiness.