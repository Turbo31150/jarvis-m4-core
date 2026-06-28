"""Pousseline — Import élèves (CSV ONDE/tableur) + champs personnalisés.

Module Flask autonome. SQL pur, aucune IA. Auth gérée globalement.
Table `eleves` existante (NE PAS recréer). Crée seulement `eleve_champs`.
"""

import csv
import io
import sqlite3
import unicodedata
from pathlib import Path

from flask import jsonify, request

ECOLE_DB = str(Path(__file__).resolve().parent / "ecole.db")


def _conn():
    c = sqlite3.connect(ECOLE_DB)
    c.row_factory = sqlite3.Row
    return c


def _init():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS eleve_champs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, eleve_id INTEGER,
            cle TEXT NOT NULL, valeur TEXT DEFAULT '', couleur TEXT DEFAULT '')""")
        c.commit()


def _norm(s):
    """Minuscule, sans accents, trim — pour reconnaitre les en-tetes de colonnes."""
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s


# Mapping en-tete normalise -> champ interne
_COLMAP = {
    "nom": "nom",
    "prenom": "prenom",
    "niveau": "niveau",
    "groupe": "groupe",
}


def _detect_dialect(text):
    """Detecte le separateur ; ou , via Sniffer, fallback ;."""
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
        return dialect
    except Exception:

        class _Fallback(csv.Dialect):
            delimiter = ";"
            quotechar = '"'
            doublequote = True
            skipinitialspace = True
            lineterminator = "\r\n"
            quoting = csv.QUOTE_MINIMAL

        return _Fallback()


def register(app):
    _init()

    @app.route("/api/eleves/import", methods=["POST"])
    def eleves_import():
        try:
            data = request.get_json(silent=True) or {}
            csv_text = (data.get("csv") or "").strip()
            remplacer = bool(data.get("remplacer", False))
            if not csv_text:
                return jsonify({"error": "CSV vide"}), 400

            dialect = _detect_dialect(csv_text)
            reader = csv.reader(io.StringIO(csv_text), dialect)
            rows = [r for r in reader if any((cell or "").strip() for cell in r)]
            if not rows:
                return jsonify({"ok": True, "importes": 0, "ignores": 0})

            # En-tete : trouve les indices des colonnes reconnues
            header = rows[0]
            col_idx = {}  # champ interne -> index
            for i, cell in enumerate(header):
                key = _COLMAP.get(_norm(cell))
                if key and key not in col_idx:
                    col_idx[key] = i

            data_rows = rows[1:] if col_idx else rows
            # Si aucun en-tete reconnu, on suppose ordre nom;prenom;niveau;groupe
            if not col_idx:
                col_idx = {"nom": 0, "prenom": 1, "niveau": 2, "groupe": 3}

            importes = 0
            ignores = 0
            with _conn() as c:
                if remplacer:
                    c.execute("DELETE FROM eleves")
                for r in data_rows:

                    def val(field):
                        idx = col_idx.get(field)
                        if idx is None or idx >= len(r):
                            return ""
                        return (r[idx] or "").strip()[:80]

                    nom = val("nom")
                    prenom = val("prenom")
                    if not nom and not prenom:
                        ignores += 1
                        continue
                    niveau = val("niveau")
                    groupe = val("groupe")
                    c.execute(
                        "INSERT INTO eleves (nom, prenom, niveau, groupe, created_at) "
                        "VALUES (?, ?, ?, ?, datetime('now'))",
                        (nom, prenom, niveau, groupe),
                    )
                    importes += 1
                c.commit()

            return jsonify({"ok": True, "importes": importes, "ignores": ignores})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/eleves/<int:eid>/champs", methods=["GET"])
    def eleve_champs_list(eid):
        try:
            with _conn() as c:
                rows = c.execute(
                    "SELECT id, cle, valeur, couleur FROM eleve_champs "
                    "WHERE eleve_id=? ORDER BY id",
                    (eid,),
                ).fetchall()
            return jsonify([dict(r) for r in rows])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/eleves/<int:eid>/champs", methods=["POST"])
    def eleve_champs_add(eid):
        try:
            data = request.get_json(silent=True) or {}
            cle = (data.get("cle") or "").strip()[:80]
            valeur = (data.get("valeur") or "").strip()[:80]
            couleur = (data.get("couleur") or "").strip()[:80]
            if not cle:
                return jsonify({"error": "cle vide"}), 400
            with _conn() as c:
                cur = c.execute(
                    "INSERT INTO eleve_champs (eleve_id, cle, valeur, couleur) "
                    "VALUES (?, ?, ?, ?)",
                    (eid, cle, valeur, couleur),
                )
                c.commit()
                new_id = cur.lastrowid
            return jsonify({"ok": True, "id": new_id})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/eleves/champs/<int:cid>", methods=["DELETE"])
    def eleve_champs_del(cid):
        try:
            with _conn() as c:
                c.execute("DELETE FROM eleve_champs WHERE id=?", (cid,))
                c.commit()
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    print("[Pousseline] Import élèves + champs perso chargé (/api/eleves/import)")
