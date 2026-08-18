#!/usr/bin/env python3
"""research-library.py — bibliothèque des séries de deep-research dans jarvis_master.db.

Ingère chaque <BASE>/research-*/findings.md dans la table `research_library`
(idempotent par slug). Sert d'index requêtable + alimente backup SQL/GitHub.

Usage :
  research-library.py [ingest] [BASE]   # défaut BASE=~/Downloads
  research-library.py list              # liste la bibliothèque
stdlib uniquement.
"""

import os
import sys
import re
import glob
import sqlite3
import datetime

DB = os.environ.get("JARVIS_DB", "/home/pamerys/jarvis/jarvis_master.db")
BASE_DEFAULT = os.path.expanduser("~/Downloads")

DDL = """CREATE TABLE IF NOT EXISTS research_library (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT UNIQUE,
  title TEXT,
  research_date TEXT,
  n_sources INTEGER,
  html_path TEXT,
  pdf_path TEXT,
  findings_path TEXT,
  summary TEXT,
  created_at TEXT
);"""


def _conn():
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    c = sqlite3.connect(DB, timeout=120)
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA busy_timeout=120000;")
    return c


def _parse(fm):
    md = open(fm, encoding="utf-8").read()
    title = next(
        (
            re.sub(r"^Research Findings:\s*", "", l[2:]).strip()
            for l in md.split("\n")
            if l.startswith("# ")
        ),
        os.path.basename(os.path.dirname(fm)),
    )
    date = next(
        (
            re.sub(r"\*+", "", l.split(":", 1)[1]).strip()
            for l in md.split("\n")
            if l.lower().lstrip("*").startswith("date")
        ),
        "",
    )
    # résumé = texte après "## Conclusion" (1er paragraphe), sinon 1er finding
    summ = ""
    m = re.search(r"##\s*Conclusion.*?\n(.+?)(?:\n##|\Z)", md, re.S)
    if m:
        summ = " ".join(m.group(1).split())[:600]
    return title, date, summ


def ingest(base):
    found = sorted(glob.glob(os.path.join(base, "research-*", "findings.md")))
    if not found:
        print(f"[lib] aucun findings.md sous {base}/research-*")
        return 0
    c = _conn()
    c.execute(DDL)
    now = datetime.datetime.now().isoformat(timespec="seconds")
    n = 0
    for fm in found:
        d = os.path.dirname(fm)
        slug = os.path.basename(d)
        title, date, summ = _parse(fm)
        nsrc = len(glob.glob(os.path.join(d, "sources", "*.md")))
        html = os.path.join(d, "report.html")
        pdf = os.path.join(d, "report.pdf")
        c.execute(
            "INSERT INTO research_library(slug,title,research_date,n_sources,html_path,pdf_path,findings_path,summary,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(slug) DO UPDATE SET "
            "title=excluded.title,research_date=excluded.research_date,n_sources=excluded.n_sources,"
            "html_path=excluded.html_path,pdf_path=excluded.pdf_path,findings_path=excluded.findings_path,summary=excluded.summary",
            (
                slug,
                title,
                date,
                nsrc,
                html if os.path.exists(html) else "",
                pdf if os.path.exists(pdf) else "",
                fm,
                summ,
                now,
            ),
        )
        n += 1
    c.commit()
    c.close()
    print(f"[lib] {n} séries ingérées/à jour dans {DB} (table research_library)")
    return 0


def lst():
    c = _conn()
    c.execute(DDL)
    rows = c.execute(
        "SELECT id,slug,n_sources,research_date,title FROM research_library ORDER BY id"
    ).fetchall()
    c.close()
    if not rows:
        print("[lib] bibliothèque vide")
        return 0
    print(f"=== Bibliothèque de recherche ({len(rows)} séries) ===")
    for r in rows:
        print(f"  #{r[0]} [{r[2]} src] {r[3] or '?':12} {r[4][:60]}")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "list":
        sys.exit(lst())
    base = (
        args[1]
        if len(args) > 1
        else (args[0] if args and args[0] != "ingest" else BASE_DEFAULT)
    )
    sys.exit(ingest(base))
