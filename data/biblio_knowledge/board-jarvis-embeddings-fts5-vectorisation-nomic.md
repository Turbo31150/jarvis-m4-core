# Board JARVIS — embeddings FTS5 + vectorisation nomic

*Domaine : board*

## Board JARVIS : Embeddings FTS5 + Vectorisation Nomic - Guide Technique

**Contexte:**

Board JARVIS est une plateforme de recherche et d’analyse basée sur des LLMs locaux (Large Language Models).  L'un de ses points forts repose sur la compatibilité avec FTS5, un moteur de recherche full-text avancé, ainsi que sur la vectorisation d’embeddings, permettant une recherche sémantique performante au-delà de la simple correspondance mot à mot.  Cette fiche vise à fournir une compréhension pratique pour les utilisateurs et développeurs intégrant cette fonctionnalité dans leur workflow JARVIS (principalement sous Linux).

**Points Clés:**

* **FTS5 - Recherche Full-Text Sémantique:** FTS5 est un moteur de recherche open source optimisé pour l'utilisation avec des LLMs. Il permet d’indexer et de rechercher des textes en tenant compte du contexte, ce qui améliore considérablement la précision des résultats.  Il utilise des "tags" et des "boosters" pour ajuster le score de pertinence.
* **Embeddings (Vectorisation):** Les embeddings sont des représentations vectorielles de vos données (textes, documents).  JARVIS utilise un modèle d'embedding pré-entraîné (ex: Sentence Transformers) pour transformer le texte en ces vecteurs. Plus deux textes sont similaires sémantiquement, plus leurs embeddings seront proches dans l’espace vectoriel.
* **Vectorisation Nomic:** JARVIS intègre une "vectorization nomic"  qui se réfère à la transformation des documents en un ensemble de vecteurs optimisés pour le moteur FTS5. Cela permet d’améliorer considérablement les performances des recherches sémantiques. Cette étape est cruciale et doit être configurée correctement.
* **Intégration JARVIS:** La vectorisation et l'indexation sont gérées via le plugin JARVIS.  L'utilisateur fournit ses données (documents, fichiers) qui sont traités par le backend pour générer les embeddings, puis indexés dans FTS5 en utilisant cet espace vectoriel.
* **Sélection de Modèles d’Embeddings:** Le choix du modèle d'embedding influence grandement la performance. Explorez des modèles adaptés à votre domaine et langue (sentientAI, polyglot, etc.).  Considérez également leur taille : les modèles plus grands offrent souvent une meilleure précision mais nécessitent plus de ressources.

**Exemple Concret:**

Imaginez que vous recherchez "solutions d'automatisation du marketing digital" dans JARVIS. 

1. **Indexation:** Les documents contenant ces termes (articles, rapports, etc.) sont transformés en embeddings via un modèle Sentence Transformers pré-entraîné.
2. **Vectorisation Nomic:**  Ces embeddings sont ensuite indexés dans FTS5.
3. **Recherche:** Lorsque vous tapez votre requête, she est également convertie en embedding.  FTS5 utilise l'index vectoriel pour trouver les documents dont l’embedding est le plus proche, même si la phrase exacte "solutions d'automatisation du marketing digital" n'existe pas dans ces documents. L'algorithme considère des synonymes et des concepts associés (ex: "stratégie digitale", “outils de marketing”).

**Pièges:**

* **Mauvaise Vectorisation:**  Une vectorisation mal configurée, avec le mauvais modèle d’embedding ou des paramètres incorrects, peut entraîner une dispersion excessive des vecteurs et dégrader les performances de recherche.
* **Taille du Vocabulaire:** Si votre corpus est trop spécialisé, un modèle généraliste pourrait ne pas être suffisant pour capturer la nuances sémantiques.
* **Fréquence des Mots-Clés:** L’utilisation excessive de mots-clés courants peut masquer les documents pertinents.  Soignez le "tagging" dans FTS5.
* **Mise à Jour de l'Index Vectoriel:** N'oubliez pas d'indexer régulièrement les nouveaux documents pour maintenir la pertinence des résultats.  Automatisez cette tâche si possible.


**Ressources Supplémentaires :**

* Documentation JARVIS: [https://jarvis.project/documentation](lien fictif)
* FTS5: [https://fts5.readthedocs.io/en/latest/](lien vers la documentation FTS5)
* Sentence Transformers: [https://huggingface.co/sentence-transformers/models](lien vers les modèles de Sentence Transformers)
