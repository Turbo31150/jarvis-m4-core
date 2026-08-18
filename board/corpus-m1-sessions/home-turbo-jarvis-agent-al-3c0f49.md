[assistant] Base capturée. J'analyse maintenant la composition réelle de l'index pour calibrer l'extraction de tête.

[assistant] Base : les têtes réellement installées sont 279 sur 28 112 candidates, et le pré-calcul coûte 0,7 s. Je sauvegarde puis modifie.

[assistant] Le daemon `biblio-filler` fait grossir l'index en direct (62 199 → 74 182 lignes pendant la session) : mon avant/après n'était pas sur les mêmes données. Je refais la comparaison sur un snapshot figé.

[assistant] Lot 1 livré. Résultat mesuré : **5/8**, pas 7/8. Je le dis avec les chiffres réels.

## 1. Diff de `bloc.sh`

Fichier : `/home/turbo/jarvis/bin/bloc.sh` · sauvegarde : `/home/turbo/jarvis/bin/bloc.sh.bak-20260804_011315` · aucun autre fichier touché.

Trois blocs ajoutés, ~30 lignes dont la moitié de commentaire :

**a) extraction de tête, partagée par les deux passes awk** (inséré après le contrôle d'existence de l'index)
```awk
function head(b,   t,n,i,w) {
  sub(/^[ \t]+/,"",b); n=split(b,t,/[ \t]+/); i=1;
  while (i<=n) { w=t[i];
    if (w ~ /^[A-Za-z_][A-Za-z0-9_]*=/ || w=="sudo" || w=="timeout" \
        || w=="nohup" || w=="env" || w=="command") { i++; continue }
    break }
  return (i<=n ? t[i] : "") }
```

**b) pré-calcul UNE fois de la liste des binaires présents**
```bash
BINS="|$(awk -F'\t' "$HEAD_AWK"'
  NR>1 { h=head($4); if (h ~ /^[A-Za-z0-9_\/][A-Za-z0-9_.+\/-]*$/) print h }' "$IDX" \
  | sort -u \
  | while read -r h; do command -v -- "$h" >/dev/null 2>&1 && echo "$h"; done \
  | paste -sd'|')|"
```
Le pré-filtre par regex ramène 74 182 blocs à 28 112 têtes distinctes plausibles, dont 279 réellement installées. Coût : 0,7 s.

**c) le bonus/malus, dans le `NR>1` juste avant `line=…`**
```awk
b=$4; sub(/^[ \t]+/,"",b);
if(head(b) in ok)                       sc+=6;   # vraie commande installée
if(substr(b,1,1)=="#" || b ~ /^\/[^ \t;|]*$/) sc-=4;  # commentaire / chemin nu
if(index(b,"[trous:"))                  sc-=2;   # template à trous
```
plus, en `BEGIN`,