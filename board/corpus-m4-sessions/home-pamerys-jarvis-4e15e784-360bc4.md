[user] Review this change for security vulnerabilities.

Changed files (you may Read these and any other file in the repo):
  - code-library/build.py
  - code-library/lib.py
  - code-library/libcode

Unified diff (only + lines are new):

=== DIFF: code-library/build.py ===
@@ -0,0 +1,100 @@
+#!/usr/bin/env python3
+"""Bibliothèque de code SQL — patterns/recettes réutilisables du système Pousseline.
+Objectif : SQL AVANT compute. Chercher un pattern validé ici avant de re-générer.
+Rejouable, idempotent (UPSERT sur nom)."""
+import sqlite3, os
+DB = os.path.join(os.path.dirname(__file__), "code_library.db")
+
+SCHEMA = """
+CREATE TABLE IF NOT EXISTS patterns(
+  id INTEGER PRIMARY KEY AUTOINCREMENT,
+  nom TEXT UNIQUE NOT NULL,
+  categorie TEXT, langage TEXT,
+  triggers TEXT,            -- mots-clés déclencheurs (recherche)
+  description TEXT,
+  quand_utiliser TEXT,
+  code TEXT,                -- squelette réutilisable
+  source TEXT,              -- fichier/skill d'origine
+  created_at TEXT DEFAULT (datetime('now','localtime'))
+);
+CREATE VIRTUAL TABLE IF NOT EXISTS patterns_fts USING fts5(nom, triggers, description, content='patterns', content_rowid='id');
+"""
+
+PATTERNS = [
+ ("cablage-onglet-front-back","frontend","python+js",
+  "onglet, orphelin, câbler, section, navigate, loadX, front, backend",
+  "Brancher un module backend Flask orphelin à un nouvel onglet du front.",
+  "Quand un module a des routes /api prêtes mais aucune UI (onglet mort/absent).",
+  "1) <div i

[assistant] Looking at this change, I need to review three small files that together implement a local SQLite-backed pattern library.

[assistant] Security analysis:

**Phase 1 — Entry points and sinks:**
- Entry point: `lib.py` CLI args (search query, `--show <nom>`), `libcode` bash wrapper passing `"$@"`.
- `build.py` has no CLI-user input; all data hardcoded in `PATTERNS`.
- Sinks: SQLite queries only (all parameterized), stdout prints.

**Phase 2 — Data flow:**
- `search(q)`: `q` from `sys.argv` goes into `patterns_fts MATCH ?` (parameterized) with fallback to `triggers LIKE ?` (parameterized). No string concatenation into SQL. FTS5 MATCH errors on malformed queries are caught. Safe.
- `show(nom)`: `nom` from CLI goes into `WHERE nom=?` (parameterized). Safe.
- Bash wrapper: `"$@"` preserves arg boundaries; `$(dirname "$0")` is quoted. Safe.
- DB path derived from `__file__`, not user input. No path traversal.

**Phase 2b — Parser differentials:** N/A.

**Phase 2c — High-miss patterns:**
- No logs/observability sinks with sensitive data.
- No IaC, no CI/CD triggers.
- No allowlists, no permission grants.
- No exec/eval/subprocess — `libcode` uses `exec python3` with quoted args.
- The stored `code` field contains snippets (including shell examples like `grep -iE '\.db$|...'`), but they are only printed via `print()` — never executed.
- No sensitive-registry fanout (self-contained tool).

**Phase 3 — Assessment:**
This is a small, self-contained local CLI that reads/writes a local SQLite DB with hardcoded content. Every SQL sink uses parameter binding. The bash wrapper properly quotes both the script path and forward