# Automation & agents — la logique des power users (forums, YouTube, startups) 2026

Source : synthèse moissonnée (ryandoser.com, dev.to/wcamon, digen.ai, teknoding.com,
upload-post n8n templates, foximusic). Capturé le 2026-08-18.

## Les praticiens de référence (à suivre, pas du hype)

- **Nate Herk** — 870K abonnés en <3 ans, ex-Goldman Sachs. Enseigne les workflows n8n,
  la construction d'agents IA, la monétisation de l'automation (angle non-codeur).
- **Jack Roberts** — business automation 7 chiffres, systèmes d'agents no-code,
  scheduling, workflows business concrets.
- **Sabrina Ramonov** — 3M+ followers, CS+Physique Berkeley, ex-fondatrice NLP (rachetée
  par Pegasystems). Prompts, systèmes d'agents, playbooks pour solopreneurs.
- **Ryan Doser** — systèmes IA pour marketeurs sans code, 1000+ vidéos.

## Pourquoi n8n domine chez les power users

Outil fair-code node-based, auto-hébergeable (Docker/serveur local). Logique complexe :
boucles, JavaScript/Python custom dans les nodes. **Le self-hosting supprime les limites
d'exécution → des milliers de workflows pour 0 € de frais de plateforme** (aligné LOI 2).

## Patterns actionnables capturés

- **4 nodes de base = 80% des automations** : Set, If, Switch, Filter. Les maîtriser d'abord.
- **Chat node vs AI Agent node** : savoir quand utiliser l'un ou l'autre.
- **Think Node** : fait pause + raisonne avant d'agir → décisions plus fines.
- **Coordination d'agents** = critique : connecter générateur d'idées → rédacteur de
  script → agents visuels en ligne de production cohérente. C'est le branchement qui
  débloque la vraie puissance, pas les agents isolés.
- **MCP + multi-modèles** : brancher MCP, agents et plusieurs modèles (ChatGPT/Claude/
  Gemini) dans un même pipeline.
- **Voie ingénieur** : LangGraph, CrewAI, Pydantic AI pour contrôle total (mémoire,
  exécution d'outils, communication multi-agent, error recovery) + modèles open-source
  locaux offline pour couper les coûts API.

## Le contre-point réaliste (leçon la plus précieuse)

Un praticien a laissé des agents piloter sa chaîne YouTube 6 semaines. Verdict :
« AI YouTube automation » = souvent un workflow n8n de 150 étapes (scrape tendances →
script GPT → images → ffmpeg → voix off → upload). **Ces systèmes produisent du contenu,
pas du BON contenu.** Raison : les outils n'ont ni mémoire, ni contexte, ni jugement —
un workflow n8n ignore que les 3 dernières vidéos ont eu un faible taux de like.

**Takeaway des meilleurs** : combiner automation agentique + jugement humain + itération
pilotée par la performance. Jamais du full hands-off.

## Application locale JARVIS

- n8n est déjà présent (:5678, 56 workflows). Le pattern « 4 nodes = 80% » et le Think
  Node sont directement transposables aux dominos.
- La leçon anti-hands-off valide le scoring/feedback des séries biblio (une sortie = une
  preuve) : ne pas générer en masse sans boucle de mesure.
- Router l'inférence des pipelines vers le cluster local (M6/OL1) suit la même logique
  0-token que le self-hosting n8n.
