[user] cession soleil j ai eu mme nacko au tel elle est tres dure avec moi elle me dis que c est complique car jai fai des mic mac avec la fusion absortion de id vers soleil elle me dit de voir avec la prefecture de beziers pour savoir si la licence est cessible ou pas bref ca sors de ses comptetences elle ve pas se mouiller il faut lui macher le travil ( avecc preuve d activite en continu + validation prefecture que  c est ok transfert licence soleil verx  sotiete x

[assistant] Je pars de la mémoire avant de te répondre — je ne veux pas te faire re-raconter le dossier.

[assistant] Mémoire lue. Je récupère les atomes décisifs en plein texte + les pièces de la fusion ID→Soleil.

[assistant] Tout est en mémoire, je n'ai rien eu à te redemander. **Un point de fond avant les livrables : Mme NAKO t'envoie au mauvais endroit, et j'ai la preuve sur pièce.**

Je crée le dossier.

[assistant] Atome persisté (`atom_ADS_TAXI_N3_APPEL_NAKO_DOSSIER_MACHE_20260805`, 4124 car., scope `cession_soleil`).

## Elle a tort sur trois points, et j'ai la preuve des trois

**1. La préfecture n'a rien à dire.** Art. L. 3121-1 : l'ADS est délivrée par **le maire**. La préfecture délivre la carte pro du conducteur, point. Elle t'envoie demander une autorisation à une administration qui n'en délivre pas.

**2. Ce n'est pas Béziers, c'est Lodève.** Saint-Gély relève de l'arrondissement de Lodève. Preuve : **l'arrêté du 10/10/2024, pris par sa propre mairie**, porte l'ampliation « à Monsieur le Sous-Préfet de **Lodève** ». Elle se trompe d'arrondissement sur ses propres actes.

**3. Le « mic-mac » de la fusion — sa mairie l'a déjà tranché il y a 4 ans.** L'arrêté du Maire du **24/11/2022** s'intitule *« changement de dénomination suite à la fusion/absorption »*, article 2 : *« la nouvelle dénomination de l'ADS n° 3 devient Ambulances du Soleil »*. Ce n'est pas ta qualification, **c'est la sienne**. Jamais retirée.

→ **C'est le levier.** On ne lui demande pas de trancher une question nouvelle. On lui demande de confirmer un arrêté que sa commune a déjà pris.

Et sur la cessibilité : le bilan EURL ID TAXI 2014 la tranche déjà — licence à l'actif **78 456,12 €** dès le 31/12/2013 + prêt SG **« PRÊT SG 69 000 LICENCE »** → acquisition à titre onéreux → mutation du 13/03/2013 → **condition des 5 ans acquise depuis mars 2018**.

## Le dossier mâché — `~/Bureau/SOLEIL/6-ADS-TAXI-N3/`

| Fic

[user] Base directory for this skill: /home/rempc/.claude/plugins/cache/claude-plugins-official/superpowers/6.2.0/skills/dispatching-parallel-agents

# Dispatching Parallel Agents

## Overview

You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

When you have multiple unrelated failures (different test files, different subsystems, different bugs), investigating them sequentially wastes time. Each investigation is independent and can happen in parallel.

**Core principle:** Dispatch one agent per independent problem domain. Let them work concurrently.

## When to Use

```dot
digraph when_to_use {
    "Multiple failures?" [shape=diamond];
    "Are they independent?" [shape=diamond];
    "Single agent investigates all" [shape=box];
    "One agent per problem domain" [shape=box];
    "Can they work in parallel?" [shape=diamond];
    "Sequential agents" [shape=box];
    "Parallel dispatch" [shape=box];

    "Multiple failures?" -> "Are they independent?" [label="yes"];
    "Are they independent?" -> "Single agent investigates all" [label="no - related"];
    "Are they independent?" -> "Can they work in parallel?" [label="yes"];
    "Can they work in parallel?" -> "Parallel dispatch" [label="yes"];
    "Can the

[assistant] Using **superpowers:dispatching-parallel-agents** — quatre domaines indépendants dans ce dossier, dont deux qui doivent vérifier mes propres affirmations avant que Brière signe.

*(Note : ça consomme des tokens agents — tu as invoqué le skill explicitement, je pars dessus.)*

[assistant] Quatre agents lancés en parallèle sur les quatre domaines indépendants du dossier :

| Agent | Domaine | Ce qu'il tranche |
|---|---|---|
| **Juridique** | Légifrance | La rédaction exacte de L. 3121-2, et surtout **quel texte** porte vraiment le droit de présentation pour une ADS d'avant 2014 — L. 3121-2 ou une disposition transitoire de la loi Thévenoud. C'est le seul point non sourcé du dossier |
| **Administratif** | Arrondissement + contrôle de légalité | Lodève vs Béziers vs Montpellier, coordonnées exactes du service à saisir, et ce que fait réellement la préfecture 34 en matière de taxis |
| **Pièces** | Disque + mails | Copie physique des pièces dans `6-ADS-TAXI-N3/PIECES/` + inventaire. Cherche le traité de fusion, le conventionnement CPAM au nom de Soleil, les TICPE |
| **Contre-vérification** | Les deux arrêtés scannés | Relit les PDF de 2022 et 2024 **mot pour mot** contre mes 14 affirmations, en cherchant activement ce qui nous **dessert** |

Les deux derniers sont là pour me contredire. Le quatrième est le plus important : toute la note repose sur le fait que l'arrêté de 2022 dit littéralement « changement de dénomination » et que celui de 2024 mentionne Lodève. Si l'un des deux ne dit pas exactement ça, la note tombe et il vaut mieux le savoir maintenant que sous la signature de Brière.

Je te fais la synthèse quand ils rentrent, et je corrige les documents s'il y a des écarts.

Pendant ce temps, une seule chose que je ne peux pas aller chercher : **le nom, le

[assistant] Le contre-vérificateur est rentré. **Il confirme mes 14 citations — et il trouve trois choses qui peuvent retourner le dossier.** Je corrige immédiatement.

[assistant] Le second agent est rentré, et **il me corrige.** Mme NAKO n'avait pas tort par hasard.

[assistant] Deux agents rentrés sur quatre. Le second me corrige, et ça change ce que tu dois dire à Mme NAKO.

## Correction : elle n'avait pas tort sur Béziers

Je t'ai dit « ce n'est pas Béziers ». **C'est inexact.** La sous-préfecture de Béziers est le **guichet unique taxis/VTC pour tout l'Hérault** — cartes professionnelles, taxis-relais, fourrières. Page officielle de la préfecture, mise à jour le 11/05/2026. Son réflexe a une vraie base.

Ce qu'elle a confondu, c'est le **guichet taxis** avec le **contrôle de légalité**. Béziers n'a aucune compétence sur la titularité d'une ADS communale, et n'en délivre aucune.

Et le contrôle de légalité n'est pas non plus à Lodève : **il a été retiré de la sous-préfecture de Lodève entre 2017 et 2021** (la mention « filtrage contrôle de légalité » figure sur son organigramme 2017, elle a disparu de ceux de 2021 et 2025). Il est centralisé à **Montpellier**, à la DRCL.

→ Donc : arrondissement = **Lodève** (confirmé INSEE), instruction = **Montpellier**, guichet taxi = **Béziers**. Trois adresses différentes. Les courriers sont refaits en conséquence : envoi principal Montpellier + copie Lodève, et **un courrier séparé à Béziers** sur le seul volet carte pro du repreneur.

## Le contre-vérificateur : mes 14 citations sont exactes, mais…

Aucune inventée, aucune fausse. Lodève est bien écrit dans les deux arrêtés. J'ai corrigé cinq citations sur la forme (guillemets, « quatre » en minuscules, « FR 069 KA » sans tirets).

**Le danger n'est pas da

[assistant] Le vérificateur juridique est rentré. **Il casse un fondement de ma note.** Un point de sa conclusion repose toutefois sur une prémisse qu'il n'a pas vérifiée — je la contrôle avant de propager l'alarme.

[assistant] Prémisse fausse : **Saint-Gély-du-Fesc n'est pas dans Montpellier Méditerranée Métropole**, mais dans la [Communauté de communes du Grand Pic Saint-Loup](https://grandpicsaintloup.fr/commune/saint-gely-du-fesc/). Je vérifie quand même le point de droit sous-jacent.

[assistant] Risque écarté : le transfert de L. 5211-9-2 suppose que l'EPCI soit **compétent en matière de voirie** — ce que la CC du Grand Pic Saint-Loup n'est pas, et la maire a pris elle-même les arrêtés en 2020, 2022 et 2024. Je corrige maintenant les fondements textuels.

[assistant] Troisième agent rentré. Il a trouvé une erreur réelle dans ma note, et un levier que je n'avais pas.

## Ce que j'avais faux

**L. 3121-1 ne donne aucune compétence au maire.** C'est une simple définition du taxi. Je le citais comme fondement de la compétence communale — c'était faux. Le bon texte est **l'article L. 2213-33 du CGCT** : *« Le maire, ou le préfet de police de Paris dans sa zone de compétence, peut délivrer des autorisations de stationnement sur la voie publique aux exploitants de taxi. »* Corrigé dans la note et dans la trame d'arrêté.

En revanche **la condition de durée était juste, au mot près.** Vérifiée sur Légifrance, version en vigueur depuis le 03/10/2014 : *« quinze ans à compter de sa date de délivrance ou de cinq ans à compter de la date de la première mutation »*. Et c'est bien l'article 6 de la loi Thévenoud qui porte ce texte, pas l'article 2.

## Le levier que je n'avais pas vu

**Article L. 3121-4 : la commune tient de par la loi un registre des transactions sur les ADS, avec mention de leur montant.**

Si le rachat de 2013 y figure, la qualification de mutation n'est plus discutable — elle est établie par un document communal, pas par notre comptabilité. C'est une bien meilleure demande à adresser à Mme NAKO que la seule copie de l'arrêté. La note la réclame désormais.

## Une fausse alerte, que j'ai coupée avant de te la transmettre

L'agent signalait un risque majeur : si la commune appartenait à Montpellier Méditerranée Métropole, le pouvoir

[user] voici le numero bodacc 
────────────────────────Annonce n° 312 du BODACC A n° 20130079 publié le 23/04/2013

[assistant] Le BODACC A de 2013 — c'est exactement la pièce qui peut trancher mutation vs délivrance. Je vais la chercher.

[assistant] C'est fini. **L'annonce dit tout.**

`ID'TAXI` — *« Établissement principal **acquis par achat** au prix stipulé de **80 000 Euros** »*, activité *« Transport de voyageurs par taxi »*, **précédent propriétaire : HUGUET Alain** (RCS Montpellier 387 968 167), **date de commencement d'activité : 13/03/2013** — la date exacte de l'arrêté du maire.

Je réécris le cœur de la note.

[assistant] Ton copier-coller correspond mot pour mot à ce que l'API du BODACC me renvoie — double confirmation, source croisée. Je finis le dossier.

[assistant] Les quatre agents sont rentrés. Voilà où on en est.

## Le BODACC ferme le dossier

C'était la seule question qui pouvait tout faire tomber : mutation ou délivrance initiale. **Elle est tranchée par une publication officielle de l'État.**

> *« Origine du fonds : Établissement principal **acquis par achat** au prix stipulé de **80 000 Euros** »*
> *« Activité : Transport de voyageurs par taxi »*
> *« **Précédent propriétaire : 387 968 167 RCS Montpellier. HUGUET (Alain)** »*
> *« Date de commencement d'activité : **13 mars 2013** »*

Trois choses en découlent, et aucune ne se discute :

1. L'ADS n'a pas été créée pour ID'TAXI — **elle lui a été vendue**, à titre onéreux.
2. Il y a un **cédant nommé**, Alain Huguet, exploitant taxi immatriculé depuis 1992. Une licence créée par une mairie n'a pas de précédent propriétaire. *(JARVIS l'avait listé le 03/08 comme candidat cédant possible — hypothèse confirmée.)*
3. La date de commencement d'activité publiée est **le 13 mars 2013, jour pour jour la date de l'arrêté du maire**. L'arrêté est la contrepartie administrative du transfert du fonds.

