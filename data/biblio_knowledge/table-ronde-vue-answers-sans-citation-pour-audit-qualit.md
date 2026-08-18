# Table Ronde — vue answers_sans_citation pour audit qualité

*Domaine : table-ronde*

# Audit Qualité : Vue `answers_sans_citation` de la Table Ronde

## Contexte
Dans l'écosystème des tables rondes (souvent implémentées via des agents autonomes ou des LLM locaux comme ceux utilisés par JARVIS), le mécanisme de réponse est crucial. La vue `answers_sans_citation` désigne spécifiquement le mode de sortie où les réponses générées sont purgées de toute référence bibliographique, citation directe ou source externe explicite dans le texte brut retourné à l'utilisateur final.

Cette configuration est stratégique pour les audits de qualité interne. Elle permet d'évaluer la capacité du modèle à synthétiser des informations complexes sans s'appuyer sur des "copier-coller" de sources, testant ainsi la cohérence intrinsèque et la créativité du raisonnement plutôt que sa capacité de référencement. Pour un administrateur Linux ou un développeur LLM local, cela représente une étape clé pour distinguer une hallucination créative d'une simple reproduction de données brutes.

## Points Clés
*   **Purge des métadonnées textuelles** : Le filtre `answers_sans_citation` supprime systématiquement les marqueurs comme `[1]`, `(Smith, 2023)` ou les liens hypertextes intégrés au corps du texte.
*   **Focus sur la synthèse sémantique** : L'objectif est de vérifier si l'agent comprend le sujet (ex: architecture Linux) et peut reformuler des concepts techniques sans jargon citationnel.
*   **Optimisation UX/UI** : Dans une interface utilisateur finale, ce mode évite d'encombrer la lecture avec des références académiques inutiles pour un support technique immédiat.
*   **Séparation des couches** : La source de vérité reste accessible dans les logs ou le contexte système, mais l'interface n'affiche que la conclusion traitée.

## Exemple Concret
Imaginez une requête posée à JARVIS concernant l'optimisation d'un serveur Nginx :

*   **Mode standard (avec citation)** : "Il faut ajuster `worker_connections` selon les recommandations de *The Linux Foundation* [1] et utiliser `nginx -t` pour valider la config."
*   **Mode `answers_sans_citation`** : "Ajustez le paramètre `worker_connections` dans le bloc `events` pour gérer plus de connexions simultanées. Validez toujours la configuration finale en exécutant la commande `nginx -t` avant de recharger le service."

Dans le second cas, l'information technique est intacte et actionnable, mais la référence à l'autorité externe a été retirée pour un audit purement fonctionnel.

## Pièges
*   **Perte de traç
