#!/usr/bin/env python3
"""
disk_index.py — Index disques multi-machines dans jarvis_master.db
Usage: python3 disk_index.py [--all-machines | --local-only] [--quiet]
"""

import argparse
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime

DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"

SCAN_DIRS = [
    "/home/turbo",
    "/opt",
    "/etc/systemd/system",
]

EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".cache", "proc", "sys", "dev"}
MAX_SIZE_KB = 1_000_000  # 1 GB

EXT_TAGS = {
    ".py": "script", ".sh": "script", ".bash": "script",
    ".db": "db", ".sqlite": "db", ".sqlite3": "db",
    ".json": "config", ".yaml": "config", ".yml": "config", ".toml": "config", ".ini": "config", ".conf": "config",
    ".log": "log",
    ".gguf": "model", ".bin": "model", ".safetensors": "model", ".pt": "model", ".onnx": "model",
}

REMOTE_MACHINES = [
    {"name": "M2", "host": "127.0.0.1", "user": "turbo"},
    {"name": "M3", "host": "127.0.0.1", "user": "turbo"},
]

def init_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS disk_index (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      machine TEXT,
      disk TEXT,
      mount TEXT,
      path TEXT,
      name TEXT,
      ext TEXT,
      size_kb INTEGER,
      modified_at TEXT,
      type TEXT,
      tags TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_disk_name ON disk_index(name);
    CREATE INDEX IF NOT EXISTS idx_disk_ext ON disk_index(ext);
    CREATE INDEX IF NOT EXISTS idx_disk_machine ON disk_index(machine);
    """)
    conn.commit()

def get_disk_for_path(path):
    """Return /dev/xxx for the mount containing path."""
    try:
        out = subprocess.check_output(["df", "--output=source", path], text=True).strip().splitlines()
        return out[-1] if len(out) > 1 else "unknown"
    except Exception:
        return "unknown"

def get_mount_for_path(path):
    try:
        out = subprocess.check_output(["df", "--output=target", path], text=True).strip().splitlines()
        return out[-1] if len(out) > 1 else "unknown"
    except Exception:
        return "unknown"

def tag_for_ext(ext):
    return EXT_TAGS.get(ext.lower(), "")

def local_scan(machine="OL1", quiet=False):
    rows = []
    now = datetime.utcnow().isoformat()
    disk_cache = {}
    mount_cache = {}

    for base in SCAN_DIRS:
        if not os.path.exists(base):
            continue
        if not quiet:
            print(f"  Scanning {base} ...", flush=True)

        for root, dirs, files in os.walk(base, followlinks=False):
            # Prune exclusions
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            # Disk/mount lookup avec cache par top-level dir
            top = "/" + root.split("/")[1] if "/" in root else root
            if top not in disk_cache:
                disk_cache[top] = get_disk_for_path(top)
                mount_cache[top] = get_mount_for_path(top)
            disk = disk_cache[top]
            mount = mount_cache[top]

            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    st = os.stat(fpath, follow_symlinks=False)
                except OSError:
                    continue

                size_kb = st.st_size // 1024
                if size_kb > MAX_SIZE_KB:
                    continue

                ext = os.path.splitext(fname)[1]
                ftype = "symlink" if os.path.islink(fpath) else "file"
                modified = datetime.utcfromtimestamp(st.st_mtime).isoformat()
                tags = tag_for_ext(ext)

                rows.append((machine, disk, mount, fpath, fname, ext, size_kb, modified, ftype, tags))

            # Also index dirs (shallow — just the dir entry itself)
            for dname in dirs:
                dpath = os.path.join(root, dname)
                try:
                    st = os.stat(dpath, follow_symlinks=False)
                except OSError:
                    continue
                modified = datetime.utcfromtimestamp(st.st_mtime).isoformat()
                rows.append((machine, disk, mount, dpath, dname, "", 0, modified, "dir", ""))

    return rows

def remote_scan(machine_info, quiet=False):
    name = machine_info["name"]
    host = machine_info["host"]
    user = machine_info["user"]

    if not quiet:
        print(f"  SSH scan {name} ({host}) ...", flush=True)

    ssh_cmd = [
        "ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes",
        f"{user}@{host}",
        "find /home/turbo /opt /etc/systemd/system -maxdepth 8 "
        r"\( -name '.git' -o -name 'node_modules' -o -name '__pycache__' \) -prune -o "
        r"-not -size +1G -printf '%y\t%p\t%f\t%s\t%T@\n' 2>/dev/null"
    ]
    try:
        out = subprocess.check_output(ssh_cmd, text=True, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        if not quiet:
            print(f"  [WARN] {name} inaccessible: {e}", flush=True)
        return []

    rows = []
    for line in out.strip().splitlines():
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        ftype_char, fpath, fname, size_bytes, mtime_ts = parts
        ftype = {"f": "file", "d": "dir", "l": "symlink"}.get(ftype_char, "file")
        try:
            size_kb = int(size_bytes) // 1024
            modified = datetime.utcfromtimestamp(float(mtime_ts)).isoformat()
        except ValueError:
            continue
        ext = os.path.splitext(fname)[1]
        tags = tag_for_ext(ext)
        rows.append((name, "remote", "remote", fpath, fname, ext, size_kb, modified, ftype, tags))

    return rows

def insert_rows(conn, rows, machine, quiet=False):
    """Delete existing entries for machine then bulk insert."""
    conn.execute("DELETE FROM disk_index WHERE machine=?", (machine,))
    conn.executemany(
        "INSERT INTO disk_index (machine,disk,mount,path,name,ext,size_kb,modified_at,type,tags) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        rows
    )
    conn.commit()
    if not quiet:
        print(f"  -> {len(rows)} entrées insérées pour {machine}", flush=True)

def main():
    parser = argparse.ArgumentParser(description="JARVIS Disk Index")
    parser.add_argument("--all-machines", action="store_true", help="Scan local + SSH remotes")
    parser.add_argument("--local-only", action="store_true", help="Scan local uniquement (OL1)")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if not args.all_machines and not args.local_only:
        args.local_only = True  # default

    t0 = time.time()
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    init_db(conn)

    total = 0

    # Local scan
    if not args.quiet:
        print("=== Scan local (OL1) ===")
    rows = local_scan(machine="OL1", quiet=args.quiet)
    insert_rows(conn, rows, "OL1", quiet=args.quiet)
    total += len(rows)

    # Remote scans
    if args.all_machines:
        for m in REMOTE_MACHINES:
            if not args.quiet:
                print(f"=== Scan {m['name']} ===")
            rows = remote_scan(m, quiet=args.quiet)
            if rows:
                insert_rows(conn, rows, m["name"], quiet=args.quiet)
                total += len(rows)

    elapsed = time.time() - t0
    db_size = os.path.getsize(DB_PATH) / 1024

    if not args.quiet:
        print(f"\nTotal: {total} fichiers | DB: {db_size:.1f} KB | Temps: {elapsed:.1f}s")

    conn.close()

if __name__ == "__main__":
    main()
