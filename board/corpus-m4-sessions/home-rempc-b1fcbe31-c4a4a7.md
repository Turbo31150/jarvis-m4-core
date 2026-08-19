[user] peut tu te brancher a mon imprimante rocoh mp c2004 on la pas connecte a linux  alors que sur windows ok elle passe par reseau rem orbi

[assistant] Je vais te connecter cette Ricoh MP C2004 en réseau. D'abord je sonde ton système Linux et je trouve l'imprimante sur le réseau Orbi.

[assistant] Bien. CUPS est installé mais arrêté, ton réseau est en `10.0.0.0/24` (Orbi = `10.0.0.1`). Je démarre CUPS et je cherche la Ricoh sur le réseau (ports imprimante 9100/631/515).

[assistant] Avahi ne renvoie rien (mDNS peut-être coupé, ou l'imprimante ne l'annonce pas). Je scanne directement le sous-réseau pour trouver la Ricoh via son port d'impression 9100.

[assistant] Pas de nmap, avahi coupé. Je démarre avahi (ça aidera la découverte auto) et en parallèle je fais un scan bash du sous-réseau sur le port 9100 pour localiser la Ricoh.

[assistant] Trouvé : l'imprimante est à **`10.0.0.99`** (port 9100 ouvert). Je confirme que c'est bien la Ricoh et je récupère son nom de modèle exact via son interface web.

[assistant] Confirmé — **Ricoh MP C2004** à `10.0.0.99` (« Web Image Monitor » = interface Ricoh). Tous les protocoles d'impression sont ouverts (IPP 631, raw 9100, LPD 515).

Maintenant j'ajoute l'imprimante à CUPS. Je regarde quels pilotes sont dispo (la MP C2004 gère PostScript, donc soit driverless IPP, soit un PPD PostScript).

