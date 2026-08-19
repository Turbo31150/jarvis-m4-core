[user] Recherche académique. Livrable : un rapport dans un fichier. Tu ne connais rien de la conversation qui précède.

## Question

**Un conseil de N experts LLM aux grilles de lecture (« lens ») volontairement divergentes, suivi d'une synthèse arbitrale, produit-il de meilleures réponses qu'un seul modèle bien prompté — ou fabrique-t-il surtout un consensus artificiel coûteux ?**

## Le système concret

`/home/turbo/jarvis/board/` — board d'experts local (Python stdlib, SQLite, LM Studio, 0 token payant). Lis `board.py` avant de chercher.

Une question → corpus interrogé (BM25 + vecteurs) → N experts répondent **en parallèle**, chacun avec sa `lens` (system prompt ~1500 car., structuré « ce que tu regardes en premier / ta question signature / **ton biais assumé** ») → un expert `is_arbitre=1` reçoit tous les avis et tranche. Chaque réponse doit citer ses sources ; une réponse sans citation est invalide et détectable en SQL.

Réel : **9 domaines, 44 experts (9 arbitres), 78 169 chunks**. Le **même** modèle (`qwen3.5-9b`) joue tous les rôles — seule la lens change. Coût observé : 4 experts + arbitre ≈ 55-75 s chacun en parallèle + 29 s d'arbitrage.

## À établir

1. **État de l'art** : *multi-agent debate*, *LLM-as-a-judge*, *self-consistency*, *mixture of agents*, *persona prompting*, *society of minds*. Privilégie les travaux avec évaluation quantitative.
2. **La divergence aide-t-elle ?** Distingue : (a) N échantillons du même prompt agrégés par vote, (b) N **personas** du même m

[assistant] While the research agents run, let me examine the lens structure and answer data.

[assistant] The DB integrity is fine — another session is actively vectorizing (3 491 → 9 278 during my work). Let me note that in the report.

[assistant] Rapport livré : **`/home/turbo/jarvis/board/recherche/01-boards-experts-llm.md`** (486 lignes, 50 sources dont 24 évaluées par les pairs avec mesure quantitative). Aucun fichier du board modifié (`board.py`, `board.db`, schéma, packs intacts ; `quick_check` = ok).

## Conclusions (10 lignes)

1. À budget de calcul apparié, **six études indépendantes** (EMNLP 2024, ICML 2024, ACL 2024, ICLR Blogposts 2025, + 2 préprints 2026) concluent que le débat multi-agents **ne bat pas** CoT + self-consistency, et peut *empirer* avec plus de budget.
2. Le gain propre au débat chez Du et al. (ICML 2024) est de **+4 points** sur GSM8K face au simple vote majoritaire — self-consistency en gagne **+17,9** face au CoT glouton.
3. Trois leviers, très inégaux : persona **+1,1 %**, modèle **+2,2 %**, les deux **+2,5 %** (Yang et al. 2026). **2 agents divers ≈ 16 agents homogènes.**
4. Dix agents partageant un modèle de base valent **≈ 1,2 voix effective** (K\* = 1,197). Le board mesure ce symptôme : **Jaccard = 1,00** entre deux experts sur la question 2.
5. Sur des modèles 7–8 B (la classe de qwen3.5-9b), le débat homogène **perd** contre l'auto-correction isolée pour **2,1–3,4× plus de jetons**, avec **85,5 % de conformité sycophante**.
6. L'arbitre LLM est mal calibré : cohérence positionnelle de 23,8 à 65 % selon le modèle, biais de verbosité jusqu'à 91,3 %, auto-préférence causalement établie (NeurIPS 2024 oral).
7. Le **« biais assumé » auto-déclaré n'est validé par aucun article**. Ce qui 