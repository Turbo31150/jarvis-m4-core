[user] nordine viens d avoir karim apaprement il n aurai pas eu l accord de financement , la banque juge la societe pas solvable

[assistant] Nordine te remonte que Karim n'aurait **pas** l'accord de financement — banque estime la société non solvable. C'est un événement majeur sur la cession. Je vérifie l'état mémoire exact (clause financement + qui est jugé non solvable) avant de te donner ma lecture et de logger.

[assistant] Voilà l'élément qui change tout dans ta mémoire, et je te donne ma lecture — **avant** de logger.

## Le point contractuel clé (clause 4.1 du compromis)

La condition suspensive de financement n'est **« défaillie » qu'avec un refus DOCUMENTÉ d'au moins 2 banques**. Donc :

**Un seul refus (Crédit Agricole du Languedoc) ≠ compromis caduc.** Le deal n'est PAS mort à ce stade. C'est un signal fort, pas un couperet. Karim garde l'obligation d'avoir déposé chez ≥2 banques (clause exigeait dépôt sous 15j) — s'il n'a sondé qu'une banque, il n'a même pas rempli la condition pour faire tomber la clause à son avantage.

## L'ambiguïté critique à lever : *quelle* société est jugée non solvable ?

Deux lectures très différentes :

1. **La structure acquéreur de Karim** (holding/ses 2 sociétés d'ambu) → problème de Karim, il re-dépose ailleurs ou le financement meurt de son côté.
2. **La cible Ambulances du Soleil elle-même** → là c'est ta pomme. Et il y a un lien que je te signale **en hypothèse à vérifier, pas comme un fait** : tu as fait la **disclosure complète des litiges sociaux à Brière le 20/07** (Coste + Soufiane ~102k + prud'hommes). Si la banque a intégré ce passif prud'homal dans la valorisation post-acquisition, ça peut expliquer un « société pas solvable ». Si c'est ça, le risque, c'est que **les autres banques refusent pour la même raison** → là le deal est vraiment menacé.

## Ce qu'il faut arracher à Nordine/Karim (dans l'ordre)

1. **Refus écrit ou verbal ?** (la clause 

[assistant] Le gate mémoire exige que je consulte la mémoire de session d'abord. Je le fais.

[assistant] Mémoire consultée — rien ne contredit ma lecture (closing non fait, crédit Karim CA Languedoc en cours, structure GAP/litiges cohérente). J'insère l'atome.

[assistant] Le fichier n'a pas été écrit (le gate avait bloqué le Write). Je le recrée maintenant.

[assistant] ✅ Loggé (`atom_cession_financement_karim_refus_alerte_20260722`, priorité 9, confidence *unconfirmed*).

## Synthèse pour toi

**Ne panique pas, mais serre la vis maintenant.**

- **Contractuellement** : 1 refus (CA Languedoc) ne fait PAS tomber le compromis. Il faut un **refus écrit de ≥2 banques** (clause 4.1) pour que la condition soit défaillie. Le deal tient juridiquement.
- **Le vrai danger** n'est pas ce refus isolé — c'est *pourquoi* : si c'est **la cible Soleil** jugée non solvable (et pas la structure de Karim), le passif prud'homal (Coste + Soufiane ~102k) risque de faire refuser **toutes** les banques. Là, c'est structurel.

**Prochaine action = 4 réponses à arracher à Nordine/Karim** (par écrit si possible) :
1. Refus **écrit ou verbal** ?
2. **Quelle société** non solvable — Karim ou Soleil ?
3. **2ᵉ banque** déposée, oui/non ?
4. Karim **redépose ou lâche** ?

Dès que tu as ça — surtout la réponse au #2 — dis-le-moi : si c'est la cible qui coince, on bascule sur l'arbitrage (renégo prix / renforcer le de-risk des litiges pour rassurer la banque / acquéreur alternatif), et là je te branche **Solal + le board cession** avant que tu répondes à Nordine.

Tu veux que je prépare dès maintenant le **message à Nordine** avec ces 4 questions cadrées, prêt à envoyer ?

[user] les bilans de soleil pas bon , les prudhom c est moi qui les prends enn charge donc peu d incidence quele strategie me sonsille tu ? baisser le rpix par ex a

[assistant] Deux infos qui tranchent tout : c'est la **cible (Soleil)** qui coince (bilans faibles), pas la structure Karim — et les prud'hommes sont à **ta** charge, donc hors sujet pour la banque. Je consulte la mémoire (pré-flight + vérifier ce qu'on sait des bilans/montage) avant de te conseiller.

[assistant] Mémoire confirme le montage (SCI murs adossés à l'actif Aigues-Mortes, apports SCI symboliques 400€, aucun crédit-vendeur évoqué jusqu'ici). J'ai ce qu'il me faut. Je logge la clarification et je te donne ma reco.

[assistant] Le gate exige explicitement `ctx_search`/`ctx_batch_execute` (context-mode reconnecté). Je le satisfais.

[assistant] ✅ Clarification loggée. Maintenant ma reco.

## Ne baisse **pas** le prix en premier réflexe

La banque refuse parce que la **SARL ne dégage pas assez de cash pour rembourser les 820k de dette d'acquisition** (les bilans sont faibles → ratio de couverture insuffisant). Baisser le prix règle ça *mécaniquement* (moins de dette = annuité plus basse = ratio qui repasse) — mais c'est le levier **le plus cher pour toi** : perte sèche nette contre ton objectif 1,5M et ton montage 150-0 B ter. Il y en a 3 moins coûteux à jouer **avant**.

**Ordre optimal (du moins cher au plus cher pour ta poche) :**

1. **Retraiter les bilans (EBITDA normatif) — gratuit.** « Bilans pas bons » ≠ forcément boîte non rentable. On réintègre ta rémunération de gérant, les charges exceptionnelles, et surtout **la reprise de salaire Coste** (charge pré-cession qui plombe le résultat mais ne se reproduira pas). Un EBITDA retraité par ton expert-comptable peut redresser la lecture **sans que tu lâches un euro**. → Première chose : savoir *pourquoi* les bilans sont mauvais — conjoncturel/exceptionnel ou structurel ?

2. **Crédit-vendeur 150–200k — LE levier n°1.** Au lieu de baisser le prix, tu acceptes qu'une tranche (sur la jambe SARL) soit payée en **différé sur 2–3 ans**, subordonnée à la banque. Effet : la banque ne finance plus que ~620–650k → ratio au vert → accord. Triple avantage : tu **gardes le prix nominal** (tu touches tout, juste étalé, avec intérêts possibles), ça **prouve ta confiance** à la b