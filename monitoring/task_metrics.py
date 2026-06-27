#!/usr/bin/env python3
"""
JARVIS Task Metrics Collector
Capture CPU%, RAM MB, GPU VRAM MB, latence par tâche exécutée.
Stocke dans pipeline_log (step="metrics_before" / "metrics_after").
"""

import sqlite3
import time
import subprocess
from pathlib import Path

DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_db(conn):
    """Ajoute les colonnes métriques à pipeline_log si absentes."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(pipeline_log)")}
    cols = {
        "cpu_percent": "REAL",
        "ram_mb": "REAL",
        "vram_mb": "REAL",
    }
    for col, dtype in cols.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE pipeline_log ADD COLUMN {col} {dtype}")
    conn.commit()


def _capture_metrics() -> dict:
    """Lit CPU%, RAM et GPU VRAM sur la machine locale."""
    import psutil

    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    ram_mb = round(ram.used / 1024 / 1024, 1)

    vram_mb = 0.0
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
            vram_mb = sum(float(v) for v in lines)
    except Exception:
        pass

    return {"cpu_percent": cpu, "ram_mb": ram_mb, "vram_mb": vram_mb}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def snapshot_before(task_id: int) -> dict:
    """
    Capture CPU%, RAM, GPU VRAM avant exécution.
    Stocke dans pipeline_log avec step='metrics_before'.
    Retourne le snapshot pour usage ultérieur par snapshot_after.
    """
    conn = _get_db()
    _migrate_db(conn)

    snap = _capture_metrics()
    snap["ts"] = time.time()

    conn.execute(
        """INSERT INTO pipeline_log
           (task_id, step, machine, cpu_percent, ram_mb, vram_mb)
           VALUES (?, 'metrics_before', 'local', ?, ?, ?)""",
        (task_id, snap["cpu_percent"], snap["ram_mb"], snap["vram_mb"])
    )
    conn.commit()
    conn.close()
    return snap


def snapshot_after(task_id: int, model: str, latency_ms: int,
                   before_snap: dict | None = None):
    """
    Capture CPU%, RAM, GPU VRAM après exécution.
    Calcule delta vs before_snap si fourni.
    Stocke dans pipeline_log avec step='metrics_after'.
    Met à jour tasks.score si delta disponible.
    """
    conn = _get_db()
    _migrate_db(conn)

    snap = _capture_metrics()

    delta_ram = 0.0
    delta_vram = 0.0
    delta_cpu = 0.0
    if before_snap:
        delta_ram = max(0.0, snap["ram_mb"] - before_snap["ram_mb"])
        delta_vram = max(0.0, snap["vram_mb"] - before_snap["vram_mb"])
        delta_cpu = max(0.0, snap["cpu_percent"] - before_snap["cpu_percent"])

    conn.execute(
        """INSERT INTO pipeline_log
           (task_id, step, machine, model, latency_ms,
            cpu_percent, ram_mb, vram_mb)
           VALUES (?, 'metrics_after', 'local', ?, ?,
                   ?, ?, ?)""",
        (task_id, model, latency_ms,
         snap["cpu_percent"], snap["ram_mb"], snap["vram_mb"])
    )

    # Score de charge : normalisation simple (plus c'est bas, mieux c'est pour le score)
    # score stocké = qualité pipeline (inchangé) ; on n'écrase pas
    # Mais on insère un log delta si pertinent
    if before_snap:
        conn.execute(
            """INSERT INTO pipeline_log
               (task_id, step, machine, model, latency_ms,
                cpu_percent, ram_mb, vram_mb)
               VALUES (?, 'metrics_delta', 'local', ?, ?,
                       ?, ?, ?)""",
            (task_id, model, latency_ms,
             round(delta_cpu, 2), round(delta_ram, 2), round(delta_vram, 2))
        )

    conn.commit()
    conn.close()


def get_heavy_tasks(limit: int = 10) -> list:
    """
    Retourne les tâches triées par consommation (RAM + VRAM + latence) desc.
    Agrège les snapshots 'metrics_after' par task_id.
    Format: [{task_id, title, avg_cpu, avg_ram_mb, avg_vram_mb, avg_latency, count}]
    """
    conn = _get_db()
    _migrate_db(conn)

    rows = conn.execute("""
        SELECT
            pl.task_id,
            t.title,
            AVG(pl.cpu_percent)  AS avg_cpu,
            AVG(pl.ram_mb)       AS avg_ram_mb,
            AVG(pl.vram_mb)      AS avg_vram_mb,
            AVG(pl.latency_ms)   AS avg_latency,
            COUNT(*)             AS count
        FROM pipeline_log pl
        LEFT JOIN tasks t ON t.id = pl.task_id
        WHERE pl.step IN ('metrics_after', 'dispatch+run')
          AND (pl.ram_mb IS NOT NULL OR pl.latency_ms IS NOT NULL)
        GROUP BY pl.task_id
        ORDER BY (COALESCE(AVG(pl.ram_mb),0)
                + COALESCE(AVG(pl.vram_mb),0)
                + COALESCE(AVG(pl.latency_ms),0)/1000.0) DESC
        LIMIT ?
    """, (limit,)).fetchall()

    conn.close()
    result = []
    for r in rows:
        result.append({
            "task_id":     r["task_id"],
            "title":       r["title"] or f"Task #{r['task_id']}",
            "avg_cpu":     round(r["avg_cpu"] or 0, 1),
            "avg_ram_mb":  round(r["avg_ram_mb"] or 0, 1),
            "avg_vram_mb": round(r["avg_vram_mb"] or 0, 1),
            "avg_latency": round(r["avg_latency"] or 0, 0),
            "count":       r["count"],
        })
    return result


def get_task_snapshots(task_id: int) -> dict:
    """
    Retourne le détail complet d'une tâche avec tous ses snapshots pipeline_log.
    """
    conn = _get_db()
    _migrate_db(conn)

    task = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not task:
        conn.close()
        return {}

    logs = conn.execute(
        """SELECT step, machine, model, latency_ms, cpu_percent, ram_mb, vram_mb,
                  quality_score, timestamp
           FROM pipeline_log WHERE task_id=? ORDER BY timestamp""",
        (task_id,)
    ).fetchall()

    conn.close()
    return {
        "task_id": task_id,
        "title":   task["title"],
        "status":  task["status"],
        "agent":   task["agent"],
        "machine": task["machine"],
        "score":   task["score"],
        "snapshots": [dict(l) for l in logs],
    }


if __name__ == "__main__":
    import json
    print("=== get_heavy_tasks() ===")
    print(json.dumps(get_heavy_tasks(), indent=2))
