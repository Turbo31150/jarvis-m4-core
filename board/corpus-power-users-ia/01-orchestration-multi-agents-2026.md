# Orchestration multi-agents — la logique des power users IA (2026)

Source : synthèse moissonnée (Tembo.io, Shipyard, ThePromptShelf, alexop.dev, halallens.no,
GitHub hermes-agency-orchestrator). Capturé le 2026-08-18.

## Les 3 tiers d'orchestration (distinction fondatrice)

« Faire tourner plusieurs agents » recouvre trois choses distinctes :

1. **Sous-agents (dans une session)** — découpent le travail, mais ne passent pas à
   l'échelle sur des workflows sophistiqués. Consomment la fenêtre de contexte de la
   session mère.
2. **Agent Teams (le palier 2026)** — une session = team lead qui coordonne et
   synthétise ; les coéquipiers sont des instances Claude Code séparées, chacune avec
   sa propre fenêtre de contexte, communiquant via une task list partagée.
   **Compromis : coût** — chaque coéquipier est une instance complète, donc bien plus
   de tokens qu'une session unique.
3. **Orchestrateurs externes** — au-dessus de Claude Code : pilotent des sessions à
   travers machines, branches, repos ; ajoutent dashboards, suivi git-worktree,
   gouvernance. Outils : Gas Town, Conductor, Multiclaude, Tembo.

## Techniques avancées capturées

- **Isolation par worktree** = pièce critique du multi-agent. Sans elle : conflits git
  (deux branches checkout à la fois), épuisement accéléré du contexte. `/worktree` natif,
  ou worktrees manuels pour l'orchestration cross-agent.
- **Définitions de rôle réutilisables** — un sous-agent (ex. `security-reviewer`) peut
  être référencé comme membre d'une Agent Team ; Claude honore l'allowlist d'outils et
  le modèle définis dans AGENTS.md, dans les deux contextes.
- **Workflows déterministes** — le flux de contrôle est fixé par du code, pas décidé
  tour par tour par le modèle. Plafond réel cité : Jarred Sumner a porté Bun de Zig à
  Rust en 6 jours grâce aux workflows dynamiques + revue de code adversariale.
- **Orchestration multi-modèles** — le vrai coup de power user : Claude Code + OpenAI
  Codex CLI + Gemini CLI en parallèle, chacun sur ses forces.
- **Fiabilité** : intégrer retry + recovery DANS le prompt d'orchestration. Des
  validateurs gardent la progression ; une étape échouée rejoue avec le feedback de
  l'échec.

## Règle de décision (quand utiliser quoi)

- **Session unique** → une seule feature, travail focalisé.
- **Agents parallèles** → exploration : relire une PR sous 3 angles, chasser 5
  hypothèses de debug simultanément.
- **Orchestrateurs** → passage à l'échelle d'une flotte.

Arbitrages réels : isolation du contexte vs surcoût de coordination ; parallélisme vs
coût en tokens ; flexibilité vs complexité de configuration.

## Application locale JARVIS

- Le tier 3 (orchestrateur externe) correspond au widget cockpit :8899 + dispatch domino.
- Le compromis coût des Agent Teams justifie la LOI 2 (0-token) : router les coéquipiers
  vers le cluster local (M6 via Tailscale, OL1) plutôt que des instances cloud.
- Worktree isolation = déjà exposé par le tool Agent (isolation: worktree).
