import sqlite3
from pathlib import Path
from flask import jsonify, request

ECOLE_DB = str(Path(__file__).resolve().parent / "ecole.db")


def _conn():
    c = sqlite3.connect(ECOLE_DB)
    c.row_factory = sqlite3.Row
    return c


def _init():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS groupes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                couleur TEXT DEFAULT '',
                critere TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS eleve_groupe (
                groupe_id INTEGER,
                eleve_id INTEGER,
                PRIMARY KEY (groupe_id, eleve_id)
            )"""
        )
        c.commit()


def register(app):
    _init()

    @app.route("/api/groupes", methods=["GET"])
    def groupes_list():
        try:
            with _conn() as c:
                groupes = c.execute(
                    """SELECT g.id, g.nom, g.couleur, g.critere, g.created_at,
                              (SELECT COUNT(*) FROM eleve_groupe eg
                               WHERE eg.groupe_id = g.id) AS nb_membres
                       FROM groupes g
                       ORDER BY g.id DESC"""
                ).fetchall()
                out = []
                for g in groupes:
                    membres = c.execute(
                        """SELECT e.id AS eleve_id, e.prenom, e.nom
                           FROM eleve_groupe eg
                           JOIN eleves e ON e.id = eg.eleve_id
                           WHERE eg.groupe_id = ?
                           ORDER BY e.nom, e.prenom""",
                        (g["id"],),
                    ).fetchall()
                    out.append(
                        {
                            "id": g["id"],
                            "nom": g["nom"],
                            "couleur": g["couleur"],
                            "critere": g["critere"],
                            "created_at": g["created_at"],
                            "nb_membres": g["nb_membres"],
                            "membres": [
                                {
                                    "eleve_id": m["eleve_id"],
                                    "prenom": m["prenom"],
                                    "nom": m["nom"],
                                }
                                for m in membres
                            ],
                        }
                    )
                return jsonify(out)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/groupes", methods=["POST"])
    def groupes_create():
        try:
            data = request.get_json(silent=True) or {}
            nom = (data.get("nom") or "").strip()[:80]
            couleur = (data.get("couleur") or "").strip()[:80]
            critere = (data.get("critere") or "").strip()[:80]
            if not nom:
                return jsonify({"error": "nom requis"}), 400
            with _conn() as c:
                cur = c.execute(
                    "INSERT INTO groupes (nom, couleur, critere) VALUES (?, ?, ?)",
                    (nom, couleur, critere),
                )
                c.commit()
                return jsonify({"ok": True, "id": cur.lastrowid})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/groupes/<int:gid>", methods=["DELETE"])
    def groupes_delete(gid):
        try:
            with _conn() as c:
                c.execute("DELETE FROM eleve_groupe WHERE groupe_id = ?", (gid,))
                c.execute("DELETE FROM groupes WHERE id = ?", (gid,))
                c.commit()
                return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/groupes/<int:gid>/membres", methods=["POST"])
    def groupes_add_membre(gid):
        try:
            data = request.get_json(silent=True) or {}
            eleve_id = data.get("eleve_id")
            if eleve_id is None:
                return jsonify({"error": "eleve_id requis"}), 400
            with _conn() as c:
                c.execute(
                    "INSERT OR IGNORE INTO eleve_groupe (groupe_id, eleve_id) VALUES (?, ?)",
                    (gid, eleve_id),
                )
                c.commit()
                return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/groupes/<int:gid>/membres/<int:eid>", methods=["DELETE"])
    def groupes_del_membre(gid, eid):
        try:
            with _conn() as c:
                c.execute(
                    "DELETE FROM eleve_groupe WHERE groupe_id = ? AND eleve_id = ?",
                    (gid, eid),
                )
                c.commit()
                return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    print("[Pousseline] Groupes de besoin chargé (/api/groupes)")
