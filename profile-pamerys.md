# Profil utilisateur — Pamerys

## Identité
- **Professeure des écoles** (enseignement primaire, France).
- **Mère**.
- Préfère des réponses **claires, concrètes, sans jargon inutile**, en **français** (orthographe et accents corrects).

## Personnalisation des réponses LLM
- Adapter le ton et les exemples au **contexte scolaire primaire** (préparation de cours, fiches, différenciation, gestion de classe, relations parents) et à la **vie de famille/organisation** quand c'est pertinent.
- Privilégier l'utile et l'actionnable (listes, étapes, modèles prêts à l'emploi).

## Contraintes matérielles M4 (à respecter par tout agent/tool)
- Laptop ASUS TUF, Intel TigerLake-H (iGPU affichage eDP) + **1 seule** RTX 3050 Mobile (4 Go VRAM).
- **Contrainte thermique forte** : cible 82°C, ne jamais lancer d'inférence locale lourde si GPU déjà au-dessus de la cible.
- M1/M2 souvent down → ne PAS supposer un cluster ; M4 doit pouvoir tout faire seul.

## Politique d'exécution (cahier des charges)
1. **SQL d'abord** : lire le cache/connaissances en base avant tout calcul.
2. **0 token** : cascade Ollama local + cloud (lm-ask.sh) si calcul nécessaire.
3. **Compute local en dernier**, on-demand uniquement, jamais en boucle 24/7.
