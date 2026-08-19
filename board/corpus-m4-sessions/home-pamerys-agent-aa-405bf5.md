[user] Tu es l'agent CORRECTION-PREUVE. Objectif : retirer/nuancer une preuve NON VÉRIFIÉE dans 2 landings + noter dans Notion. Aucun secret. Rien publié.

FAIT : la mention « SaaS mairies 290-890 €/mois » (repo workflow-gestion) est INTROUVABLE/non étayée dans les sources (confirmé par l'audit preuves). Elle ne doit PAS être présentée comme un fait de vente.

ÉTAPE 1 — Édite (Read puis Edit, minimal, ne casse pas le HTML) :
- /home/pamerys/jarvis/livrables/alkymia-sovereign/landing.html
- /home/pamerys/jarvis/livrables/alkymia-suite/landing.html
Dans chaque : trouve la/les mentions « mairies », « 290-890 » ou « SaaS mairies » et remplace par une formulation NEUTRE et honnête, soit :
- la retirer, soit la remplacer par « [RÉFÉRENCE-CLIENT À CONFIRMER] » / « projet de gestion pour collectivité (à documenter) ».
Ne touche à rien d'autre. Vérifie que le HTML reste valide (balises équilibrées). Sauvegarde .bak avant édition.

ÉTAPE 2 — Vérifie aussi rapidement (grep/Read) si d'autres landings (jarvis-domino-engine, formation, board-souverain-b2b) contiennent la même mention mairies non vérifiée ; si oui, corrige pareil.

ÉTAPE 3 — Note dans Notion, sur la page « 🏆 Preuves & crédibilité AlkymIA » (cherche-la via search « Preuves crédibilité AlkymIA »), append un callout « ⚠️ CORRECTIF appliqué aux landings : la mention 'SaaS mairies 290-890€/mois' a été retirée/nuancée (non étayée). À ne réintroduire que si Franck confirme un vrai client. »
REST : token /home/pamerys/.config/jarvis/notio

[assistant] Now applying the edits. The two main files first, then the pack-n8n (which is already partly nuanced but still asserts usage).

[assistant] Terminé.

Fichiers corrigés (3, .bak créés pour les 2 landings principaux) :

| Fichier | Avant | Après |
|---|---|---|
| alkymia-suite/landing.html | « Des mairies déjà équipées… mairies en SaaS souverain (290 à 890 €/mois) » | « Un savoir-faire orienté collectivités… Projet de gestion pour collectivité (à documenter) — [RÉFÉRENCE-CLIENT À CONFIRMER] » |
| alkymia-sovereign/landing.html | « Déjà en production dans le secteur public… mairies en SaaS souverain (290 à 890 €/mois) » | « Une approche orientée secteur public… Projet de gestion pour collectivité (à documenter) — [RÉFÉRENCE-CLIENT À CONFIRMER] » |
| pack-n8n-workflows/landing.html (trouvé en plus) | « SaaS mairies » / « en usage auprès de collectivités » | « Collectivités » / « Projet de gestion pour collectivité (à documenter) [RÉFÉRENCE-CLIENT À CONFIRMER] » |

Autres landings vérifiées : jarvis-domino-engine et board-souverain-b2b = aucune mention (rien à corriger) ; pas de dossier « formation ».

- Mention « 290/890 » : 0 occurrence restante dans les 3 fichiers.
- HTML valide : oui (balises `<div>` et `<p>` équilibrées dans les 3 fichiers).
- Callout Notion : ajouté sur la page « 🏆 Preuves & crédibilité AlkymIA (réelles) » (⚠️ fond jaune, statut OK).
- Aucun secret affiché, rien publié en ligne (édition locale + note Notion uniquement).