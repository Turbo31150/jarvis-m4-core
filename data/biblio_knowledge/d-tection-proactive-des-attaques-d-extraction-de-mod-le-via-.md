# Détection proactive des attaques d'extraction de modèle via l'analyse des patterns de réponse (response entropy) pour identifier les tentatives de reconstruction du poids du modèle.

*Domaine : Sécurité - Model Extraction & Membership Inference Attacks*

# Détection Proactive d'Extraction de Modèle via l'Entropie des Réponses

## Contexte
Dans les environnements déployant des LLM locaux (ex: Ollama, vLLM) ou des agents autonomes (JARVIS), la sécurité ne se limite pas à la prévention des injections de prompt. Une menace subtile mais destructrice est l'**attaque d'extraction de modèle** (*Model Extraction Attack*). Un attaquant interroge le modèle avec des prompts spécifiques pour reconstruire mathématiquement ses poids internes, volant ainsi la propriété intellectuelle ou créant un clone fonctionnel.

La méthode traditionnelle (analyse des logs textuels) est souvent insuffisante car les réponses semblent normales. La solution réside dans l'analyse métrique de **l'entropie des réponses** (*Response Entropy*). Cette approche proactive détecte les tentatives de reconstruction en identifiant les motifs statistiques anormaux générés par le modèle sous pression d'extraction.

## Points Clés

*   **Principe de l'Entropie de Réponse** : L'entropie mesure le degré de prédictibilité ou de "surprise" dans la distribution des tokens générés. Lors d'une attaque d'extraction, les prompts sont souvent conçus pour forcer le modèle à sortir de sa distribution naturelle (out-of-distribution), provoquant une entropie locale anormalement élevée ou, à l'inverse, une rigidité excessive (entropie basse) dans des zones critiques du vocabulaire.
*   **Signature d'Attaque** : Les attaques de reconstruction (ex: *White-Box*, *Black-Box*) génèrent des séquences où le modèle oscille entre plusieurs probabilités maximales pour chaque token, ou produit des motifs répétitifs artificiels destinés à calibrer l'erreur quadratique moyenne. L'analyse de l'entropie par fenêtre glissante permet d'isoler ces anomalies en temps réel.
*   **Implémentation Linux/Local** : Sur une architecture JARVIS/Linux, cette détection s'intègre au niveau du serveur d'inférence (ex: via un wrapper Python interceptant les sorties de vLLM ou llama.cpp). Il n'est pas nécessaire de connaître les poids secrets ; il suffit de surveiller la variance de l'entropie des tokens générés par rapport à une baseline "normale".
*   **Seuil Dynamique** : Établir un seuil statique est risqué. La détection efficace utilise une fenêtre de référence (ex: les 100 derniers prompts) pour calculer la déviation standard de l'entropie. Si `|Entropie_actuelle - Entropie_moyenne_baseline| > k * Sigma`, un alerte est déclenché.

## Exemple
