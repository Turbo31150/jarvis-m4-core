---
id: npc-worldwide-npcpy-skills-knowledge-graph-skill-skill-md
name: "knowledge-graph-skill"
author: "NPC-Worldwide"
repository: "https://github.com/NPC-Worldwide/npcpy/tree/main/skills/knowledge_graph_skill"
skill_url: "https://skillsmp.com/creators/npc-worldwide/npcpy/skills-knowledge-graph-skill"
stars: 1456
verified: false
quality_score: 100
security_score: 90
status: "SAFE"
collected_at: "2026-08-07T17:30:13.180302"
---

# Résumé
Skill for searching and evolving the SQLite-backed Knowledge Graph. Use this when you need structured fact/concept/link search across one or more teams, NPCs, or directory scopes.
The Knowledge Graph (KG) is stored in the application's database (not YAML). It is scoped by (team_name, npc_name, directory_path). Facts and concepts carry generation numbers and origin tags.
Search methods (choose the right one):
1. Keyword search — fast substring match over fact statements.
   `kg_search_facts(engine_or_kg, "keyword")` → List[str]

2. Embedding search — semantic cosine similarity via vector embeddings.
   `kg_embedding_search(engine_or_kg, query="...", embedding_model="nomic-embed-text",
    embedding_provider="ollama", similarity_threshold=0.6, max_results=20)`
   → List[dict] with 'content', 'type', 'score'

3. Link search — graph traversal (BFS/DFS) starting from keyword-matched seeds.
   `kg_link_search(engine_or_kg, query="...", max_depth=2, breadth_per_step=5,
    strategy="bfs", max_results=20)`
   → List[

# Objectif
Skill d'automatisation/intégration pour knowledge-graph-skill.

# Déclencheurs d’utilisation
Mots-clés associés: knowledge-graph-skill, NPC-Worldwide

# Procédure
Consulter le dépôt source: https://github.com/NPC-Worldwide/npcpy/tree/main/skills/knowledge_graph_skill

# Adaptation Gemini CLI / Claude Code / Jarvis OS
Incorpore ce skill en suivant la structure d'appel native du repository source.
