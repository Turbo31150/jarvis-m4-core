[assistant] Deux atomes ont bougé **aujourd'hui** (20/07). Je charge le nouveau + les index clés.

[assistant] Le batch d'aujourd'hui = ré-indexation (même timestamp). Le **vrai nouveau contenu** date du 15-17/07. Je charge les index + Soufiane en entier.

[assistant] Contexte chargé (Postgres, atomes 12→16/07). Rien de neuf en base depuis le 16/07 — le batch de ce matin = simple ré-indexation. Donc le « nouveau » que tu as, c'est **toi** qui me l'apportes. Voici où on en est pour te caler direct :

## 🗂️ Soleil — Coste / Soufiane : état au 16/07

**3 procédures parallèles, à ne jamais mélanger :**

| Volet | Réf / instance | État |
|---|---|---|
| **Licenciement inaptitude** Emma Coste | Capstan El Mir 26.0231 · DREETS requis (protégée ~14/10) | Convocation entretien **envoyée 15/07** LRAR (87001429717077B). **Entretien lundi 27/07 10h** siège, tu conduis. Puis dépôt DREETS. |
| **CPAM / ITI** Emma | Dossier AT 250731346 · Bruniquel | Mail CPAM **envoyé 16/07** (clapas). NE PAS renvoyer formulaire ITI avant notif licenciement. Salaire L.1226-4 depuis 01/07 (paie normale). |
| **Prud'hommes** Emma | BCO 08/09 · Capstan Wacogne 26.0350 | Scénario **0€ validé cross-model** (board+Gemini) grâce aux 3 armes (feuilles de route effectif ~2h40/nuit, prescription, Emma seule). Verrou = qualifier les *trous* comme temps libre. |

## 🆕 Le 2ᵉ réclamant — SOUFIANE DRIOUECH

- **Identité** : Sofiane Driouech, ambulancier nuit. CDD 18/09/2024 → **CDI 18/12/2024**, ancienneté ~22 mois (courte). Binôme **Joshua Bernad** (CDI 2021). **Travaille encore** (≠ Emma en AT).
- **Même recommandé, même demande** qu'Emma (HS/nuit). Signalé par Aurélie le 15/07.
- **Défense réplicable** : même profil nuit → feuilles de route Joshua/Soufiane à dépouiller en symétriqu

[assistant] Je vais lire le mail clapas pour récupérer ce qu'Aurélie a scanné. Je repère d'abord la config IMAP.

[assistant] App-password clapas invalide (rotée/révoquée ?). Per l'atome, clapas est intégré dans **jarvis-mail** — je passe par là.

[assistant] Trois scans arrivés **ce matin 20/07** (uid 47179/47180/47181, scanner RNP583879). Je les ouvre et récupère les PJ.

[assistant] 1 dossier = 3 scans (pages/parties). Je dois télécharger les PJ. Je regarde comment jarvis-mail s'authentifie (mon login manuel a échoué mais l'outil marche) et s'il sait extraire les pièces jointes.

[assistant] jarvis-mail lit le texte mais pas les PJ. J'écris un fetch réutilisant l'auth de `manage-imap.py` (qui marche) pour sauver les PDF.

[assistant] Parfait, j'ai les 3 PDF (mêmes fichiers). Je les analyse — ce sont des scans, je vérifie s'ils ont une couche texte sinon OCR.

[assistant] 53 pages scannées, zéro couche texte → OCR nécessaire (tesseract fra). Je lance l'OCR des 3 dossiers en tâche de fond.

[assistant] OCR lancé en fond (53 pages, ~3-5 min). En attendant, voici ce que je sais et ce que je cherche dans ces PDF.

**Fichiers récupérés** (2 copies : mail clapas archivé + `~/Bureau/SOL-OPS/Soufiane-DRIOUECH/`) :
- `20260720095103830.pdf` — 15 pages
- `20260720095203581.pdf` — 18 pages
- `20260720095256311.pdf` — 20 pages
- **Total 53 pages**, scans images A4 paysage, sans couche texte → OCR fra en cours.

**Ce que je vais extraire pour cadrer la défense** (playbook réplique Emma) :
1. **Nature exacte** : requête prud'homale Soufiane Driouech ? Convocation greffe (BCO) ? Date de saisine + N° RG.
2. **Demandes chiffrées** : rappel HS travail de nuit, montant réclamé, période visée, éventuelle résiliation judiciaire / prise d'acte.
3. **Période réclamée** → test prescription L.3245-1 (ancienneté ~22 mois, CDD 18/09/2024 → CDI 18/12/2024).
4. **Moyens** identiques à Emma (accord modulation, décompte HS) → défense feuilles de route effectif faible réplicable.

Je te fais la synthèse dès que l'OCR sort. Je surveille.

[assistant] Dossier 1 = **la requête complète + convocation**. Données clés déjà là. J'extrais le dispositif complet (« PAR CES MOTIFS ») et j'attends l'OCR des pièces (dossiers 2-3).

[assistant] J'ai le gros du dispositif. Je récupère la fin (résiliation → art.700) et je vérifie l'OCR des pièces.

[assistant] Dispositif complet capté. Je calcule le total, je confirme l'avocat adverse vs Emma, et je checke les pièces.

[assistant] OCR terminé, tout capté. Je confirme l'avocat adverse d'Emma pour établir le copier-coller, puis je te livre la synthèse et je logue en mémoire (donnée → conteneur).

[assistant] Tout est capté et recoupé. **Point capital : c'est un copier-coller quasi mot pour mot de la requête Emma** (même avocat Me Deplaix — l'OCR dit *« l'employeur rémunérait **la salariée** »* au féminin dans une requête pour un homme). Je logue en mémoire puis je te livre la synthèse.

[assistant] L'INSERT n'a pas persisté (0 row). Je reprends via fichier pour éviter tout souci de quoting/encodage.

[assistant] A memory gate bloque l'écriture tant que je n'ai pas consulté la mémoire de session via ctx. Je le fais.

[assistant] Atome mémoire écrit (prio 9). Voici la synthèse complète.

---

# 🔴 Soufiane DRIOUECH — requête prud'homale reçue & analysée

**3 PDF scannés par Aurélie (53 pages)** récupérés dans la boîte clapas ce matin 09:51-09:52, OCR'd et analysés. Sauvés dans `~/Bureau/SOL-OPS/Soufiane-DRIOUECH/`.

