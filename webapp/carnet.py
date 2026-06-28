"""Carnet de notes - module Flask d'analytique des notes (Pousseline).

Moyennes par eleve/matiere et donnees pour diagramme radar.
SQL pur, aucune IA. Auth geree globalement (pas de decorateur).
Les notes sont ramenees sur /20 : note_sur20 = note / sur * 20.
Les lignes ou sur = 0 (ou NULL) sont ignorees via NULLIF(sur, 0).
"""

import sqlite3
from pathlib import Path

from flask import jsonify, request

ECOLE_DB = str(Path(__file__).resolve().parent / "ecole.db")


def _conn():
    c = sqlite3.connect(ECOLE_DB)
    c.row_factory = sqlite3.Row
    return c


def _r1(x):
    """Arrondi a 1 decimale, en preservant None."""
    return None if x is None else round(x, 1)


def register(app):

    @app.route("/api/carnet/moyennes", methods=["GET"])
    def carnet_moyennes():
        try:
            periode = request.args.get("periode")
            params = []
            where = "WHERE NULLIF(ev.sur, 0) IS NOT NULL AND ev.note IS NOT NULL"
            if periode:
                where += " AND ev.periode = ?"
                params.append(periode)

            con = _conn()
            try:
                # Moyenne generale et nb_notes par eleve
                rows = con.execute(
                    f"""
                    SELECT e.id AS eleve_id, e.prenom, e.nom,
                           AVG(ev.note / NULLIF(ev.sur, 0) * 20.0) AS moyenne_generale,
                           COUNT(*) AS nb_notes
                    FROM eleves e
                    JOIN evaluations ev ON ev.eleve_id = e.id
                    {where}
                    GROUP BY e.id, e.prenom, e.nom
                    ORDER BY e.nom, e.prenom
                    """,
                    params,
                ).fetchall()

                # Moyennes par matiere par eleve
                mrows = con.execute(
                    f"""
                    SELECT ev.eleve_id, ev.matiere,
                           AVG(ev.note / NULLIF(ev.sur, 0) * 20.0) AS moy
                    FROM evaluations ev
                    {where}
                    GROUP BY ev.eleve_id, ev.matiere
                    """,
                    params,
                ).fetchall()
            finally:
                con.close()

            par_mat = {}
            for m in mrows:
                par_mat.setdefault(m["eleve_id"], {})[m["matiere"]] = _r1(m["moy"])

            result = []
            for row in rows:
                eid = row["eleve_id"]
                result.append(
                    {
                        "eleve_id": eid,
                        "prenom": row["prenom"],
                        "nom": row["nom"],
                        "moyenne_generale": _r1(row["moyenne_generale"]),
                        "nb_notes": row["nb_notes"],
                        "par_matiere": par_mat.get(eid, {}),
                    }
                )
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/carnet/eleve/<int:eid>/radar", methods=["GET"])
    def carnet_radar(eid):
        try:
            periode = request.args.get("periode")
            base = "FROM evaluations ev WHERE NULLIF(ev.sur, 0) IS NOT NULL AND ev.note IS NOT NULL"
            p_params = []
            if periode:
                base += " AND ev.periode = ?"
                p_params.append(periode)

            con = _conn()
            try:
                eleve = con.execute(
                    "SELECT prenom, nom FROM eleves WHERE id = ?", (eid,)
                ).fetchone()

                # Toutes les matieres presentes en base (selon filtre periode)
                mats = con.execute(
                    f"SELECT DISTINCT ev.matiere {base} ORDER BY ev.matiere", p_params
                ).fetchall()

                # Moyenne classe par matiere
                classe = con.execute(
                    f"""
                    SELECT ev.matiere,
                           AVG(ev.note / NULLIF(ev.sur, 0) * 20.0) AS moy
                    {base}
                    GROUP BY ev.matiere
                    """,
                    p_params,
                ).fetchall()

                # Moyenne de l'eleve par matiere
                el_params = list(p_params) + [eid]
                eleve_moy = con.execute(
                    f"""
                    SELECT ev.matiere,
                           AVG(ev.note / NULLIF(ev.sur, 0) * 20.0) AS moy
                    {base} AND ev.eleve_id = ?
                    GROUP BY ev.matiere
                    """,
                    el_params,
                ).fetchall()
            finally:
                con.close()

            classe_map = {c["matiere"]: _r1(c["moy"]) for c in classe}
            eleve_map = {e["matiere"]: _r1(e["moy"]) for e in eleve_moy}

            axes = []
            for m in mats:
                mat = m["matiere"]
                axes.append(
                    {
                        "matiere": mat,
                        "eleve": eleve_map.get(mat),
                        "classe": classe_map.get(mat),
                    }
                )

            return jsonify(
                {
                    "eleve": {
                        "prenom": eleve["prenom"] if eleve else None,
                        "nom": eleve["nom"] if eleve else None,
                    },
                    "axes": axes,
                }
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/carnet/eleve/<int:eid>", methods=["GET"])
    def carnet_eleve(eid):
        try:
            con = _conn()
            try:
                rows = con.execute(
                    """
                    SELECT matiere, competence, note, sur, periode
                    FROM evaluations
                    WHERE eleve_id = ?
                    ORDER BY periode, matiere, competence
                    """,
                    (eid,),
                ).fetchall()
            finally:
                con.close()

            result = []
            for r in rows:
                sur = r["sur"]
                note = r["note"]
                sur20 = None
                if sur and note is not None:
                    sur20 = _r1(note / sur * 20.0)
                result.append(
                    {
                        "matiere": r["matiere"],
                        "competence": r["competence"],
                        "note": note,
                        "sur": sur,
                        "sur20": sur20,
                        "periode": r["periode"],
                    }
                )
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    print("[Pousseline] Carnet de notes charge (/api/carnet)")
