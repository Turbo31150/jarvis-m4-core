[user] Tu fais une recherche documentaire web rigoureuse (WebSearch + WebFetch). Sujet : **déduplication au-delà de l'égalité exacte dans les grands corpus textuels**.

Charge d'abord les outils : ToolSearch avec query "select:WebSearch,WebFetch".

Questions précises :
1. MinHash + LSH, SimHash, suffix-array / substring dedup : principes, seuils de similarité Jaccard réellement utilisés (ex. 0,8 ? 0,7 ?), nombre de permutations/hashes, taille des shingles (n-grams).
2. Complexité algorithmique et coût réel : combien coûte un MinHash-LSH sur 200 000 documents ? sur 1 million ? sur 1 milliard ? Cherche des chiffres de temps CPU/mémoire publiés.
3. Ce qui est **réellement utilisé en production** :
   - C4 / T5 (Raffel et al. 2020) — quelle méthode de dedup, quel volume retiré
   - RefinedWeb (Penedo et al. 2023, Falcon) — fuzzy dedup MinHash, % retiré
   - FineWeb / FineWeb-Edu (HuggingFace 2024) — leur article de blog détaille les expériences de dedup, y compris le résultat contre-intuitif que la dedup globale inter-dumps a DÉGRADÉ la performance vs dedup par dump. Récupère les chiffres exacts.
   - Dolma (AI2), The Pile, Gopher (Rae et al. 2021) et leurs règles de dedup
   - Lee et al. 2021/2022 "Deduplicating Training Data Makes Language Models Better" — chiffres de mémorisation, gains mesurés
   - Moteurs de recherche web : shingling de Broder (1997), Charikar SimHash (2002), Manku et al. WWW 2007 "Detecting near-duplicates for web crawling" (chiffres : 8 milliards de pages, 64-bit

[assistant] Let me fetch the FineWeb sources directly and search the other themes in parallel.

[assistant] J'ai rassemblé et vérifié les sources. Voici le livrable.

---

# Déduplication au-delà de l'égalité exacte dans les grands corpus textuels
**Notes de recherche — sources primaires vérifiées, chiffres tracés**

Convention de rigueur utilisée partout : **[M]** = mesuré/publié dans la source citée · **[A]** = affirmé sans mesure · **[C]** = calculé par moi à partir de paramètres publiés · **[X]** = pas de réponse solide trouvée.

---

## 1. Les trois familles techniques et leurs paramètres réels

### 1.1 Shingling + MinHash + LSH

**Principe** : document → ensemble de *shingles* (n-grammes de mots ou de caractères) → signature MinHash de *k* hachages → partition de la signature en *r* bandes de *b* lignes → deux documents partageant la valeur d'au moins une bande sont candidats. Probabilité de collision : `P = 1 − (1 − s^b)^r` où `s` = indice de Jaccard réel (formule explicite dans Lee et al. 2021, annexe A).

**Paramètres réellement employés en production** (tous **[M]**, relevés dans les articles) :

| Système | Shingle | k (hachages) | Bandes × lignes | Seuil | Source |
|---|---|---|---|---|---|
| Broder/AltaVista 1997 | 10 mots, empreintes Rabin 40 bits, 1 shingle sur 25 | — (sketch) | — | **resemblance 50 %** | src-tn-1997-015 |
| Gopher / MassiveText 2021 | **13-grammes** | non publié | non publié | **Jaccard > 0,8** | arXiv 2112.11446 §A.1.1 |
| Lee et al. 2021 (NearDup) | **5-grammes** (tabulation hashing) | **9 000** | 450 bandes × 20 lignes | **Jaccard > 0,8 ET simila