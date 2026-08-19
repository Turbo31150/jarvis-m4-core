[user] Tu lis des READMEs GitHub via l'outil MCP github-mcp-server (owner=Turbo31150). D'abord charge l'outil: ToolSearch query "select:mcp__github-mcp-server__get_file_contents". Puis pour CHAQUE repo de la liste ci-dessous, lis path="README.md" (si erreur/absent, essaie "readme.md" puis "README.MD"). Extrais de façon FACTUELLE (d'après le README seulement): à quoi ça sert (1-2 lignes), fonctionnalités clés, stack technique, maturité (badge/version/WIP/vide), vendable oui/non/partiel. Si aucun README ou vide → maturité="à documenter". Remplace tout secret/token/clé qui traînerait par [SECRET]. Ne pousse/modifie RIEN.

Repos: jarvis-os-public, alkymia-os, jarvis-core, jarvis-linux, jarvis-cowork, JARVIS-OMEGA, jarvis-cluster, jarvis-agentic-ops, jarvis-master-orchestrateur, labo-bibliotheque-centrale, jarvis-zero-token, jarvis-dominos, planning-app, workflow-gestion, jarvis-content-pipeline

Réponds UNIQUEMENT par un tableau markdown compact: | Repo | À quoi ça sert | Fonctionnalités | Stack | Maturité | Vendable |. Une ligne par repo, cellules courtes. Termine par une ligne "NON LUS: ..." listant les repos pour lesquels aucun README n'a pu être lu.

[assistant] Je récupère plus de contenu des 3 gros READMEs (jarvis-linux, jarvis-cowork, jarvis-cluster).

[assistant] Tous les 15 READMEs lus. Tableau factuel.

| Repo | À quoi ça sert | Fonctionnalités | Stack | Maturité | Vendable |
|---|---|---|---|---|---|
| jarvis-os-public | Vitrine commerciale/dossier de présentation de JARVIS OS (IA locale souveraine) | Pitch, benchmarks vérifiés (99,6% fiabilité, ~1,1s latence, 0€), démos vidéo, CV/portfolio, roadmap, FAQ | Python 3.11, CUDA, Docker Swarm, Redis, LM Studio/Ollama, Whisper, React 19 | Mûr (dossier commercial complet, MIT, chiffres datés 17/07/2026) | Oui (support de vente) |
| alkymia-os | Présentation produit AlkymIA-OS (OS IA distribué local pour PME) | Cluster multi-machines, pipeline vocal STT/TTS, orchestration agents, contenu social, trading, monitoring, tunnel B2B | Cluster local, LLM open-source, n8n, SQLite/PostgreSQL/Redis | Mûr (README marketing abouti, offre audit gratuit) | Oui (offre services PME) |
| jarvis-core | Hub/portfolio central JARVIS OS + services freelance | Cluster 5 nœuds/10 GPU, 900+ agents, 24 MCP, cache 96,9%, liens vers sous-repos, grille tarifaire | Python 3.12, llama-server/Ollama/Nginx LB, SQLite/PG/Redis/Pinecone, N8N | Mûr (code source privé sous NDA), MIT | Oui (services freelance) |
| jarvis-linux | Couche d'orchestration multi-agents self-hosted pour Linux | 166 CLIs, 79 chaînes Domino, 928 agents, auto-réparation <8s, transcription CUDA, analyse PDF | Docker Swarm, Redis, PostgreSQL, LLM locaux, Whisper CUDA, modifs kernel/systemd | Mûr (v3.0, MIT, benchmarks détaillés) | Oui (positionné vs GPT