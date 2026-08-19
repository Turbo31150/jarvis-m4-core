[assistant] Le bootstrap présente un défaut : les blocs mobiles ratent souvent la cellule post (n=31). Je stratifie par cellule et j'ajoute le critère d'abandon.

[assistant] Point critique détecté : la longueur des réponses a chuté après la coupure (car. médian 3540 → 290). C'est un confondant de composition. J'ajoute le contrôle et je fige un instantané reproductible.

[assistant] La série révèle l'essentiel : le niveau pré-immédiat était déjà à 12–13 ms/car. Je vérifie le second critère en fenêtre courte.

[assistant] Reproductibilité vérifiée : le rerun redonne exactement `+0.7911` / `+120,6 %` / IC `[+7,8 % ; +1185,3 %]`.

**Résumé — E1 volet 2**

**Question retenue** : la bascule GPU 2→5 (LM Studio M1, 12:42:00 CEST, ancrée sur 3 traces convergentes) a-t-elle modifié le temps de génération par caractère de `lmstudio-m1`, relativement au témoin `ollama` ?

**N réel** : 1 287 requêtes réussies + 180 abandons, 06:06→13:31 CEST le 06/08. Cellules : traité 541 avant / **67 après** ; témoin 597 / 82. Post-période = **49 min seulement**. Les bases SQLite ne portent aucune mesure de latence exploitable (`protocole_runs` n=50, `dag_runs` n=4, table `llm_cascade_log` absente de `jarvis_master.db`) — seul le JSONL du hub est viable. Appariement par prompt impossible (2 `phash` communs sur 342).

**Méthode** : DiD-ITS sur `log(ms/chars)`, inférence par bootstrap par blocs mobiles **stratifié par cellule** (10 000 tirages) + placebo in-time (2 000 coupures fictives). Test t/ANOVA écartés : autocorrélation des résidus **+0,455**, asymétrie **+8,69**, dérive de charge journalière commune, traitement composite.

**Résultat principal** : DiD = **+120,6 %** de ms/caractère, IC95 % [+7,8 % ; +1 185 %], p=0,038 — **mais le placebo in-time donne p=0,4325** (|DiD| placebo médian 0,734 vs 0,791 observé), et l'effet tombe à **+5,1 % (p=0,78)** avec une fenêtre pré de 2 h. La série 30 min explique tout : le traité était déjà à 12,6–13,0 ms/car dans les 45 min *précédant* la bascule ; le « saut » vient du creux 