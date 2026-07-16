# Pack modèles — Communication école-famille

Modèles **prêts à remplir** (0 donnée élève) + **générateur cascade 0-token** pour
devancer les tâches récurrentes : mails parents, mots collectifs, réunions, autorisations.

## Générer un brouillon (cascade IA locale, gratuit)
```bash
cd ~/jarvis/webapp/modeles-communication
./generer.sh                                   # liste les modèles
./generer.sh mail-difficulte "faits datés + propose un RDV"
./generer.sh mot-sortie "Louvre, 12 mai, car, pique-nique"
```
→ brouillon affiché + sauvé dans `brouillons/`. **Toujours relire** (faits, dates, RGPD) avant envoi.

## Catalogue
| Dossier | Modèle | Usage |
|---|---|---|
| mails/ | `mail-progres` | valoriser un progrès |
| mails/ | `mail-difficulte` | alerter sans inquiéter (+ RDV) |
| mails/ | `mail-absence` | signaler / demander justificatif |
| mails/ | `mail-rdv` | proposer une rencontre |
| collectifs/ | `mot-sortie` | sortie **+ coupon d'autorisation** |
| collectifs/ | `mot-materiel-info` | info / matériel |
| collectifs/ | `mot-reunion-rentree` | inviter à la réunion de classe |
| reunions/ | `convocation-equipe-educative` | convocation formelle |
| reunions/ | `compte-rendu-reunion` | tracer décisions |
| reunions/ | `prep-reunion-parents` | trame d'animation |
| autorisations/ | `autorisation-sortie` | sortie (à signer) |
| autorisations/ | `droit-image` | photos/vidéos scolaires |
| autorisations/ | `decharge-recuperation` | personnes habilitées |
| conflit/ | `reponse-parent-mecontent` | apaiser, ne pas répondre à chaud |

## Règles (RGPD / institutionnel)
- Vouvoiement, factuel, jamais de jugement sur l'enfant.
- Un message individuel ne parle que de l'enfant concerné — jamais d'un autre élève.
- Aucune donnée sensible (santé, situation familiale) dans un envoi collectif.
- Toujours finir par une solution / un RDV + signature (nom, classe, école).

## Cascade & données réelles
Le générateur remplit à partir de faits que **vous** fournissez. Pour un mail nominatif
tiré de la base élèves, utiliser la route webapp `POST /api/mail-parent/draft`
(`prof_routes.py`) — les prénoms viennent de la table `eleves`, jamais stockés ici.
