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
        c.execute("""CREATE TABLE IF NOT EXISTS ateliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            domaine TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        c.commit()


def register(app):
    _init()

    @app.route("/api/ateliers", methods=["GET"])
    def ateliers_list():
        try:
            with _conn() as c:
                rows = c.execute(
                    "SELECT id, nom, domaine, created_at FROM ateliers ORDER BY id"
                ).fetchall()
            return jsonify([dict(r) for r in rows])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ateliers", methods=["POST"])
    def ateliers_create():
        try:
            data = request.get_json(silent=True) or {}
            nom = (data.get("nom") or "").strip()[:80]
            domaine = (data.get("domaine") or "").strip()[:80]
            if not nom:
                return jsonify({"error": "nom vide"}), 400
            with _conn() as c:
                cur = c.execute(
                    "INSERT INTO ateliers (nom, domaine) VALUES (?, ?)",
                    (nom, domaine),
                )
                c.commit()
                aid = cur.lastrowid
            return jsonify({"ok": True, "id": aid})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ateliers/<int:aid>", methods=["DELETE"])
    def ateliers_delete(aid):
        try:
            with _conn() as c:
                c.execute("DELETE FROM ateliers WHERE id = ?", (aid,))
                c.commit()
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ateliers/rotation", methods=["GET"])
    def ateliers_rotation():
        try:
            # Groupes
            raw_groupes = (request.args.get("groupes") or "A,B,C,D").strip()
            groupes = [g.strip()[:80] for g in raw_groupes.split(",") if g.strip()]
            if not groupes:
                groupes = ["A", "B", "C", "D"]

            # Ateliers en base
            with _conn() as c:
                rows = c.execute("SELECT nom FROM ateliers ORDER BY id").fetchall()
            ateliers = [r["nom"] for r in rows]

            if not ateliers:
                return jsonify({"error": "aucun atelier en base"}), 400

            n_g = len(groupes)

            # On aligne le nombre d'ateliers sur le nombre de groupes :
            # - si moins d'ateliers que de groupes -> complete par des ateliers "Libre N"
            # - si plus d'ateliers que de groupes -> limite aux n_g premiers
            if len(ateliers) < n_g:
                manquants = n_g - len(ateliers)
                for i in range(manquants):
                    ateliers.append("Libre " + str(i + 1))
            elif len(ateliers) > n_g:
                ateliers = ateliers[:n_g]

            n = len(ateliers)  # = n_g, carre latin n x n

            # Nombre de jours
            jours_param = request.args.get("jours")
            if jours_param is None:
                jours = n
            else:
                try:
                    jours = int(jours_param)
                except (TypeError, ValueError):
                    jours = n
            if jours < 1:
                jours = 1
            # Au-dela de n jours la rotation circulaire se repete : on borne a n
            if jours > n:
                jours = n

            # Rotation circulaire (carre latin) : jour j, groupe i -> atelier (i+j) % n
            rotation = []
            for j in range(jours):
                affectations = []
                for i in range(n):
                    affectations.append(
                        {
                            "groupe": groupes[i],
                            "atelier": ateliers[(i + j) % n],
                        }
                    )
                rotation.append({"jour": j + 1, "affectations": affectations})

            return jsonify(
                {
                    "ateliers": ateliers,
                    "groupes": groupes,
                    "rotation": rotation,
                }
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    print("[Pousseline] Ateliers maternelle chargé (/api/ateliers)")
