#!/usr/bin/env python3
"""SQLite → PostgreSQL sync bridge — M1 JARVIS"""

import sqlite3
import sys
from datetime import datetime

DRY_RUN = "--dry-run" in sys.argv

SQLITE_DBS = {
    "cowork": "/home/pamerys/jarvis/cowork_engine.db",
    "jarvis": "/home/pamerys/jarvis/data/jarvis.db",
    "etoile": "/home/pamerys/jarvis/data/etoile.db",
}

PG_CONN = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", 5432)),
    "dbname": os.environ.get("PG_DB", "jarvis"),
    "user": os.environ.get("PG_USER", "jarvis"),
    "password": os.environ["PG_PASSWORD"],
}

SYNC_TABLES = [
    (
        "cowork",
        "bench_uid",
        "unified",
        "cowork_benchmarks",
        [
            "uid",
            "machine",
            "scenario",
            "model",
            "latency_ms",
            "quality_score",
            "ts",
            "status",
        ],
    ),
    (
        "cowork",
        "model_usage_log",
        "unified",
        "model_usage_log",
        [
            "ts",
            "machine",
            "model",
            "backend",
            "task_type",
            "latency_ms",
            "quality_score",
            "routed_via",
        ],
    ),
    (
        "etoile",
        "jarvis_cluster_nodes",
        "unified",
        "cluster__nodes",
        ["alias", "ip", "hostname", "os", "role", "status", "last_seen"],
    ),
    (
        "jarvis",
        "jarvis_agents",
        "unified",
        "core__agents",
        ["id", "name", "type", "endpoint", "status"],
    ),
]


def main():
    try:
        import psycopg2

        pg = psycopg2.connect(**PG_CONN)
        pg_cur = pg.cursor()
    except Exception as e:
        print(f"[bridge] PG connexion échouée: {e}")
        return

    synced = 0
    for src_db, src_table, pg_schema, pg_table, cols in SYNC_TABLES:
        db_path = SQLITE_DBS[src_db]
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT {','.join(cols)} FROM {src_table} ORDER BY rowid DESC LIMIT 500"
            ).fetchall()
            conn.close()
        except Exception as e:
            print(f"[bridge] SQLite {src_db}.{src_table}: {e}")
            continue

        col_str = ",".join(cols)
        placeholders = ",".join(["%s"] * len(cols))
        upsert = f"""INSERT INTO {pg_schema}.{pg_table} ({col_str})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING"""

        for row in rows:
            values = tuple(row[c] for c in cols if c in row.keys())
            if len(values) < len(cols):
                continue
            if DRY_RUN:
                print(f"[dry] {pg_schema}.{pg_table} ← {dict(zip(cols, values))}")
            else:
                try:
                    pg_cur.execute(upsert, values)
                    synced += 1
                except Exception:
                    pass

    if not DRY_RUN:
        pg.commit()
    pg.close()
    print(
        f"[bridge] Sync {'(dry) ' if DRY_RUN else ''}terminé — {synced} rows synced @ {datetime.utcnow().isoformat()}"
    )


if __name__ == "__main__":
    main()
