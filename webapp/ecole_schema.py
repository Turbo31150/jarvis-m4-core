#!/usr/bin/env python3
"""Schéma ecole.db — Espace Prof. init_ecole_db() appelable par server.py."""

import sqlite3
from pathlib import Path

ECOLE_DB = Path(__file__).resolve().parent / "ecole.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS eleves (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nom TEXT, prenom TEXT,
  niveau TEXT,                 -- TPS/PS/MS/GS/CP/CE1/CE2/CM1/CM2
  groupe TEXT,                 -- groupe de besoin/travail
  points_forts TEXT,
  besoins TEXT,                -- AESH, PPRE, dys… (différenciation)
  notes_json TEXT DEFAULT '{}',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS exercices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titre TEXT, matiere TEXT, niveau TEXT, notion TEXT,
  contenu_md TEXT,             -- énoncé standard
  variantes_json TEXT,         -- {soutien, standard, approfondissement}
  eleve_id INTEGER,            -- si adapté à un élève précis
  backend TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS corrections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exercice_id INTEGER, eleve_id INTEGER,
  enonce TEXT, reponse TEXT, feedback TEXT, score REAL,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sequences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titre TEXT, sujet TEXT, niveau TEXT, duree_min INTEGER,
  contenu_md TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cahier_journal (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT UNIQUE, contenu_md TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS presence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  eleve_id INTEGER, date TEXT, present INTEGER DEFAULT 1,
  UNIQUE(eleve_id, date)
);

CREATE TABLE IF NOT EXISTS ai_cache (
  key TEXT PRIMARY KEY, question TEXT, answer TEXT,
  backend TEXT, hits INTEGER DEFAULT 0, ts TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bulletins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  eleve_id INTEGER, periode TEXT,
  type TEXT,                    -- appreciation | lsu | synthese
  contenu_md TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS programmations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  matiere TEXT, niveau TEXT, portee TEXT,   -- portee: annuelle | periode
  periode TEXT, contenu_md TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS kv (
  k TEXT PRIMARY KEY, v TEXT, ts TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS evaluations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  eleve_id INTEGER, matiere TEXT, competence TEXT,
  note REAL, sur REAL DEFAULT 10, periode TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS comportement (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  eleve_id INTEGER, delta INTEGER DEFAULT 1, motif TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ceintures (
  eleve_id INTEGER, domaine TEXT, couleur TEXT DEFAULT 'blanche',
  ts TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (eleve_id, domaine)
);
"""


def init_ecole_db():
    ECOLE_DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(ECOLE_DB)) as c:
        c.executescript(SCHEMA)
    return ECOLE_DB


if __name__ == "__main__":
    db = init_ecole_db()
    with sqlite3.connect(str(db)) as c:
        tables = [
            r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        ]
    print(f"[ecole.db] créée: {db}")
    print("  tables:", tables)