## L'affaire
| | |
|---|---|
| **Juridiction** | CPH de **NÎMES** — N° affaire **2026-00150277** (réf 30220 Aigues-Mortes) |
| **Convocation datée** | 07/07/2026 |
| **Audience BCO (concil.)** | **mardi 29/09/2026 9h00** (Emma = 08/09, même CPH — 3 semaines après) |
| **Requérant** | Sofiane Driouech, né 01/08/1990 (Tétouan), domicilié **12100 Millau** (Aveyron) |
| **Avocat adverse** | **Me Guilhem DEPLAIX** (Cabinet Deplaix, Montpellier) — **LE MÊME QU'EMMA** |
| **Statut** | Travaille encore · ancienneté ~22 mois (CDD 18/09/24 → CDI, avenant 17/12/24) |

## 💰 14 chefs de demande — **TOTAL ≈ 102 049 €** (hors astreintes 150 €/j)
C'est **~3-4× la demande d'Emma** (~25-30k). Les gros postes :
- **Rappel HS nuit** : 18 480,80 € (+CP 1 848)
- **Travail dissimulé** : **24 306,30 €** (6 mois de salaire) ← le plus gros
- **Résiliation judiciaire** (torts employeur) : licenciement sans cause 12 300 + préavis 8 264 + CP 826 + indemnité 2 066
- Repos compensateur nuit 6 017 · repas/casse-croûte 4 269 · solde CP 4 132 · durées max / repos 2×5 000 · dimanches/fériés · exécution déloyale 5 000 · tenue 2 000 · art.700 2 500

## 🎯 Le point qui change tout : c'est un **copier-coller de la requête Emma**


[assistant] Je crée un Drive dédié « Prud'hommes Soufiane » sur le même modèle que celui d'Emma, et j'y pousse les 3 PDF. Je regarde d'abord l'outil rclone/Drive utilisé pour Emma.

