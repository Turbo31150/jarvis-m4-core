[user] Tu mènes une recherche académique rigoureuse sur une question de recherche d'information. Tu ne connais rien de la conversation qui précède. Livrable : un rapport écrit dans un fichier.

## La question de recherche

**Sur un corpus très hétérogène de 78 169 fragments (mémoires techniques, code source, documentation, fiches de connaissance), la fusion par rang réciproque (RRF) de BM25 et de la similarité cosinus est-elle le bon choix — ou faut-il pondérer les voies, ajouter un reranker, ou changer de stratégie de découpage ?**

## Le système concret qui motive la question

`/home/turbo/jarvis/board/` — moteur de RAG local (Python stdlib, SQLite, LM Studio en local). **Lis `board.py` (fonctions `chunk_text`, `retrieve`, `embed`) et `board_schema.sql` avant de chercher.**

Implémentation actuelle, à vérifier toi-même dans le code :
- **Découpage** : 1400 caractères, chevauchement 200, coupure sur frontière lisible (`\n\n`, `\n`, `. `), rejet des fragments < 80 caractères.
- **Lexical** : SQLite FTS5, `bm25()`, tokenizer `unicode61 remove_diacritics 2`. Les tokens de la question (`\w{3,}`, max 8) sont joints par `OR`.
- **Vectoriel** : embeddings `text-embedding-nomic-embed-text-v1.5`, **dimension 768**, stockés en BLOB float32, cosinus calculé **en Python sur tous les chunks du domaine** (pas d'index ANN).
- **Fusion** : RRF avec constante k=60, `1/(60+rang)`, top 40 de chaque voie, puis top-k final.

Chiffres réels : **78 169 chunks, dont seulement 3 291 vectorisés (4 %)**. Le 

[assistant] I'll start by reading the actual system code and database, then research the literature.

[assistant] Key code observations noted. Now let me check the real database and start the literature search.

[assistant] Major lead: the embedding model may be English-only. Verifying on primary sources and checking the actual corpus language.