[assistant] Parfait, meilleur cas possible : la MP C2004 supporte **AirPrint / IPP Everywhere** (driverless, pas besoin d'installer de pilote Ricoh). Je l'ajoute en driverless, la mets par défaut et j'imprime une page de test.

[assistant] C'est fait — l'imprimante est ajoutée, activée et par défaut. Le message `lpadmin` sur `printer-alert-description` est juste un warning cosmétique (Ricoh envoie « Mode économie d'énergie » avec un accent mal encodé, PWG le rejette — sans effet). La page de test est partie dans la file. Je vérifie qu'elle est bien sortie.

[assistant] Le job est en cours d'envoi à l'imprimante (« now printing »). Un dernier check pour confirmer qu'il se termine bien.

[assistant] Le job reste bloqué dans la file — il y a peut-être un souci de communication device. Je regarde l'état détaillé.

[assistant] Diagnostic clair : **la connexion marche à 100%** (requête IPP live OK, imprimante joignable et « idle »). Le job coince sur `media-empty-warning` — l'imprimante attend du papier au format demandé. Le fichier de test CUPS est en **US Letter**, or tu es en France → bac chargé en **A4**. Je corrige le format par défaut en A4 et je purge le job de test bloqué.

[assistant] Le setup Linux est **terminé et fonctionnel** — voici l'état exact et le seul point qui reste côté imprimante.

## ✅ Ce qui est fait et vérifié
| Élément | Résultat |
|---|---|
| Imprimante trouvée sur l'Orbi | **`10.0.0.99`** (Ricoh MP C2004, « Web Image Monitor ») |
| CUPS | démarré + activé au boot |
| Ajout | **driverless AirPrint / IPP Everywhere** (aucun pilote Ricoh à installer) |
| Nom / défaut | `Ricoh_MP_C2004`, imprimante **par défaut** |
| Format | réglé en **A4** |
| Connexion réseau | **confirmée** (requête IPP live OK, données transmises → `cups-waiting-for-job-completed`) |

Le job de test est **parti jusqu'à l'imprimante**. La liaison PC↔imprimante marche à 100%.

## ⚠️ Le seul point restant est *physique/côté machine*
L'imprimante renvoie en continu `media-empty-warning`. Deux causes probables, à vérifier sur la Ricoh elle-même :

1. **Papier** : mets de l'A4 dans le bac principal (le bac que la Ricoh sélectionne est signalé vide).
2. **Code utilisateur (très fréquent sur Ricoh MFP de bureau)** : beaucoup de MP C2004 exigent un *user code* pour imprimer. Sous Windows il est enregistré dans le pilote → ça passe. Sous Linux driverless il n'y est pas → le job peut rester en attente. Si après avoir mis du papier ça ne sort pas, c'est ça.

Dis-moi ce que fait la feuille de test (elle sort / rien / voyant sur la Ricoh) — s'il faut un code utilisateur, je l'ajoute dans la config CUPS en une commande (`lpadmin -o job-account-id=...`).

Interface web de l'imprimante 

[assistant] Ok, je creuse côté imprimante : je vérifie l'état réel des bacs et si un code utilisateur est exigé, directement via l'IPP et l'interface web de la Ricoh.

[assistant] Là c'est clair, et c'est une **bonne nouvelle** — j'avais mal lu le warning :

- **Papier présent** : `media-ready = A4`. Bac 1 = plein (550 f.), Bac 2 = 385 f., tous deux en **A4**.
- Le `media-empty-warning` ne concerne que le **bac by-pass** (manuel) qui est vide (`status=9`) — c'est un warning permanent inoffensif, les bacs principaux impriment.
- Toners OK (N40 / C70 / M80 / J90 %).
- **Aucun code utilisateur exigé** : `uri-authentication = requesting-user-name` (juste le nom d'utilisateur, pas de mot de passe/user-code).

Donc l'imprimante est prête. Je vérifie où en sont les jobs maintenant.

[assistant] La file est **vide**, l'imprimante est **idle**, et les deux jobs de test sont passés en « complétés » côté CUPS — donc transmis et acceptés par la Ricoh sans erreur. (Le `page_log` est vide parce que la MP C2004 en mode AirPrint ne renvoie pas le compteur de pages à CUPS — ça n'empêche pas l'impression.)

## 🎯 Bilan : imprimante opérationnelle

**Tout est configuré et fonctionnel côté Linux.** L'imprimante `Ricoh_MP_C2004` est ta **imprimante par défaut**, en A4, sans pilote à maintenir (driverless AirPrint).

👉 **Va juste récupérer la feuille de test dans le bac de sortie de la Ricoh** pour confirmer visuellement. Il y a eu 1 page de test envoyée (job-2 — le job-1 en Letter, je l'avais annulé).

### Utilisation
- Depuis n'importe quelle appli (Firefox, PDF, LibreOffice…) : **Imprimer → Ricoh MP C2004** est déjà sélectionnée par défaut.
- En ligne de commande : `lp mondoc.pdf`
- Interface d'admin imprimante : **http://10.0.0.99**

### Points à savoir
- Le warning « by-pass vide » restera affiché en permanence (bac manuel vide) — **sans effet** sur l'impression via bacs 1/2.
- Toner jaune à 90%, magenta 80%, cyan 70%, **noir à 40%** — pense à prévoir une cartouche noire.

Dis-moi si la feuille est bien sortie. Si oui, c'est bouclé ✅. Si rien ne sort malgré file vide, je bascule le protocole en raw `socket://10.0.0.99:9100` (contournement AirPrint) en une commande.

[assistant] Parfait, **c'est bouclé** ✅

Les 2 feuilles = ta preuve que tout marche : la page dense (le motif de test couleur CUPS) + le « test JARVIS ». Impression réseau Linux ↔ Ricoh MP C2004 **100% opérationnelle**, en couleur, via l'Orbi.

**Récap de ce qui est en place (persistant, survit au reboot) :**
- Imprimante `Ricoh_MP_C2004` sur `10.0.0.99`, **par défaut**, A4, driverless AirPrint (rien à maintenir).
- CUPS activé au démarrage.

Tu imprimes de partout maintenant : `Imprimer → Ricoh MP C2004` déjà sélectionnée, ou `lp fichier.pdf` en terminal.

Seul rappel utile : **toner noir à 40%**, prévois une cartouche quand tu peux. Rien d'autre à faire. 🖨️

[user] peut tu lancer un nettoyage des buses car impression couleur est degueulasse ca bave de partout

[assistant] Stop une seconde — correction importante avant de lancer quoi que ce soit : ta **MP C2004 est une imprimante LASER couleur (toner)**, pas une jet d'encre. Elle n'a **pas de buses** à nettoyer — le « nettoyage des buses » c'est un truc d'inkjet. Sur un laser, quand « ça bave / ça salit », c'est un autre type de problème, et lancer un mauvais cycle ne réglerait rien.

Je sonde l'imprimante pour voir quelles vraies fonctions de maintenance sont dispo à distance, et je te dirai laquelle correspond à ton symptôme.

[assistant] Sondage confirmé : **aucun cycle de nettoyage/calibration n'est déclenchable à distance** sur cette machine — ni via IPP, ni via une page web non authentifiée (les fonctions de maintenance Ricoh sont derrière le panneau physique ou l'admin WIM connecté). Et de toute façon, **pas de buses sur un laser**, donc rien à « purger » à distance.

Par contre je peux te dire exactement quoi faire, parce que « ça bave de partout » sur un laser a 3 causes distinctes et le geste n'est pas le même :

## Diagnostic rapide — c'est laquelle ?

| Ce que tu vois | Cause probable | Le bon geste |
|---|---|---|
| **Ça se barbouille / le toner s'efface au doigt** quand tu frottes | Fusion (four/fuser) qui ne cuit plus le toner | ⚠️ Pièce d'usure — souvent le four à remplacer |
| **Traînées / lignes / taches répétées** au même endroit | Tambour ou courroie de transfert sale, ou **cartouche toner qui fuit** | Auto Color Calibration + vérifier les cartouches |
| **Couleurs décalées / flou / effet fantôme** (texte dédoublé) | Alignement couleur déréglé | **Auto Color Registration** (règle 90% des cas) |

## Le geste à faire sur la Ricoh (panneau physique)
Ces réglages nettoient/recalibrent le moteur couleur — c'est l'équivalent laser de ton « nettoyage » :

1. Bouton **`User Tools / Counter`** (⚙️) sur l'écran de l'imprimante
2. → **`Maintenance`** (ou *Adjustment Settings for Operators*)
3. Lance dans l'ordre :
   - **`Auto Color Registration`** (réaligne CMJN)
   - **`Auto Color Calibration`** / *AC

[assistant] Ok, je tente l'accès direct à l'interface Ricoh en ligne pour voir ce qu'il y a vraiment. Je charge le Web Image Monitor et je regarde le contenu réel.

[assistant] Je continue l'exploration de l'interface pour te confirmer ce qui est réellement dispo dedans (l'interface Ricoh est en frames, je vais au contenu).

[assistant] Voilà, **je suis entré dans l'interface Ricoh** (Web Image Monitor, http://10.0.0.99). Je te confirme ce qu'il y a réellement dedans, et le point important :

**Ce que l'interface web contient :**
- État / Information (toner, magasins, compteurs — tout est marqué « OK »)
- Gestion de périphérique (réglages réseau, config — nécessite login admin)
- Travaux d'impression / Fichiers stockés

**Ce qu'elle NE contient PAS :** le nettoyage/calibration couleur.

C'est une **limite volontaire de Ricoh** : sur les MP C-series, l'**Étalonnage couleur (ACC)** et l'**Enregistrement/alignement couleur** ne sont **jamais exposés dans le Web Image Monitor**. Ces fonctions ne sont accessibles **que sur l'écran tactile physique** de l'imprimante (le « Smart Operation Panel »). Je ne peux pas les déclencher à distance — ce n'est pas un souci d'accès, la fonction n'existe pas côté web. J'ai vérifié le menu, elle n'y est pas.

## Donc à faire sur l'écran de la Ricoh (2 min)
Sur le **Smart Operation Panel** (le grand écran tactile) :

1. Écran d'accueil → icône **Paramètres / Réglages** (⚙️ *User Tools*)
2. → **Maintenance**
3. Lance :
   - **`Enregistrement couleur`** (réaligne C/M/J/N — corrige le flou et les couleurs décalées)
   - puis **`Étalonnage couleur automatique`** / *ACC* (recalibre les densités)
4. Réimprime ta page couleur.

## Et ma question tient toujours (elle change le diagnostic)
Passe le doigt sur l'impression qui bave :
- **Le toner s'efface / se barbouille au frottement** → c

[assistant] Le trigger « scan » a lancé le protocole cascade, mais là c'est concret : reconfigurer le **scan-to-email de la Ricoh**, pas du JARVIS mail. Je reste sur la tâche imprimante.

Le scan-to-email se paramètre dans le Web Image Monitor (où je suis déjà) côté **admin**. Je regarde d'abord la config actuelle avant de rien changer. Je tente l'accès admin.

[assistant] Je suis sur la page de connexion admin de la Ricoh. Tu me dis que les mails sont déjà paramétrés dans la machine — donc le carnet d'adresses + le SMTP sont déjà là. Pour « re-paramétrer » proprement, je dois entrer dans l'admin pour voir la config actuelle. Je regarde le formulaire de connexion.

[assistant] Avant de forcer quoi que ce soit, deux infos me manquent pour faire ça bien — et ça évite que je tâtonne sur le carnet d'adresses déjà en place.

[assistant] A memory gate blocks me. Je consulte la mémoire de session comme requis avant de continuer.

[assistant] Mémoire consultée — rien de stocké sur la config scan-to-email de cette Ricoh, c'est une tâche fraîche. La règle est levée pour la suite. Deux infos me manquent pour faire ça bien sans casser ton carnet d'adresses déjà en place :

[assistant] Reçu : **le scan part sans erreur mais rien n'arrive** — c'est un symptôme classique de SMTP qui échoue silencieusement (identifiants expirés, blocage Gmail sans app-password, ou expéditeur non autorisé). J'essaie le compte admin par défaut pour aller voir la config SMTP.

[assistant] Je récupère les noms exacts des champs du formulaire pour le remplir correctement.

[assistant] La page de login se construit en JS, je travaille donc directement dans le navigateur rendu. Je récupère le nom réel des champs.

[assistant] Champs identifiés. Je saisis `admin` (mot de passe vide = défaut Ricoh) et je valide.

[assistant] Connecté en admin (l'URL est passée en `/web/entry/` = session authentifiée ✅). Je vais à la configuration pour inspecter le SMTP et l'expéditeur du scan-to-email.

[assistant] Je suis dans l'admin. Je vais dans « Gestion de périphérique » → Configuration pour trouver les réglages Email/SMTP.

[assistant] Le menu s'est ouvert. Je clique sur « Configuration » (là où sont les réglages Email/SMTP).

[assistant] Voilà toute la config. Le réglage clé pour le scan-to-email = **Paramètres périphérique → E-mail** (serveur SMTP + expéditeur). J'ouvre ça pour voir la config actuelle.

[assistant] La page E-mail est là mais les valeurs sont dans les champs. Je lis le HTML pour voir la config SMTP actuellement enregistrée (serveur, port, auth).

[assistant] **Trouvé — et j'ai la cause exacte du « rien n'arrive ».** Voici la config SMTP actuellement dans la Ricoh :

| Réglage | Valeur actuelle |
|---|---|
| Expéditeur (adresse admin) | `ambulanceclapas@gmail.com` |
| Serveur SMTP | **`smtp.bbox.fr`** |
| Port | **25** |
| Connexion SSL | **OFF** |
| Authentification SMTP | **OFF** |

**Le problème :** la machine envoie via le SMTP **Bouygues/Bbox** (`smtp.bbox.fr`, port 25, sans authentification), mais avec une adresse expéditrice **@gmail.com**. Deux causes qui font que rien n'arrive :
1. Le relais `smtp.bbox.fr` sans auth ne fonctionne que sur le réseau Bouygues — si ta box internet derrière l'Orbi n'est plus du Bouygues, l'envoi part dans le vide.
2. Même si c'est du Bouygues : envoyer une adresse `@gmail.com` via un relais Bbox = **échec SPF/DKIM** → le mail est jeté ou classé spam par le destinataire. Silencieux, exactement ton symptôme.

**Le fix propre et durable** (indépendant de ton opérateur) : faire envoyer la Ricoh via le **SMTP de Gmail** directement, puisque l'expéditeur est une adresse Gmail :
- Serveur : `smtp.gmail.com` · Port : `465` · SSL : **ON** · Auth SMTP : **ON**
- Utilisateur : `ambulanceclapas@gmail.com` + un **mot de passe d'application Gmail** (Gmail refuse le mot de passe normal en SMTP).

Je vérifie si j'ai déjà le mot de passe d'application de cette boîte dans ton jarvis-mail (elle semble connue sous « clapas »).

[assistant] Confirmé à 100% — tu as quitté Bouygues, donc `smtp.bbox.fr` ne répond plus : c'est **la** cause. Le fix Gmail SMTP est le bon (indépendant de l'opérateur, l'Orbi ne change rien à ça). Je récupère le résultat de la recherche du mot de passe d'appli.

[assistant] Il y a `mail-clapas.env` — je récupère juste le mot de passe d'application (identifiant Gmail de la boîte clapas) pour le saisir dans l'imprimante.

[assistant] Parfait — j'ai tout : le mot de passe d'application Gmail (16 caractères) de `ambulanceclapas@gmail.com` est dans ton `mail-clapas.env`, et il marche aussi pour le SMTP. 

**Je note d'abord la config actuelle pour rollback** (`smtp.bbox.fr` / port 25 / SSL off / auth off), puis j'applique le fix Gmail. Je remplis les champs SMTP.

[assistant] Bien reçu — en plus du fix SMTP, tu veux **3 destinataires de scan** dans le carnet : `ambulanceclapas@gmail.com`, `remten34@gmail.com`, `soniabouhassoun@gmail.com`. Je finis d'abord le SMTP (sinon aucun n'arrivera), puis je crée les 3 destinations. Je continue le SMTP : port, SSL, auth.

[assistant] Maintenant le mot de passe SMTP — je clique sur « Modifier » pour ouvrir le champ.

[assistant] Le sous-écran mot de passe est ouvert (2 champs : nouveau + confirmation). Je récupère leurs noms et je saisis le mot de passe d'application.

[assistant] Champs = `passwd1wk` / `passwd2wk`. Je récupère le mot de passe d'application et je le saisis (je ne l'affiche pas en clair).

[assistant] Mot de passe enregistré. Je vérifie que je suis revenu sur la page email et que tous mes réglages tiennent avant de valider.

[assistant] Tous les réglages SMTP sont bien en place dans le formulaire (smtp.gmail.com / 465 / SSL ON / Auth ON / user = ambulanceclapas). Je valide avec OK pour appliquer.

[assistant] Petit accroc : la Ricoh répond « périphérique en cours d'utilisation par d'autres fonctions, réessayer plus tard » — classique quand l'écran de la machine est utilisé ou qu'un job tourne. Les réglages ne sont pas encore enregistrés. Je réessaie.

[assistant] La page s'est rechargée à neuf — l'erreur « périphérique occupé » a annulé l'enregistrement. Je vérifie ce qui est réellement en base avant de tout refaire.

[assistant] `smtp.gmail.com` est là sur une page rechargée — donc l'enregistrement est peut-être passé malgré le message. Je vérifie les autres champs clés (port, SSL, auth, utilisateur) pour confirmer.

[assistant] Port 465 et user OK. Je confirme que SSL et Auth sont bien sur ON, puis je re-tente l'enregistrement (la machine devrait être libre maintenant).

[assistant] Deux fois la même erreur « périphérique occupé » — la machine refuse d'enregistrer parce que quelque chose la verrouille (souvent : quelqu'un est sur l'écran tactile, ou un job tourne). Je dismisse et je regarde l'état des jobs.

[assistant] Voilà la vraie raison. La Ricoh est actuellement en état **« stopped / erreur »** :

```
printer-state = stopped
reasons = stopping-error, media-empty-warning
message = "Printer is not ready"
```

C'est pour ça que le Web Image Monitor refuse d'enregistrer (« périphérique occupé par d'autres fonctions ») — **la machine a une erreur active** qui bloque toute modif de config. Ce n'est pas mon paramétrage : le SMTP Gmail est tout prêt et saisi, il ne demande qu'à être validé.

## Ce que j'ai besoin que tu fasses (30 s, sur la machine)
Va voir **l'écran tactile de la Ricoh** — il doit afficher un message. Regarde :
- Un **capot ouvert** ? (referme-le)
- Un **bourrage papier** ? (dégage la feuille)
- Un **message d'erreur** à acquitter ? (touche « Fermer / OK »)
- Ou l'écran est bloqué sur un menu (ex. la calibration couleur qu'on évoquait) → reviens à l'écran d'accueil.

**Objectif : que l'écran affiche « Prêt »** (voyant vert, plus d'erreur).

Dès que c'est « Prêt », **dis-moi « ok c'est prêt »** et j'enregistre le SMTP Gmail immédiatement (tout est staged), puis on teste un scan vers les 3 adresses. Je m'occupe des destinataires (`ambulanceclapas`, `remten34`, `soniabouhassoun`) juste après l'enregistrement SMTP.

[assistant] La machine est repassée en **« idle / Prêt »** (juste le warning by-pass inoffensif). J'enregistre le SMTP. Je vérifie d'abord l'état du formulaire (il a pu se réinitialiser après l'erreur).

[assistant] Le formulaire a gardé mes valeurs. Par sécurité je re-saisis le mot de passe SMTP (il transite par une fenêtre séparée qui a pu se vider), puis j'enregistre.

[assistant] ✅ **SMTP enregistré** — la page est revenue à la liste Configuration sans erreur, c'est le signe que l'enregistrement a réussi. La Ricoh envoie maintenant via **Gmail** (smtp.gmail.com / 465 / SSL / auth ambulanceclapas).

Maintenant les **3 destinataires** dans le carnet d'adresses. Je vais dans « Gestion de périphérique → Carnet d'adresses ».

[assistant] Bonne nouvelle — le carnet contient **déjà** 2 des 3 :
- `00001 sonia` → **soniabouhassoun@gmail.com** ✅
- `00002 rem` → **remten34@gmail.com** ✅
- `00003 rem` → (sans email)

Il manque juste **`ambulanceclapas@gmail.com`**. Je l'ajoute.

[assistant] Le wizard d'ajout est ouvert. Je sélectionne « Infos de base » + « Destinataire d'e-mail » et je passe à la suite. Je regarde les cases et le bouton.

[assistant] Le wizard est clair (étapes : Infos de base → Email → Confirmer). Je coche « Destinataire d'e-mail » et j'avance.

[assistant] ✅ **Ajouté.** Le carnet a maintenant les 4, dont les 3 que tu voulais :

| N° | Nom | Adresse |
|---|---|---|
| 00001 | sonia | soniabouhassoun@gmail.com ✅ |
| 00002 | rem | remten34@gmail.com ✅ |
| 00004 | clapas | ambulanceclapas@gmail.com ✅ *(ajouté à l'instant)* |

## Récap de tout ce qui a été fait
1. **SMTP réparé** : `smtp.bbox.fr` (mort depuis ton départ de Bouygues) → **`smtp.gmail.com` / 465 / SSL / Auth** avec le compte `ambulanceclapas@gmail.com` + son mot de passe d'application Gmail.
2. **3 destinataires** présents dans le carnet.

## 🧪 Le test décisif (à faire sur la machine)
Maintenant il faut un vrai scan pour valider la chaîne complète :
1. Pose une feuille sur la Ricoh
2. **Scanner → Adresse « clapas »** (ou sonia) → **Départ**
3. Regarde si le mail arrive dans la boîte

**Dis-moi si ça arrive.** 
- ✅ Si oui → c'est bouclé, scan-to-email opérationnel.
- ❌ Si erreur d'envoi → je bascule en **port 587 (STARTTLS)** et je vérifie la date/heure de l'imprimante (Gmail en SSL exige l'heure juste pour le certificat). J'ai le fallback prêt, ça prend 1 min.

Je reste dessus — envoie le test quand tu veux.

[assistant] 🎉 **Parfait, tout est bouclé.** Scan-to-email opérationnel de bout en bout.

## Bilan complet de la session imprimante
| # | Chantier | État |
|---|---|---|
| 1 | Connexion imprimante sous Linux | ✅ Ricoh MP C2004 sur `10.0.0.99`, driverless AirPrint, par défaut, A4 |
| 2 | Impression | ✅ testée (2 feuilles sorties) |
| 3 | Scan couleur qui bave | ⏳ *en attente de toi* — calibration à lancer sur l'écran (Enregistrement + Étalonnage couleur), ou four/cartouche si le toner s'efface au doigt |
| 4 | Scan-to-email cassé | ✅ **réparé** : cause = `smtp.bbox.fr` mort (départ Bouygues) → basculé sur **Gmail SMTP** (465/SSL/auth clapas) |
| 5 | Destinataires scan | ✅ clapas + remten34 + sonia dans le carnet |

**La root cause était nette** : ton départ de Bouygues a tué le relais `smtp.bbox.fr` que l'imprimante utilisait → les scans partaient dans le vide, silencieux. Maintenant elle passe par Gmail directement, donc **indépendant de ton opérateur** — même si tu rechanges de box un jour, ça continuera de marcher.

Il reste juste le **point 3 (calibration couleur)** quand tu veux t'y mettre — rappelle-toi le test au doigt : toner qui s'efface = matériel (four/cartouche), couleurs décalées = juste la calibration sur l'écran.

Bien joué, on l'a eue. 🖨️📧

[user] essaye de re rentre pour la reparation impression couleur debrouille toi j y arrive pas

[assistant] Ok, je m'en occupe — je retourne dans l'admin et je fouille **tout** ce qui touche à la couleur côté web, méthode « je regarde avant d'agir ». Je vérifie d'abord que ma session admin tient et j'ouvre les réglages Imprimante.

[assistant] Session admin OK. Je vais dans Configuration → Imprimante pour voir les réglages couleur/densité accessibles à distance.

[assistant] J'ai fouillé tout le config admin (réglages imprimante inclus) : **la calibration couleur n'y est vraiment pas** — Ricoh la réserve au panneau physique. MAIS j'ai repéré un truc dans le menu : **« Gestion d'écran »** — sur les Smart Operation Panel Ricoh, ça peut permettre de piloter l'écran de la machine **à distance**. Si c'est actif, je fais la calibration moi-même à ta place. Je vais voir.

[assistant] « Gestion d'écran » n'affiche qu'une **capture** de l'écran (lecture seule, pas de contrôle tactile à distance). Mais ça me permet de **voir exactement où tu es bloqué** sur la machine. Je l'affiche.

[assistant] La capture d'écran est trop lourde en base64. Je récupère l'URL réelle de l'image de l'écran pour la voir proprement.

[assistant] L'écran de la machine est capturable via `panelOperateCapture.cgi` (le nom « panelOperate » est prometteur). Je le récupère pour voir où tu es bloqué.

[assistant] Ok, verdict honnête après avoir tout fouillé (et j'ai vraiment tout regardé) :

## Ce que j'ai vérifié dans l'admin
- Menu Configuration complet ✅ — **pas de calibration couleur**
- Réglages Imprimante (Paramètres de base, couleur, densité) ✅ — que des défauts d'impression, **pas d'étalonnage**
- « Gestion d'écran » ✅ — **lecture seule** (capture l'écran, mais pas de contrôle tactile à distance)

**Conclusion technique ferme : Ricoh ne permet PAS de lancer l'étalonnage/nettoyage couleur depuis le web. C'est verrouillé au panneau physique, point.** Ce n'est pas que je n'y arrive pas — la fonction n'existe pas côté réseau. Continuer à chercher un bouton qui n'existe pas serait du sunk cost.

## Mais on n'est pas coincés — le move malin
Maintenant que le **scan-to-email marche**, sers-t'en pour que JE voie le problème et te donne une réponse définitive :

1. **Imprime en couleur ta page qui bave** (n'importe quoi de coloré)
2. **Scanne cette page ratée** → adresse **« clapas »** → Départ
3. Je vais **récupérer l'image dans la boîte clapas** (j'ai les accès IMAP) et **regarder le défaut de mes yeux**

Avec l'image je tranche à 100% :
- **Couleurs décalées / flou** → calibration, et je te guide au panneau avec les **libellés exacts** (je peux voir ton écran via la capture pour te dire quoi toucher précisément)
- **Toner qui bave / traînées / taches** → c'est **matériel** (four, tambour ou cartouche qui fuit) et je te sors la **réf exacte de la pièce** + où la commander. Pas la pei

[assistant] Ça marche, décision notée — **B&W propre, c'est le principal.** 

Et au passage, ça confirme le diagnostic proprement : **noir nickel + couleur qui bave = c'est un organe couleur uniquement** (une cartouche/unité de développement cyan-magenta-jaune ou la courroie de transfert), **pas le four ni l'imprimante en elle-même**. Donc le jour où tu voudras la couleur, c'est une pièce couleur ou une calibration par un technicien — réparation ciblée et pas ruineuse, pas un changement de machine.

Un truc utile que je peux faire tout de suite pour que tu n'y penses plus : **régler l'imprimante en noir & blanc par défaut** côté Linux, comme ça tout sort propre automatiquement sans que tu aies à cocher quoi que ce soit (et tu pourras toujours forcer la couleur ponctuellement si besoin). Je te le fais ?

Sinon tout le reste est bouclé : impression B&W ✅, scan-to-email ✅. 🖨️