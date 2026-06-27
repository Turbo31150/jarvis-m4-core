#!/usr/bin/env python3
"""
JARVIS Loop Monitor — auto-monitoring daemon
Checks every 60s:
  - running >10min → flag stalled
  - failed → retry (max 3)
  - pending >5min → dispatch if agent available
Logs each cycle to pipeline_log.
Stops on SIGTERM, resumes from DB on restart.
"""

import sqlite3
import time
import signal
import sys
import os
import subprocess
from datetime import datetime, timedelta, timezone

DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"
LOOP_INTERVAL = 60  # seconds between cycles
STALL_THRESHOLD_MIN = 10  # minutes before running→stalled
PENDING_DISPATCH_MIN = 5  # minutes before pending→dispatch
MAX_RETRIES = 3
DEBUG = "--debug" in sys.argv

_running = True


def sigterm_handler(_sig, _frame):
    global _running
    print("\n[LOOP] SIGTERM received — shutting down gracefully.")
    _running = False


signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGINT, sigterm_handler)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def log_step(
    conn,
    task_id,
    step,
    machine="local",
    model="loop_monitor",
    latency_ms=0,
    quality_score=None,
):
    conn.execute(
        """INSERT INTO pipeline_log
           (task_id, step, machine, model, latency_ms, quality_score)
           VALUES (?,?,?,?,?,?)""",
        (task_id, step, machine, model, latency_ms, quality_score),
    )
    conn.commit()


def debug(msg):
    if DEBUG:
        print(f"  [DBG] {msg}")


def dispatch_task(task_id: int, title: str, agent: str, machine: str, conn):
    """Fire-and-forget dispatch via claudelm. Returns True on success."""
    t_start = time.time()
    prompt = f"Execute JARVIS task (agent={agent}): {title}"
    try:
        result = subprocess.run(
            ["claudelm", "--no-system", prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        latency = int((time.time() - t_start) * 1000)
        output = result.stdout.strip()
        quality = min(1.0, len(output) / 500.0)
        conn.execute(
            """UPDATE tasks SET status='done', progress=100, score=?,
               updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (round(quality * 10, 2), task_id),
        )
        conn.commit()
        log_step(conn, task_id, "loop_dispatch", machine, "claudelm", latency, quality)
        debug(f"Task #{task_id} dispatched OK latency={latency}ms score={quality:.2f}")
        return True
    except subprocess.TimeoutExpired:
        conn.execute(
            "UPDATE tasks SET status='failed', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (task_id,),
        )
        conn.commit()
        log_step(conn, task_id, "loop_dispatch_timeout", machine)
        debug(f"Task #{task_id} dispatch TIMEOUT → failed")
        return False
    except Exception as e:
        debug(f"Task #{task_id} dispatch error: {e}")
        return False


def count_retries(task_id: int, conn) -> int:
    """Count how many times loop already retried this task."""
    return conn.execute(
        "SELECT COUNT(*) FROM pipeline_log WHERE task_id=? AND step LIKE 'loop%'",
        (task_id,),
    ).fetchone()[0]


def run_cycle(conn):
    now = datetime.now(timezone.utc)
    stall_cutoff = now - timedelta(minutes=STALL_THRESHOLD_MIN)
    pending_cutoff = now - timedelta(minutes=PENDING_DISPATCH_MIN)

    # 1. Detect stalled running tasks
    stalled = conn.execute(
        """SELECT id, title, agent, machine FROM tasks
           WHERE status='running'
           AND datetime(updated_at) < ?""",
        (stall_cutoff.strftime("%Y-%m-%d %H:%M:%S"),),
    ).fetchall()

    for t in stalled:
        print(f"  [STALL] Task #{t['id']}: {t['title'][:60]}")
        conn.execute(
            "UPDATE tasks SET status='failed', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (t["id"],),
        )
        conn.commit()
        log_step(conn, t["id"], "stall_detected", t["machine"] or "?")

    # 2. Retry failed tasks (max MAX_RETRIES)
    failed = conn.execute(
        "SELECT id, title, agent, machine FROM tasks WHERE status='failed'"
    ).fetchall()

    for t in failed:
        retries = count_retries(t["id"], conn)
        if retries >= MAX_RETRIES:
            debug(f"Task #{t['id']} exceeded max retries ({MAX_RETRIES}) — skip")
            continue
        print(
            f"  [RETRY {retries + 1}/{MAX_RETRIES}] Task #{t['id']}: {t['title'][:60]}"
        )
        conn.execute(
            "UPDATE tasks SET status='running', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (t["id"],),
        )
        conn.commit()
        dispatch_task(
            t["id"],
            t["title"],
            t["agent"] or "omega-dev-agent",
            t["machine"] or "M1",
            conn,
        )

    # 3. Dispatch long-pending tasks
    pending = conn.execute(
        """SELECT id, title, agent, machine FROM tasks
           WHERE status='pending'
           AND datetime(created_at) < ?""",
        (pending_cutoff.strftime("%Y-%m-%d %H:%M:%S"),),
    ).fetchall()

    for t in pending:
        print(f"  [DISPATCH] Task #{t['id']}: {t['title'][:60]}")
        conn.execute(
            "UPDATE tasks SET status='running', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (t["id"],),
        )
        conn.commit()
        dispatch_task(
            t["id"],
            t["title"],
            t["agent"] or "omega-dev-agent",
            t["machine"] or "M1",
            conn,
        )

    summary = f"stalled={len(stalled)} retried={len(failed)} dispatched={len(pending)}"
    return summary


def main():
    cycle = 0
    print(
        f"[LOOP] Started {'(DEBUG)' if DEBUG else ''} — interval={LOOP_INTERVAL}s  PID={os.getpid()}"
    )
    print(f"       DB: {DB_PATH}")
    print("       SIGTERM / Ctrl-C to stop.\n")

    while _running:
        cycle += 1
        conn = get_db()
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[LOOP] Cycle #{cycle} at {ts}")

        try:
            summary = run_cycle(conn)
            print(f"         → {summary}")
        except Exception as e:
            print(f"[LOOP] ERROR in cycle #{cycle}: {e}")
        finally:
            conn.close()

        if not _running:
            break

        # Sleep in 1s ticks so SIGTERM is responsive
        for _ in range(LOOP_INTERVAL):
            if not _running:
                break
            time.sleep(1)

    print("[LOOP] Stopped.")


if __name__ == "__main__":
    main()
