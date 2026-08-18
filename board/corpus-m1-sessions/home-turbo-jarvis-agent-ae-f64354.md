[assistant] `commande-directe` existe déjà (11 829 lignes) — les ~370 orphelines sont l'écart avec les 12 199 en base. Vérifions la clé de correspondance.

[assistant] 386 orphelins confirmés. Extraction propre (les ids semblent contenir des sauts de ligne — je nettoie).

[assistant] Cause racine trouvée : 343 des 386 orphelins sont des blocs **multi-lignes** — l'ingestion précédente les avait sautés. Je prépare l'extraction.

[assistant] Backup faite (md5 identique). La base grossit en direct (daemon biblio-filler) — je travaille sur le snapshot JSON figé.