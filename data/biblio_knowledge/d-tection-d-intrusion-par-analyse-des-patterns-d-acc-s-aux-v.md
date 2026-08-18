# Détection d'Intrusion par Analyse des Patterns d'Accès aux Vecteurs : Identification des Attaques de Poisoning et d'Évasion

*Domaine : Sécurité*

# Détection d'Intrusion : Analyse des Patterns d'Accès aux Vecteurs (Poisoning & Évasion)

## Contexte
Dans les architectures modernes basées sur l'IA locale (JARVIS, LLMs open-source) et les systèmes Linux, la sécurité ne se limite plus à la protection du périmètre réseau. Elle s'étend désormais à l'intégrité des modèles et des données d'entraînement. Les attaques de type **Poisoning** (empoisonnement) visent à corrompre le modèle pendant sa phase d'apprentissage ou d'inférence, tandis que les attaques d'**Évasion** tentent de tromper un modèle déjà déployé en manipulant légèrement les entrées. La détection repose sur l'analyse fine des patterns d'accès aux vecteurs (inputs) et des métriques de sortie anormales.

## Points Clés

*   **Surveillance des Vecteurs d'Entrée** : Implémentez une validation stricte des inputs avant qu'ils n'atteignent le modèle. Surveillez les longueurs de chaînes, l'injection de caractères spéciaux (ex: `<|eot_id|>`, `\x00`) et les tentatives de surcharge mémoire.
*   **Détection d'Évasion par Dérive de Distribution** : Un attaquant d'évasion modifie subtilement une image ou un texte pour contourner la classification. Surveillez les écarts statistiques entre la distribution des données entrantes en temps réel et celle du jeu d'entraînement (drift). Une divergence soudaine peut indiquer une tentative d'injection de prompt malveillant.
*   **Identification des Patterns de Poisoning** : Lors de l'inférence, si un modèle "empoisonné" répond systématiquement avec des instructions cachées ou des données corrompues pour certaines requêtes spécifiques, cela constitue un signal d'alarme. Analysez les logs d'accès pour détecter les séquences répétitives qui ne correspondent pas aux patterns normaux d'utilisation.
*   **Isolation et Quarantaine Automatique** : En cas de détection de pattern suspect, le système doit immédiatement isoler l'instance du modèle (ex: arrêt du service Docker/Python) et bloquer la source de l'input au niveau du pare-feu local ou de la couche application.
*   **Journalisation Intègre** : Chaque interaction avec le vecteur d'entrée doit être loguée avec un hash cryptographique pour permettre une reconstruction forensique en cas d'attaque confirmée.

## Exemple Concret : Scénario LLM Local

Imaginez un modèle LLM déployé localement sur un serveur Linux via une API FastAPI (JARVIS). Un attaquant tente une attaque d'évasion par
