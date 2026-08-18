[assistant] Le corpus est très hétérogène (prose + « — » + commande, `[trous:]`, chemins nus). J'écris le classifieur.

[assistant] Note importante : l'index est passé de 70 191 à 74 183 lignes pendant le travail — quelque chose l'alimente encore. Je mesure l'avant/après sur le même état.

[assistant] Le classifieur est correct sur `cloud-init`/`cascade-bibliotheques` (ils existent). Reste un faux positif : `bash lib.sh …` (chemin relatif). J'ajoute la vérification du script passé à l'interpréteur.

[assistant] Jointure `(nom, source)` : 0 doublon, donc exacte. Note : `biblio_filler.py --loop` **tourne toujours** (PID 364331) et ajoute ~4 000 blocs/minute — je ne le tue pas, mais mes mesures bougent. Je modifie maintenant `bloc.sh`.

[assistant] Maintenant le gain de perf dans `bloc.sh` : quand la table des types existe, le bonus « binaire installé » se déduit du `kind` — plus besoin des ~28 000 `command -v`.

[assistant] 8/8 sortent une commande. Je vérifie maintenant qu'elles s'exécutent réellement, puis j'audite la justesse du classifieur sur 60 blocs.

[assistant] Deux problèmes : mon tirage était dégénéré (`/dev/zero`), et il révèle un vrai bug — des `.md` classés `exec`.

[assistant] Index stabilisé à 94 168. Audit de justesse — vrai tirage aléatoire de 60 blocs.

[assistant] Tirage uniforme : je juge chacun. Il est dominé par les chemins nus (51 % du corpus), donc j'ajoute un échantillon **stratifié** (12 par type) qui éprouve réellement les cas durs.

[assistant] 100 % sur les deux échantillons — je cherche activement les erreurs plutôt que de m'arrêter là : faux négatifs (`doc` qui seraient des commandes) et `exec` résiduellement douteux.

[assistant] Cette chasse ciblée a trouvé de vraies erreurs : `cat <fichier_élève>` et `sed … <ton@email>` classés `exec` (ma regex de placeholder était ASCII-only), `for … do kafka-run-class` classé `exec` (tête = mot-clé shell, jamais vérifiée), et `Agent(subagent_type=…)` classé `doc`. Je corrige les trois.

[assistant] Les 6 corrections tiennent. Audit final : nouveau tirage aléatoire de 60 (indépendant du premier) et remesure des 8 intentions.

[assistant] 60/60 sur ce tirage. Vérification finale : les 8 intentions, les temps, et les garde-fous (table absente, `--tous`, élargissement, `BLOC_LIMIT`, bascule cascade).

[assistant] Bug réel trouvé : avec la table absente, `bloc.sh` renvoie ∅ au lieu de retomber sur le comportement historique — le piège classique de `NR==FNR` quand le premier fichier est vide (NR et FNR restent égaux, tout l'index est avalé comme table). Je corrige avec `FILENAME`.

[assistant] Un dernier faux positif de fond : `echo 'longue prose de conseil'` passe le filtre `exec` alors qu'il ne fait rien. Je mesure l'ampleur avant de décider.

[assistant] 1 % des `exec` (92/9052). Le cas net — la commande retenue est *uniquement* un `echo 'prose'` — mérite d'être écarté ; les `find … && echo … && cat …` restent des commandes.

[assistant] Dernier tirage de 60 (post-corrections) pour donner le chiffre de justesse définitif.

[assistant] Tirage uniforme final : 60/60. Mais il est flatté par la composition du corpus (55 % de chemins nus, faciles). Je refais un **stratifié** post-corrections — c'est le test discriminant.

[assistant] Stratifié final : 60/60 également. Le travail est terminé.

---

## LOT 2 — livré

**Fichiers** (absolus)
- `/home/turbo/jarvis/bin/biblio-classify.py` — nouveau classifieur
- `/home/turbo/labo/bibliotheque/lib/BLOCS-KIND.tsv` — sortie `nom⇥source⇥kind`
- `/home/turbo/jarvis/bin/bloc.sh` — modifié (filtre + `--tous`)
- `/home/turbo/jarvis/bin/bloc.sh.bak-lot2-20260804-011456` — sauvegarde avant modification

`BLOCS-INDEX.tsv` n'a pas été touché ; aucun autre script modifié.

### 1. Répartition par type (102 150 blocs)

| kind | n | % |
|---|---:|---:|
| doc | 55 880 | 54,7 % |
| pointeur | 17 307 | 16,9 % |
| template | 13 075 | 12,8 % |
| **exec** | **8 982** | **8,8 %** |
| noop | 6 907 | 6,8 % |

Ton diagnostic est confirmé et même sous-estimé : **91 % du corpus n'est pas exécutable**. Un malus de score ne pouvait pas suffire.

### 2. Justesse du classifieur

**120/120 (100 %)** sur la version livrée : 60 blocs en tirage uniforme + 60 en tirage stratifié (12 par type, bien plus discriminant).

Ce chiffre n'est honnête que parce que j'ai chassé les erreurs au lieu d'accepter le premier 100 %. Le tirage uniforme est flatté par le corpus (55 % de chemins nus, triviaux) ; une inspection ciblée des cas frontière a révélé **6 classes d'erreur**, toutes corrigées ensuite :

| erreur | cause | correctif |
|---|---|---|
| `README.md` → exec | tout `~/prompts` est en chmod 775, `os.access(X_OK)` dit oui | extensions documentaires exclues |
| `cat <fichier_élève>`, `sed … <ton@email>