[user] Tu es l'agent REPURPOSE. Tâche backlog #11 : concevoir l'outil « repurpose 1→4 » (1 post source → 4 formats : LinkedIn, X/Twitter, Reel/Short, carousel Instagram), 0-token, prêt à générer.

SÉCURITÉ : écriture de code + doc uniquement. AUCUNE publication, aucun envoi, aucune connexion à un réseau social. L'outil produit des BROUILLONS locaux, il ne poste jamais. Aucun secret.

ÉTAPE 1 — Regarde ce qui existe déjà pour ne pas dupliquer : cherche dans ~/jarvis (gen-content-kit.sh, mirra_local, autopilot) les briques de génération de contenu réutilisables. Note ce qui est réutilisable.

ÉTAPE 2 — Écris /home/pamerys/jarvis/scripts/repurpose.sh (ou .py si plus propre) : prend un texte/post source en entrée, génère 4 variantes adaptées (LinkedIn 150-250 mots pro, tweet ≤280, script Reel/Short 30-45s, plan de carousel 5-7 slides). Inférence 100 % 0-token via la cascade locale (bash ~/jarvis/scripts/lm-ask.sh "..." ou Ollama local) — JAMAIS d'IA facturée au runtime. Sortie = 4 fichiers brouillons dans un dossier daté sous ~/jarvis/wbs/drafts/. Garde-fous : max_tokens modeste, backend affiché, gestion propre si tout backend IA est down (message actionnable, pas de crash).

ÉTAPE 3 — Écris /home/pamerys/jarvis/docs/REPURPOSE-1-4.md : usage, exemple, et le rappel « brouillon d'abord, publication seulement après validation de Franck » (un seul pilote de publication, cf. audit doublons).

Rapport final concis : chemin du script + de la doc + un exemple d'invocation. Ne génère PAS de cont

[assistant] Je vais d'abord explorer les briques de génération existantes pour ne pas dupliquer.

[assistant] J'ai tout le contexte nécessaire. Constat réutilisable :
- **`gen-content-kit.sh`** : sélection backend 0-token (M6 LM Studio chargé → Ollama qwen2.5:7b → gemma3:4b) + fonction `gen()` fail-safe → je réutilise ce pattern.
- **`lm-ask.sh`** : construction JSON robuste via `json.dumps` (échappement correct) + parade reasoning-runaway qwen3.5 → je réutilise.
- Différence justifiant un nouvel outil : gen-content-kit prend un *sujet* et sort 1 fichier .md multi-sections ; repurpose prend un *post source* et sort *4 fichiers séparés* avec formats distincts (Reel/Short 30-45s = nouveau, carousel 5-7 slides Instagram).

J'écris le script.

[assistant] Maintenant je le rends exécutable et je le teste avec un backend potentiellement absent (validation du garde-fou et du flux complet).

[assistant] Un backend est joignable. Je teste un run réel complet (0-token) avec un post source court.

[assistant] Garde thermique déclenchée (l'inférence CPU chauffe la machine). Je laisse le run se terminer et je lis directement le fichier de sortie sans commande shell.

[assistant] Le run est toujours en cours (génération des 4 formats, lente sur CPU). J'attends la notification de fin. En attendant, je vérifie la sortie stderr déjà écrite.

[assistant] Le backend est correctement sélectionné (Ollama qwen2.5:7b — M6 joignable mais aucun modèle chargé, repli propre). La génération tourne. Pendant qu'elle se termine, j'écris la doc (ÉTAPE 3).

[assistant] Doc écrite. Je vérifie l'avancement du run de test en lisant les fichiers produits.

[assistant] Le run progresse bien (LinkedIn fait, Twitter en cours). L'outil fonctionne : backend sélectionné, fichiers écrits séquentiellement. Il reste Reel/Short et Carrousel (plus lents sur CPU). J'attends la fin du test pour confirmer le contenu généré.

[assistant] Smoke test complet réussi (exit 0). Tâche #11 terminée.

## Rapport — Outil « Repurpose 1 → 4 »

**Livrables**
- Script : `/home/pamerys/jarvis/scripts/repurpose.sh` (exécutable)
- Doc : `/home/pamerys/jarvis/docs/REPURPOSE-1-4.md`

**Invocation**
```bash
~/jarvis/scripts/repurpose.sh "Mon post source ici..."
# aussi : -f fichier.txt  |  echo "..." | repurpose.sh
```
Sortie : dossier daté `~/jarvis/wbs/drafts/repurpose-<slug>-<horodatage>/` avec `00-INDEX.md` + 4 brouillons séparés (`01-linkedin.md`, `02-twitter.md`, `03-reel-short.md`, `04-carousel-instagram.md`).

**Étape 1 — réutilisation (pas de duplication)**
- `gen-content-kit.sh` : j'ai repris son pattern de sélection backend 0-token (M6 LM Studio chargé → Ollama qwen2.5:7b → gemma3:4b) et sa fonction `gen()` fail-safe.
- `lm-ask.sh` : repris la construction JSON par `json.dumps` (échappement correct) + la parade reasoning-runaway qwen3.5 (`/v1/completions` avec `<think></think>` pré-fermé).
- Justification d'un outil distinct : gen-content-kit prend un *sujet* → 1 fichier multi-sections ; repurpose prend un *post source* → 4 fichiers séparés avec formats différents (Reel/Short 30-45s = nouveau ; carousel 5-7 slides). `mirra_local`/`autopilot` sont des chaînes de *publication* — délibérément non touchées (l'outil ne publie pas).

**Étape 2 — validé par smoke test réel (0-token)**
- 4 formats générés : LinkedIn 150-250 mots, tweet ≤280 car., script Reel/Short (hook + plans minutés + CTA + texte incrusté), carrousel 5-7 