→ **Mutation. Cinq ans. Acquis depuis le 13 mars 2018. La licence est cessible, et la preuve est publique et opposable à tous.** Fini l'argument comptable indirect.

Deux corrections à propager : le prix du fonds est **80 000 €** (pas 65 000), soit un ancrage de **+62,5 % sur treize ans** — vérifiable par l'acquéreur. Et le gérant d'ID'TAXI en 2013 était **Renaud Wallet**, pas toi. Ne présen

[user] pour l instant l idee est de renvoye un mail a mme nacko pour lui enlever tous les doutes : 1 lui prouver la cessibilite de la licence par l historique et article de loi ne lui laisse aucun doute , pour le leasing c est dans les mmoeurs tous les taxi y ont recours )  2 lui dire que nous avons un acquereur 3 lui mettre en pj la ximune de piece et eventuellement lui rediger un lettre d intention a l attention du maire de voiloir ceder la lucence a un confrere dan le secteur , julie va me scenne le cernat metro logique

[assistant] Ton call — j'assume que ça part sans attendre Brière. Je te le dis une fois : une note qui articule des articles de loi sous ta signature t'engage, alors que sous la sienne elle engage son assurance. Cela dit, la démonstration tient sur pièces publiques, donc le risque est faible.

Je lis l'inventaire réel pour ne rien inventer dans la liste de pièces.

[assistant] Deux découvertes de plus dans l'inventaire, qui servent directement le mail : le **référentiel national taxi** porte *« début d'activité 13/03/2013 »* avec l'historique complet des véhicules sans interruption, et la chaîne d'arrêtés est plus fournie que je ne le croyais (2013 → 2016 → 2018 → 2020 → 2022 → 2024).

[assistant] Trois documents prêts dans `~/Bureau/SOLEIL/6-ADS-TAXI-N3/` :

| Fichier | Rôle |
|---|---|
| `05-MAIL-NAKO-V2` | Le mail. Six sections : le BODACC, la loi, l'exploitation continue, la fusion déjà tranchée par sa mairie, le leasing, l'acquéreur |
| `06-LETTRE-INTENTION-MAIRE` | Lettre formelle à Michèle Lernout, en recommandé. C'est elle qui **date** et engage la démarche |
| `07-ANNEXE-BORDEREAU` | Version propre du bordereau, 19 pièces, sans note interne — c'est celle-ci qu'on joint |

**Le mouvement de fond du mail** : on ne lui demande plus « la licence est-elle cessible ? ». On le lui démontre par une publication de l'État qu'elle peut vérifier en trente secondes, puis on lui demande « comment souhaitez-vous que je procède ? ». Elle n'a plus à trancher un principe, seulement à indiquer une procédure. C'est exactement ce qu'une personne qui refuse d'engager sa responsabilité peut faire.

**Sur le leasing**, j'ai écrit dans ton sens. Le filet de sécurité est la phrase *« votre propre arrêté du 10 octobre 2024 a d'ailleurs été pris sur ce véhicule »* — la commune l'a déjà autorisé en connaissance de cause. Si tu préfères ne pas ouvrir le sujet, supprime le § 5, le mail tient sans.

**Ce que j'ai volontairement gardé hors du mail** : les 130 000 €, l'échéance du 08/08, et le fait que la carte grise est nommément au nom de BPCE Lease. Le § 6 dit « prix supérieur à celui de 2013 » sans chiffrer.

## Trois vérifs avant d'envoyer

**L'attestation d'assurance du dossier expire le

[assistant] Ce n'est pas un PV isolé — c'est **le carnet complet, cinq vérifications de 2022 à 2026**. Et il contient la meilleure preuve du dossier.

[assistant] Copié dans le dossier (`06-carnet-metrologique-COMPLET-2022-2026.pdf`, MD5 vérifié). Ce n'est pas la pièce que j'attendais — c'est mieux.

## Le kilométrage est l'argument le plus fort du dossier

Cinq vérifications, chacune par un organisme agréé qui relève le compteur :

| Date | Titulaire au PV | Véhicule | Km |
|---|---|---|---|
| 04/04/2022 | **IDTAXI** | FR-069-KA | 200 539 |
| 15/04/2024 | AMBULANCES DU SOLEIL | FR-069-KA | 420 987 |
| 09/10/2024 | AMBULANCES DU SOLEIL | GZ-634-HP *(neuf)* | 445 |
| 06/10/2025 | AMBULANCES DU SOLEIL | GZ-634-HP | **75 618** |
| **28/04/2026** | AMBULANCES DU SOLEIL | GZ-634-HP | **129 595** |

**75 173 km en douze mois, puis 53 977 km en moins de sept mois.** Contre une « exploitation effective et continue », c'est imbattable : ce n'est ni déclaratif ni interprétable, c'est un tiers agréé qui a lu le compteur. Et la dernière date d'il y a moins de quatre mois.

## Ça corrige aussi ce que je t'ai dit tout à l'heure

Je t'avais présenté comme point faible que « tout est encore au nom d'ID TAXI ». **C'est plus étroit que ça.** Le carnet montre que le basculement a bien été fait : PV d'avril 2022 au nom d'IDTAXI, PV de 2024, 2025 et 2026 au nom d'AMBULANCES DU SOLEIL — exactement dans l'ordre attendu après l'arrêté de dénomination du 24/11/2022.

Le retard ne concerne donc que **les référentiels nationaux et les bulletins CPAM**. Et le mail retourne le carnet contre cette objection avant même qu'elle soit posée.

Détail qui referme la bouc

[user] retire l assurance non essentiel , et voici un modele de lettre a l attetion du maire mail est suffisant a pparement : '/home/rempc/Téléchargements/JARVIS-OS-08-05-2026_12_43_PM.pdf'

[assistant] Le modèle est bon pour le **registre** — court, simple, une demande plutôt qu'une démonstration. Mais il contient un piège que je ne peux pas recopier.

**« l'autorisation n° X, créée par la commune en date du… »** — dans notre cas, écrire ça reviendrait à admettre une primo-attribution, donc la règle des **quinze ans**, donc une cessibilité en **2028**. C'est exactement l'inverse de ce que le BODACC établit. Le modèle dit aussi « au cours des trois dernières années », qui ne correspond à aucun seuil légal.

Je garde la forme, je corrige le fond. Et la maire est **Madame** Michèle Lernout.

[assistant] Fait. Assurance retirée du bordereau, lettre refaite au format du modèle.

**Ce que j'ai changé au modèle, et pourquoi :**

| Le modèle | Ce que j'écris |
|---|---|
| « autorisation n° X, **créée par la commune** » | « **acquise à titre onéreux** » + citation du BODACC |
| « **reprise** par notre société » | « **absorbée** », « prise d'acte par arrêté du 24/11/2022 » |
| « exploitée… au cours des **trois dernières années** » | « effective et continue », sans borne |
| « **Monsieur** le Maire » | **Madame Michèle LERNOUT** |

Le premier était le vrai danger : « créée par la commune » nous ferait basculer sur la règle des quinze ans, donc cessibilité en 2028. Le troisième aussi, dans une moindre mesure — trois ans ne correspond à rien dans le texte, et l'écrire invite à demander pourquoi trois.

**La logique à deux documents est maintenant nette :** le mail démontre à Mme Nako (BODACC, article de loi, kilométrages, sa propre mairie qui a déjà tranché la fusion) ; la lettre, courte, demande à la Maire. On démontre à l'agent, on demande à l'élue.

## Il reste trois choses avant d'envoyer

**Le § 6 sur l'acquéreur.** J'y écris qu'il *est* titulaire d'une carte professionnelle en cours de validité. Si tu ne l'as pas vue de tes yeux, remplace par « m'a indiqué être titulaire ». Ne jamais affirmer à une mairie un fait qu'on n'a pas vérifié.

