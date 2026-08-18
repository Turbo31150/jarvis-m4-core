"""
Module Pousseline — Sorties scolaires
Expose def register(app) pour branchement dans server.py.
"""

import json
import sqlite3

from flask import jsonify, request

try:
    import ai_local

    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

DB = "/home/pamerys/jarvis/webapp/ecole.db"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS sorties (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    titre                 TEXT    NOT NULL,
    date                  TEXT    NOT NULL,
    lieu                  TEXT    NOT NULL,
    transport             TEXT,
    cout_par_eleve        REAL    DEFAULT 0,
    encadrants            TEXT,
    objectif_pedagogique  TEXT,
    statut                TEXT    NOT NULL DEFAULT 'prevue'
                              CHECK(statut IN ('prevue','confirmee','annulee')),
    autorisations_json    TEXT    NOT NULL DEFAULT '{}',
    created_at            TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


def _get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def _init_table():
    with _get_conn() as conn:
        conn.execute(CREATE_TABLE)
        conn.commit()


def _row_to_dict(row):
    d = dict(row)
    try:
        d["autorisations_json"] = json.loads(d["autorisations_json"] or "{}")
    except (json.JSONDecodeError, TypeError):
        d["autorisations_json"] = {}
    return d


def _generic_mot_parents(sortie):
    """Modèle générique quand l'IA est indisponible."""
    return (
        f"Madame, Monsieur,\n\n"
        f"Nous avons le plaisir de vous informer qu'une sortie scolaire est organisée "
        f"le {sortie['date']} à {sortie['lieu']}.\n\n"
        f"Objectif pédagogique : {sortie['objectif_pedagogique'] or 'Non précisé'}.\n"
        f"Transport : {sortie['transport'] or 'Non précisé'}.\n"
        f"Participation financière : {sortie['cout_par_eleve']:.2f} €.\n\n"
        f"Merci de compléter et retourner le talon ci-dessous avant le "
        f"{sortie['date']}.\n\n"
        f"─────────────────── TALON-RÉPONSE ───────────────────\n"
        f"Nom et prénom de l'élève : ........................................\n"
        f"□ Autorise  □ N'autorise pas  mon enfant à participer à la sortie.\n"
        f"□ Ci-joint la participation de {sortie['cout_par_eleve']:.2f} €.\n"
        f"Date : ....................  Signature : ..........................\n"
        f"─────────────────────────────────────────────────────"
    )


def register(app):
    _init_table()

    # ------------------------------------------------------------------
    # GET /api/sorties — liste triée par date
    # ------------------------------------------------------------------
    @app.route("/api/sorties", methods=["GET"])
    def get_sorties():
        try:
            with _get_conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM sorties ORDER BY date ASC"
                ).fetchall()
            return jsonify([_row_to_dict(r) for r in rows])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ------------------------------------------------------------------
    # POST /api/sorties — créer une sortie
    # ------------------------------------------------------------------
    @app.route("/api/sorties", methods=["POST"])
    def create_sortie():
        try:
            data = request.get_json(force=True) or {}
            titre = data.get("titre", "")
            date = data.get("date", "")
            lieu = data.get("lieu", "")
            transport = data.get("transport", "")
            cout_par_eleve = float(data.get("cout_par_eleve", 0))
            encadrants = data.get("encadrants", "")
            objectif = data.get("objectif_pedagogique", "")
            statut = data.get("statut", "prevue")
            autorisations_json = json.dumps(data.get("autorisations_json", {}))

            if not titre or not date or not lieu:
                return jsonify({"error": "titre, date et lieu sont obligatoires"}), 400

            with _get_conn() as conn:
                cur = conn.execute(
                    """INSERT INTO sorties
                       (titre, date, lieu, transport, cout_par_eleve, encadrants,
                        objectif_pedagogique, statut, autorisations_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        titre,
                        date,
                        lieu,
                        transport,
                        cout_par_eleve,
                        encadrants,
                        objectif,
                        statut,
                        autorisations_json,
                    ),
                )
                conn.commit()
                row = conn.execute(
                    "SELECT * FROM sorties WHERE id = ?", (cur.lastrowid,)
                ).fetchone()
            return jsonify(_row_to_dict(row)), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ------------------------------------------------------------------
    # PATCH /api/sorties/<sid> — modifier une sortie
    # ------------------------------------------------------------------
    @app.route("/api/sorties/<int:sid>", methods=["PATCH"])
    def update_sortie(sid):
        try:
            data = request.get_json(force=True) or {}
            allowed = {
                "titre",
                "date",
                "lieu",
                "transport",
                "cout_par_eleve",
                "encadrants",
                "objectif_pedagogique",
                "statut",
            }
            fields = {k: v for k, v in data.items() if k in allowed}
            if not fields:
                return jsonify({"error": "Aucun champ modifiable fourni"}), 400

            set_clause = ", ".join(f"{k} = ?" for k in fields)
            values = list(fields.values()) + [sid]

            with _get_conn() as conn:
                conn.execute(f"UPDATE sorties SET {set_clause} WHERE id = ?", values)
                conn.commit()
                row = conn.execute(
                    "SELECT * FROM sorties WHERE id = ?", (sid,)
                ).fetchone()
            if row is None:
                return jsonify({"error": "Sortie introuvable"}), 404
            return jsonify(_row_to_dict(row))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ------------------------------------------------------------------
    # DELETE /api/sorties/<sid> — supprimer une sortie
    # ------------------------------------------------------------------
    @app.route("/api/sorties/<int:sid>", methods=["DELETE"])
    def delete_sortie(sid):
        try:
            with _get_conn() as conn:
                cur = conn.execute("DELETE FROM sorties WHERE id = ?", (sid,))
                conn.commit()
            if cur.rowcount == 0:
                return jsonify({"error": "Sortie introuvable"}), 404
            return jsonify({"deleted": sid})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ------------------------------------------------------------------
    # POST /api/sorties/<sid>/autorisation — mettre à jour une autorisation
    # ------------------------------------------------------------------
    @app.route("/api/sorties/<int:sid>/autorisation", methods=["POST"])
    def set_autorisation(sid):
        try:
            data = request.get_json(force=True) or {}
            eleve_id = data.get("eleve_id")
            ok = data.get("ok")
            if eleve_id is None or ok is None:
                return jsonify({"error": "eleve_id et ok sont obligatoires"}), 400

            with _get_conn() as conn:
                row = conn.execute(
                    "SELECT autorisations_json FROM sorties WHERE id = ?", (sid,)
                ).fetchone()
                if row is None:
                    return jsonify({"error": "Sortie introuvable"}), 404

                autorisations = json.loads(row["autorisations_json"] or "{}")
                autorisations[str(eleve_id)] = bool(ok)

                conn.execute(
                    "UPDATE sorties SET autorisations_json = ? WHERE id = ?",
                    (json.dumps(autorisations), sid),
                )
                conn.commit()

            total = len(autorisations)
            autorises = sum(1 for v in autorisations.values() if v)
            return jsonify(
                {
                    "sortie_id": sid,
                    "autorises": autorises,
                    "total": total,
                    "autorisations": autorisations,
                }
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ------------------------------------------------------------------
    # POST /api/sorties/<sid>/mot-parents — générer le mot aux parents
    # ------------------------------------------------------------------
    @app.route("/api/sorties/<int:sid>/mot-parents", methods=["POST"])
    def mot_parents(sid):
        try:
            with _get_conn() as conn:
                row = conn.execute(
                    "SELECT * FROM sorties WHERE id = ?", (sid,)
                ).fetchone()
            if row is None:
                return jsonify({"error": "Sortie introuvable"}), 404

            sortie = _row_to_dict(row)

            if AI_AVAILABLE:
                system_prompt = (
                    "Tu es secrétaire pédagogique d'une école primaire française. "
                    "Rédige un mot d'information officiel destiné aux parents, "
                    "soigné, bienveillant et complet, suivi d'un talon-réponse détachable. "
                    "Utilise le vouvoiement. Sois concis (max 250 mots)."
                )
                user_prompt = (
                    f"Sortie scolaire : {sortie['titre']}\n"
                    f"Date : {sortie['date']}\n"
                    f"Lieu : {sortie['lieu']}\n"
                    f"Transport : {sortie['transport'] or 'Non précisé'}\n"
                    f"Coût par élève : {sortie['cout_par_eleve']:.2f} €\n"
                    f"Objectif pédagogique : {sortie['objectif_pedagogique'] or 'Non précisé'}\n"
                    f"Encadrants : {sortie['encadrants'] or 'Non précisé'}\n\n"
                    "Génère le mot complet avec talon-réponse."
                )
                try:
                    # generate(user, system=...) : l'ordre était inversé, et la
                    # fonction renvoie un dict — pas une chaîne.
                    res = ai_local.generate(user_prompt, system=system_prompt)
                    return jsonify({"texte": res["text"], "source": res["backend"]})
                except Exception:
                    pass  # fallback générique ci-dessous

            texte = _generic_mot_parents(sortie)
            return jsonify({"texte": texte, "source": "modele_generique"})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    print("[Pousseline] Sorties chargé")
