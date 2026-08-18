[assistant] Je commence par consulter le contexte réel du système (sans rien modifier) puis je lance la recherche documentaire.

[assistant] Je lance trois agents de recherche en parallèle sur les axes, et je conduis mes propres recherches de vérification en parallèle.

[assistant] Toutes les citations à risque sont vérifiées (les trois arXiv existent avec les chiffres annoncés, et le résultat FineWeb est confirmé mot pour mot). Je rédige le rapport.

[assistant] Rapport écrit : `/home/turbo/jarvis/board/recherche/04-moisson-passage-echelle.md` (83 Ko, 716 lignes, 12 recommandations numérotées R1 à R12, ~80 sources).

## Résumé des conclusions décisives

**1. La croissance n'est pas le problème — la règle de sélection l'est.** FineWeb (vérifié mot pour mot à la source) : une déduplication MinHash appliquée *globalement* à travers tous les crawls a produit 4 000 Gt sans aucun gain, la *même* appliquée *par lot* en a produit 20 000 Gt au niveau de l'état de l'art. Sur un dump donné, le modèle entraîné sur les 90 % **rejetés** bat celui entraîné sur les 10 % **conservés** — une règle globale sur un corpus qui s'accumule dans le temps ne trie pas, elle biaise.

**2. Il n'existe aucun seuil publié**, ni de volume ni de déséquilibre de source. C'est un résultat, pas une dérobade : le seul travail isolant la variable « taille de corpus » est un préprint de juin 2026 (arXiv 2606.11350, vérifié). La question « à partir de quel N ? » doit être instrumentée localement, pas cherchée dans la littérature.

**3. Ce qui dégrade le rappel, c'est le voisin proche mais faux, pas le volume.** Un seul document « related but not relevant » coûte 25 % d'exactitude, dix-huit en coûtent 58 % ; les documents aléatoires sont quasi inoffensifs. À 68 % de monoculture, chaque nouveau bloc de la source dominante est un candidat *hard negative* pour les requêtes des autres sources.

**4. Le registre FTS5 figé n'est pas un mur d'échelle** : FTS5 tient 18,2 M lignes e