**Le siège social.** La lettre porte 8 rue du Vieux Bourgidou, Aigues-Mortes — c'est l'adresse de l'arrêté de 2024 et du traité de fusion. Vérif

[user] pour l instant on demande a avoir le feu vert sur la cessibilite de la licence apres on leur enverra a qui on vend

[assistant] Compris — deux temps. On fait valider le principe, on nomme ensuite. J'ajuste les deux documents.

[assistant] Deux temps — mais pas comme tu l'as formulé, et pas comme je viens de l'écrire. Je corrige.

**Le problème d'une question de principe :** il n'existe aucun acte administratif qui s'appelle « confirmation de cessibilité ». Le seul acte, c'est l'arrêté d'attribution à un successeur nommé. Donc si tu lui demandes *« est-ce cessible ? »*, elle peut répondre en toute légitimité *« je ne peux pas me prononcer sans connaître le successeur »* — et tu as perdu une semaine en offrant à quelqu'un qui fuit la responsabilité la meilleure raison du monde de ne pas répondre.

**La bonne posture :** ne pas poser la question, mais **acter**. On ne demande pas *« est-ce cessible ? »*, on dit *« c'est cessible, voici pourquoi, et sauf observation de votre part sous quinzaine je vous présente le successeur »*. Silence = accord tacite sur le principe. Elle n'a rien à signer, rien à engager — ce qui est exactement ce qu'elle cherche.

[assistant] **Deux temps, mais avec ta réserve intégrée.** Trois raisons :

**1.** « Tout d'un coup » n'est pas exécutable aujourd'hui — je n'ai toujours pas l'identité de l'acquéreur. Ce serait un mail à trous.

**2.** Nommer le repreneur ouvre un second front. Elle passerait de « la licence est-elle cessible ? » à « et lui, remplit-il les conditions ? ». Deux questions à esquiver au lieu d'une, sur un dossier où elle cherche justement des raisons de ne pas trancher.

**3.** Ton instinct est bon : le point qu'elle a soulevé, c'est la cessibilité. On lui fait refermer ce qu'elle a ouvert, et on avance.

Ce que j'ai changé par rapport à ta formulation, c'est **le mode**. Pas « donnez-moi le feu vert » — ça se refuse. Mais :

> *« Au vu des pièces jointes, l'autorisation relève du droit de présentation et la condition de durée est acquise depuis le 13 mars 2018. **Sauf observation de votre part**, je considérerai ce point comme acquis et vous adresserai la présentation du successeur dans les prochains jours. »*

Elle n'a rien à signer, rien à engager, et son silence travaille pour toi. Les deux seules demandes concrètes portent sur des pièces et sur la forme de la procédure — deux choses qu'un service sait répondre sans se mouiller.

**Le déclencheur pour basculer en une seule étape** est écrit dans les notes : si elle répond « je ne peux rien dire sans le nom », tu envoies l'identité complète **le jour même**, sans négocier. D'où l'intérêt d'avoir le dossier du repreneur prêt d'avance — c

[assistant] Non — la lettre est encore en markdown. La règle du 08/07 dit d'apposer ta signature par défaut, donc je produis le PDF signé. Je vérifie d'abord l'outillage.

[assistant] Une page, texte conforme. Je vérifie visuellement que la signature s'est bien apposée.

[assistant] Non, elle ne l'était pas — c'était encore du markdown. Elle l'est maintenant.

**`~/Bureau/SOLEIL/6-ADS-TAXI-N3/LETTRE-MAIRE-ADS-N3-SIGNEE.pdf`** — une page A4, datée du 5 août 2026, ta signature apposée sous « Gérant de la SARL AMBULANCES DU SOLEIL ». Vérifié au sol : PDF rendu en image et relu, la signature est bien là.

Le HTML source reste à côté (`lettre-maire.html`) — si tu veux changer un mot, je régénère en dix secondes.

**Ce que la lettre dit, en cinq paragraphes :** demande de présentation d'un successeur au titre de L. 3121-2 al. 2 · autorisation **acquise à titre onéreux**, BODACC à l'appui avec le prix, le cédant et la date · absorption dont la commune a pris acte en 2022 · l'identité du successeur suivra dans un second temps, protocole sous condition suspensive de ton agrément · le carnet métrologique en pièce jointe.

Deux points à vérifier avant qu'elle parte :

**L'adresse du siège.** J'ai mis 8 rue du Vieux Bourgidou, Aigues-Mortes — c'est celle de l'arrêté municipal de 2024 et du traité de fusion. Confirme-la sur le Kbis du 28/04/2026.

**Le cachet de la société.** Je n'ai que ta signature en stock, pas de tampon. Si tu veux le cachet, scanne-le et je le rajoute.

[user] Base directory for this skill: /home/rempc/.claude/plugins/cache/claude-plugins-official/superpowers/6.2.0/skills/using-superpowers

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## The Rule

**Invoke relevant or requested skills BEFORE any response or action** — including clarifying questions, exploring the codebase, or checking files. If it turns out wrong for the situation, you don't have to use it.

**Before entering plan mode:** if you haven't already brainstormed, invoke the brainstorming skill first.

Then announce "Using [skill] to [purpose]" and follow the skill exactly. If it has a checklist, create a todo per item.

## Skill Priority

When multiple skills apply, process skills come first — they set the approach, then implementation skills (frontend-design, etc.) carry it out. Brainstorming and systematic-debugging are Superpowers' most common process skills, but the rule holds for any of them.

- "Let's build X" → superpowers:brainstorming first, then implementation skills.
- "Fix this bug" → superpowers:systematic-debugging first, then domain skills.

## Red Flags

These thoughts mean S

[assistant] Using **cross-model-claim-preflight** — c'est exactement la situation qu'il décrit : un livrable juridique à fortes affirmations de droit, sur le point de partir vers une mairie, où une affirmation fausse coûte cher.

[user] Base directory for this skill: /home/rempc/.claude/skills/cross-model-claim-preflight

# Cross-Model Claim Preflight

## Overview
Before a high-stakes deliverable reaches a human expert or gets acted on, run a fast, free cross-model check on its load-bearing claims. Deferring to the expert is correct — but a 30-second independent check **pre-flags the claim most likely to be wrong**, so the expert's review is targeted and errors surface *before* handoff, not after.

**Core principle:** Defer to the expert AND pre-flight. The models don't replace the expert — they tell you *where to look*.

## When to Use
- A note/memo/plan asserts specific law, tax rules, figures, or technical facts that will be relied on.
- It is about to be emailed to a lawyer/accountant/doctor, published, or used to decide.
- Wrong-if-acted-on cost is high (money, legal exposure, safety).

**Not for:** low-stakes drafts, opinion pieces, or claims already sourced to primary authority.

## The Recipe
1. **Extract the load-bearing claims** — the 3–8 statements that, if wrong, break the deliverable. Ignore prose.
2. **Frame each as JUSTE / IMPRÉCIS / FAUX + one-line correction.** Force a verdict, not an essay.
3. **Route to ≥2 INDEPENDENT free models** (0 token): a local/cheap model (OpenClaw) **and** a different-lineage model (Gemini). Independence matters — same-family models share blind spots.
4. **Flag CONVERGENT verdicts.** Two models say FAUX on the same claim = high signal → elevate it to the expert's q

[assistant] Using **cross-model-claim-preflight**. J'extrais les claims porteurs et je localise les deux routes gratuites.

[assistant] Routes trouvées. Je construis le jeu de claims et je l'envoie à deux lignées **différentes** — Gemini (Google) et la cascade locale via qwen/gpt-oss (Alibaba/OpenAI). Pas gemma, qui partagerait l'angle mort de Gemini.

[assistant] Les deux routes tournent en parallèle. Pendant ce temps, voici les 9 claims que je leur ai soumis — ce sont ceux qui, s'ils tombent, font tomber le dossier :

| # | Claim porteur |
|---|---|
| **C1** | Rédaction de L. 3121-2 al. 2 (15 ans / 5 ans, alternatives) |
| **C2** | Compétence du maire fondée sur **L. 2213-33 CGCT**, pas L. 3121-1 |
| **C3** | Le BODACC « Ventes et cessions » de 2013 **prouve une mutation**, pas une primo-délivrance |
| **C4** | La fusion-absorption 2020 (TUP, même holding) **n'est pas une mutation** |
| **C5** | Conclusion : cessible depuis mars 2018 |
| **C6** | L. 3121-4 — registre communal des transactions |
| **C7** | Le leasing du véhicule ne fait pas obstacle à la cession |
| **C8** | La préfecture n'a pas compétence sur la cessibilité |
| **C9** | L. 3121-3 inapplicable (une seule ADS) |

**C3, C4 et C5 sont le cœur.** C3 est ma déduction — le BODACC prouve l'achat d'un *fonds de commerce de taxi*, et j'en déduis que l'ADS a suivi par présentation de successeur. C4 n'a aucune source jurisprudentielle, l'agent Légifrance a cherché et n'a rien trouvé. Si les deux modèles convergent en FAUX sur l'un des trois, c'est ça que Brière doit regarder en premier — et le mail ne part pas avant.

Je te fais la synthèse dès qu'ils rentrent.

[user] Base directory for this skill: /home/rempc/.claude/plugins/cache/claude-plugins-official/superpowers/6.2.0/skills/dispatching-parallel-agents

# Dispatching Parallel Agents

## Overview

You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

When you have multiple unrelated failures (different test files, different subsystems, different bugs), investigating them sequentially wastes time. Each investigation is independent and can happen in parallel.

**Core principle:** Dispatch one agent per independent problem domain. Let them work concurrently.

## When to Use

