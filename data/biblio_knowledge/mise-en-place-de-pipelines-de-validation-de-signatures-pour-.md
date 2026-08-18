# Mise en place de pipelines de validation de signatures pour les images de base générées dynamiquement par des agents de sécurité sur les nœuds du cluster.

*Domaine : Sécurité - Supply Chain - Conteneurisation Dynamique*

# Sécurisation des Images Dynamiques : Pipelines de Validation de Signatures

## Contexte
Dans les architectures modernes basées sur **Kubernetes** et des agents de sécurité autonomes (comme ceux du projet **JARVIS**), la génération dynamique d'images de base est une pratique courante pour répondre à des besoins spécifiques sans reposer sur un registre centralisé statique. Cependant, cette approche introduit une surface d'attaque critique : si un agent compromis ou malveillant génère une image contenant une vulnérabilité ou un backdoor, celle-ci sera déployée immédiatement par le contrôleur Kubernetes.

Pour contrer cela, il est impératif de mettre en place un **pipeline de validation de signatures** (notamment basé sur **Cosign**) avant que l'image ne soit poussée vers le registre interne ou déployée. Ce processus assure l'intégrité et l'authenticité du contenu généré par les agents locaux, garantissant qu'une image signée n'est jamais exécutée sans vérification préalable.

## Points Clés
*   **Génération avec Intention de Sécurité** : Les agents doivent signer l'image *in situ* immédiatement après sa construction (ex: `docker build` ou `buildah`) avant toute manipulation réseau.
*   **Utilisation de Cosign** : L'outil standard de l'industrie pour les images OCI. Il permet la signature cryptographique et la vérification des attestations (SBOM, attestation de sécurité).
*   **Clés de Signature Rotatives** : Évitez les clés statiques partagées. Utilisez un système de gestion de secrets (ex: Vault) ou des clés générées spécifiquement par l'agent pour chaque contexte de confiance.
*   **Vérification au Point d'Ingestion** : Le registre interne ou le contrôleur Kubernetes doit rejeter toute image non signée ou dont la signature ne correspond pas à la clé publique de confiance (Root of Trust).
*   **Attestations SBOM** : Inclure un *Software Bill of Materials* signé dans l'image pour permettre une traçabilité fine des dépendances introduites dynamiquement.

## Exemple Concret : Flux de Travail Agent JARVIS

Imaginons un nœud du cluster où un agent LLM local génère une image `secure-agent-v1` pour isoler une charge de travail sensible.

1.  **Construction** : L'agent construit l'image localement dans un cache temporaire.
2.  **Signature Immédiate** : Avant de pousser l'image, l'agent exécute la commande suivante en utilisant une clé privée gérée localement ou via Vault :
    ```bash
    cosign sign --key /etc/secrets/cosign-key.pem \
      --yes \
      registry.internal/secure-agent-v1:latest
    ```
3
