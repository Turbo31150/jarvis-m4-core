[user] Tu produis UNE section de spec markdown pour durcir l'écosystème JARVIS. Lis d'abord /home/rempc/jarvis/docs/exports/pack-methode-jarvis/01-MATRICE-VECTORIELLE.md pour rester cohérent (4 lois A1-A4, A0/A5, briques ; publish = seul effet de bord A4 ; agent = feuille A1-bis ; 3 états NORMAL/DEGRADED_LOCAL/NO_LLM). Regarde aussi si présents : ~/jarvis/scripts/publish/action_schema.py et ~/.config/jarvis/publish-policy.json (Safety Floor réel).

CONTEXTE (faille trouvée par red-team multi-IA) : en mode dégradé (fallback ollama local, modèle plus faible), un modèle local peut VALIDER une action qu'un modèle fort refuserait (régression de garde-fous). Piège : l'orchestrateur prend « réponse disponible » pour « réponse fiable ». La sûreté ne doit pas dépendre de la force du modèle.

TA TÂCHE : écris une section « ## A5+ — Policy déterministe hors-LLM + least-privilege dégradé » (markdown, ~250 mots), respectant les 4 lois, SANS 8e brique. Couvre concrètement :
- La décision d'autoriser une action à effet de bord est prise par un MOTEUR DÉTERMINISTE (validation de schéma + policy locale bornée type/cible/fréquence/plafond), JAMAIS par le LLM. Le LLM propose, la policy dispose.
- La policy vit hors du modèle (fichier versionné, ex. publish-policy.json), s'applique identiquement quel que soit le provider.
- Dégradation stricte : en DEGRADED_LOCAL / NO_LLM, réduire les privilèges par défaut (read-only, pas d'auto-commit, confirmation humaine obligatoire, allowlist plus étroite).
- « Dis

[assistant] I'll read the reference material first to stay coherent with the established structure.

[assistant] ## A5+ — Policy déterministe hors-LLM + least-privilege dégradé

> Durcissement de **A4** (effet de bord, brique `publish` seule ⬛) contre la régression de garde-fous en mode dégradé. **Pas une 8ᵉ brique** : un invariant transversal qui verrouille le gate `peut_agir`.

**Le LLM propose, la policy dispose.** L'autorisation d'une action à effet de bord est rendue par un **moteur déterministe** (`validate_action`, `stdlib-only`, zéro appel réseau/LLM) : validation de schéma typé (liste fermée `action_type`, clés `target` bornées, anti-reconstruction) + **policy locale** bornée `type/cible/fréquence/plafond`. Un modèle — fort ou faible — ne *valide* jamais sa propre sortie ; le lint LLM reste un **enrichissement optionnel qui ne conditionne jamais la validité** (loi A1 : l'agent délègue, il ne gouverne pas A4).

**Policy hors du modèle.** Les règles vivent dans un fichier versionné (`~/.config/jarvis/publish-policy.json`), appliqué **identiquement quel que soit le provider** (openclaw/ollama/gemini/chatgpt). Changer de modèle ne change pas la frontière ; `trust_level` reste un signal, jamais une élévation.

**Dégradation stricte = moins de privilèges.** En `DEGRADED_LOCAL`/`NO_LLM`, le défaut se **rétrécit** : read-only, pas d'auto-commit, flux `stage→approve(humain)→commit(hash)` obligatoire, allowlist plus étroite. Un modèle local plus faible ne peut donc **jamais élargir** ce qu'un modèle fort refuserait.

**Disponible ≠ fiable.** L'orchestrateur (Ω) n'infère **aucune confianc