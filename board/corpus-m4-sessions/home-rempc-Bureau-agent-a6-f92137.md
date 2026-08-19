[user] Claude Code v2.1.204, model claude-opus-5. L'utilisateur veut MAXIMISER la fenêtre de contexte utilisable.

Réponds précisément et factuellement (pas de supposition — si tu ne sais pas, dis-le) :

1. Le contexte long (1M tokens) : est-il disponible pour Opus 5 dans Claude Code ? Si oui, comment l'activer exactement (nom exact du setting dans settings.json, ou env var type ANTHROPIC_BETAS / MAX_THINKING_TOKENS, ou option /config) ? Quelle est la fenêtre par défaut d'Opus 5 dans Claude Code ?

2. `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` : quelle est sa sémantique exacte (pourcentage de remplissage déclenchant l'autocompact ?), sa valeur par défaut, et sa plage valide ? Est-ce un réglage supporté/documenté ?

3. Comment désactiver totalement l'autocompact si souhaité (setting `autoCompactEnabled` ? /config ?) et quelles sont les conséquences (que se passe-t-il quand la fenêtre est pleine sans autocompact ?).

4. `MAX_MCP_OUTPUT_TOKENS` : valeur par défaut, effet, valeur max raisonnable.

5. Y a-t-il d'autres réglages officiels qui augmentent le contexte utilisable ou réduisent sa consommation (ex : réglages sur les résultats d'outils, sur le nombre de tokens de sortie, sur le chargement différé des outils MCP) ?

Donne pour chaque point : le nom exact du réglage, où le mettre (settings.json `env` vs shell), et la source (doc officielle si tu peux la vérifier).
<context_window_protection>
  <priority_instructions>
    Every byte a tool returns enters your conversation memory and costs r

[assistant] Je vais vérifier la documentation officielle Claude Code pour répondre factuellement à chaque point.

[assistant] Basé sur ma recherche, voici les réponses factuelles avec sources vérifiées et limitations claires :

---

## 1. **Contexte 1M tokens pour Opus 5 dans Claude Code**

**Réponse courte** : Oui, disponible. C'est **automatique**, pas de setting à activer.

- **Fenêtre par défaut Opus 5** : **1M tokens** (c'est aussi le maximum absolu)
- **Comment** : Aucune configuration nécessaire. Sélectionnez Opus 5 via `/model claude-opus-5` ou `settings.json` `"model": "claude-opus-5"` 
- **Prérequis** : Claude Code v2.1.219+ (run `claude update` si manquant)
- **Source officielle** : [What's new in Claude Opus 5 - Claude Platform Docs](https://platform.claude.com/docs/en/about-claude/models/whats-new-opus-5)

---

## 2. **CLAUDE_AUTOCOMPACT_PCT_OVERRIDE**

| Aspect | Détail |
|--------|--------|
| **Sémantique** | Pourcentage de remplissage de la fenêtre de contexte déclenchant l'autocompact |
| **Plage valide** | 1–100%, mais **capped au maximum ~83%** (ne peut pas être augmenté au-delà) |
| **Valeur par défaut** | ~83% (autocompact se déclenche près de la limite) |
| **Recommandé** | 40–70% pour plus de compactions préventives |
| **Statut support** | ⚠️ **Officiel mais avec bug documenté** |

**LE PROBLÈME CRITIQUE** : Quand vous mettez `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` dans `settings.json` sous `env`, **il est ignoré silencieusement par la logique d'autocompact de Claude Code**.

**Workaround** : Exporter la variable dans le shell **avant** de lancer Claude Code :
```bash
export CLAUDE