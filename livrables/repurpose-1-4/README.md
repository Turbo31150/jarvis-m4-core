# repurpose 1 → 4

Un post source → **4 formats prêts à relire**, générés 100 % en local (0 token
facturé) : LinkedIn, X/Twitter, script Reel/Short, plan de carrousel Instagram.
Aucune publication automatique : l'outil ne produit que des **brouillons**.

## Contenu
```
repurpose.sh          # le générateur (Bash + cascade IA locale)
REPURPOSE-1-4.md      # documentation
README.md / FICHE-VENTE.md / LICENSE.txt
```

## Prérequis
Un backend IA local 0-token, dans cet ordre de repli :
1. LM Studio (variable `M6_HOST`, défaut `<LLM_HOST>:1234`) avec un modèle chargé, ou
2. Ollama (`OLLAMA_URL`, défaut `http://127.0.0.1:11434`) avec `qwen2.5:7b` ou `gemma3:4b`.

Aucune IA facturée n'est utilisée en repli : si aucun backend local ne répond,
l'outil s'arrête proprement.

## Usage
```bash
chmod +x repurpose.sh
repurpose.sh "<texte du post source>"
repurpose.sh -f post.txt
echo "<texte>" | repurpose.sh
```
Sortie : un dossier daté sous `$HOME/jarvis/wbs/drafts/repurpose-<slug>-<date>/`
contenant `00-INDEX.md`, `01-linkedin.md`, `02-twitter.md`, `03-reel-short.md`,
`04-carousel-instagram.md`.

## Sécurité
Génération locale, brouillons uniquement. Rien n'est publié ni envoyé.
