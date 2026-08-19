# SEQUENCE MODELE — campagne prospection freelance IA (19/08/2026)
# A rejouer telle quelle. Ce qui a marche, ce qui a coince, et pourquoi.

## L'enchainement qui a produit du resultat
1. MESURER LE MARCHE AVANT DE PARLER. moisson_freework.py (JSON-LD JobPosting) ->
   344 puis 1400+ missions datees, avec TJM. C'est cette mesure qui a fait pivoter
   le positionnement : « IA locale souveraine » n'est PAS demande sur le marche
   generaliste (0 des 16 missions Occitanie la mentionne). Sans la mesure, on aurait
   campagne sur une accroche que personne ne cherche.
2. PIVOTER LE DISCOURS SUR CE QUI EST ACHETE. v1 parlait aux PME (souverainete).
   v2 parle aux AGENCES (delivery technique, marque blanche, absorption de pics).
   Changement de CIBLE, pas de vocabulaire — c'est ce qui rend un pivot reel.
3. SORTIR DU PLAFOND GEOGRAPHIQUE. Toulouse plafonne (mesure : 400-520 sur la plupart),
   Paris monte a 700-900. La delivery ne demande pas de presentiel -> viser le remote.
   NB : une mission Toulouse a 570-800 (Architecte IA/MLOps, Talents Finance) a
   partiellement invalide le plafond. Toujours re-mesurer, ne pas figer une conclusion.
4. DEUX NATURES DE CASH, NE JAMAIS LES MELANGER.
   - Forfait avec acompte (offres 1/2/3) = cash a la SIGNATURE. Seul chemin vers
     « 1k en 10 jours » : acompte 40% d'un Sprint a 2500 = 1000 EUR.
   - Regie FreeWork = cash a J+45. Excellent pipeline de fond, inutile pour l'urgence.
   Dans le tracker : acompte % = 0 sur la regie, sinon le tableau de bord ment.
5. LE VOLUME NE VIENT PAS DE LINKEDIN. Plafond 15-20 invitations/semaine + quota
   gratuit atteint en une journee. Le gisement dense est FreeWork (1400+ missions).
   LinkedIn = canal de POSITIONNEMENT (le post), pas de volume.
6. PUBLIER LE POST > 100 COMMENTAIRES. Confirme sur le terrain.

## Les pieges rencontres (couter cher deux fois serait bete)
- LIGNE D'EXEMPLE DANS UN TABLEUR : « Cabinet Dupont 2500 a 0.3 » etait dans la plage
  agregee -> 750 EUR de pipeline fantome des l'ouverture. Toujours ecraser les exemples.
- CHIFFRES PERIMES QUI SURVIVENT : « 1000+ agents / 12 GPU / 6 machines / <300 ms »
  invalides le 18/08 (reel : 928 / 6 / 3-4 / <500 ms mesure) mais toujours presents
  dans le mega-prompt, le cron quotidien, le post v1 et le pack commentaires.
  Un chiffre perime se propage plus vite qu'il ne se corrige.
- EMAILS EN contact@ : 9 des 12 agences moissonnees sont sur ce motif generique.
  Les 12 domaines ont des MX valides (verifie), mais MX valide != adresse existante.
  Parade : envoyer par lots de 3-4, surveiller les bounces avant d'elargir.
- MODELE THINKING QUI NE REND RIEN : qwen3.5-9b consomme 100% de max_tokens en
  reasoning_tokens et renvoie un contenu VIDE. enable_thinking:false et
  reasoning_effort sont IGNORES par cette version de LM Studio. Ne pas compter
  dessus pour de la generation en masse sans budget de tokens tres large.
- COMPTER LES SUCCES SANS LIRE LE CONTENU : « 10/15 generees » etait faux, les 10
  etaient vides. Un compteur qui ne teste que l'absence d'erreur ne mesure rien.
- CONCURRENCE SUR UN SEUL NOEUD : board (4 experts) + vectorisation (4 workers)
  depassent le PARALLEL=4 de M6 -> HTTP 500 et voie vectorielle hors service.
  BOARD_ASK_PAR=1 pour les faire cohabiter.
- GPU EN D3cold : les 4 GPU de M6 se sont endormis sans pouvoir se reveiller
  (« Unable to change power state from D3cold to D0 »), driver corrompu (kernel oops
  dans nvidia_modeset). Symptomes trompeurs en amont : embedding passe de 0,29 s a
  20 s, modeles qui refusent de charger, thinking interminable. Tout venait de la.
  Seul remede : reboot. Forcer power/control=on ne suffit pas.

## Regle d'or confirmee
Preparer, jamais envoyer. Le clic reste chez Franck. Aucune adresse devinee.