```dot
digraph when_to_use {
    "Multiple failures?" [shape=diamond];
    "Are they independent?" [shape=diamond];
    "Single agent investigates all" [shape=box];
    "One agent per problem domain" [shape=box];
    "Can they work in parallel?" [shape=diamond];
    "Sequential agents" [shape=box];
    "Parallel dispatch" [shape=box];

    "Multiple failures?" -> "Are they independent?" [label="yes"];
    "Are they independent?" -> "Single agent investigates all" [label="no - related"];
    "Are they independent?" -> "Can they work in parallel?" [label="yes"];
    "Can they work in parallel?" -> "Parallel dispatch" [label="yes"];
    "Can the

[assistant] Using **superpowers:dispatching-parallel-agents**. Quatre domaines indépendants, dont deux qui attaquent précisément les claims que je viens de signaler comme les plus fragiles.

[assistant] Verdict Gemini rentré. La cascade tourne encore, plus les quatre agents.

## Sept JUSTE sur neuf — mais lis les deux exceptions

**C4 — Gemini dit JUSTE, et c'est là qu'il faut se méfier.** Il écrit : *« La jurisprudence du Conseil d'État confirme qu'une fusion-absorption entre sociétés d'un même groupe ne constitue pas une mutation. »* **Sans aucune référence.** Or mon agent Légifrance a cherché cette jurisprudence et n'a rien trouvé.

Un modèle qui affirme l'existence d'une jurisprudence sans pouvoir la nommer, c'est le profil exact d'une hallucination confortante — celle qui te dit ce que tu veux entendre sur ton point le plus fragile. **Je ne la cite nulle part**, et c'est précisément ce que l'agent B est en train de chercher en ce moment.

**C6 — Gemini se trompe, et j'ai le texte pour le prouver.** Il dit que c'est au cédant de justifier l'exploitation, pas au nouveau titulaire. Or L. 3121-4 dit littéralement : *« Le nouveau titulaire remet alors à cette autorité les documents justificatifs de l'exploitation effective et continue de l'autorisation par son prédécesseur. »* Verbatim relevé sur Légifrance. Ma formulation était exacte.

C'est utile : ça calibre la confiance à accorder au reste de ses verdicts.

**C1 — nuance non bloquante.** Il ajoute que la première mutation doit être postérieure à la loi du 20 janvier 1995. Absent du texte que j'ai relevé, mais sans effet ici : notre mutation est de 2013.

## Ce qui reste sur le feu

| En cours | Objet |
|---|---|
| Casca

[user] Base directory for this skill: /home/rempc/.claude/plugins/cache/jarvis-local/jarvis/3.4.7/skills/dispatch-multi-ia

# Orchestration Multi-IA depuis Claude Code

## When to Use

- Dispatcher une tache vers un modele local (M1 / OL1).
- Lancer un consensus multi-modele (Claude + M1 + OL1).
- Verifier un fait via une IA web (Perplexity).
- Encadrer une publication (preparer → verifier → valider → publier).

## What This Skill Does

1. Route le prompt vers l'endpoint local approprie (M1 ou OL1).
2. Execute un pipeline de consensus pondere a 3 modeles.
3. Cross-check les reponses critiques via Perplexity.
4. Bloque toute publication sans OK explicite utilisateur.

## Workflow

1. Identifier le besoin : execution simple, consensus, ou verification web.
2. Pour un appel local, utiliser les curl de `references/local-endpoints.md` (M1 = LM Studio, OL1 = Ollama).
3. Pour un consensus, suivre le pipeline et la grille de poids de `references/consensus.md` (seuil de validation >= 0.65).
4. Pour valider des faits/versions/CVE, executer le workflow de `references/web-verification.md` via le navigateur automatise.
5. Avant tout deploiement/post/commit, appliquer le pipeline 5 etapes de `references/publication-pipeline.md` et sa checklist.
6. Ne jamais publier sans "OK" explicite de l'utilisateur.

## References

- `references/local-endpoints.md` — endpoints M1 (LM Studio :1234) et OL1 (Ollama :11434), curl complets, cas d'usage.
- `references/consensus.md` — pipeline consensus 3 modeles, sc

[assistant] Using **jarvis:dispatch-multi-ia** pour ajouter la troisième voix et scorer proprement. Je lis d'abord la grille de pondération.

[assistant] La cascade est rentrée — backend `gpt-oss:120b`, lignée OpenAI, bien indépendante de Gemini.

[assistant] Deuxième verdict : **8 JUSTE, 1 IMPRÉCIS**. Je lance la troisième voix (M1, lignée Qwen) pour compléter le protocole à trois modèles.

[assistant] M1 tourne en fond. Voici la convergence sur les deux lignées déjà rentrées.

| Claim | Gemini | gpt-oss:120b | |
|---|---|---|---|
| C1 — rédaction L. 3121-2 | IMPRÉCIS | JUSTE | divergent |
| **C2 — compétence L. 2213-33 CGCT** | JUSTE | JUSTE | **convergent** |
| **C3 — le BODACC prouve une mutation** | JUSTE | JUSTE | **convergent** |
| **C4 — la fusion/TUP n'est pas une mutation** | JUSTE | JUSTE | **convergent** |
| **C5 — cessible depuis mars 2018** | JUSTE | JUSTE | **convergent** |
| C6 — registre L. 3121-4 | IMPRÉCIS | JUSTE | divergent |
| **C7 — le leasing ne bloque pas** | JUSTE | JUSTE | **convergent** |
| **C8 — la préfecture n'a pas compétence** | JUSTE | JUSTE | **convergent** |
| C9 — L. 3121-3 inapplicable | JUSTE | IMPRÉCIS | divergent |

## Le résultat qui compte : aucun FAUX convergent

C'est l'objet du préflight. **Aucun claim n'est signalé faux par les deux modèles**, et les trois qui portent le dossier — C3, C4, C5 — sont convergents JUSTE.

Sur les trois divergences, j'ai le texte verbatim de Légifrance et **ma formulation tient dans les trois cas** :

- **C1** : gpt-oss vote JUSTE mais décrit la condition comme « cumulative ». Le texte dit *« quinze ans… **ou** cinq ans »*. Les branches sont alternatives. Son vote est bon, sa motivation est fausse.
- **C6** : Gemini prétend que c'est au cédant de justifier. Le texte dit *« Le **nouveau titulaire** remet alors à cette autorité les documents justificatifs… par son prédécesseur »*.
- **C9** : gpt-oss di

[assistant] M1 est injoignable — connection timed out. C'est la machine de Franck, elle est probablement éteinte. Le seuil du préflight (≥ 2 lignées indépendantes) est déjà atteint, mais je tente la voie bonus prévue au protocole.

[assistant] Préflight clos. **Deux lignées indépendantes, aucun FAUX convergent** — le seuil du protocole est atteint.

Les deux autres voix n'ont pas répondu, et pour des raisons différentes :

- **M1 est entièrement éteint** — les ports 1234 *et* 22 sont en timeout. C'est la machine de Franck hors ligne, pas une panne LM Studio. La cascade a basculé toute seule sur la tour, ce qui est le comportement attendu.
- **`ask-chatgpt.py` est cassé** : HTTP 401, *« Incorrect API key provided: lm-studio »*. Ta clé OpenAI a été écrasée par un reliquat de config LM Studio. Hors chemin critique aujourd'hui, mais la route est silencieusement morte — tu la croyais disponible, elle ne l'est pas. C'est noté en mémoire.

## Ce que le préflight a produit

**Feu vert pour envoyer.** C3, C4 et C5 — les trois claims qui portent tout — sont convergents JUSTE sur les deux lignées. Aucun claim signalé faux nulle part.

Et une chose que le préflight a produite sans que je la cherche : **la calibration**. Sur les trois divergences, j'avais le verbatim Légifrance, et ma formulation tient dans les trois cas. Gemini se trompe sur C6, gpt-oss se trompe sur C9 et motive mal C1 tout en votant juste. Ça dit quelle confiance accorder à leur accord ailleurs.

**La limite est la même qu'au départ, et elle n'a pas bougé :** deux modèles d'accord sur C4 ne sourcent pas C4. Gemini a affirmé une jurisprudence du Conseil d'État sans pouvoir la nommer. Je ne la citerai dans aucun écrit, et c'est la première question pour Brière

[assistant] Ce rapport est sévère et il a raison sur des points graves. Deux faits à vérifier avant tout le reste — dont un qui est dans le PDF signé.

[assistant] **RCS Nîmes confirmé** — greffe du Tribunal de Commerce de Nîmes, n° de gestion 2000B00686. J'ai écrit Montpellier dans les trois documents et dans le PDF signé. Je vérifie aussi la dénomination exacte et le maire en exercice.

[assistant] Kbis à jour : **AMBULANCES DU SOLEIL** au pluriel (mes documents sont bons), siège d'Aigues-Mortes confirmé, et l'objet social mentionne bien l'activité **taxi**. Reste le point le plus dangereux.

[assistant] **Non confirmé — et c'est bloquant.** Les municipales de mars 2026 ont eu lieu, et je ne trouve aucune source publiant le résultat pour Saint-Gély-du-Fesc. Une lettre adressée nommément à un maire sortant se disqualifie à la première ligne. Je passe à la formule neutre et je regénère.

[assistant] PDF regénéré et vérifié : **RCS Nîmes**, formule neutre, et surtout la déduction BODACC est désormais assumée comme telle au lieu d'être présentée comme un constat.

Je corrige maintenant le mail sur les mêmes points.

[assistant] L'agent jurisprudence est rentré, et il change la donne sur le point le plus faible.

**D'abord : la jurisprudence de Gemini n'existe pas.** Juricaf renvoie « Aucun résultat » sur la requête exacte. J'ai bien fait de refuser de la citer — elle serait partie dans un courrier officiel.

Mais il a trouvé mieux que ce que je cherchais.

[assistant] Le second agent jurisprudence est rentré, et il apporte à la fois la meilleure formulation du dossier et le scénario qui pourrait le faire tomber.

[assistant] Trois agents rentrés sur quatre. Voici ce qui a changé.

## Le relecteur adverse a trouvé une erreur dans le PDF que tu venais de signer

**Le RCS était faux.** J'écrivais « RCS Montpellier 432 485 050 » partout. Le Kbis du 28/04/2026 dit **greffe du Tribunal de commerce de Nîmes, R.C.S. Nîmes**, n° de gestion 2000B00686. Le dossier se contredisait lui-même, puisque le Kbis était joint.

**Et un risque que je n'avais pas vu :** les municipales ont eu lieu en mars 2026. Aucune source ne publie le résultat pour Saint-Gély-du-Fesc, et rien au dossier ne confirme que Michèle Lernout est toujours maire. Une lettre adressée nommément à un maire sortant se disqualifie à la première ligne. **Passé en « Madame, Monsieur le Maire »** — un appel au 04 67 66 86 00 te permettra de personnaliser si tu veux.

Le PDF est regénéré et revérifié à l'image. Au passage, le Kbis confirme deux choses : le siège d'Aigues-Mortes est à jour, et l'objet social mentionne bien l'activité **taxi**.

## Sur le fond, la recherche a produit trois choses

**La jurisprudence de Gemini n'existe pas.** Juricaf renvoie « Aucun résultat » sur la requête exacte. Elle serait partie dans un courrier officiel si je l'avais crue.

**La meilleure formulation du dossier vient d'un guide préfectoral** — celui de l'Oise, destiné aux maires : *« 5 ans (ADS ayant déjà muté de propriétaire) ou 15 ans (1ʳᵉ mutation depuis sa délivrance par la mairie) »*. Autrement dit : **onéreux → 5 ans, gratuit → 15 ans.** C'est notre équati

[user] bon on va deja faire avec ca prepare le mail le plus factuel possible pour nacko en reponse a notre 1er mail enlve lui tous les doutes sur son mic mac elle croi que la fusion etait il y a 1 ou 2 ans

[assistant] Le vrai malentendu est là : **elle situe la fusion en 2022** parce qu'elle voit l'arrêté de changement de dénomination du 24 novembre 2022. Or la fusion date de 2020 — l'arrêté de 2022 n'est qu'un rattrapage d'intitulé, deux ans plus tard.

C'est factuel, ça se prouve par pièces, et ça retire tout le « mic-mac ».

[assistant] C'est exactement ce que je viens d'écrire : **treize lignes, treize pièces en face.** Je produis maintenant la pièce centrale qui manquait au dossier.

[assistant] La pièce centrale existe maintenant en PDF, avec le texte verbatim, l'identifiant de l'annonce et l'URL de vérification. Honnête : elle s'annonce comme une reproduction, pas comme un original.

[assistant] « 1991 » — je ne l'ai nulle part. Je vérifie ce que le registre dit de M. Huguet avant de l'écrire.

[assistant] Deux choses.

**Le quatrième agent est rentré** sur la régularisation CPAM. Point clé : ce n'est pas une correction de raison sociale, c'est **une nouvelle demande de conventionnement** — et ameli exige *« les ADS actualisées par l'autorité administrative compétente »*. Donc la mairie est le chemin critique, la CPAM vient après. Bonne nouvelle : le n° d'Assurance Maladie **342590445 n'a jamais changé**, l'écart est documentaire et non comptable, et une régularisation spontanée transforme le manquement en simple mise à jour. Le levier se referme si la caisse le découvre elle-même.

**Mais je bloque sur 1991.** Je ne l'ai nulle part, et c'est précisément le genre de fait qui ruinerait le document : toute sa force vient de ce que chaque ligne a une pièce en face. Voici ce que le registre national me donne pour les exploitants de Saint-Gély-du-Fesc :

- **Jean-Paul VILLAR (TAXI VILLAR)** — SIREN 383 248 846, immatriculé le **4 octobre 1991**, toujours actif
- **Alain HUGUET** — SIREN 387 968 167, immatriculé le **9 juillet 1992**, cessé le 30/09/2022

Huguet, notre cédant de 2013, est donc de **1992** au registre, pas 1991.

[assistant] **C'est un fait majeur, et il simplifie tout.**

Si la commune a créé l'ADS n° 3 en 1991, alors l'arrêté de 2013 **ne peut pas être une primo-délivrance** — la licence existait vingt-deux ans avant. Et surtout : la branche des **quinze ans à compter de la délivrance est acquise depuis 2006**. Les deux branches de L. 3121-2 sont satisfaites, quelle que soit la qualification retenue pour 2013.

Le scénario d'Appoigny qui m'inquiétait tombe de lui-même.

[assistant] Bien vu — et c'est ce qu'il faut faire. Je ne l'assène pas, je le **fais confirmer par elle**. C'est plus honnête, et tactiquement meilleur : elle devient la source du fait décisif au lieu d'en être la contradictrice.

[assistant] Le mail est prêt : **`08-MAIL-NAKO-V3-REPONSE-FACTUELLE.md`**, en réponse dans le fil du 3 août.

## Ce qu'il fait

**Il commence par lui expliquer pourquoi elle s'est trompée, au lieu de la corriger.** Le seul document communal qui parle de la fusion porte la date de 2022 — sa confusion est logique. La fusion, elle, date du 24 novembre 2020, avec effet au 31 décembre 2020, et la radiation d'ID'TAXI est du 15 juillet 2021.

Puis une **chronologie de quinze lignes, chacune adossée à une pièce**. C'est la seule arme qui marche contre une impression de « mic-mac » : pas un argument, un tableau. Et la phrase qui la referme — *il n'y a eu que deux sociétés, jamais davantage*.

## Le 1991 : je ne l'écris pas, je le lui demande

Tu as raison de dire « à vérifier ». Je n'ai aucune pièce, et le registre montre que ton cédant Huguet est immatriculé en **1992**, pas 1991 — le 1991 du registre, c'est Villar, dont la société est d'ailleurs toujours active à Saint-Gély.

Donc la ligne porte *« 1991 (à confirmer) — date que nous croyons exacte, mais que seuls vos registres peuvent établir »*, et c'est devenu la **demande n° 1** du mail.

Deux raisons. La première est qu'une date non sourcée dans un document dont toute la force vient du contraire détruirait exactement ce qu'on cherche. La seconde est tactique : elle devient la source du fait décisif au lieu d'en être la contradictrice.

**Et ce fait vaut la peine d'être obtenu.** Si l'ADS a bien été créée en 1991, l'arrêté de 2013 ne peut pa

[user] Run the "deep-research" workflow.

Deep research harness — fan-out web searches, fetch sources, adversarially verify claims, synthesize a cited report.

When the user wants a deep, multi-source, fact-checked research report on any topic. BEFORE invoking, check if the question is specific enough to research directly — if underspecified (e.g., "what car to buy" without budget/use-case/region), ask 2-3 clarifying questions to narrow scope. Then pass the refined question as args, weaving the answers in.

Phases:
- Scope: Decompose question (from args) into 5 search angles
- Search: 5 parallel WebSearch agents, one per angle
- Fetch: URL-dedup, fetch top 15 sources, extract falsifiable claims
- Verify: 3-vote adversarial verification per claim (need 2/3 refutes to kill)
- Synthesize: Merge semantic dupes, rank by confidence, cite sources

Invoke: Workflow({ name: "deep-research" })

[assistant] `/deep-research` sans argument — je ne vais pas deviner. Mais je sais quelles questions du dossier sont encore ouvertes, et une seule est vraiment décisive maintenant.

Depuis que tu as donné 1991, tout bascule sur un point : la condition des quinze ans porte-t-elle sur **l'autorisation** (exploitée par des titulaires successifs depuis 1991) ou sur **le titulaire actuel** ? Le texte dit *« l'exploitation effective et continue de l'autorisation »* — ce qui nous arrange — mais la CAA de Lyon a enregistré un plaideur soutenant l'inverse. C'est la seule question qui reste entre toi et un dossier fermé.

[assistant] Noté, et ça explique le trou que le relecteur avait trouvé — pas de vérification entre avril 2022 et avril 2024. Je lance la recherche, puis je reviens sur l'amende.

[assistant] Il existe déjà un `search-ads-idtaxi.py`. Je regarde l'outillage et les comptes disponibles.

[assistant] **Découverte importante : `idtaxi34` EST configuré.** La mémoire disait le contraire — c'est faux, et c'est la boîte qui couvre 2013. Je la fouille.

[assistant] Deux fouilles lancées sur `idtaxi34`. Voilà où on en est.

## Ce que la fouille a déjà donné

**`idtaxi34` est bien branché** — la mémoire disait qu'il ne l'était pas, c'était faux. C'est la boîte qui remonte à 2013, donc celle qui peut contenir l'acte d'achat à Huguet, et peut-être une trace de la création de 1991. C'est la piste la plus prometteuse de la journée.

**Sur l'amende : rien de métrologique pour l'instant.** Les mails ANTAI trouvés sont des contraventions routières ordinaires, pas des sanctions taximètre. En revanche, `Auto Électricité Establet` envoie des rappels annuels — *« Vignette annuelle de VP Taxi, échéance : 09/10/2025 »*. Il y a donc un système de relance, ce qui rend l'oubli de 2023 d'autant plus explicable.

**Une piste à ouvrir :** un mail du 4 octobre 2017, de Jacqueline Berlaud, objet « TR: ID TAXI », qui remonte à la fois sur « taximètre » et sur « Establet ». Antérieur à ton rachat des parts.

## Sur l'amende, ma lecture

Elle ne t'expose pas autant que tu le crains, et elle a même une vertu.

Une lacune métrologique **n'est pas une interruption d'exploitation**. La condition légale porte sur *« l'exploitation effective et continue de l'autorisation »*, pas sur la conformité du taximètre. C'est une non-conformité technique distincte, sanctionnée comme telle, qui n'emporte ni retrait ni suspension de l'ADS.

Et surtout : **on ne verbalise pas le taximètre d'un taxi qui ne roule pas.** L'amende suppose un contrôle en service. C'est, paradoxalement,

[assistant] La fouille donne autre chose que ce que je cherchais, et c'est mieux.

**Aucune trace de l'amende métrologique** dans les boîtes, ni de Huguet, ni de la cession 2013 — cette boîte ne porte pas 2013.

**Mais il y a un fil CPAM de janvier-février 2021 : « ID TAXI 342590445 — Changement de société ».** Tu as prévenu la CPAM de la fusion, à l'époque. Je lis.

[assistant] Les UID viennent du dossier « Tous les messages », pas de l'INBOX — d'où l'erreur. L'outil dédié sait le faire.

[assistant] Trouvé, et ça renverse le point faible du dossier.

**Ce n'est pas une négligence — c'est un arbitrage pris avec la CPAM, par écrit, en 2021.**

- **20/01/2021** — tu écris à la CPAM 34, tu expliques l'absorption, tu joins `FUSION ID SOLEIL.pdf`, tu demandes si tu gardes le 342590445 ou si tu bascules sur le FINESS du Gard.
- **25/01** — tu envoies le RNT pour clôturer au 31/12/2020 et tu saisis la CPAM 30.
- **Début février** — la CPAM du Gard répond : *« votre dossier sera géré par la CPAM de l'Hérault […] demandez-leur de réactiver votre numéro car ils avaient arrêté votre conventionnement au 31/12/2020 »*.
- **08/02/2021** — tu écris à la CPAM 34 : *« nous restons donc en CPAM 34 avec le nom idtaxi, on change juste l'adresse et le RIB »*, Kbis et RIB joints.

Voilà pourquoi tout est resté à l'en-tête ID'TAXI : **la caisse a été informée de la fusion avec le traité en pièce jointe, et le maintien du nom a été acté avec elle.** Tu as les mails, avec dates et interlocuteur nommé (Rudy Hasemann, CPAM 34, 29 cours Gambetta).

Ce que je te présentais ce matin comme « le seul angle d'attaque réel » n'en est plus un.

[assistant] Persisté en mémoire, et la note du mail est corrigée : si le point est soulevé, tu réponds avec ces quatre mails, pas avec « régularisation en cours ».

**Deux choses que la fouille n'a pas trouvées**, et je préfère te le dire plutôt que de te laisser croire :

- **Aucune trace de l'amende métrologique** dans les trois boîtes. Les hits ANTAI sont des contraventions routières ordinaires. Elle est soit papier, soit ailleurs.
- **Rien de 2013 dans `idtaxi34`** — ni Huguet, ni cession, ni l'avocat séquestre. Le contenu utile de cette boîte démarre vers 2018. Inutile d'y rechercher 2013, c'est une piste morte.

Une seule piste reste ouverte si tu veux l'historique d'avant ton rachat : un mail du **4 octobre 2017** dans `clapas`, de Jacqueline Berlaud, objet « TR: ID TAXI ».

---

**Sur le mode 0 token :** j'arrête les lancements. Mais le deep-research que tu as demandé il y a vingt minutes tourne encore en fond, et c'est lui qui consomme — cinq agents de recherche, fetch de sources, vérification adversariale à trois voix.

Dis-moi : **je le laisse finir ou je le coupe ?** Il cherche la seule question qui reste vraiment ouverte — les quinze ans se comptent-ils sur l'autorisation ou sur son titulaire — et avec 1991 c'est ce qui ferme le dossier. Mais si tu veux le silence budgétaire immédiat, un mot et je le stoppe.

[assistant] Je l'ai lue en entier. C'est bien l'amende, et elle est plus précise que ton souvenir.

## Ce que dit le document

**Avis de procès-verbal d'infraction** — article 26 du décret du 30 novembre 1944 sur le contrôle des instruments de mesure.

- **26 mars 2024, 9h30, à Nîmes** — contrôle par **Isabelle Sabatier-Tachy**, agent de l'État, service métrologie légale (DREETS Occitanie)
- Visé : **AMBULANCES DU SOLEIL**, 8 rue du Vieux Bourgidou, Aigues-Mortes — SIREN 432 485 050, SIRET 43248505000053
- Personne rencontrée : **Mme Camille PELLIER**, chauffeur
- Instrument : **taximètre Digitax F1 Plus, n° 1405209**, véhicule **FR-069-KA**
- Motif écrit à la main : *« Vérification périodique du 04/04/2022 »*
- Et sur la page du carnet : **REFUS — « Date limite vérification périodique dépassée (04/04/2023) »**

Donc la chronologie exacte : VP faite le 04/04/2022, valable jusqu'au **04/04/2023**, contrôle le **26/03/2024** avec près de douze mois de retard, régularisation le **15/04/2024** — trois semaines après le PV. Ça colle exactement au carnet.

## Mon analyse

**Ça ne casse rien sur le fond.** Une vérification périodique dépassée est une non-conformité de l'instrument, pas une interruption d'exploitation de l'autorisation. Et le document **prouve le contraire** : le 26 mars 2024, le taxi roulait, avec une conductrice à bord, et il a été contrôlé sur la route. C'est une pièce d'exploitation effective, pas une pièce à charge sur ce point.

**Mais deux choses te concernent vraiment.**

[user] as tu maintenant tout les elements pour que nacko est juste a dire ok c est tres clair maintenant

[assistant] Honnêtement : **oui sur ce qui la bloquait, non sur ce qu'elle doit trancher.** Ce sont deux choses différentes, et il faut les séparer.

## Sur le « mic-mac » — oui, c'est complet

C'est ce qu'elle t'a reproché au téléphone, et c'est réglé.

| Ce qu'elle croyait | Ce que le dossier prouve | Pièce |
|---|---|---|
| Fusion il y a 1-2 ans | Traité du 24/11/2020, effet 31/12/2020 | Dossier de fusion, 49 p. |
| — | Radiation d'ID'TAXI le 15/07/2021 | Kbis, mention 28717 |
| Historique confus | Deux sociétés en treize ans, jamais plus | Chronologie de 15 lignes, chacune sourcée |
| La fusion serait louche | Sa propre mairie l'a qualifiée de « changement de dénomination » | Arrêté du 24/11/2022 |
| L'origine est floue | Fonds acheté 80 000 € à M. Huguet | BODACC, désormais en PDF |
| L'exploitation est douteuse | 129 595 km relevés par un organisme agréé, dernier contrôle avril 2026 | Carnet + référentiel national |

Là-dessus, elle peut dire « ok, c'est clair ». Rien ne manque.

## Sur la cessibilité — non, et ce n'est pas un trou dans mon travail

Trois documents décideraient, et **les trois sont dans ses tiroirs, pas dans les tiens** :

- **L'arrêté du 13 mars 2013 et ses visas.** S'il vise une présentation de successeur ou nomme Huguet, c'est plié. S'il porte « délivrance » sans cédant, on bascule sur quinze ans.
- **Le registre des transactions de l'article L. 3121-4.** Si la vente de 2013 y figure avec son montant, la mutation est irréfutable.
- **La date de création de 1991.

[user] oui ok une fois que tout les doutes leve prepare le mail a la suite du 1er en brouillon pour que je le valide pour l envoie

[assistant] Il y a un protocole établi pour ça — je le relis avant d'agir, et je récupère le mail du 3 août pour enchaîner dans le même fil.

[assistant] Protocole clair : brouillon dans la boîte, tu relis dans Gmail, tu donnes le GO, j'envoie. Je ne touche pas à l'envoi.

D'abord les trois corrections du bordereau.

[assistant] Brouillon déposé. **Rien n'est envoyé.**

| | |
|---|---|
| **Boîte** | `ambudusoleil@gmail.com` → `[Gmail]/Brouillons` |
| **UID** | **79189** |
| **Objet** | Re: Licence de taxi n° 3 - SARL Ambulances du Soleil - projet de cession |
| **Fil** | Chaîné sur ton mail du 3 août (In-Reply-To + References) |
| **Pièces** | 11 fichiers, ~15,7 Mo |

**Les pièces jointes :** l'annonce BODACC · le dossier de fusion complet (49 p.) · le Kbis de radiation d'ID'TAXI · le Kbis de Soleil · les arrêtés municipaux de 2018, 2022 et 2024 · le carnet métrologique complet 2022-2026 · le référentiel national taxi · l'attestation CPAM · les comptes 2014 d'ID'TAXI.

Le corps reprend la chronologie en quinze lignes, chacune avec sa pièce, et se termine sur les cinq documents qu'elle seule détient.

## Trois choses à savoir avant de valider

**Le 1991 est écrit « à confirmer ».** C'est délibéré — on n'a aucune pièce, et c'est devenu la demande n° 1. Si tu veux l'affirmer, dis-le-moi, mais je te le déconseille : c'est exactement ce qui rouvrirait l'impression de flou qu'on vient de fermer.

**Le mail ne qualifie pas la cessibilité.** Il dit « je constate », pas « c'est cessible ». Si elle trouve dans ses registres un document qui contredit, on ne perd rien.

**L'amende métrologique n'y est pas**, et le carnet joint ne contient que les procès-verbaux d'intervention — pas la page du refus de mars 2024. Je l'ai vérifiée page par page.

---

Relis-le dans Gmail. Quand tu me donnes le GO, j'envoie ce brou

[assistant] Non, elle n'est nulle part — elle n'est pas jointe au brouillon. Et pour être franc, je ne l'ai pas écartée par calcul en montant la liste des pièces : j'ai assemblé les preuves et je ne l'y ai pas mise.

Cela dit, en y réfléchissant, **je pense qu'il ne faut pas la joindre à ce mail-ci.**

Ce mail a un seul travail : faire tomber le soupçon de Mme Nako. Il est coopératif, il dit *« rien qui engage la commune à ce stade »*, il demande cinq pièces. Y agrafer une demande formelle signée adressée à la Maire change sa nature — et surtout, ça passe par-dessus la tête de la personne qu'on est justement en train de rassurer. C'est le meilleur moyen de raidir quelqu'un qui se sent déjà mise en cause.

La lettre reprend tout son sens **au temps 2**, quand tu présentes le successeur : là, un acte formel à l'élue est logique, daté, et il ouvre la procédure pour de bon.

Trois options, à toi de trancher :

**La garder pour le temps 2** — mon conseil. Le brouillon part tel quel.

**La joindre quand même** — si tu veux dater la démarche dès maintenant, pour l'échéance. Je supprime le brouillon 79189 et j'en recrée un identique avec la lettre en douzième pièce. Deux minutes.

**L'envoyer séparément à la Maire**, en courrier ou en mail distinct, quelques jours après celui-ci. Ça sépare proprement les deux registres : l'explication à l'agent, la demande à l'élue.

Dis-moi laquelle et j'exécute. Le brouillon ne bouge pas tant que tu n'as pas tranché.

[assistant] Using **jarvis:board** — c'est la version vivante de l'outil (celui sur NotebookLM :3900 est mort depuis mai).

[user] Base directory for this skill: /home/rempc/jarvis/.claude/skills/board

# /board — Conseil JARVIS unifié (jarvis-board)

**Outil** : `~/jarvis/bin/jarvis-board` (Python `scripts/board/cli.py`). Spec : `~/jarvis/docs/specs/2026-07-11-jarvis-board-design.md`.
**Doctrine** : NotebookLM MORT (decision #419). `board.*` Postgres JARVIS-native. Cheap-first, plancher souverain LOI #1.

## Quand l'utiliser
Arbitrage stratégique/technique, best-practice floue, doute (< 1000% sûr) → **règle SACRÉE : ne jamais répondre sans interroger le board**. Remplace « demande au aboard + chatgpt + gemini ».

## Comment (une seule commande)
`~/jarvis/bin` n'est pas sur le PATH → **utiliser le chemin complet** (comme jarvis-media/jarvis-mail),
ou `export PATH="$PATH:$HOME/jarvis/bin"` d'abord.
```bash
B=~/jarvis/bin/jarvis-board

