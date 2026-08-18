#!/usr/bin/env python3
"""
cascade-log-ingest.py — Ingesteur idempotent JSONL -> SQLite + outil de stats.

Source : /home/pamerys/jarvis/data/llm_cascade_log.jsonl  (ecrit par chat_proxy.js, port 18800)
Cible  : /home/pamerys/jarvis/data/jarvis_master.db        (DB partagee, mode WAL)

Usage :
  python3 cascade-log-ingest.py            # ingestion (defaut)
  python3 cascade-log-ingest.py --stats    # affiche les statistiques

stdlib uniquement : sqlite3, json, os, sys.
Transactions courtes, DB jamais verrouillee longtemps.
Lecture seule du JSONL.
"""

import os
import sys
import json
import sqlite3

# Chemins surchargeables par env (testabilité : smoke sur DB+log jetables).
JSONL_PATH = os.environ.get(
    "CASCADE_LOG", "/home/pamerys/jarvis/data/llm_cascade_log.jsonl"
)
DB_PATH = os.environ.get("CASCADE_DB", "/home/pamerys/jarvis/data/jarvis_master.db")


def connect():
    """Ouvre la DB en WAL avec busy_timeout (DB partagee)."""
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def ensure_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS llm_cascade_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts TEXT, via TEXT, served TEXT, ms INTEGER,
          ok INTEGER, tried INTEGER, chars INTEGER,
          UNIQUE(ts, via, served, ms)
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ingest_state (
          source TEXT PRIMARY KEY,
          last_line INTEGER
        );
        """
    )
    conn.commit()


def get_last_line(conn, source):
    row = conn.execute(
        "SELECT last_line FROM ingest_state WHERE source=?", (source,)
    ).fetchone()
    return row[0] if row else 0


def set_last_line(conn, source, n):
    conn.execute(
        "INSERT INTO ingest_state(source, last_line) VALUES(?,?) "
        "ON CONFLICT(source) DO UPDATE SET last_line=excluded.last_line",
        (source, n),
    )


def ingest():
    if not os.path.exists(JSONL_PATH):
        print(f"[ingest] source absente : {JSONL_PATH} (rien a faire)")
        return 0

    conn = connect()
    try:
        ensure_schema(conn)

        # Lecture seule du JSONL ; on compte les lignes totales presentes.
        with open(JSONL_PATH, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        total_lines = len(lines)

        last_line = get_last_line(conn, JSONL_PATH)

        # Cas tronque/retreci : fichier plus court que le curseur -> reset offset.
        reset = False
        if total_lines < last_line:
            reset = True
            last_line = 0

        read = inserted = ignored = parse_err = 0

        # On garde INSERT OR IGNORE comme filet meme avec le curseur.
        # Transaction courte : un seul commit pour le batch des nouvelles lignes.
        for idx in range(last_line, total_lines):
            raw = lines[idx].strip()
            if not raw:
                continue
            read += 1
            try:
                rec = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                parse_err += 1
                continue

            ok_val = rec.get("ok")
            cur = conn.execute(
                "INSERT OR IGNORE INTO llm_cascade_log "
                "(ts, via, served, ms, ok, tried, chars) VALUES (?,?,?,?,?,?,?)",
                (
                    rec.get("ts"),
                    rec.get("via"),
                    rec.get("served"),
                    rec.get("ms"),
                    1 if ok_val else 0,
                    rec.get("tried"),
                    rec.get("chars"),
                ),
            )
            if cur.rowcount == 1:
                inserted += 1
            else:
                ignored += 1

        set_last_line(conn, JSONL_PATH, total_lines)
        conn.commit()
    finally:
        conn.close()

    note = " (curseur reset : fichier tronque)" if reset else ""
    print(
        f"[ingest]{note} lignes lues={read} inserees={inserted} "
        f"ignorees(doublons)={ignored} erreurs_parse={parse_err} "
        f"| total_fichier={total_lines}"
    )
    return inserted


def _percentile(sorted_vals, pct):
    """Percentile par methode nearest-rank sur une liste triee non vide."""
    if not sorted_vals:
        return None
    k = max(1, int(round(pct / 100.0 * len(sorted_vals))))
    k = min(k, len(sorted_vals))
    return sorted_vals[k - 1]


def stats():
    if not os.path.exists(DB_PATH):
        print(f"[stats] DB absente : {DB_PATH}")
        return
    conn = connect()
    try:
        ensure_schema(conn)
        total = conn.execute("SELECT COUNT(*) FROM llm_cascade_log").fetchone()[0]
        if total == 0:
            print("[stats] table vide — lancer l'ingestion d'abord.")
            return

        ok_count = conn.execute(
            "SELECT COUNT(*) FROM llm_cascade_log WHERE ok=1"
        ).fetchone()[0]
        fallback_count = conn.execute(
            "SELECT COUNT(*) FROM llm_cascade_log WHERE tried>0"
        ).fetchone()[0]
        avg_ms = conn.execute(
            "SELECT AVG(ms) FROM llm_cascade_log WHERE ms IS NOT NULL"
        ).fetchone()[0]
        ms_vals = [
            r[0]
            for r in conn.execute(
                "SELECT ms FROM llm_cascade_log WHERE ms IS NOT NULL ORDER BY ms"
            ).fetchall()
        ]
        by_served = conn.execute(
            "SELECT COALESCE(served,'<null>') s, COUNT(*) c, AVG(ms) a "
            "FROM llm_cascade_log GROUP BY s ORDER BY c DESC"
        ).fetchall()
        by_via = conn.execute(
            "SELECT COALESCE(via,'<null>') v, COUNT(*) c "
            "FROM llm_cascade_log GROUP BY v ORDER BY c DESC"
        ).fetchall()
    finally:
        conn.close()

    p50 = _percentile(ms_vals, 50)
    p95 = _percentile(ms_vals, 95)

    print("=" * 56)
    print("CASCADE LLM — STATS")
    print("=" * 56)
    print(f"Total routages      : {total}")
    print(f"Taux OK             : {ok_count}/{total} ({100.0 * ok_count / total:.1f}%)")
    print(
        f"Taux fallback (>0)  : {fallback_count}/{total} "
        f"({100.0 * fallback_count / total:.1f}%)"
    )
    print("-" * 56)
    print("Latence (ms)")
    print(f"  moyenne : {avg_ms:.0f}" if avg_ms is not None else "  moyenne : n/a")
    print(f"  p50     : {p50}")
    print(f"  p95     : {p95}")
    print("-" * 56)
    print("Repartition par backend (served) :")
    for s, c, a in by_served:
        a_txt = f"{a:.0f}ms" if a is not None else "n/a"
        print(f"  {c:>4}  {100.0 * c / total:5.1f}%  avg={a_txt:>8}  {s}")
    print("-" * 56)
    print("Repartition par via :")
    for v, c in by_via:
        print(f"  {c:>4}  {100.0 * c / total:5.1f}%  {v}")
    print("=" * 56)


def main(argv):
    if "--stats" in argv:
        stats()
    else:
        ingest()


if __name__ == "__main__":
    main(sys.argv[1:])
