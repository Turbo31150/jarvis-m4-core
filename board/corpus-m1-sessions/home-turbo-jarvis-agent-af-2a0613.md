[user] Recherche web rigoureuse sur le RERANKING (cross-encoder) après une récupération hybride BM25+dense, pour un rapport technique. Tu dois trouver des SOURCES PRIMAIRES avec des CHIFFRES EXACTS. N'invente AUCUN chiffre.

Questions à documenter :
1. Le gain mesuré d'un cross-encoder / reranker appliqué après une première passe. Sources attendues : BEIR (Thakur et al. 2021, arXiv 2104.08663) — les chiffres exacts de BM25 seul vs BM25+CE (cross-encoder MiniLM) en nDCG@10 moyen sur les 18 datasets ; le papier original monoBERT/duoBERT (Nogueira & Cho 2019, "Passage Re-ranking with BERT", arXiv 1901.04085) ; RankGPT (Sun et al. 2023, arXiv 2304.09542) ; la doc/blog Anthropic Contextual Retrieval (chiffre 2.9% -> 1.9% d'échec).
2. Le COÛT : latence d'un cross-encoder. Cherche des chiffres publiés de latence/débit (ms par paire query-document, ou docs/s) pour des rerankers légers : ms-marco-MiniLM-L-6-v2 (sentence-transformers), bge-reranker-base / bge-reranker-v2-m3 (BAAI, arXiv 2402.03216 pour BGE-M3), jina-reranker-v2, mxbai-rerank. Compare aussi taille de modèle (nb de paramètres).
3. Options exécutables EN LOCAL sur une machine avec GPU NVIDIA, en particulier : est-ce que LM Studio, Ollama, ou llama.cpp supportent les modèles de reranking (endpoint /v1/rerank ou équivalent) ? Cherche la documentation officielle et les issues GitHub. Est-ce que llama.cpp a un support rerank (llama-server --reranking) ? Depuis quelle version/PR ?
4. Y a-t-il des résultats CONTRADICTOIRES — des trava

[assistant] I'll research this rigorously with web searches. Let me load the web tools first.

[assistant] I'll research this systematically. Let me start with parallel searches on the core topics.

[assistant] The BEIR PDF was saved locally. Let me extract its tables precisely, and grab the monoBERT table.

[assistant] While the subagents work, let me cover the hybrid-specific angle the user framed.

[assistant] Ollama confirmed: no rerank endpoint in the official API docs. Let me check on the two research subagents.

[assistant] Everything is verified from primary sources. Composing the report.

---

# Reranking (cross-encoder) après récupération hybride BM25+dense — rapport technique

**Méthode** : tous les chiffres ci-dessous ont été extraits **directement des PDF sources** (`curl` + `pdftotext -layout`) ou de la documentation officielle, pas de résumés secondaires. Chaque chiffre est étiqueté **EXACT** (lu tel quel dans la source) ou **CALCULÉ** (arithmétique effectuée par moi sur des chiffres exacts). Aucun chiffre n'est inventé.

---

## 1. Le gain mesuré du reranking

### 1.1 BEIR — la référence (Thakur et al., NeurIPS 2021 Datasets & Benchmarks)

Configuration exacte du papier : **BM25 (Anserini) top-100 → re-rangé par un cross-encoder MiniLM 6 couches, 384-h**, distillé sur MS MARCO depuis un ensemble de 3 maîtres (BERT-base, BERT-large, ALBERT-large). Le papier précise avoir évalué **14 cross-encoders publics** avant de retenir celui-ci.

Table 2 du papier, nDCG@10 — **EXACT** :

| Dataset | BM25 | BM25+CE | Δ relatif (CALCULÉ) |
|---|---|---|---|
| TREC-COVID | 0.656 | **0.757** | +15,4 % |
| BioASQ | 0.465 | 0.523 | +12,5 % |
| NFCorpus | 0.325 | 0.350 | +7,7 % |
| NQ | 0.329 | 0.533 | **+62,0 %** |
| HotpotQA | 0.603 | 0.707 | +17,2 % |
| FiQA-2018 | 0.236 | 0.347 | **+47,0 %** |
| Signal-1M (RT) | 0.330 | 0.338 | +2,4 % |
| TREC-NEWS | 0.398 | 0.431 | +8,3 % |
| Robust04 | 0.408 | 0.475 | +16,4 % |
| **ArguAna** | 0.315 | **0.311** | **−1,3 %** |
| **Touché-2020** | 0.367 | **0.271** | *