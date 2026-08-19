# Brouillons LinkedIn — 19/08/2026 — Franck Delmas
Chiffres autorisés : 6 GPU NVIDIA · 928 agents · < 500 ms mesuré · 0 cloud
Chiffres INTERDITS : 12 GPU · 6 machines · 1000+ agents · < 300 ms

## POST — les 3 offres

La plupart des PME n'ont pas un problème d'IA. Elles ont un problème de temps.

Personne ne se lève le matin en voulant "faire de l'IA". On veut arrêter de
ressaisir les mêmes devis, arrêter de relancer à la main, arrêter de perdre
deux heures par jour dans la glu administrative.

Alors j'ai arrêté de vendre de la technologie. Je vends trois résultats,
à prix fixe, sans abonnement :

🟢 Sprint Automatisation IA — 1 500 €
1 à 3 workflows branchés sur vos outils existants, documentés. Livré en 2 à 4 jours.

🟡 Assistant IA sur vos données — 3 000 €
Un agent qui répond sur VOS documents. Local ou cloud, vous choisissez. 3 à 5 jours.

🔴 Audit + POC IA locale souveraine — 2 500 €
Pour la santé, le juridique, le public, la finance, l'industrie : faisabilité,
POC, roadmap, et le volet EU AI Act. 3 à 6 jours.

Le troisième est celui que je préfère, parce qu'il répond à la question que
personne n'ose poser : "et si je ne veux pas que mes données partent chez un
tiers ?" Réponse : le traitement tourne chez vous. Concrètement, chez moi :
n8n auto-hébergé en Docker Swarm, PostgreSQL, des modèles servis en local par
Ollama et LM Studio sur 6 GPU, supervisés par Grafana et Prometheus. Une
transcription mesurée sous 500 ms. Ce n'est pas une plaquette, c'est la stack
qui tourne pendant que j'écris ce post.

Je ne vous dirai pas que je n'utilise jamais le cloud — j'y vais quand c'est
le bon outil. Ce que je garantis, c'est que VOS données n'ont pas besoin d'en
sortir.

Audit de cadrage gratuit, 20 minutes. Si je ne vois pas de gain net, je vous
le dis et on s'arrête là.

Toulouse et à distance. 👇 En commentaire ou en DM.

## COMMENTAIRE 1 — post gouvernance / data-first
Le point gouvernance est le plus sous-estimé en Europe : avec le RGPD et l'AI Act,
la friction d'aujourd'hui devient votre seul argument défendable devant un
régulateur demain. Je vois trop de PME qui veulent l'agent avant d'avoir un
propriétaire sur leurs données — on finit toujours par remonter la lineage dans
la douleur. Data-first, ce n'est pas un luxe : c'est ce qui rend l'IA auditable.

## COMMENTAIRE 2 — post mémoire des agents (Paul Iusztin)
Roadmap solide. J'ajouterais deux choses : l'oubli maîtrisé (eviction + TTL) et
la souveraineté du store. Chez mes clients PME, garder la mémoire de l'agent
100% locale change tout côté RGPD et côté coûts. Le "maintained" est l'étape qui
casse en prod — un graphe propre à J+1 devient un cimetière à J+90 sans politique
de rétention.

## COMMENTAIRE 3 — post GenAI au-delà du prompting (Ojas Varshney)
D'accord sur le fond : build ≠ appeler une API. Un contrepoint au tout-cloud —
une bonne partie de ce stack (RAG, PEFT, inference) tourne très bien 100% en
local, ce qui devient indispensable quand le client ne peut pas envoyer ses
données sur Bedrock pour raisons RGPD. Le vrai skill : choisir cloud ou local
selon la donnée, pas par défaut.
