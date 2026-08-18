# Repurpose 1 → 4

Un post source, quatre déclinaisons prêtes à relire — **100 % local, 0 token facturé, aucune publication automatique**.

Outil : `~/jarvis/scripts/repurpose.sh`

## Ce que ça fait

À partir d'un seul post source, l'outil génère quatre variantes adaptées à chaque canal :

| # | Format | Contrainte |
|---|--------|-----------|
| 1 | **LinkedIn** | 150-250 mots, ton professionnel, accroche + corps aéré + CTA + 3 hashtags |
| 2 | **X / Twitter** | un tweet ≤ 280 caractères, autoportant, ≤ 1 hashtag |
| 3 | **Reel / Short** | script vidéo 30-45 s : hook 3 s + plans minutés + CTA + texte incrusté |
| 4 | **Carrousel Instagram** | 5-7 slides (`Slide N — TITRE : contenu`) + légende + hashtags |

Chaque variante est écrite dans son **propre fichier brouillon**, dans un dossier daté.

## Inférence 0-token (cascade locale)

Aucune IA facturée au runtime. Cascade, dans l'ordre :

1. **M6 LM Studio** (`10.42.0.230:1234`) si un modèle est **chargé** ;
2. sinon **Ollama local** (`127.0.0.1:11434`) — `qwen2.5:7b` de préférence, sinon `gemma3:4b`, sinon le premier modèle installé ;
3. si aucun backend local ne répond → **message actionnable, pas de crash, aucun repli cloud**.

Le backend réellement utilisé est affiché dans l'en-tête de chaque brouillon (transparence).
`max_tokens` volontairement modeste (180-620 selon le format) pour rester rapide et frugal.

> Note thermique (M4) : la génération sollicite le CPU si elle passe par Ollama local.
> La garde 82 °C reste prioritaire ; préférer M6 chargé quand la machine chauffe.

## Usage

```bash
# post source en argument
~/jarvis/scripts/repurpose.sh "Texte de mon post source ici..."

# depuis un fichier
~/jarvis/scripts/repurpose.sh -f ~/notes/post.txt

# depuis stdin
echo "Texte de mon post" | ~/jarvis/scripts/repurpose.sh
```

L'outil affiche sur stdout le chemin du dossier de sortie :

```
/home/pamerys/jarvis/wbs/drafts/repurpose-<slug>-<horodatage>/
├── 00-INDEX.md               # récap + post source + prochaine étape
├── 01-linkedin.md
├── 02-twitter.md
├── 03-reel-short.md
└── 04-carousel-instagram.md
```

## Exemple

```bash
$ ~/jarvis/scripts/repurpose.sh "J'ai automatisé la préparation de mes séances \
de maternelle avec une IA locale. 2 heures gagnées chaque dimanche soir, \
zéro donnée envoyée dans le cloud."
→ Repurpose 1→4 (0-token via Ollama local (qwen2.5:7b))
  · LinkedIn…
  · X / Twitter…
  · Reel / Short…
  · Carrousel Instagram…
/home/pamerys/jarvis/wbs/drafts/repurpose-j-ai-automatis-la-pr-paration-20260814-1930/
```

## Garde-fous

- **Brouillon d'abord.** L'outil n'écrit que des fichiers locaux. Il **ne poste jamais**,
  n'envoie rien, ne se connecte à aucun réseau social. Aucun secret n'est lu ni requis.
- **Publication seulement après validation de Franck.** La mise en ligne reste
  **manuelle** et passe par le **pilote de publication unique** — jamais par cet outil,
  ni par un second outil de publication en parallèle (cf. audit des doublons : un seul
  pilote de publication pour éviter les doubles envois).
- **Post source vide → erreur** (exit 2), jamais de substitution silencieuse.
- **Aucun backend local → exit 3** avec le geste correctif (charger un modèle M6 ou
  démarrer Ollama). Pas de repli sur une IA facturée.

## Flux recommandé

```
post source → repurpose.sh → 4 brouillons → RELECTURE/validation → pilote de publication unique
```
