# Trieur dématérialisé par élève — 0 € · 0 papier · réutilisable
Logique : au lieu d'un porte-vues papier par élève (coût + papier), un "trieur" NUMÉRIQUE par élève.

## Le moins cher (gratuit, déjà dispo)
- **1 dossier numérique par élève** = déjà présent dans l'app (carnet : `/api/carnet/eleve/<id>`).
  Chaque élève a son historique (évals, comportement, ceintures, travaux) — c'est le trieur.
- **QR / lien unique par élève** vers son dossier partagé (Drive) → le parent scanne, tout est classé,
  zéro impression. (Générable en lot ; 1 QR = 1 élève.)
- **Rubriques standard** (mêmes onglets qu'un porte-vues) : Lecture · Maths · Arts · Vie de classe · Autonomie.

## Si un support papier reste nécessaire (sortie, autorisation)
- Dématérialiser d'abord (coupon numérique / case à cocher en ligne). N'imprimer QUE le strict minimum,
  recto-verso, 1 page, réutilisable d'une année sur l'autre (placeholders).

## Optimisation ressources
- 1 modèle → N élèves (fusion prénom via `/api/mail-parent/draft` ou publipostage).
- Rien de jetable : les modèles et dossiers se réutilisent chaque année (changer date/prénom).
- Papier économisé ≈ (nb élèves × nb feuilles porte-vues) → 0.

## Fournitures : ce qui reste vraiment utile (liste minimale MS)
- Porte-vues : **optionnel** si trieur numérique adopté. Sinon **1 porte-vues 40 vues** partagé/prêté suffit.
- Le reste (colle, crayons…) : mutualiser en bacs de table plutôt qu'un lot par élève (moins cher, moins de perte).
