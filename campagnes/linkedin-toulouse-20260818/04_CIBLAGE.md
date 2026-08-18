# CIBLAGE — où trouver les cibles

## A. RECRUTEURS DÉJÀ EN BASE (10 profils réels, URLs vérifiées)
Table : jarvis_master.db → campagne_linkedin_20260818 (canal='RECRUTEUR')
Liste :  sqlite3 ~/jarvis/jarvis_master.db "SELECT nom,entreprise,profil_url FROM campagne_linkedin_20260818 WHERE statut='A_INVITER';"

## B. EN TROUVER D'AUTRES — recherches LinkedIn prêtes à ouvrir
Filtrer ensuite : Lieu = Toulouse et périphérie · Relations = 2e degré

1. Recruteurs tech généralistes
   https://www.linkedin.com/search/results/people/?keywords=recruteur%20tech%20toulouse
2. Talent Acquisition
   https://www.linkedin.com/search/results/people/?keywords=talent%20acquisition%20toulouse
3. Chasseurs de tête IT
   https://www.linkedin.com/search/results/people/?keywords=chasseur%20de%20t%C3%AAte%20IT%20toulouse
4. DRH / RRH locaux
   https://www.linkedin.com/search/results/people/?keywords=DRH%20toulouse
5. Recruteurs spécialisés IA / Data
   https://www.linkedin.com/search/results/people/?keywords=recruteur%20data%20IA%20toulouse

## C. STARTUPS « DANS LE BESOIN » — la preuve avant le message
Une startup « dans le besoin » se repère à un signal PUBLIC et DATÉ. Trois signaux valables :
  S1. Elle recrute un profil IA/data/DevOps  → offre d'emploi ouverte
  S2. Elle vient de lever des fonds          → communiqué daté
  S3. Elle publie sur un problème technique  → post LinkedIn récent

Recherches prêtes :
- Offres IA Toulouse (S1)
  https://www.linkedin.com/jobs/search/?keywords=ing%C3%A9nieur%20IA&location=Toulouse
- Offres DevOps/Infra Toulouse (S1)
  https://www.linkedin.com/jobs/search/?keywords=DevOps%20infrastructure&location=Toulouse
- Écosystème local (S2) : https://www.latribune.fr/toulouse/  ·  https://toulouse.latribune.fr
- Annuaire French Tech Toulouse (S2) : https://lafrenchtech-toulouse.com

RÈGLE : pas de signal daté = pas de message. La ligne {preuve} du message C
doit citer le signal, sinon le message part à la poubelle.

## D. CE QUI EST BLOQUÉ — à savoir
Les 18 emails « recruteurs » de la table recruteurs_toulouse sont NON PROUVÉS
(0/18 présents dans contacts_preuve : construits par motif, jamais vérifiés en HTML).
=> Règle d'or : AUCUN envoi SMTP vers ces 18 adresses.
=> Ces 18 entreprises se travaillent via LinkedIn ou via leur formulaire officiel.
