# Table Ronde — contrainte citation obligatoire corpus

*Domaine : table-ronde*

# Contrainte "Citation Obligatoire Corpus" en Table Ronde

## Contexte
Dans les architectures de type **Table Ronde** (souvent utilisées pour le RAG - *Retrieval Augmented Generation* ou les systèmes d'agents collaboratifs), une contrainte spécifique impose que toute réponse générée par l'LLM doit s'appuyer exclusivement sur des citations extraites du corpus de référence fourni lors de la phase de récupération (*retrieval*). Cette contrainte est cruciale pour garantir la **fidélité factuelle**, éviter les hallucinations et assurer la traçabilité des informations, particulièrement dans des environnements Linux ou des déploiements JARVIS où l'intégrité des données est primordiale.

## Points Clés
*   **Source Unique de Vérité** : Le modèle ne doit jamais utiliser ses connaissances paramétriques (entraînement) pour compléter les réponses. Chaque affirmation doit être ancrée dans le contexte récupéré.
*   **Formatage Strict** : Les citations doivent respecter un format normalisé (ex: `[Citation #1]`, `--- Source A ---`) pour permettre une validation post-génération automatisée par des scripts Python ou Bash.
*   **Gestion de l'Absence de Données** : Si le corpus ne contient pas la réponse à la requête, le système doit déclencher un protocole d'échec explicite ("Information non trouvée dans le corpus") plutôt que de générer une réponse spéculative.
*   **Préservation du Contexte** : Le chunking (découpage) du corpus doit être suffisamment granulaire pour fournir les phrases exactes nécessaires, sans couper les idées au milieu d'une citation obligatoire.

## Exemple Concret
**Requête utilisateur** : "Quel est le protocole de sécurité recommandé pour SSH dans notre documentation interne ?"

**Réponse LLM (avec contrainte active)** :
> Selon la directive de sécurité v2.1 du corpus, l'utilisation de clés RSA de 2048 bits ou plus est obligatoire pour tous les nouveaux serveurs.
> `[Citation #3 : "SSH doit utiliser des clés RSA >= 2048"]`
> De plus, le saut de version (jump host) doit être configuré avec une authentification mutuelle.
> `[Citation #7 : "Jump host requires mutual authentication"]`

*Note : Aucune information externe n'a été ajoutée à ces affirmations.*

## Pièges Techniques
*   **Hallucination de Citation** : Le risque majeur est que l'LLM invente une citation ou attribue un contenu du corpus à une source incorrecte. Cela brise la confiance du système et fausse les logs d'audit.
*   **Sur-synthèse** : Tenter de résumer trop longuément peut
