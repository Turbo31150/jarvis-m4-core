# Agent SOUVERAINETÉ / LEGAL

*Focus : RGPD, CLOUD Act, NIS2, IA Act, hébergement, logs*

En tant qu'auditeur conformité & souveraineté, voici mon rapport suite à l'analyse du contexte "Boutique Prof IA / Pousseline — écosystème JARVIS OS".

## Points forts

*   **Approche "Locale" de l'application :** L'accent mis sur l'application "locale" (`Prof IA — L'assistant local qui épaule chaque enseignant`, `Pourquoi « local » change tout pour l'école`) est un atout majeur pour la souveraineté des données et la conformité RGPD. Il suggère que les données pédagogiques et personnelles des enseignants/élèves sont traitées en local, réduisant l'exposition à des infrastructures cloud tierces et étrangères.
*   **Transparence affichée :** La mention explicite de "rgpd" sur le site web (`signals: ["rgpd"]`) indique une prise de conscience initiale de cette réglementation.
*   **Taille contenue de l'application :** Le nombre de fichiers (215) et la taille (726.16 MB) de l'application locale suggèrent une codebase gérable et potentiellement moins complexe à auditer et sécuriser qu'un système distribué massif.

## Risques

*   **Exposition CLOUD Act via l'hébergement web :** Le site vitrine `https://prof-ia-74635.netlify.app/` est hébergé sur Netlify, une entreprise américaine. Cela expose potentiellement les données collectées (même minimales comme les adresses IP, user-agents ou cookies de navigation) au CLOUD Act, en contradiction avec les principes de souveraineté des données pour un public européen et un service destiné au secteur de l'éducation.
*   **Gestion des secrets critique :** La détection de `secrets_files: ["certs/server.key", "certs/ca.key"]` dans le scan local est un risque de sécurité **majeur**. Le stockage de clés privées directement dans l'environnement d'une application ou un dépôt non sécurisé peut entraîner un compromis complet du système en cas d'accès non autorisé au poste de travail ou à l'application. Cela enfreint les bonnes pratiques de sécurité et expose à des attaques d'usurpation.
*   **Conformité NIS2 non évidente :** Le secteur de l'éducation, notamment lorsqu'il s'agit d'outils critiques comme une "Boutique Prof IA" affectant les processus pédagogiques, pourrait être concerné par NIS2 selon l'interprétation nationale. L'absence de `compliance_markers` pour NIS2 et la gestion des secrets défaillante signalent un manque de maturité sur la cybersécurité.
*   **IA Act — Classification et documentation :** L'usage de l'IA (`Prof IA`, `JARVIS OS`) dans un contexte éducatif (préparation de séquence, évaluation, différenciation) pourrait potentiellement classer l'application comme "système d'IA à haut risque" selon l'IA Act (ex: systèmes IA utilisés pour déterminer l'accès à l'éducation ou pour l'évaluation de personnes dans ce cadre). L'absence d'information sur la classification, les données d'entraînement, ou les tests de robustesse est un risque.
*   **Localisation des données :** Bien que l'application soit "locale", il n'est pas précisé si des données (télémétrie, logs, modèles d'IA mis à jour, données d'utilisation agrégées) sont transmises à des services cloud. Si c'est le cas, leur localisation et la conformité des sous-traitants doivent être vérifiées.

## Opportunités

*   **Renforcer l'argument de souveraineté :** Capitaliser sur l'approche "locale" pour positionner Prof IA comme une solution respectueuse de la souveraineté des données, en contraste avec les solutions cloud américaines. Cela peut être un argument commercial fort pour les établissements scolaires en Europe.
*   **Implémenter une PSSI robuste :** Développer une Politique de Sécurité des Systèmes d'Information (PSSI) complète, incluant la gestion des accès, la gestion des incidents, la revue de code et la sensibilisation, afin de se conformer à NIS2 et rassurer les utilisateurs.
*   **Adopter des pratiques DevSecOps :** Intégrer la sécurité dès la conception (Security by Design) et tout au long du cycle de vie du développement, notamment pour la gestion des secrets et la revue des vulnérabilités.
*   **Documenter la conformité IA Act :** Réaliser une analyse d'impact pour l'IA, documenter les objectifs, les risques, les mécanismes de surveillance humaine, la robustesse, l'exactitude et la sécurité des systèmes IA. Publier une déclaration de conformité si nécessaire.

## Quick-wins

*   **Sécurisation immédiate des secrets :** **Urgent** — Retirer les fichiers `certs/server.key` et `certs/ca.key` de l'arborescence de l'application. Mettre en place une méthode de stockage sécurisée et éphémère (ex: variables d'environnement, secrets manager dédié, ou KMS) pour les clés privées, avec des permissions d'accès strictes et une politique de rotation.
*   **Migration de l'hébergement web :** Migrer le site vitrine `prof-ia-74635.netlify.app` vers un hébergeur cloud européen (ex: OVHcloud, Scaleway, Infomaniak) pour éliminer l'exposition au CLOUD Act et renforcer la souveraineté.
*   **Vérification de la politique de confidentialité web :** S'assurer que la politique de confidentialité du site Netlify est exhaustive, transparente et conforme au RGPD pour les données collectées via le site (cookies, formulaires, etc.). Mettre en place un bandeau de consentement aux cookies conforme.
*   **Clarifier la localisation des données de l'application locale :** Documenter précisément où sont stockées et traitées toutes les données générées ou utilisées par l'application "locale", et s'assurer qu'aucune donnée personnelle n'est envoyée à des services cloud non-européens sans consentement explicite et base légale.
*   **Évaluer le niveau de risque de l'IA :** Procéder à une auto-évaluation rapide selon les critères de l'IA Act pour déterminer si le système "Prof IA" est à haut risque et quelles obligations en découleraient.
