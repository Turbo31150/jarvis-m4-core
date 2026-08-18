#!/usr/bin/env python3
"""jarvis_auto_heal.py — Daemon de surveillance et d'auto-réparation du système JARVIS."""

import time, subprocess, urllib.request, sqlite3, os

DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"
PORTS = [8899, 9742, 18800, 4173]

def check_ports():
    for p in PORTS:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{p}/", timeout=1):
                pass
        except Exception:
            pass

def clean_locks():
    tmp_files = ["/tmp/planning_widget.log", "/tmp/desktop_widget.log"]
    for f in tmp_files:
        if os.path.exists(f) and os.path.getsize(f) > 5 * 1024 * 1024:
            with open(f, "w") as out:
                out.write("")

def main():
    check_ports()
    clean_locks()

if __name__ == "__main__":
    main()
