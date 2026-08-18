#!/usr/bin/env python3
"""
audit_commands.py — Handlers CLI pour `jarvis audit:*`
MODE AUDIT / DEEP RESEARCH. Réutilise ~/jarvis/scripts/jarvis-audit.sh
(pipeline init→scan-local→scan-web→multi-agents→report→todo→cascade, 0 token API).
Logge chaque run dans ~/jarvis/db/cli_history.db (table audit_runs).
"""

import os
import sqlite3
import subprocess
import time

JARVIS = os.environ.get("JARVIS_HOME", os.path.expanduser("~/jarvis"))
AUDIT_SH = os.path.join(JARVIS, "scripts", "jarvis-audit.sh")
HIST_DB = os.path.join(JARVIS, "db", "cli_history.db")

SUBCMDS = (
    "run",
    "init",
    "scan-local",
    "scan-web",
    "multi-agents",
    "report",
    "todo",
    "cascade",
)


def _ensure_table():
    os.makedirs(os.path.dirname(HIST_DB), exist_ok=True)
    con = sqlite3.connect(HIST_DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS audit_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP,
            subcmd TEXT, profile TEXT, mode TEXT,
            target TEXT, topic TEXT, rundir TEXT, outcome TEXT
        )""")
    con.commit()
    con.close()


def _log(subcmd, args, rundir, outcome):
    try:
        _ensure_table()
        con = sqlite3.connect(HIST_DB)
        con.execute(
            "INSERT INTO audit_runs(subcmd,profile,mode,target,topic,rundir,outcome)"
            " VALUES(?,?,?,?,?,?,?)",
            (
                subcmd,
                getattr(args, "profile", None),
                getattr(args, "mode", None),
                getattr(args, "target", None),
                getattr(args, "topic", None),
                rundir,
                outcome,
            ),
        )
        con.commit()
        con.close()
    except Exception as e:  # logging ne doit jamais casser le run
        print(f"[audit] warn: log SQLite échoué: {e}")


def cmd_audit(args, _conn=None):
    """Dispatch `jarvis audit <subcmd> [opts]` vers jarvis-audit.sh."""
    sub = getattr(args, "audit_cmd", None)
    if not sub:
        print(
            "jarvis audit <run|init|scan-local|scan-web|multi-agents|report|todo|cascade>"
        )
        print("  --target DIR --topic TXT --profile tech|business|souverainete|full")
        print("  --mode fast|standard|deep --client NOM --previous RAPPORT.md")
        return
    if not os.path.isfile(AUDIT_SH):
        print(f"[audit] ERREUR: script introuvable: {AUDIT_SH}")
        return

    cmd = ["bash", AUDIT_SH, sub]
    for flag in ("target", "topic", "profile", "mode", "client", "previous"):
        val = getattr(args, flag, None)
        if val:
            cmd += [f"--{flag}", str(val)]
    if getattr(args, "real_agents", False):
        cmd += ["--real-agents"]

    print(f"[audit] $ {' '.join(cmd)}")
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    print(out.rstrip())

    # extraire le rundir des logs ([init] ... -> <rundir>)
    rundir = ""
    for line in out.splitlines():
        if "->" in line and "/audit/runs/" in line:
            rundir = line.split("->")[-1].strip()
            break
    outcome = "success" if proc.returncode == 0 else f"fail({proc.returncode})"
    _log(sub, args, rundir, outcome)
    print(
        f"[audit] {outcome} en {time.time() - t0:.0f}s"
        + (f" · run={rundir}" if rundir else "")
    )
