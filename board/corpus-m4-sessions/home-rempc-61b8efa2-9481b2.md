[user] demain rdv emma entretien pour licenciement inaptidue peut tu me dire ou tu as mis le script stp

[assistant] Trouvé.

Le script est ici :

**`/home/rempc/Bureau/SOL-OPS/Capstan-Emma-COSTE/`**

- **`SCRIPT-ENTRETIEN-PREALABLE-COSTE-27juillet-VALIDE.pdf`** ← la version validée à imprimer/emporter demain
- `SCRIPT-ENTRETIEN-PREALABLE-COSTE-27juillet-VALIDE.md` (même contenu, éditable)
- `SCRIPT-ENTRETIEN-PREALABLE-COSTE-27juillet-BROUILLON.md` (brouillon)

Le dossier contient aussi le reste du dossier DREETS (avis d'inaptitude Dr Léger 01 juin, convocation signée, courrier-type notif licenciement post-autorisation).

Deux points à vérifier ce soir :
- L'intitulé du fichier dit **27 juillet** — ton RDV est bien demain (27/07) ? On est le 26.
- Tu veux que je te sorte un récap 1-page (points à dire / à ne PAS dire) à partir du script validé pour l'avoir sous les yeux, ou tu pars juste avec le PDF ?

[assistant] Envoyé à l'imprimante ✅

- **Imprimante** : Ricoh MP C2004 (par défaut)
- **Fichier** : `SCRIPT-ENTRETIEN-PREALABLE-COSTE-27juillet-VALIDE.pdf`
- **Job** : `Ricoh_MP_C2004-7`

Ça sort maintenant. Tu veux que je t'imprime aussi la **convocation signée** et l'**avis d'inaptitude Dr Léger** du dossier DREETS pour les avoir en main pendant l'entretien ?

[assistant] Non, **rien d'obligatoire à lui faire signer**. L'entretien préalable n'impose aucune signature de la salariée. Mais attention à deux nuances, d'après la méthode validée avec El Mir (ligne 16 de ton index dossier) :

**1. Ce n'est pas « juste on informe »** — légalement c'est :
- tu **exposes les motifs** envisagés (inaptitude + impossibilité de reclassement),
- tu **recueilles ses observations**,
- tu **ne décides RIEN sur place** (surtout pas de notifier le licenciement — l'autorisation DREETS n'est pas encore là, elle est salariée protégée).

**2. Le seul document « à signer » = le compte-rendu d'entretien** (celui prévu dans ta méthode El Mir). Ce n'est **pas une obligation pour elle**, c'est une **preuve pour ton dossier DREETS** que l'entretien a bien eu lieu :
- vous le signez tous les deux en fin d'entretien,
- **si elle refuse de signer → aucun blocage** : tu le notes, et c'est couvert par **ton assesseur/témoin + l'audio annoncé en ouverture** (les deux garde-fous déjà prévus dans le script).

Donc : tu n'as **rien à lui présenter en début d'entretien**. Le seul papier qui circule, c'est le CR **à la fin**, et son refus éventuel n'a aucune conséquence grâce au témoin + audio.

⚠️ Un point : c'est Me El Mir (Capstan) qui pilote le dossier — si tu veux blindé à 100 %, un SMS ce soir « rien à faire signer à Emma demain, juste CR de fin ? » te confirme en 30 s. Tu veux que je te prépare ce message ?

[assistant] Sauvegardé en mémoire durable (Postgres `jarvis_main` → `memory_atoms`, priorité 8). ✅

**Atom** : `atom_coste_protocole_entretien_27juillet_20260727` (scope `soleil`)

Ce qui est gravé pour demain matin :
- **RDV** : lun 27/07 10h, siège Aigues-Mortes — Emma COSTE, inaptitude AT (salariée protégée, L.1226-12)
- **Script** : `~/Bureau/SOL-OPS/Capstan-Emma-COSTE/SCRIPT-...-VALIDE.pdf` (imprimé, validé El Mir 23/07)
- **Méthode** : audio annoncé en ouverture → témoin/assesseur → exposer motifs → recueillir observations → **ne rien décider sur place**
- **Signature** : rien en amont ; seul le **compte-rendu signé en fin** ; refus d'Emma = couvert par témoin + audio
- **Suite** : dépôt DREETS **après** l'entretien ; jamais notifier avant autorisation inspecteur ; salaire dû depuis 01/07
- **Pilote** : Me El Mir (Capstan) réf 26.0231

C'est retrouvable dès demain via `jarvis-mem --grep "coste entretien"` ou au boot de session. Tu veux que je te prépare aussi le **SMS de confirmation à El Mir** (rien à faire signer / juste CR de fin) pour clôturer le point ?