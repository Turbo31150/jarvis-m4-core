import sqlite3
from datetime import date as _date, timedelta as _timedelta
from pathlib import Path
from flask import jsonify, request

ECOLE_DB = str(Path(__file__).resolve().parent / "ecole.db")


def _conn():
    c = sqlite3.connect(ECOLE_DB)
    c.row_factory = sqlite3.Row
    return c


def _valid_date(s):
    """Valide une date 'YYYY-MM-DD'. Retourne la chaine normalisee ou None."""
    if not isinstance(s, str):
        return None
    s = s.strip()
    try:
        return _date.fromisoformat(s).isoformat()
    except (ValueError, TypeError):
        return None


def register(app):
    @app.route("/api/appel/<jour>", methods=["GET"])
    def appel_du_jour(jour):
        try:
            j = _valid_date(jour)
            if not j:
                return jsonify({"error": "date invalide (attendu YYYY-MM-DD)"}), 400
            con = _conn()
            try:
                rows = con.execute(
                    """
                    SELECT e.id AS eleve_id,
                           e.prenom AS prenom,
                           e.nom AS nom,
                           COALESCE(p.present, 1) AS present
                    FROM eleves e
                    LEFT JOIN presence p
                           ON p.eleve_id = e.id AND p.date = ?
                    ORDER BY e.nom COLLATE NOCASE, e.prenom COLLATE NOCASE
                    """,
                    (j,),
                ).fetchall()
            finally:
                con.close()
            return jsonify(
                [
                    {
                        "eleve_id": r["eleve_id"],
                        "prenom": r["prenom"],
                        "nom": r["nom"],
                        "present": int(r["present"]),
                    }
                    for r in rows
                ]
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/appel/marquer", methods=["POST"])
    def appel_marquer():
        try:
            data = request.get_json(silent=True) or {}

            # eleve_id entier
            try:
                eleve_id = int(data.get("eleve_id"))
            except (TypeError, ValueError):
                return jsonify({"error": "eleve_id entier requis"}), 400

            # date valide
            d = _valid_date(data.get("date"))
            if not d:
                return jsonify({"error": "date invalide (attendu YYYY-MM-DD)"}), 400

            # present dans {0,1}
            try:
                present = int(data.get("present"))
            except (TypeError, ValueError):
                return jsonify({"error": "present doit valoir 0 ou 1"}), 400
            if present not in (0, 1):
                return jsonify({"error": "present doit valoir 0 ou 1"}), 400

            con = _conn()
            try:
                con.execute(
                    """
                    INSERT INTO presence(eleve_id, date, present)
                    VALUES(?, ?, ?)
                    ON CONFLICT(eleve_id, date)
                    DO UPDATE SET present = excluded.present
                    """,
                    (eleve_id, d, present),
                )
                con.commit()
            finally:
                con.close()
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/appel/stats", methods=["GET"])
    def appel_stats():
        try:
            debut = _valid_date(request.args.get("debut"))
            fin = _valid_date(request.args.get("fin"))

            # Par defaut : 30 derniers jours
            if not debut or not fin:
                today = _date.today()
                fin = today.isoformat()
                debut = (today - _timedelta(days=29)).isoformat()

            # Borne : s'assurer que debut <= fin
            if debut > fin:
                debut, fin = fin, debut

            con = _conn()
            try:
                rows = con.execute(
                    """
                    SELECT e.id AS eleve_id,
                           e.prenom AS prenom,
                           e.nom AS nom,
                           COUNT(p.id) AS jours_comptes,
                           SUM(CASE WHEN p.present = 0 THEN 1 ELSE 0 END) AS absences
                    FROM eleves e
                    LEFT JOIN presence p
                           ON p.eleve_id = e.id
                          AND p.date >= ?
                          AND p.date <= ?
                    GROUP BY e.id, e.prenom, e.nom
                    ORDER BY e.nom COLLATE NOCASE, e.prenom COLLATE NOCASE
                    """,
                    (debut, fin),
                ).fetchall()
            finally:
                con.close()

            result = []
            for r in rows:
                jours = int(r["jours_comptes"] or 0)
                absences = int(r["absences"] or 0)
                if jours > 0:
                    taux = round((jours - absences) / jours * 100, 1)
                else:
                    taux = 100.0
                result.append(
                    {
                        "eleve_id": r["eleve_id"],
                        "prenom": r["prenom"],
                        "nom": r["nom"],
                        "absences": absences,
                        "jours_comptes": jours,
                        "taux_present": taux,
                    }
                )
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    print("[Pousseline] Registre d'appel charge (/api/appel)")
