# Board JARVIS — ingest de documents Markdown

*Domaine : board*

# Board JARVIS : Ingestion de Documents Markdown - Fiche Technique

**Contexte:**

JARVIS est une application open-source collaborative basée sur LLM (Large Language Model) et offrant des fonctionnalités de board pour la gestion de projets et l'annotation de documents. Une composante clé de cette fonctionnalité est l’ingestion efficace de fichiers Markdown, essentiels pour structurer le contenu de ces boards. Cette fiche documente les aspects techniques importants pour utiliser JARVIS afin d'intégrer correctement vos documents Markdown. L'accent est mis sur une infrastructure Linux basée sur des outils standards utilisés en développement et en apprentissage machine local.

**Points Clés:**

* **Formatage Strict:** JARVIS attend un formatage Markdown strictement conforme à la norme [CommonMark](https://www.commonmark.org/).  Les variations de syntaxe peuvent entraîner des erreurs d'ingestion ou une interprétation erronée du contenu.
* **Base64 Encodage:** Par défaut, JARVIS utilise le Base64 encoding pour incruster les fichiers Markdown directement dans la base de données NoSQL (MongoDB). Ceci permet un stockage compact et une gestion simple des documents.
* **Parsing Markdown:**  JARVIS utilise Jekyll comme moteur de parsing Markdown.  Jekyll est connu pour sa fiabilité et son respect de la norme CommonMark. Il garantit que le contenu structuré (titres, listes, etc.) est extrait correctement.
* **Indexation Vectorielle:** Une fois le markdown ingéré, JARVIS convertit le contenu en embeddings vectoriels via un LLM local servi par LlamaCPP ou un moteur similaire. Cela permet une recherche sémantique accrue et la création de liens entre les documents.
* **Configuration du LLM:** Le choix du LLM est crucial pour la qualité des embeddings. Des modèles comme Mistral ou Zephyr sont souvent recommandés pour leur performance. La configuration (taille du contexte, paramètres) peut impacter les performances et la consommation de ressources.
* **Logique d’Ingestion JARVIS:**  L'ingestion se fait via une API REST qui accepte un nom de fichier Markdown et l'encode B64.  JARVIS effectue ensuite le parsing, crée les embeddings, et stocke les données dans MongoDB.


**Exemple Concret:**

Supposons que vous ayez un document Markdown nommé `projet_alpha.md` contenant :

```markdown
# Projet Alpha - Phase 1

## Objectifs

* Augmenter la visibilité du produit.
* Améliorer l'expérience utilisateur.

## Tâches

- Développer de nouvelles fonctionnalités.
- Mettre à jour l'interface utilisateur.
```

Vous envoyez ce document à JARVIS via sa API avec le contenu encodé en Base64.  JARVIS analysera ce Markdown, créera des embeddings vectoriels pour chaque titre et liste, puis indexera ces embeddings dans MongoDB. L’utilisateur pourra ensuite rechercher "projet alpha" et obtenir les documents liés basés sur la similarité sémantique.

**Pièges:**

* **Images et Liens Externes:**  JARVIS a tendance à mal gérer les images incluses directement dans le Markdown. Les liens vers des ressources externes peuvent ne pas être suivis correctement sans configuration supplémentaire (par exemple, en utilisant un service de link extraction).
* **Tables Complexes:**  Les tables complexes avec plusieurs colonnes et styles personnalisés peuvent poser problème. Testez minutieusement votre Markdown avant l'ingestion.
* **Erreurs d’Encodage B64:** Une erreur lors de l'encodage en Base64 peut compromettre l'intégralité du document. Assurez-vous de bien utiliser un outil fiable pour l'encodage et le décodage.
* **Taille des Fichiers:** La taille maximale des fichiers ingérés est limitée par la configuration de MongoDB.  Pour les documents volumineux, envisagez de diviser le contenu en plusieurs fichiers plus petits ou d’utiliser une solution d’archivage (par exemple, ZIP) avant l'ingestion.
* **Qualité du LLM :** La qualité des embeddings dépend fortement de la capacité du LLM à saisir le sens du texte. Des documents mal écrits ou contenant des ambiguïtés peuvent produire des embeddings inutiles.

Cette fiche fournit une base solide pour comprendre et utiliser l’ingestion de documents Markdown dans JARVIS. N’hésitez pas à consulter la documentation complète et les exemples pour une intégration optimale.
