# DOSSIER COMPLET — Essence AlkymIA : Checkpoint sécurisé

> Dossier self-contained. Source : Notion (Naming, Board prix packs, Présentations, Preuves). Aucun secret dans ce dossier.

## Nom commercial & tagline
**Les Essences AlkymIA — Checkpoint sécurisé** — « Sauvegardez votre app sans jamais fuiter une donnée. »
Brique à la carte, aussi intégrée au Pack Gouvernance Claude Code. (Nom technique : checkpoint-securise.)

## Cible
Développeurs, makers et enseignants qui versionnent une app (webapp, outil local) et veulent un backup + push GitHub garantissant zéro secret / zéro donnée personnelle poussés.

## Problème
Un `git push` mal cadré expose vite une base `*.db`, un `.env` ou une clé ; on veut un garde-fou automatique, pas une checklist manuelle.

## Promesse
Un checkpoint qui sauvegarde le code (backup SQLite local + commit/push) tout en bloquant systématiquement bases, secrets et binaires lourds. Garantie « 0 secret / 0 PII poussé ».

## Ce qui est inclus (fichiers réels de ce dossier)
- `scripts/checkpoint.sh` — driver de sauvegarde + garde anti-fuite
- `SKILL.md` — skill Claude Code (déclencheurs)
- `README.md` — usage
- `FICHE-VENTE.md` — argumentaire
- `LICENSE.txt` — licence propriétaire

## Différenciateur
Garde-fou RGPD intégré (filtre `.db`/`.env`/`.key`/`.pem`/binaires avant tout push) + tout reste local, épaulé par un humain joignable.

## Preuves réelles (honnêtes)
- PassCerfa — application IA d'assistance aux démarches administratives, 100 % on-premise (RGPD), prouve la maîtrise de la conformité. [source : passcerfa-app]
- Plus de 160 dépôts de code — capacité de production démontrée.
- [À CONFIRMER] Témoignage + STAT d'adoption.

## Offre, prix & CTA
**29 €** — paiement unique (ancrage Essences). Inclus dans le Pack Gouvernance Claude Code (79 €).
CTA : « Je commence par une Essence ».
Canal : Gumroad.

## Landing
Pas de landing dédiée (brique à la carte).

## Placeholders honnêtes restants
- Témoignage + statistique d'adoption.
- Contact support dans `LICENSE.txt`.
