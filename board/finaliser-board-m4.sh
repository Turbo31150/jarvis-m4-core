#!/usr/bin/env bash
# Finalise la synchro du board sur M4 — à lancer quand `board.py embed` a terminé.
#
# Contexte (2026-08-14) : M6 avait le corpus le plus large (247 739 chunks),
# M4 avait 2,5x plus d'embeddings. Le board unifié (corpus M6 + embeddings M4 +
# historique des deux) a été construit dans board.db.new et déjà déployé sur M6.
# Ici on rattrape les embeddings que M4 a produits DEPUIS cette fusion, puis on bascule.
#
# Idempotent : relançable sans risque.
set -euo pipefail

D=/storage/m1-mirror/databases
NEW="$D/board.db.new"
CUR="$D/board.db"
STAMP=$(date +%Y%m%d-%H%M%S)

[ -f "$NEW" ] || { echo "board.db.new absent — rien à faire (bascule déjà effectuée ?)"; exit 0; }

if pgrep -f 'board.py embed' >/dev/null; then
    echo "REFUS : un board.py embed tourne encore. Relance ce script après sa fin."
    pgrep -af 'board.py embed' | head -3
    exit 1
fi

if fuser "$CUR" >/dev/null 2>&1; then
    echo "REFUS : $CUR est ouvert par un processus."
    fuser -v "$CUR" 2>&1 | head -5
    exit 1
fi

echo "== rattrapage des embeddings produits depuis la fusion =="
avant=$(sqlite3 "$NEW" "select count(*) from chunks where embedding is not null;")
sqlite3 "$NEW" <<SQL
ATTACH DATABASE 'file:$CUR?mode=ro' AS ancien;
BEGIN;
UPDATE chunks
   SET embedding = (SELECT b.embedding FROM ancien.chunks b WHERE b.id = chunks.id)
 WHERE embedding IS NULL
   AND EXISTS (SELECT 1 FROM ancien.chunks b WHERE b.id = chunks.id AND b.embedding IS NOT NULL);
-- l'historique de consultation a pu s'enrichir lui aussi
INSERT OR IGNORE INTO queries   SELECT * FROM ancien.queries;
INSERT OR IGNORE INTO answers   SELECT * FROM ancien.answers;
INSERT OR IGNORE INTO citations SELECT * FROM ancien.citations;
COMMIT;
DETACH DATABASE ancien;
SQL
apres=$(sqlite3 "$NEW" "select count(*) from chunks where embedding is not null;")
echo "   vectorisés : $avant -> $apres"

echo "== contrôle d'intégrité =="
[ "$(sqlite3 "$NEW" 'pragma quick_check;' | head -1)" = "ok" ] || { echo "ÉCHEC quick_check — bascule annulée"; exit 1; }

echo "== bascule =="
mv "$CUR" "$D/board.db.avant-sync-$STAMP"
mv "$NEW" "$CUR"
sqlite3 "file:$CUR?mode=ro" \
  "select 'ACTIF : chunks='||(select count(*) from chunks)||' vectorises='||(select count(*) from chunks where embedding is not null)||' queries='||(select count(*) from queries);"
echo "ancien conservé : $D/board.db.avant-sync-$STAMP"
echo
echo "ATTENTION : /storage est à 97%. Supprime l'ancien quand tu es sûr :"
echo "  rm $D/board.db.avant-sync-$STAMP"
