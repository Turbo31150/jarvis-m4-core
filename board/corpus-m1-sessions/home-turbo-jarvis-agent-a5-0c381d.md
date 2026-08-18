[user] Recherche technique rigoureuse. Livrable : un rapport dans un fichier. Tu ne connais rien de la conversation qui précède.

## Question

**Sur un corpus très hétérogène de 78 169 fragments (mémoires techniques, code source, documentation), la fusion par rang réciproque (RRF) de BM25 et du cosinus est-elle le bon choix — ou faut-il pondérer, reranker, ou changer le découpage ?**

## Le système concret

`/home/turbo/jarvis/board/` — RAG local (Python stdlib, SQLite, LM Studio). **Lis `board.py` (`chunk_text`, `retrieve`, `embed`) et `board_schema.sql` avant de chercher**, et vérifie toi-même ce qui suit :

- **Découpage** : 1400 caractères, chevauchement 200, coupure sur frontière lisible, rejet < 80 caractères.
- **Lexical** : SQLite FTS5, `bm25()`, tokenizer `unicode61 remove_diacritics 2`. Tokens de la question (`\w{3,}`, max 8) joints par `OR`.
- **Vectoriel** : `text-embedding-nomic-embed-text-v1.5`, **dim 768**, BLOB float32, cosinus calculé **en Python sur tous les chunks du domaine** — aucun index ANN.
- **Fusion** : RRF, `1/(60+rang)`, top 40 par voie.

Réel : **78 169 chunks dont seulement ~3 300 vectorisés (4 %)**. Répartition par domaine : 47 423 / 17 504 / 11 024 / 2 218.

## À établir

1. **RRF** : origine (Cormack et al.), pourquoi k=60, quand il bat une fusion pondérée, quand il échoue.
2. **Le déséquilibre de couverture** — question centrale : fusionner une liste BM25 complète avec une liste vectorielle qui ne voit que 4 % du corpus, quel biais ? Faut-il désacti

[assistant] Confirmed: 78 169 chunks, 3 691 vectorisés (4,72 %). Let me benchmark the cosine bottleneck while researching.

[assistant] Table 2 includes **nomic-embed-text-v1** — the board's exact model family. Let me get the rest.

[assistant] The key counter-evidence to RRF is Bruch et al. Let me get it plus CoIR numbers.

[assistant] Critical finding: RRF underperforms the dense retriever alone on MS MARCO. Let me verify that table directly.

[assistant] CoIR Table 3 acquired. Now a potentially critical detail about the board's exact embedding model.

[assistant] Confirmed a real defect. Let me now test the FTS5 tokenizer behaviour on code identifiers, empirically, read-only.

[assistant] The FTS index is dominated by French stopwords. Let me measure the actual impact on the board's real query path.

[assistant] Vectorisation appears to be running concurrently. Let me confirm and test the 8-token truncation.

[assistant] The 8-token truncation drops the most discriminative terms. Now the RRF primary source.

[assistant] Primary RRF source secured with the k-sensitivity table. Now let me quantify the coverage bias empirically on the real index.

[assistant] Decisive. Now the honest control: queries whose true answer lies in the **non**-vectorised 80%.

[assistant] Control experiment done — the vector path degraded 13/60 and improved 0/60. Let me capture the final state and check the reranking research.

[assistant] The reranking research returned findings that change my recommendations materially. Let me correct the report.

[assistant] `board.py` changed at 16:50 — another session is editing it live. Let me pin the version my analysis is based on.

[assistant] Rapport livré : **`/home/turbo/jarvis/board/recherche/02-rag-hybride-rrf.md`** (945 lignes, 28 références dont 12 empiriques, aucun fichier du board modifié).

## Conclusions (10 lignes)

RRF est bien fondé et `k=60` ne doit pas bouger — le papier de Cormack et al. montre lui-même un plateau de 0,6 % entre k=20 et k=100. Le vrai problème n'est pas la fusion, c'est **ce qu'on lui donne à fusionner**. Bruch et al. mesurent que RRF tombe *sous* le meilleur des deux systèmes seuls (MS MARCO .425 vs .441) quand une voie est faible ; ici la voie vectorielle ne voit que 12 % du corpus (1,83 % sur `orchestration-agents`) et injecte pourtant 40 candidats sans seuil, dont le premier pèse exactement autant que le premier BM25. Mesuré sur la base réelle : les fragments vectorisés font 20 % du corpus mais **78 % du top-6 RRF** (×3,8), et **43 % du top-6 BM25 est délogé**. Contre-épreuve décisive : quand la réponse est hors du périmètre vectorisé — le cas de 88 % du corpus — la voie vectorielle **améliore 0 fois sur 60 et dégrade 13 fois**. Deux défauts annexes sont plus coûteux encore : `[:8]` garde les 8 *premiers* mots et jette `sigkill`, `status`, `sha256` en gardant `pourquoi`, `est`, `que` ; et le modèle est appelé **sans les préfixes `search_query:`/`search_document:` que son éditeur déclare obligatoires**. La taille des fragments, elle, est déjà bonne (284 tokens en moyenne, dans l'optimum publié), le recouvrement est neutre, code et prose sont déjà séparés par `domain_id`, et aucu