# Conseil complet : route → board local souverain + Gemini + ChatGPT → merge
$B "<la question>"

# Variantes utiles
$B "<Q>" --domain <id>             # forcer un domaine (skip routing)
$B "<Q>" --mode debate|consensus|expert
$B "<Q>" --voices local            # 100% souverain (0 dépendance externe)
$B "<Q>" --seed-url <URL>          # auto-source alimenté par jarvis-media (vidéo/podcast/X)
$B "<Q>" --no-source               # ne PAS créer de domaine si gap
$B "<Q>" --json                    # voix brutes (le merge final = Opus/toi)
$B domains                         # les 14 domaines
$B voices                          # santé local/gemini/chatgpt
```

## Pipeline (ce qui se

[assistant] Board lancé sur les cinq questions qui comptent : envoyer tel quel ou non, demander les pièces plutôt qu'affirmer, joindre ou non la lettre à la Maire, assumer le « 1991 à confirmer », et surtout — ce que je n'ai pas vu.

Je lui ai donné le contexte complet, y compris ce qu'on a **volontairement écarté** du mail : le prix, l'acquéreur, l'échéance, la clause d'acquiescement tacite, et l'amende métrologique. Un audit qui ignore les omissions délibérées ne sert à rien.

Je te fais la synthèse dès qu'il rend — et le brouillon 79189 ne bouge pas d'ici là.

[assistant] Le board a échoué, et pour une raison qui compte : son auto-source appelle `docker exec jarvis-postgres` **en local**, or la pile a migré sur la tour le 3 août. Le conteneur local n'existe plus.

Je regarde s'il existe un domaine qui couvre la question avant de contourner.

[assistant] Le board est **hors service**, et pas qu'un peu : `domains` renvoie **0 domaine**. Il interroge un conteneur local qui n'existe plus depuis la migration du 3 août. Deux autres voix sont tombées aussi — Qwen (modèle passé en payant) et ChatGPT (la clé cassée que j'avais déjà repérée).

Restent trois voix vertes. Je fais l'audit avec elles.

[assistant] Deux voix lancées sur l'audit. Pendant qu'elles tournent, une chose que tu dois savoir sur ton infra.

## Le board est mort, silencieusement

`jarvis-board domains` renvoie **0 domaine**. Pas « le board est vide » — il ne peut pas lire ses données. Il appelle `docker exec jarvis-postgres` **en local**, et depuis la migration du 3 août, la pile tourne sur la tour. Le conteneur local est arrêté en `restart=no`, conformément à ce qui était prévu.

Résultat : le board t'annonce poliment « aucun domaine ne couvre la question » alors que la vraie cause est qu'il n'atteint plus sa base. C'est exactement le type de panne muette que la nuit du 3 au 4 août devait éradiquer — celle-là est passée au travers.

Le healthcheck des voix le confirme, et il en sort deux autres :

| Voix | État |
|---|---|
| OpenClaw | 🟢 |
| Groq — Llama 3.3 70B | 🟢 |
| OpenRouter — Nemotron | 🟢 |
| **board** | 🔴 conteneur local absent |
| **Qwen** | 🔴 le modèle gratuit est passé en payant |
| **ChatGPT** | 🔴 clé écrasée par un reliquat LM Studio |

Trois voix sur six. Aucune de ces trois pannes n'est bloquante aujourd'hui, mais tu croyais avoir six avis et tu en as trois. Le board mérite un correctif — c'est une ligne à changer, le `docker exec` doit passer par `ssh root@100.124.69.1`.

Je te le note pour plus tard, ce n'est pas le sujet de l'heure. La synthèse de l'audit arrive.

[assistant] Gemini est catégorique : **ne pas envoyer en l'état.** La première voix a échoué (fichier vide). Je vérifie et je relance sur une voix verte — une recommandation de tout réécrire mérite un second avis.

[assistant] Voix Groq lancée. En attendant, voici mon désaccord avec Gemini — parce que je ne vais pas te relayer un avis que je crois faux sur un point.

## Là où Gemini a raison, et c'est sévère

**Le volume.** 1 800 mots et 11 pièces jointes à un agent municipal qui te soupçonne déjà, c'est trop. Son argument est bon : quelqu'un de méfiant qu'on submerge de documents n'en conclut pas « tout est clair », il en conclut « c'est bien compliqué, cette affaire ». Le remède devient le symptôme.

**La lettre à la Maire.** Il confirme ce que je te disais : ne pas la joindre. Il va plus loin — ce serait un contournement qui garantirait son opposition frontale.

**Le « 1991 (à confirmer) ».** Il a raison et sa reformulation est meilleure que la mienne. *« L'autorisation a été créée, selon nos informations, en 1991. Pourriez-vous nous en confirmer la date exacte ? »* — même honnêteté, sans le point d'interrogation planté au milieu de la chronologie.

## Là où je pense qu'il a tort

Il te conseille d'**affirmer la cessibilité**. Je ne le suivrai pas.

Il raisonne en psychologie de négociation, et sur ce terrain il a raison : affirmer est plus fort que demander. Mais il ne connaît pas la fragilité juridique du dossier. La CAA de Lyon a jugé un cas où un fonds de taxi vendu à prix s'accompagnait d'une **restitution gratuite** de la licence à la commune, suivie d'une délivrance nouvelle — donc quinze ans. Le seul document qui distingue les deux scénarios, ce sont les **visas de l'arrêté de 2013**, et

[assistant] Trois voix, et sur trois points elles sont **unanimes** : ne pas envoyer en l'état, ne pas joindre la lettre à la Maire, retirer le « 1991 à confirmer ». Quand Gemini, Llama 70B et la cascade convergent sans se connaître, je ne discute pas.

Sur le quatrième point — affirmer ou demander — elles divergent, et je maintiens ma position. Mais elles m'ont fait voir ce qui clochait vraiment : ce n'est pas de **demander** qui affaiblit, c'est de **s'excuser**. « Je ne me permets pas d'en tirer une qualification » sonne incertain. J'énonce les faits sèchement et je demande la procédure. Même prudence juridique, posture bien plus ferme.

[assistant] Audit passé, brouillon refait. **Un seul brouillon en boîte**, l'ancien est supprimé.

| | Avant | Après |
|---|---|---|
| Brouillon | 79189 | **79190** |
| Mots | 1 800 | **553** |
| Pièces jointes | 11 — 15,7 Mo | **4 — 8,5 Mo** |

**Les quatre pièces retenues :** le BODACC de 2013, le dossier de fusion, le Kbis de radiation d'ID'TAXI, le référentiel national taxi. Le reste attend — le mail se termine par *« le dossier complet est prêt, dites-moi ce qui vous serait utile »*. Elle demande, tu envoies. C'est elle qui pilote, et les sept autres pièces deviennent une réponse à sa demande au lieu d'un déluge.

## Ce que l'audit a changé

**La chronologie passe de quinze lignes à quatre dates.** 13 mars 2013, 24 novembre 2020, 15 juillet 2021, 24 novembre 2022. Suivies d'une phrase : *il n'y a eu que deux sociétés en treize ans, et jamais davantage.* C'est ça qui tue le « mic-mac », pas quinze lignes de tableau.

**Le « 1991 à confirmer » a disparu.** Les trois voix ont dit la même chose et elles ont raison : planter un point d'interrogation au milieu de sa propre chronologie, c'est rouvrir le doute qu'on vient de fermer. La date de création reste demandée, mais en fin de mail, comme une pièce parmi deux.

**Le ton a durci là où il fallait.** J'ai supprimé « je ne me permets pas d'en tirer une qualification à votre place ». Les faits sont maintenant énoncés sèchement — achat 80 000 €, cédant nommé, date de commencement égale au jour de l'arrêté, numéro préexistant — et la demande

[assistant] Non, je ne suis pas sûr de moi — et ta question met le doigt sur une vraie faiblesse de mon audit.

**Les trois voix n'ont pas lu le mail.** Elles ont lu *ma description* du mail : « 1 800 mots, 11 pièces jointes ». Elles ont réagi à une statistique. Or il y a une différence entre 1 800 mots de délayage et 1 800 mots où chaque ligne est un fait avec sa pièce en face. La première est une surcharge, la seconde est un document de référence. Elles ne pouvaient pas faire la distinction.

Et surtout : **tu lui as parlé, pas moi.** Ce que tu sens de ce qu'elle a besoin de voir vaut plus que trois modèles qui raisonnent sur un résumé.

Ce que j'aurais dû faire dès le départ : **sortir la chronologie du corps du mail et en faire une pièce jointe.** Le mail reste court — elle lit six cents mots. La chronologie complète, quinze lignes avec chaque pièce en regard, devient un document propre qu'elle ouvre si elle veut vérifier. On ne perd rien, on n'écrase personne.

Je la fabrique.

[assistant] Une page, treize lignes, chaque fait avec le document qui l'établit en regard. Voilà ce qui devait être une pièce jointe depuis le début.

[assistant] Le 79190 n'a pas été supprimé — l'UID avait bougé. Il y a deux brouillons en boîte, exactement ce que le protocole interdit. Je nettoie.

[assistant] Tu avais raison, et l'erreur était méthodologique de mon côté.

**Brouillon `79193`, un seul en boîte** — j'ai supprimé le doublon qui s'était créé au passage.

## Ce que ta question a corrigé

Mon audit était biaisé : les trois voix ont jugé **« 1 800 mots et 11 pièces jointes »** comme une statistique. Elles n'ont jamais vu le texte. Elles ne pouvaient pas distinguer du délayage d'une chronologie où chaque ligne porte un fait et sa preuve. J'ai relayé leur verdict sans voir que je leur avais donné un résumé, pas un document.

La bonne réponse n'était ni la version longue ni la version amputée : **c'était de sortir la chronologie du corps du mail.**

## Ce qui part maintenant

**Un mail de six cents mots** — la fusion date de 2020 et voici pourquoi elle a pu croire 2022, quatre dates clés, l'achat de 2013 avec le BODACC mot pour mot, l'exploitation ininterrompue, et deux demandes : la forme de présentation du successeur, et l'arrêté de 2013.

**Cinq pièces jointes**, dont la nouvelle : `CHRONOLOGIE-ADS-N3-piece-par-piece.pdf`. Une page A4, treize lignes, trois colonnes — date, fait, document qui l'établit. Y compris ses propres arrêtés, ce qui lui montre qu'on ne lui cache rien et qu'elle peut tout recouper depuis ses tiroirs.

Elle lit six cents mots. Si elle veut vérifier, tout est là, en un clic, présenté proprement. Et le mail se termine toujours par *« dites-moi ce qui vous serait utile »* — les huit autres pièces restent en réserve.

On ne perd rien de la démonstration

[assistant] **Envoyé et vérifié au sol.**

```
ENVOYE -> mairie@saintgelydufesc.com
TRACE dans [Gmail]/Messages envoyés : OUI
BROUILLON uid 79193 supprimé — zéro doublon
```

Contre-vérifié indépendamment : **0 brouillon restant**, **5 pièces jointes** présentes dans la copie envoyée, et l'en-tête `In-Reply-To` pointe bien sur ton mail du 3 août — **le fil est chaîné**, elle le retrouvera sous la même conversation.

Message-ID de la copie envoyée : `<178593318188.261886.14618775085040587525@gmail.com>`

## Ce qui part

Six cents mots qui commencent par lui expliquer pourquoi elle a pu croire que la fusion datait de 2022. La chronologie complète en pièce jointe, une page, treize lignes, chacune avec le document qui l'établit — y compris ses propres arrêtés. Le BODACC, le dossier de fusion, le Kbis de radiation, le référentiel national.

Et une porte ouverte : *dites-moi ce qui vous serait utile.*

## La leçon que ta question a produite

Je l'ai écrite en mémoire parce qu'elle vaut au-delà de ce dossier. J'ai fait auditer le mail par trois modèles qui ont tous dit « trop long, ne pas envoyer » — **et aucun n'avait lu le mail.** Ils ont jugé ma description : « 1 800 mots, 11 pièces jointes ». Une statistique. Ils ne pouvaient pas distinguer du remplissage d'une chronologie où chaque ligne porte un fait et sa preuve.

J'ai relayé leur verdict et coupé trop fort. Tu l'as senti. La bonne réponse n'était ni le long ni l'amputé.

**Ne jamais faire auditer un livrable sur son résumé.**

## Ce qui

[assistant] Protocole de fermeture — six étapes, et je vérifie chacune au lieu de l'affirmer.

[assistant] 16 atomes sur 16 vérifiés en base. Contre-vérification par l'outil de lecture, puis backup off-site.

[assistant] Backup en cours. Étapes 1 à 4 faites et **prouvées**, pas affirmées.

| Étape | État |
|---|---|
| 1 — Écriture Postgres | ✅ 16 atomes |
| 2 — Index de reprise | ✅ `atom_INDEX_ads_taxi_n3_20260805`, type `rule`, priorité 9, 6 529 caractères |
| 3 — Vérification | ✅ `SELECT` : 16/16 · `jarvis-mem --grep` les retrouve |
| 4 — SQLite | ✅ sans objet (`memory_atoms` est Postgres-only) |
| 5 — Backup GitHub | ⏳ en cours |
| 6 — Preuve du dump | à venir |

## Ce qui est sauvegardé

Quatorze atomes sur le dossier ADS, plus deux qui comptent au-delà.

**L'index de reprise** est fait pour qu'une session future n'ait rien à redemander : les données certifiées sur pièces, les trois questions encore ouvertes, les prochaines actions, les fichiers, le mail envoyé avec son Message-ID et son chaînage — et surtout **quatre pièges à ne pas refaire**. Le RCS Nîmes. La carte grise au nom de BPCE Lease. Le PV métrologique du 26 mars 2024 qu'il ne faut jamais joindre. Et le fait que l'en-tête ID'TAXI sur les référentiels CPAM n'est pas une négligence mais un arbitrage acté avec la caisse en février 2021.

**Un post-mortem sur ton infra** — les trois voix mortes en silence, dont le board. Avec la leçon qui compte plus que les pannes : tu croyais avoir six avis, tu en avais trois, et rien ne t'a jamais alerté. Tout protocole qui promet un consensus doit commencer par sonder ses voix.

Et la leçon de méthode que ta question a produite : **ne jamais faire auditer un livrable sur son résumé.** Elle est 

[assistant] **Protocole complet. Les six étapes, toutes prouvées.**

| Étape | Preuve |
|---|---|
| 1 — Écriture Postgres | 16 atomes |
| 2 — Index de reprise | `atom_INDEX_ads_taxi_n3_20260805` · `rule` · priorité 9 · 6 529 car. |
| 3 — Vérification base | `SELECT` 16/16 · `jarvis-mem --grep` les retrouve |
| 4 — SQLite | Sans objet (`memory_atoms` est Postgres-only) |
| 5 — Push GitHub | `6602a0e..c37b640 master -> master` · **Push successful** · 525 Mo |
| 6 — **Preuve du dump** | **16 ids sur 16 retrouvés** dans `pg_jarvis_main_20260805_143810.sql.gz` (20 Mo) |

Aucun claim non vérifié : j'ai décompressé le dump réellement poussé et grepé chacun des seize identifiants. Tous présents.

## Ce que la journée laisse derrière elle

**Un mail parti**, chaîné dans le fil du 3 août, cinq pièces jointes, trace confirmée, zéro brouillon résiduel.

**Un dossier complet** dans `~/Bureau/SOLEIL/6-ADS-TAXI-N3/` — 28 pièces inventoriées, une chronologie d'une page pièce par pièce, une lettre signée en réserve pour le temps 2, et un brief pour Brière.

**Une preuve qui n'existait pas ce matin** : le BODACC du 23 avril 2013. Elle était dans une base publique et gratuite, pas dans les archives que tout le monde fouillait depuis deux jours.

**Trois choses qu'on croyait vraies et qui étaient fausses** : le RCS était Nîmes et non Montpellier, l'en-tête ID'TAXI sur les documents CPAM n'était pas une négligence mais un arbitrage acté avec la caisse, et Mme Nako n'avait pas tort sur Béziers — c'est bien le

[assistant] Le deep-research est rentré — **98 agents, 5,4 M de tokens**. Et il apporte la conclusion qui manquait. Je lis le reste.

[assistant] Résultat honnête et important. Je le persiste, puis je reprends le backup pour qu'il y soit.

[assistant] Sauvegarde close, atome vérifié dans le dump poussé (`c37b640..20bd9bc`).

Et le deep-research **renverse le pronostic de ce matin.**

## Le risque que je te signalais est désamorcé

L'affaire d'Appoigny — celle qui pouvait faire basculer sur quinze ans — **ne nous oppose rien.** L'argument y avait bien été soulevé, dans un mémoire du 23 août 2013, mais **la cour n'y a jamais répondu** : elle a tranché sur un tout autre terrain, l'absence de constat d'inaptitude physique. Et ses faits étaient différents des nôtres : la licence avait été restituée gratuitement à la commune puis délivrée à neuf en 2000. Sur ces faits-là, les deux lectures donnaient la même date.

## Toutes les routes mènent à « cessible en 2026 »

| Lecture | Point de départ | Acquis depuis |
|---|---|---|
| Réelle — 15 ans depuis la création | 1991 | **2006** |
| Réelle — 5 ans depuis la première mutation | 2013 | **2018** |
| Personnelle — création de la personne morale | Soleil immatriculée en 2000 | **2005** |
| Personnelle la plus hostile — depuis la fusion | 2020 | **2025** |

Le point qui m'a le plus surpris : une **réponse ministérielle du 1er février 2005** dit que lorsque le titulaire est une société, le délai se compte **à partir de la date de création de la personne morale**. Ambulances du Soleil est immatriculée depuis le 3 août 2000. Vingt-six ans. Même en lecture personnelle — celle que je craignais — la condition est largement remplie.

**Un seul scénario perdant subsiste, et il est étroit :** l