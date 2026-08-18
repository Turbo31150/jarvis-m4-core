# Fiche de vente — cloud-router-8

> Prix PROPOSÉ, à valider par Franck (cohérent avec les scripts/dev-tools 39 €).

## Accroche
Traitez des centaines de prompts en parallèle sur le cloud Ollama gratuit —
sans surchauffer votre machine, sans jamais exposer une clé.

## Le problème
Un modèle local, c'est lent et ça chauffe dès qu'on enchaîne les prompts. Les
clés cloud, elles, se gaspillent quand on les utilise une par une.

## La solution
cloud-router-8 répartit automatiquement votre file de prompts sur jusqu'à 8 clés
Ollama Cloud, en parallèle, avec rotation intelligente : clé saturée = clé
suivante, clé morte = retirée. Sortie JSONL idempotente : le batch reprend
exactement où il s'est arrêté.

## Ce que vous recevez
- Le routeur Python (aucune dépendance, stdlib seule)
- Documentation détaillée (`CLOUD-ROUTER-8.md`)
- Mode `--selftest` pour vérifier vos clés d'un coup

## Points forts
- 0 chaleur machine (tout est déporté)
- Sécurité clé : jamais en dur, jamais affichée
- Idempotent, retry backoff, workers configurables

## Prix
**39 € — paiement unique** [PROPOSÉ, à valider].

## Cible
Développeurs, indépendants et makers qui génèrent du contenu en volume via IA.