[assistant] Structure comprise : les 3 Drives Emma (CSE/Licenciement/Prud'hommes) vivent sous le Shared Drive parent `0AGL3egmwvVIOUk9PVA`. Je crée un nouveau dossier Soufiane à côté. D'abord je probe le parent (probe-first).

[assistant] Convention de nommage claire (`CONTENTIEUX-COSTE-CPH-NIMES-2026-00128332`). Je crée le pendant Soufiane et j'uploade les 3 PDF renommés proprement.

[assistant] Dossier créé : `1hjJxNXwpNjO5smXPKpm4EWAHcnqogDfj`. Je vérifie le contenu des dossiers 2 et 3 pour les nommer correctement avant upload.

[assistant] Les 3 scans = **une seule requête de 53 pages** découpée en 3 (convocation+dispositif / discussion / résiliation). Je les uploade renommés en parties.

[assistant] ✅ Les 3 fichiers sont déposés et vérifiés. Je consigne le folder-id du Drive dans la mémoire.

[assistant] ✅ **Drive Prud'hommes Soufiane créé et rempli.**

## 📁 `CONTENTIEUX-DRIOUECH-CPH-NIMES-2026-00150277`
Créé sous le Shared Drive Soleil (parent `0AGL3egmwvVIOUk9PVA`), à côté du Drive contentieux Emma — **même convention de nommage**.

🔗 https://drive.google.com/drive/folders/1hjJxNXwpNjO5smXPKpm4EWAHcnqogDfj

| Fichier | Contenu | Taille |
|---|---|---|
| `01-REQUETE-DRIOUECH-...-convocation-BCO-29092026-p1sur3.pdf` | Convocation greffe + dispositif (14 chefs, ~102k€) + début discussion (HS) | 15 p |
| `02-REQUETE-DRIOUECH-discussion-p2sur3.pdf` | Discussion (durées max, repos, majorations…) | 18 p |
| `03-REQUETE-DRIOUECH-resiliation-pieces-p3sur3.pdf` | Résiliation judiciaire + pièces | 20 p |

- **Statut partage** : 🔒 **privé** (owner rem.invest34) — je ne l'ai **pas** ouvert en anyone-with-link. Pour Emma, l'atome signalait justement le risque du lien racine qui expose la note-armée. Ici il n'y a que la requête adverse, mais je te laisse décider du partage (El Mir).
- Copies locales conservées dans `~/Bureau/SOL-OPS/Soufiane-DRIOUECH/` + OCR texte dans `/ocr`.
- Folder-id consigné en mémoire (atom Soufiane, prio 9).

**Prochaine étape** — dis-moi laquelle je lance :
1. **Partager le Drive avec El Mir** (lien reader) + te préparer le **mail Capstan** (tu valides avant envoi)
2. **Note de défense chiffrée** chef par chef (façon note-armée Emma, les 14 chefs → exposition réelle)
3. **Récupérer les feuilles de route Soufiane/Joshua** pour le dépouillage symétrique

[user] '/home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/Bulletins 2024.pdf' '/home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/Bulletins 2025.pdf' '/home/rempc/Bureau/SOL-OPS/Soufiane-DRIOUECH/Bulletins 2026.pdf' outes les salaires

[assistant] Tes bulletins de salaire Soufiane (2024/2025/2026) — pièce maîtresse pour contrer les HS + le travail dissimulé (« payé transparent »). Je les ajoute au Drive et je vérifie s'ils sont exploitables (texte vs scan).

[assistant] Bulletins avec couche texte (pas besoin d'OCR). Je les uploade au Drive puis j'extrais les données de paie.

[assistant] 6 pièces au Drive. J'extrais maintenant les données de paie (couche texte OK) — je traite en sandbox et ne remonte que le tableau utile pour la défense.

[assistant] **Trouvé l'arme #1** dans les bulletins : la ligne *« Majoration (nuit, dimanche, férié) mensualisé 175.94 »* apparaît **explicitement sur le bulletin** → paie transparente = ça tue le chef *travail dissimulé* (24k, intention impossible à prouver) ET prouve que la majoration nuit/dim/férié **était payée**.

Maintenant tes contrats. Je les cherche dans le dossier cession Soleil (data-room) et dans le mail clapas.

[assistant] CDI trouvé sur disque. Il manque le/les CDD (Pièces 1-2 de la requête). Je regarde le résultat du find complet + le mail clapas.

[assistant] Sur disque je n'ai que le **CDI** (18/12/2024). Les 2 CDD (Pièces 1-2 requête, sept 2024) n'y sont pas. Je vérifie la structure data-room avant de conclure.

[assistant] Fait. Voici le point complet.

## 📁 Drive Soufiane — 7 pièces maintenant

🔗 https://drive.google.com/drive/folders/1hjJxNXwpNjO5smXPKpm4EWAHcnqogDfj

| # | Pièce |
|---|---|
| 01-03 | Requête prud'homale (53 p, 3 parties) |
| 04-06 | Bulletins salaire 2024 / 2025 / 2026 |
| 07 | **CDI 18/12/2024** |

## 💥 Ce que les bulletins révèlent (arme de défense)

- **Ligne « Majoration (nuit, dimanche, férié) mensualisé » = 175,94 €/mois**, **visible sur le bulletin**.
  → **Tue le chef travail dissimulé (24 306 €)** : majorations payées **en toute transparence** = zéro élément intentionnel de dissimulation.
  → C'est exactement la déduction de **4 324,42 €** que l'adversaire concède lui-même (12 mois × ~175,94 ≈ ça).
- **Salaire de base 1 766,96 €** (= exactement le montant contractuel cité dans la requête) → cohérence, pas de sous-paiement.
- **Net évolution** : 1 656 € (2024, mois partiels + précarité) → **2 389 €** (2025) → **2 388 €** (2026). Stable.
- L'argument adverse *« rémunéré sur une indemnité de 150 € au lieu du taux horaire »* est **factuellement contredit** par la ligne majoration mensualisée du bulletin.

## ⚠️ Contrats — état réel
- ✅ **CDI 18/12/2024** : sur disque (data-room), uploadé.
- ❌ **Les 2 CDD (sept 2024, Pièces 1-2 requête) + avenant 17/12/2024** : **introuvables sur disque** (dossier data-room ne contient que « CDI actifs », pas de CDD archivé) et pas retrouvés en pièce jointe clapas.

Deux sources propres possibles pour les CDD manquants :
1. **Silae** (lo

[assistant] Trouvé. Les CDD sont dans les fils Bonniol :
- **CDD 1** (terme 31/07/2024) → uid 35894/35903 (7 mai 2024)
- **CDD 2** (terme 17/12/2024) → uid 38090/38107 (18-19 sept 2024)
- **Avenant CDI 17/12/2024** → uid 40001 (27 déc 2024)

Je télécharge les PJ de ces mails.

[assistant] Les 3 contrats récupérés (les 2 CDD + l'avenant CDI). Note : l'avenant = exactement le fichier « CDI 18-12-2024 » déjà uploadé (#07, même taille 141775b). J'uploade les 2 CDD manquants et je nettoie le bruit (logos/signatures png).

[assistant] Complet. Je consigne tout en mémoire (contrats + trouvaille bulletins + point d'ancienneté).

[assistant] ✅ **Drive Soufiane complet — 9 pièces, dossier prêt.**

🔗 https://drive.google.com/drive/folders/1hjJxNXwpNjO5smXPKpm4EWAHcnqogDfj

| # | Pièce | Source |
|---|---|---|
| 01-03 | Requête prud'homale (53 p) | mail clapas |
| 04-06 | Bulletins salaire 2024 / 2025 / 2026 | Bureau |
| 07 | Avenant → CDI 18/12/2024 | data-room |
| **08** | **CDD 1 : 01/05 → 31/07/2024** | **mail soleil (Bonniol, uid 35903)** |
| **09** | **CDD 2 : 18/09 → 17/12/2024** | **mail soleil (Bonniol, uid 38107)** |

## 🎯 Deux munitions sorties du travail pendant la collecte

**1. Les bulletins tuent le travail dissimulé (24 306 €)**
La ligne *« Majoration (nuit, dimanche, férié) mensualisé — 175,94 € »* figure **noir sur blanc sur le bulletin** → payé en transparence, **zéro élément intentionnel** de dissimulation (condition sine qua non du chef). Et ça correspond à la déduction de 4 324,42 € que l'avocat concède lui-même. Leur phrase *« rémunéré sur une indemnité de 150 € au lieu du taux horaire »* est factuellement fausse.

**2. L'ancienneté n'est PAS continue** ⭐
- CDD1 finit **31/07/2024** → CDD2 démarre **18/09/2024** = **~7 semaines de trou** (avec solde de tout compte juillet 2024, que la requête produit en Pièce 22).
- Donc pas de continuité → **barème Macron encore plus bas** que les ~22 mois supposés, et l'indemnité de licenciement (2 066 €) / préavis (8 264 €) réclamés dans le package résiliation judiciaire s'en trouvent fragilisés.

Tout est consigné en mémoire (atome Soufiane, 5 555 car., pr

[assistant] Bien vu — je te monte une vraie arborescence de dossier juridique et je range les 9 PDF dedans (au lieu du vrac). Je probe d'abord les noms exacts puis je réorganise.

[assistant] « Fais comme avec Coste » — je calque la structure du Drive contentieux Emma. Je l'inspecte d'abord.

[assistant] Structure Emma comprise. Je réplique la même logique pour Soufiane (adverse / contrats+bulletins / pièces employeur / confidentiel) et je range les 9 PDF.

[assistant] Rangé. Je crée maintenant le sommaire « COMMENCER ICI » (comme Emma) et je vérifie l'arbo finale.

[assistant] I create a proper `00-SOMMAIRE-ET-BORDEREAU.pdf` like Emma's. Let me write it as HTML → PDF (clean rendering).

[assistant] ✅ **Drive Soufiane restructuré à l'identique du dossier Coste.** Je consigne la structure finale en mémoire.

[assistant] ✅ **Drive contentieux Soufiane — vraie arborescence, calquée sur le dossier Coste.**

🔗 https://drive.google.com/drive/folders/1hjJxNXwpNjO5smXPKpm4EWAHcnqogDfj

```
📁 00 - COMMENCER ICI (sommaire)
   📄 00-SOMMAIRE-ET-BORDEREAU.pdf   ← généré (repères + bordereau + 14 chefs + axes défense)
📁 01 - DEMANDE ADVERSE (requete + convocation)
   📄 requête p1/3 (convocation + dispositif)
   📄 requête p2/3 (discussion)
   📄 requête p3/3 (résiliation + pièces)
📁 02 - Pieces 1-3 - Contrats (CDD + avenant CDI)
   📄 Piece1-CDD-01052024-31072024.pdf
   📄 Piece2-CDD-18092024-17122024.pdf
   📄 Piece3-Avenant-CDI-18122024.pdf
📁 03 - Piece 4 - Bulletins de salaire
   📄 Bulletins-2024 / 2025 / 2026.pdf
📁 04 - PIECES EMPLOYEUR (defense)      ← vide (feuilles de route Driouech/Bernad à réunir)
📁 05 - CONFIDENTIEL CONSEIL - NE PAS COMMUNIQUER   ← vide (note-armée à venir)
```

- **Même logique que le Drive Emma** : 00 sommaire / 01 demande adverse / 02-03 pièces contractuelles / 04 pièces employeur / 05 confidentiel conseil.
- **Sommaire-bordereau PDF** en tête : repères de l'affaire (CPH Nîmes, BCO 29/09, Me Deplaix), bordereau des 6 dossiers, tableau des **14 chefs (~102 k€)**, et les 3 axes de défense (bulletins → travail dissimulé mort, ancienneté fragmentée, HS réplicable Coste).
- 🔒 Toujours **privé** (owner rem.invest34), pas de partage lien.
- Structure consignée en mémoire (atome Soufiane).

Il reste 2 dossiers vides à remplir (**04 pièces employeur** = feuilles de route Driouech/Bernad ·

[user] 1 en dernier  on attend aurelie  qui scanne feuille de route , on peut deja faire 1 mail capstan pour 1 informer de ce nouveau fait 2 savoir si ok pour prendre en cherge ce  2 eme dossier et lui dire copier coller du 1er a tel point qu il a mi au feminin , prepare mail capstan adan sle fil prudhom demande demande lui si on distingue les 2 dossier  en parallele ou ensemble vu que c ets les meme mais pas les meme dates , tu lui met en pj la demande de saisine et le lien drive

[assistant] Compris. Règle stricte : **je prépare le brouillon, zéro envoi auto** — tu valides le contenu exact avant. D'abord je retrouve le fil prud'hommes Capstan (bon destinataire + message pour répondre dedans).

[assistant] Le fil prud'hommes = **« 26.0350 - AMBULANCE DU SOLEIL c/ Emma COSTE »**, géré par **Me Karine WACOGNE** + **Me Anne-Laure PERIES**. Je lis le dernier message du fil pour récupérer destinataires exacts + headers de réponse.

[assistant] J'ai tout : le fil **26.0350** (To: Wacogne · Cc: Périès, El Mir, Massiave). Je prépare (1) la requête fusionnée+compressée pour la PJ (les 3 scans font 32 Mo > limite Gmail 25 Mo), et (2) le brouillon. **Aucun envoi — tu valideras le texte exact d'abord.**

[assistant] Requête fusionnée+compressée : **9,4 Mo, 53 p** (passe sous la limite Gmail). Voici le brouillon complet — **rien n'est envoyé**, je te le soumets pour validation.

[assistant] # 📧 Brouillon mail Capstan — à valider avant envoi

**Logistique de l'envoi :**
| | |
|---|---|
| **Fil** | RE: **26.0350 - AMBULANCE DU SOLEIL c/ Emma COSTE** (reste dans le fil prud'hommes, comme demandé) |
| **De** | rem.invest34@gmail.com |
| **À** | Me Karine WACOGNE `KWACOGNE@capstan.fr` |
| **Cc** | Me Anne-Laure PERIES `alperies@capstan.fr` · Me Lina EL MIR `LELMIR@Capstan.fr` · Me Stéphanie MASSIAVE `SMASSIAVE@Capstan.fr` |
| **PJ** | `REQUETE-DRIOUECH-complete.pdf` (53 p, 9,4 Mo) |

---

**Corps :**

> Maître,
>
> Je reviens vers vous dans le dossier prud'homal Ambulance du Soleil pour vous signaler un fait nouveau.
>
> Nous venons de recevoir, par le greffe, une seconde requête prud'homale dirigée contre la SARL Ambulance du Soleil, à la requête cette fois de Monsieur Sofiane DRIOUECH, ambulancier de nuit — il travaille sur l'autre binôme de l'équipe de nuit, dans une configuration en tout point comparable à celle de Madame COSTE.
>
> Les éléments de la convocation :
> - Conseil de Prud'hommes de Nîmes — N° d'affaire 2026-00150277
> - Audience du bureau de conciliation et d'orientation : mardi 29 septembre 2026 à 9h00
> - Avocat du demandeur : Maître Guilhem DEPLAIX — le même conseil que celui de Madame COSTE
>
> Point notable : la requête de Monsieur DRIOUECH est un quasi copier-coller de celle de Madame COSTE — mêmes chefs de demande (rappel d'heures supplémentaires de nuit, majorations, travail dissimulé, résiliation judiciaire), même argumentaire. La reprise es

[user] avant le go rajoute que le salarie est toujours en activite quelle attitude a tenir ? ( ou on attend peut etre la confirmation qu elle prend en charge le dossier? ) une ca traite ok

[assistant] Je fais deux choses : (1) j'ajoute la 4ᵉ question (salarié toujours en poste), (2) tu m'as validé le partage Drive (« 1 ça traite ok ») → je partage en lecture aux 4 adresses Capstan. Puis tu me donnes le go final pour l'envoi.

D'abord la 4ᵉ question dans le brouillon :

[assistant] Maintenant le partage Drive. Je récupère le token rclone (compte rem.invest34) et j'ajoute les 4 avocats Capstan en lecture via l'API Drive.

[assistant] **Blocage partage** : les adresses Capstan **n'ont pas de compte Google** → impossible de partager en lecture nominative. Le seul mécanisme qui marche (celui utilisé pour le Drive Emma) = **« toute personne disposant du lien » en lecture**.

C'est un partage par **lien public obscur** (moins contrôlé que du nominatif). Vu que le dossier `05 - CONFIDENTIEL CONSEIL` accueillera notre stratégie, je propose la parade suivante avant d'activer le lien :

- ✅ Activer **lien public lecture** sur le dossier (nécessaire pour que Capstan ouvre)
- 🛡️ **Sortir le confidentiel du périmètre partagé** : je supprime le sous-dossier `05 - CONFIDENTIEL CONSEIL` de ce Drive et je garde la note de défense **en local uniquement** (jamais dans l'arbo partagée). Comme ça le lien n'expose que des pièces communicables (requête adverse + contrats + bulletins).

**Le brouillon est prêt avec ta 4ᵉ question ajoutée.** Voici les 4 questions finales :

> 1. Confirmez-vous la prise en charge de ce second dossier par votre cabinet ?
> 2. …mener les deux procédures en parallèle (dossiers distincts) ou les traiter ensemble ?
> 3. Quelles pièces/diligences immédiates attendez-vous ? (feuilles de route en cours de récupération)
> 4. **Monsieur DRIOUECH est toujours en activité au sein de l'entreprise. Quelle attitude devons-nous adopter à son égard dans la gestion quotidienne (planning, organisation du travail) dans l'attente de l'audience, afin de ne pas nous exposer à un grief supplémentaire ? Devons-nous nous 

[assistant] Go. J'exécute : (1) sortir le confidentiel, (2) activer le lien lecture, (3) préparer et envoyer le mail dans le fil.

[assistant] Drive OK (confidentiel sorti, lien lecture actif). Maintenant l'envoi — je vérifie que l'outil gère PJ + Cc + réponse dans le fil.

[assistant] Outil parfait (PJ + Cc + In-Reply-To supportés). Je récupère le Message-ID du fil pour répondre dedans, puis **dry-run** de contrôle.

[assistant] ✅ **Envoyé — dossier Soufiane bouclé pour aujourd'hui.**

## Récap de ce qui vient de partir
**Mail Capstan** (fil prud'hommes 26.0350, depuis rem.invest34) :
- **À** : Me Wacogne · **Cc** : Me Périès, Me El Mir, Me Massiave
- **PJ** : requête complète 53 p (9,4 Mo)
- **4 questions** posées, dont ta n°4 (salarié toujours en activité → quelle attitude / statu quo jusqu'à confirmation de prise en charge)
- **Lien Drive** inclus (lecture publique activée — Capstan n'a pas de compte Google, le nominatif était impossible)

## Sécurité appliquée
- 🛡️ Dossier `05 - CONFIDENTIEL CONSEIL` **retiré de l'arbo partagée** → le lien public n'expose que du communicable (requête adverse + contrats + bulletins). **La note de défense restera en local**, jamais dans le Drive partagé.

## Drive final partagé
```
00 - COMMENCER ICI (sommaire + bordereau + 14 chefs)
01 - DEMANDE ADVERSE (requête 3 parties)
02 - Pièces 1-3 - Contrats (2 CDD + avenant CDI)
03 - Pièce 4 - Bulletins 2024/25/26
04 - PIECES EMPLOYEUR (defense) ← vide, en attente feuilles de route Aurélie
```

## Ce qu'on attend
1. **Réponse Capstan** (prise en charge + parallèle/joint + attitude vis-à-vis de Soufiane)
2. **Aurélie** scanne les **feuilles de route** → j'alimenterai `04 - PIECES EMPLOYEUR`
3. Ensuite : **note de défense chiffrée** chef par chef (en local, dossier confidentiel)

Tout est consigné en mémoire (atome Soufiane). Rien d'autre à faire côté toi pour l'instant — on est en attente de leur retour.

[assistant] La réponse auto de Wacogne redirige vers **alperies@ · smassiave@ · lelmir@** — **les trois sont déjà en Cc de ton mail**. Donc les bonnes personnes l'ont déjà reçu, avec la requête et le lien Drive. Rien n'est perdu.

**Rappel du partage des rôles** (dit par Wacogne le 25/06) : Me **PERIES** reprend la partie **conseil**, Me **MASSIAVE** la partie **judiciaire**, Me **EL MIR** part bientôt en congé maternité.

Un bémol : ils l'ont en **Cc**, pas en **À** → risque que personne ne se l'attribue franchement, surtout avec l'absence de Wacogne (la « boîte d'entrée » du dossier).

**Ma reco** : un court mail de relance, cette fois avec **Me PERIES en À** (elle pilote le conseil = c'est elle qui tranche la prise en charge), Cc Massiave + El Mir. Message bref du type :

> Maître,
> Me Wacogne étant absente, je me permets de vous adresser directement le message ci-dessous, relatif à une seconde requête prud'homale (M. Sofiane DRIOUECH) reçue ce jour. Je reste à votre disposition pour en échanger.
> *(+ le corps déjà rédigé en rappel, ou juste le renvoi du fil)*

Tu veux que je **prépare ce mail de relance à Périès** (même fil 26.0350, requête déjà en PJ ou non, lien Drive) ? Je te le soumets en brouillon et **je n'envoie qu'après ton go**. Ou on **laisse tel quel** et on attend qu'un des trois réagisse ?

[assistant] Je prépare la relance à Me Périès. Voici le brouillon exact — **je n'envoie qu'après ton go** (comme convenu).

[assistant] # 📧 Relance à Me PERIES — prête (dry-run OK)

| | |
|---|---|
| **Fil** | RE: 26.0350 - AMBULANCE DU SOLEIL c/ Emma COSTE (même conversation) |
| **À** | Me Anne-Laure **PERIES** `alperies@capstan.fr` *(elle pilote le conseil)* |
| **Cc** | Me Massiave · Me El Mir |
| **PJ** | aucune (requête déjà jointe au mail de ce matin + lien Drive) |

**Corps :**

> Maître,
>
> Me Wacogne étant absente (sa réponse automatique me renvoyant vers vous), je me permets de vous adresser directement ce dossier.
>
> Nous avons reçu ce jour une seconde requête prud'homale dirigée contre la SARL Ambulance du Soleil, à la requête de Monsieur Sofiane DRIOUECH, ambulancier de nuit, dans une configuration comparable à celle de Madame COSTE. Elle émane du même conseil (Maître Guilhem DEPLAIX) et reprend quasi mot pour mot la requête de Madame COSTE — au point qu'un passage vise encore « la salariée » au féminin, alors que le demandeur est un homme. Le montant total réclamé s'élève à environ 102 000 €.
>
> - Conseil de Prud'hommes de Nîmes — N° d'affaire 2026-00150277
> - Audience du bureau de conciliation et d'orientation : mardi 29 septembre 2026 à 9h00
>
> Mes questions figurent dans mon message de ce jour, que vous avez reçu en copie :
> 1. …prise en charge de ce second dossier ?
> 2. …parallèle (dossiers distincts) ou ensemble ?
> 3. …pièces / diligences immédiates ? (feuilles de route en cours)
> 4. …M. DRIOUECH toujours en activité : quelle attitude / statu quo jusqu'à confirmation ?
>
> La requ

[assistant] ✅ **Relance envoyée à Me PERIES** (Cc Massiave + El Mir), dans le fil 26.0350. Contournement de l'absence de Wacogne réglé — la décideuse conseil a maintenant le dossier en direct.

## État du dossier Soufiane — clôture de session
| Volet | État |
|---|---|
| Requête reçue + analysée | ✅ (CPH Nîmes, BCO 29/09, ~102k€, copier-coller Emma) |
| Drive contentieux structuré | ✅ 4 dossiers, sommaire-bordereau, lien lecture actif |
| Pièces réunies | ✅ requête + 2 CDD + avenant CDI + bulletins |
| Mail Capstan (Wacogne + 3 en Cc) | ✅ envoyé ce matin |
| Relance Me Périès (Wacogne absente) | ✅ envoyée |
| Munitions défense repérées | ✅ travail dissimulé mort (majoration sur bulletin) + ancienneté fragmentée |

## En attente (rien à faire de ton côté)
1. **Réponse Périès/Massiave** → prise en charge + parallèle/joint + attitude vis-à-vis de Soufiane
2. **Aurélie** → scan des **feuilles de route** → j'alimenterai `04 - PIECES EMPLOYEUR`
3. Ensuite → **note de défense chiffrée** (en local, hors Drive partagé)

Tout est consigné en mémoire. Dès qu'un des deux (réponse Capstan **ou** feuilles de route) arrive, tu me le signales et j'enchaîne.

[assistant] Parfait. On est en attente sur deux fronts :

1. **Réponse Capstan** (Me Périès / Massiave) — prise en charge, parallèle vs joint, attitude vis-à-vis de Soufiane
2. **Feuilles de route** scannées par Aurélie → dossier `04 - PIECES EMPLOYEUR`

Tout est en place et consigné en mémoire (atome Soufiane). Dès qu'un retour tombe, tu me le signales et j'enchaîne — note de défense chiffrée, alimentation du Drive, ou réponse à Capstan selon ce qui arrive.

Bon, je lâche l'affaire. 👍

[assistant] Oui, c'est le bon move. Deux raisons :

1. **Contexte propre** — on est là en mode « défense prud'hommes ». Le mail Bastien, c'est l'angle **cession/GAP** (disclosure du litige à l'acquéreur), un cadre mémoire différent (Brière séquestre, principe GAP, closing). Une session neuve chargera le bon dossier (`atom_INDEX_cession_soleil` + principe GAP) sans traîner le bruit prud'hommes.

2. **Tout est déjà persistté** — l'atome Soufiane (prio 9) contient ce que la nouvelle session doit reprendre. Elle le retrouvera via le pré-flight mémoire.

**Point d'ancrage pour la nouvelle session** (le cœur du mail Bastien) :
- Soufiane DRIOUECH = **2ᵉ litige social pré-cession** (après Emma) → **disclosure obligatoire** à l'acquéreur (bonne foi anti-dol), **closing PAS fait** (crédit CA Languedoc en cours) = disclosure **pré-closing**, pas activation GAP.
- Traitement = **dans la GAP bornée** (plafond 123k / franchise 10k, garant **Holding La Lironde**), **jamais** de carve-out perso — principe déjà tranché le 15/07.
- À cadrer avec **Brière (cession)** + **Nordine** + **El Mir (droit social)** ; question de nego : carve-out nommé vs GAP générale vs provision dédiée.

Quand tu ouvres la nouvelle session, lance simplement : *« charge le dossier cession, on prépare le mail Bastien pour disclosure Soufiane »* — et je repars du bon pied.

On se retrouve là-bas. 👍

[user] derniere question est ce que lettre temoignage 1 julie regulatrice c est elle qui envoie les heures gere les contrats et communicaation avec bonniol 2 aurelie elle qui facture et qui a le feuilles de routes 3 layla ancienne salarie de nuit qui a etait binome emma quelque temps elle peut me faire un lettre qu on peut lui rediger elle l ecris manuscris

[assistant] Bonne question — et elle tombe pile dans le dossier défense. Réponse cash sur les 3, avec le piège à éviter.

## Les 3 témoins — valeur réelle

| Témoin | Ce qu'elle peut attester | Poids |
|---|---|---|
| **Julie** (régulatrice — plannings, heures, contrats, lien Bonniol) | L'**organisation réelle** des nuits, le suivi/paiement des heures, le régime d'équivalence, comment les HS étaient gérées → frappe au cœur du rappel d'HS | 🟠 Fort sur le fond **mais salariée en poste** = lien de subordination → l'adverse plaidera la pression |
| **Aurélie** (facturation, détient les feuilles de route) | La **réalité de l'activité de nuit** (peu de courses, gros trous), + elle **authentifie les feuilles de route** comme pièces | 🟠 Utile mais idem : salariée actuelle |
| **Layla** (ex-nuit, **ex-binôme d'Emma**) | Le vécu des vacations : grande amplitude mais **temps effectif faible, permanence/inaction entre les courses, possibilité de se reposer/vaquer** → détruit l'argument « temps de travail effectif » | 🟢 **La meilleure** : ancienne salariée = **zéro subordination**, crédibilité maximale. Et vaut pour **Emma ET Soufiane** |

**Layla est la pièce maîtresse.** Une ex-collègue de nuit qui dit « on avait de longs trous, on pouvait se reposer », c'est ce qui fait basculer le dossier vers le 0.

## ⚠️ Le piège à ne PAS faire

Une attestation, c'est **l'article 202 CPC** : **manuscrite de la main du témoin**, datée/signée, avec la mention manuscrite qu'elle est produite en justice et que le f

[assistant] Nickel. Je note les 3 témoins et le report en mémoire pour ne rien perdre, et je te laisse appeler Capstan.

[assistant] C'est noté en mémoire (3 témoins + caveat art. 202 + report « on voit ça plus tard, tu appelles Capstan »).

**Récap session Soufiane — tout est bouclé et persisté :**
- ✅ Requête reçue, analysée, Drive structuré, pièces réunies
- ✅ Mail Capstan + relance Périès envoyés
- 🕓 En attente : réponse Capstan · feuilles de route Aurélie · attestations (après ton appel)
- ➡️ Cession/mail Bastien → **nouvelle session** quand tu veux

Bon appel à Capstan. On se retrouve pour la cession. 👍

[assistant] Protocole sauvegarde déclenché — je charge la règle exacte et je l'applique (sûr à 100%, chaque écriture vérifiée par SELECT, souvenir du post-mortem faux-save).

[assistant] Règle chargée. J'applique les 6 étapes. D'abord l'atome INDEX de reprise (point d'entrée unique), écrit via fichier pour éviter tout souci de quoting.

[assistant] Les 2 atomes persistent (INDEX 3278 car., détail 8628 car.). Vérif par `jarvis-mem --grep`, puis backup off-site.

[assistant] Push successful. **Étape 6 — preuve du backup** : je grep les ids des atomes dans le dump poussé (pas de claim non vérifié).

[assistant] ✅ **Protocole sauvegarde exécuté — les 6 étapes vérifiées, zéro claim non prouvé.**

| Étape | Résultat |
|---|---|
| 1. Atomes Postgres | ✅ `atom_soufiane_requete_recue_analyse_20260720` (8628 car.) |
| 2. Atome INDEX reprise | ✅ `atom_INDEX_soufiane_prudhommes_20260720` (3278 car., prio 9) créé |
| 3. Vérif persistance | ✅ SELECT OK + `jarvis-mem --grep DRIOUECH` retrouve les 2 |
| 4. SQLite | ✅ N/A (memory_atoms = Postgres-only, pas un trou) |
| 5. Backup off-site GitHub | ✅ **Push successful** (commit f88f217, 465 MB) |
| 6. Preuve du backup | ✅ ids présents dans le dump poussé (détail ×2, INDEX ×1) |

**Point de reprise unique** pour la prochaine fois : `atom_INDEX_soufiane_prudhommes_20260720` — il contient tout (affaire, munitions défense, Drive, mails envoyés + threading, état/attente, disclosure cession Bastien, témoins à voir).

Session Soufiane sauvegardée et fermée proprement. Tu peux ouvrir la session cession quand tu veux. 👍

[user] maintenant il faudrait faire le mail a bastien aussi un nouveau fil pour le mettre au courant pour soufian

[assistant] On enchaîne sur le mail Bastien. Je charge le contexte cession (Brière, GAP, statut disclosure Emma) avant de rédiger — nouveau fil, et **rien envoyé sans ton go**.

[assistant] Contexte cession chargé. Brière = `bb@briere-avocat.fr` (Me Bastian Brière). Cadre : Soufiane = litige social **pré-cession** → à intégrer à la **GAP bornée** (garant Holding La Lironde), comme Emma/Abello — closing pas encore réitéré. Voici le brouillon (nouveau fil) :

[assistant] Compris — **rien n'envoyé** (juste un dry-run, aucun mail parti). J'annule.

Le mail Bastien Brière = **dossier cession** → on le fera dans la **session cession dédiée**, comme prévu. Pas ici.

- ✅ Aucun envoi
- 📄 Brouillon **conservé** pour la session cession : `~/Bureau/SOL-OPS/Soufiane-DRIOUECH/DRAFT-mail-briere-cession-soufiane.txt` (tu le retrouveras, ou je le régénère là-bas)
- 🧠 L'atome INDEX Soufiane note déjà : *disclosure cession = mail Bastien Brière à faire en session cession*

Donc côté **cette session** (défense prud'hommes), on reste sur : attente réponse Capstan + feuilles de route Aurélie. Le volet cession (Brière, GAP, disclosure) → nouvelle session quand tu l'ouvres.

Rien d'autre à faire. 👍

[user] me suis trompe bastien dans autre session donc annule et remplace ca maintenant il faudrait faire le mail a bastien aussi un nouveau fil pour le mettre au courant pour soufian  par maintenant il faudrait faire le mail aadrien social bonniol  aussi un nouveau fil pour le mettre au courant pour soufian

[assistant] Clair : le mail Bastien = **annulé ici** (il reste pour la session cession, rien envoyé). **Maintenant → mail à Adrien FADAT (Bonniol social)**, nouveau fil, pour l'informer de Soufiane.

Je confirme l'adresse d'Adrien + le compte d'envoi habituel (clapas pour Bonniol), et je teste que l'envoi clapas fonctionne.

[assistant] Adrien FADAT = **adrien.fadat@bonniolconseil.fr** · inbox équipe = **social.montpellier@bonniolconseil.fr** (convention : To Social Montpellier, Cc Adrien). Expéditeur habituel Bonniol = **clapas**. Je teste que l'envoi clapas fonctionne (mon login manuel avait échoué plus tôt).

[assistant] clapas SMTP OK (le fail manuel de tout à l'heure était un artefact). Voici le brouillon Adrien — nouveau fil, **rien envoyé avant ton go** :

[assistant] # 📧 Mail Adrien FADAT (Bonniol social) — nouveau fil, prêt (dry-run OK)

| | |
|---|---|
| **De** | Rémi TENA `<ambulanceclapas@gmail.com>` *(compte habituel pour Bonniol)* |
| **À** | `social.montpellier@bonniolconseil.fr` |
| **Cc** | Adrien FADAT `adrien.fadat@bonniolconseil.fr` |
| **Objet** | SARL Ambulance du Soleil — nouvelle requête prud'homale (M. Sofiane DRIOUECH) — information |
| **PJ** | requête complète 53 p (9,4 Mo) |
| **Fil** | **nouveau** (pas de threading) |

**Corps :**

> Bonjour Adrien,
>
> Je vous informe d'un fait nouveau concernant la SARL Ambulance du Soleil.
>
> Nous avons reçu ce jour une seconde requête prud'homale, à la requête de Monsieur Sofiane DRIOUECH, ambulancier de nuit — même profil que Madame Emma COSTE, sur l'autre binôme de l'équipe de nuit. Elle émane du même avocat que celui de Madame COSTE (Maître Guilhem DEPLAIX) et en reprend quasiment mot pour mot le contenu (un passage vise d'ailleurs encore « la salariée » au féminin, alors que le demandeur est un homme).
>
> - Conseil de Prud'hommes de Nîmes — N° 2026-00150277
> - Audience de conciliation : 29 septembre 2026
> - Montant total réclamé : environ 102 000 €
>
> Les demandes portent en grande partie sur des éléments de paie : rappel d'HS de nuit, majorations (nuit, dimanches, fériés), travail dissimulé, rappels de CP, casse-croûte et repas, régularisation organismes.
>
> Je souhaitais vous en informer… et recueillir votre avis sur deux points :
> 1. Confirmez-vous que les bulletins

[assistant] Ok : je retire la question 1 (déjà vue) et je remplace la PJ par **la convocation prud'homale** seule. Je repère les pages de la convocation dans le scan.

[assistant] Convocation greffe = **pages 1-3** (p4 = courrier avocat, p5+ = requête). J'extrais la convocation seule.

[assistant] Convocation extraite (3 p, 768 Ko). Je corrige le brouillon : suppression de la question 1, PJ = convocation.

[assistant] # 📧 Mail Adrien FADAT — corrigé (dry-run OK)

| | |
|---|---|
| **De** | Rémi TENA `<ambulanceclapas@gmail.com>` |
| **À** | `social.montpellier@bonniolconseil.fr` |
| **Cc** | Adrien FADAT `adrien.fadat@bonniolconseil.fr` |
| **Objet** | SARL Ambulance du Soleil — nouvelle requête prud'homale (M. Sofiane DRIOUECH) — information |
| **PJ** | ✏️ **CONVOCATION** prud'homale (3 p) — *plus la requête complète* |
| **Fil** | nouveau |

**Modifs appliquées :**
- ❌ Question 1 (confirmation paie/majorations) **retirée** — déjà vue
- ✅ Reste **une seule question** : point paie/DSN à sécuriser (salarié toujours en poste)
- ✅ PJ = **convocation** (pages 1-3 du greffe CPH Nîmes) au lieu de la requête 53 p

Le corps final est affiché ci-dessus.

**Tu confirmes l'envoi ?** (« go » / « envoie ») — ou autre correction.

[assistant] ✅ **Envoyé à Adrien.** Je consigne en mémoire et je sauve la convocation extraite.

[assistant] ✅ **Mail Adrien FADAT (Bonniol social) envoyé** — nouveau fil, convocation en PJ, question paie/DSN. Consigné en mémoire.

## Point de situation — communications Soufiane
| Destinataire | Angle | État |
|---|---|---|
| **Capstan** (Wacogne + Cc) | Défense judiciaire | ✅ envoyé ce matin |
| **Me Périès** (relance, Wacogne absente) | Défense judiciaire | ✅ envoyé |
| **Adrien FADAT** (Bonniol social) | Paie / DSN / social | ✅ **envoyé à l'instant** |
| **Bastien Brière** (cession) | Disclosure / GAP | 🅿️ **parké** → session cession dédiée (brouillon prêt, non envoyé) |

## En attente
- Réponse **Adrien** (point paie/DSN à sécuriser)
- Réponse **Capstan** (prise en charge, parallèle/joint, attitude Soufiane)
- **Feuilles de route** Aurélie → dossier `04 - PIECES EMPLOYEUR`

Tout est à jour dans l'atome INDEX. Le mail Bastien t'attend pour quand tu ouvres la session cession. 👍

[assistant] Protocole sauvegarde — les atomes sont déjà écrits (mis à jour depuis le dernier backup avec le mail Adrien). Je vérifie, re-backup, et je prouve.

[assistant] Push OK (c09807c). **Étape 6 — preuve** : je grep les ids + le nouveau contenu (mail Adrien) dans le dump poussé.

[assistant] ✅ **Protocole sauvegarde exécuté — vérifié bout en bout.**

| Étape | Résultat |
|---|---|
| 1-2. Atomes + INDEX | ✅ détail (8628 c.) + INDEX (3962 c., prio 9) à jour |
| 3. Persistance | ✅ SELECT OK + `jarvis-mem --grep` retrouve |
| 4. SQLite | ✅ N/A (Postgres-only) |
| 5. Backup GitHub | ✅ **Push successful** (commit c09807c) |
| 6. Preuve backup | ✅ ids dans le dump (INDEX ×1, détail ×2) **+ le contenu « MAIL ADRIEN BONNIOL » présent** → dump bien à jour |

Le dump poussé contient la dernière version (mail Adrien inclus), pas une ancienne — preuve faite, pas de faux-save.

**Session Soufiane sauvegardée et fermée.** Point de reprise unique : `atom_INDEX_soufiane_prudhommes_20260720`. Le mail Bastien Brière (cession) reste parké pour la session dédiée. 👍

[user] super juste detail que je viens de percuter tu m ad i qu il dmeande un licenciement? ( j ai pas lu le dossier ) ?

[assistant] Bonne question, et la nuance est importante — je te la précise **sur le texte exact de la requête** (pas de mémoire).

## Non, il ne demande PAS que tu le licencies

Chef n°11 de son dispositif, mot pour mot :

> *« JUGER que la demande de **résiliation judiciaire** du contrat de travail de Monsieur DRIOUECH est bien fondée et **s'analyse en un licenciement dépourvu de cause réelle et sérieuse** »*
> *« FIXER la date de rupture du contrat de travail à la date de la décision de justice à intervenir »*

Ce qu'il demande, c'est une **résiliation judiciaire** : **c'est LUI qui demande au juge de mettre fin à son contrat**, en imputant la faute à l'employeur. Ce n'est pas à toi de le licencier.

## Comment ça marche
- Il reste **salarié en poste** aujourd'hui.
- Il demande au **Conseil de Prud'hommes** de **prononcer la rupture** de son contrat aux torts exclusifs de l'employeur.
- **Si le juge accepte** → ça produit les **effets d'un licenciement sans cause réelle et sérieuse** → il touche le package : dommages-intérêts (12 300 €), préavis (8 264 €), indemnité de licenciement (2 066 €).
- **Si le juge refuse** → **le contrat continue**, il reste salarié.

## La conséquence pratique (que tu avais senti)
👉 **Tu n'as rien à faire, surtout pas le licencier toi-même.** C'est exactement pour ça que la 4ᵉ question à Capstan (*attitude à tenir, statu quo, salarié toujours en poste*) est la bonne : on **défend**, on **ne provoque pas** de rupture de notre côté (le licencier maintenant = n

[assistant] On ferme. J'ai lancé le protocole complet il y a quelques minutes — je vérifie juste que rien de neuf n'est en attente depuis, pour ne pas re-pusher inutilement (ni claim un faux save).

[assistant] ✅ **Fermé — tout est déjà sauvegardé, rien de neuf à pousser.**

- Atomes Soufiane : dernière modif **10:46** (INDEX) → le dump poussé à **12:52** (commit c09807c) les contient déjà, prouvé au grep tout à l'heure.
- La clarification « résiliation judiciaire ≠ demande de licenciement » est **déjà** dans l'atome (« veut sortir aux torts employeur ») → pas de nouveau contenu à écrire.
- Off-site GitHub **à jour**, aucun faux-save.

**Session Soufiane close.** Reprise = `atom_INDEX_soufiane_prudhommes_20260720`.

**Reste ouvert (pour plus tard) :**
- Réponses en attente : Capstan (Périès) · Adrien (paie/DSN) · feuilles de route Aurélie
- Mail **Bastien Brière** (cession/GAP) → session cession dédiée, brouillon parké
- Attestations témoins (Layla notamment) → après ton appel Capstan

Bonne suite. 👍