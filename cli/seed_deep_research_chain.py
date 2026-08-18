#!/usr/bin/env python3
"""
seed_deep_research_chain.py — enregistre les outils & la chaîne domino "deep-research"
dans la table tool_map de jarvis_master.db (même schéma/format que seed_tools.py).

Idempotent : ON CONFLICT(name) DO UPDATE. N'altère aucun autre outil ni commande.

Chaîne domino (triggers JSON = liste de `name` que cascade.py sait résoudre par BFS) :

    skill:deep-research               (recherche web → findings.md)
        └─► cli:deep-research-report  (findings.md → report.html + index)
              └─► cli:research-library (ingère séries → table research_library)
                    └─► skill:run-jarvis-sql-backup (persistance SQLite+Postgres → GitHub)
"""

import json
import sqlite3

DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"


def upsert(
    conn, name, category, loader, keywords, triggers="[]", memory_kb=0, priority=5
):
    """Format identique à cli/seed_tools.py::upsert."""
    conn.execute(
        """INSERT INTO tool_map (name, category, loader, keywords, triggers, memory_kb, priority)
           VALUES (?,?,?,?,?,?,?)
           ON CONFLICT(name) DO UPDATE SET
             category=excluded.category,
             loader=excluded.loader,
             keywords=excluded.keywords,
             triggers=excluded.triggers,
             memory_kb=excluded.memory_kb,
             priority=excluded.priority""",
        (name, category, loader, keywords, triggers, memory_kb, priority),
    )


# name, category, loader, keywords, triggers, memory_kb, priority
TOOLS = [
    # Entrée : recherche web (skill jarvis-os:deep-research) → déclenche la génération du rapport
    (
        "skill:deep-research",
        "skill",
        "claude-code-skill:deep-research",
        json.dumps(
            [
                "deep",
                "research",
                "recherche",
                "web",
                "findings",
                "sources",
                "investigate",
            ]
        ),
        json.dumps(["cli:deep-research-report"]),
        64,
        7,
    ),
    # Étape 2 : findings.md → report.html + index
    (
        "cli:deep-research-report",
        "cli",
        "python3 /home/turbo/jarvis/scripts/deep-research-report.py",
        json.dumps(
            [
                "deep",
                "research",
                "report",
                "html",
                "pdf",
                "findings",
                "markdown",
                "recherche",
            ]
        ),
        json.dumps(["cli:research-library"]),
        16,
        6,
    ),
    # Étape 3 : ingère les séries deep-research → table research_library
    (
        "cli:research-library",
        "cli",
        "python3 /home/turbo/jarvis/scripts/research-library.py",
        json.dumps(
            [
                "research",
                "library",
                "ingest",
                "archive",
                "sql",
                "recherche",
                "bibliotheque",
            ]
        ),
        json.dumps(["skill:run-jarvis-sql-backup"]),
        16,
        6,
    ),
    # Étape 4 (terminal) : persistance bases SQLite + Postgres → GitHub LFS + mirror M5
    (
        "skill:run-jarvis-sql-backup",
        "skill",
        "claude-code-skill:run-jarvis-sql-backup",
        json.dumps(
            [
                "sql",
                "backup",
                "sauvegarde",
                "snapshot",
                "dump",
                "postgres",
                "sqlite",
                "mirror",
                "github",
            ]
        ),
        json.dumps([]),
        64,
        7,
    ),
]


def main():
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(DB_PATH, timeout=120)
    try:
        conn.execute("PRAGMA busy_timeout=120000")
        for t in TOOLS:
            upsert(conn, *t)
        conn.commit()
    finally:
        conn.close()
    print(
        f"[seed-deep-research] {len(TOOLS)} outils/chaîne domino enregistrés dans tool_map"
    )
    for t in TOOLS:
        trg = json.loads(t[4])
        arrow = f"  → {trg}" if trg else ""
        print(f"  [{t[1]:5}] {t[0]}{arrow}")


if __name__ == "__main__":
    main()
