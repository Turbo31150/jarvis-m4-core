import sqlite3
from flask import jsonify, request

try:
    import ai_local

    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

DB_PATH = "/home/pamerys/jarvis/webapp/ecole.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_tables():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS collegues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('PE','directeur','ATSEM','AESH','remplaçant')),
                niveaux TEXT DEFAULT '',
                email TEXT DEFAULT '',
                telephone TEXT DEFAULT '',
                jours_presence TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reunions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titre TEXT NOT NULL,
                date TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('conseil_ecole','conseil_cycle','equipe','parents')),
                ordre_du_jour TEXT DEFAULT '',
                participants TEXT DEFAULT '',
                compte_rendu TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def register(app):
    init_tables()

    # ─── COLLÈGUES ────────────────────────────────────────────────

    @app.route("/api/collegues", methods=["GET"])
    def list_collegues():
        try:
            conn = get_db()
            rows = conn.execute(
                "SELECT * FROM collegues ORDER BY nom, prenom"
            ).fetchall()
            conn.close()
            return jsonify([dict(r) for r in rows])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/collegues", methods=["POST"])
    def create_collegue():
        try:
            data = request.get_json(force=True)
            required = ("nom", "prenom", "role")
            missing = [f for f in required if not data.get(f)]
            if missing:
                return jsonify({"error": f"Champs requis manquants : {missing}"}), 400
            conn = get_db()
            cur = conn.execute(
                """INSERT INTO collegues (nom, prenom, role, niveaux, email, telephone, jours_presence, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["nom"],
                    data["prenom"],
                    data["role"],
                    data.get("niveaux", ""),
                    data.get("email", ""),
                    data.get("telephone", ""),
                    data.get("jours_presence", ""),
                    data.get("notes", ""),
                ),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM collegues WHERE id=?", (cur.lastrowid,)
            ).fetchone()
            conn.close()
            return jsonify(dict(row)), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/collegues/<int:cid>", methods=["PATCH"])
    def update_collegue(cid):
        try:
            data = request.get_json(force=True)
            allowed = (
                "nom",
                "prenom",
                "role",
                "niveaux",
                "email",
                "telephone",
                "jours_presence",
                "notes",
            )
            fields = {k: v for k, v in data.items() if k in allowed}
            if not fields:
                return jsonify({"error": "Aucun champ modifiable fourni"}), 400
            set_clause = ", ".join(f"{k}=?" for k in fields)
            conn = get_db()
            conn.execute(
                f"UPDATE collegues SET {set_clause} WHERE id=?",
                (*fields.values(), cid),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM collegues WHERE id=?", (cid,)).fetchone()
            conn.close()
            if row is None:
                return jsonify({"error": "Collègue introuvable"}), 404
            return jsonify(dict(row))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/collegues/<int:cid>", methods=["DELETE"])
    def delete_collegue(cid):
        try:
            conn = get_db()
            res = conn.execute("DELETE FROM collegues WHERE id=?", (cid,))
            conn.commit()
            conn.close()
            if res.rowcount == 0:
                return jsonify({"error": "Collègue introuvable"}), 404
            return jsonify({"deleted": cid})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ─── RÉUNIONS ─────────────────────────────────────────────────

    @app.route("/api/reunions", methods=["GET"])
    def list_reunions():
        try:
            conn = get_db()
            rows = conn.execute("SELECT * FROM reunions ORDER BY date DESC").fetchall()
            conn.close()
            return jsonify([dict(r) for r in rows])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/reunions", methods=["POST"])
    def create_reunion():
        try:
            data = request.get_json(force=True)
            required = ("titre", "date", "type")
            missing = [f for f in required if not data.get(f)]
            if missing:
                return jsonify({"error": f"Champs requis manquants : {missing}"}), 400
            conn = get_db()
            cur = conn.execute(
                """INSERT INTO reunions (titre, date, type, ordre_du_jour, participants, compte_rendu)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    data["titre"],
                    data["date"],
                    data["type"],
                    data.get("ordre_du_jour", ""),
                    data.get("participants", ""),
                    data.get("compte_rendu", ""),
                ),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM reunions WHERE id=?", (cur.lastrowid,)
            ).fetchone()
            conn.close()
            return jsonify(dict(row)), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/reunions/<int:rid>", methods=["PATCH"])
    def update_reunion(rid):
        try:
            data = request.get_json(force=True)
            allowed = (
                "titre",
                "date",
                "type",
                "ordre_du_jour",
                "participants",
                "compte_rendu",
            )
            fields = {k: v for k, v in data.items() if k in allowed}
            if not fields:
                return jsonify({"error": "Aucun champ modifiable fourni"}), 400
            set_clause = ", ".join(f"{k}=?" for k in fields)
            conn = get_db()
            conn.execute(
                f"UPDATE reunions SET {set_clause} WHERE id=?",
                (*fields.values(), rid),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM reunions WHERE id=?", (rid,)).fetchone()
            conn.close()
            if row is None:
                return jsonify({"error": "Réunion introuvable"}), 404
            return jsonify(dict(row))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/reunions/<int:rid>", methods=["DELETE"])
    def delete_reunion(rid):
        try:
            conn = get_db()
            res = conn.execute("DELETE FROM reunions WHERE id=?", (rid,))
            conn.commit()
            conn.close()
            if res.rowcount == 0:
                return jsonify({"error": "Réunion introuvable"}), 404
            return jsonify({"deleted": rid})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ─── IA : ORDRE DU JOUR ───────────────────────────────────────

    @app.route("/api/reunions/<int:rid>/ordre-du-jour", methods=["POST"])
    def generer_ordre_du_jour(rid):
        try:
            conn = get_db()
            row = conn.execute("SELECT * FROM reunions WHERE id=?", (rid,)).fetchone()
            conn.close()
            if row is None:
                return jsonify({"error": "Réunion introuvable"}), 404

            reunion = dict(row)
            titre = reunion["titre"]
            type_reunion = reunion["type"]

            type_labels = {
                "conseil_ecole": "Conseil d'école",
                "conseil_cycle": "Conseil de cycle",
                "equipe": "Réunion d'équipe",
                "parents": "Réunion parents",
            }
            label = type_labels.get(type_reunion, type_reunion)

            if AI_AVAILABLE:
                try:
                    system = (
                        "Tu es un assistant pour enseignants du primaire en France. "
                        "Tu rédiges des ordres du jour clairs, structurés et concis, "
                        "adaptés au contexte scolaire français."
                    )
                    user = (
                        f"Génère un ordre du jour structuré pour une réunion de type '{label}' "
                        f"intitulée : '{titre}'. "
                        "Utilise des points numérotés. Inclus : accueil, points de fond, "
                        "questions diverses, date de la prochaine réunion. Sois concis."
                    )
                    # generate(user, system=...) : l'ordre était inversé, et la
                    # fonction renvoie un dict — pas une chaîne.
                    res = ai_local.generate(user, system=system)
                    return jsonify({"texte": res["text"], "source": res["backend"]})
                except Exception:
                    pass

            # Fallback générique
            texte = (
                f"ORDRE DU JOUR — {label} : {titre}\n\n"
                "1. Accueil et émargement\n"
                "2. Approbation du compte-rendu de la dernière réunion\n"
                "3. Points à l'ordre du jour\n"
                "   3.1. \n"
                "   3.2. \n"
                "4. Questions diverses\n"
                "5. Date et objet de la prochaine réunion\n"
            )
            return jsonify({"texte": texte, "source": "modele"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ─── IA : COMPTE-RENDU ────────────────────────────────────────

    @app.route("/api/reunions/<int:rid>/compte-rendu", methods=["POST"])
    def generer_compte_rendu(rid):
        try:
            conn = get_db()
            row = conn.execute("SELECT * FROM reunions WHERE id=?", (rid,)).fetchone()
            conn.close()
            if row is None:
                return jsonify({"error": "Réunion introuvable"}), 404

            reunion = dict(row)
            ordre = reunion.get("ordre_du_jour", "").strip()
            titre = reunion["titre"]
            date = reunion["date"]
            participants = reunion.get("participants", "").strip()

            type_labels = {
                "conseil_ecole": "Conseil d'école",
                "conseil_cycle": "Conseil de cycle",
                "equipe": "Réunion d'équipe",
                "parents": "Réunion parents",
            }
            label = type_labels.get(reunion["type"], reunion["type"])

            if AI_AVAILABLE and ordre:
                try:
                    system = (
                        "Tu es un assistant pour enseignants du primaire en France. "
                        "Tu rédiges des modèles de comptes-rendus de réunion clairs, "
                        "structurés, au format officiel scolaire français."
                    )
                    user = (
                        f"Génère un modèle de compte-rendu pour la réunion suivante :\n"
                        f"Type : {label}\n"
                        f"Titre : {titre}\n"
                        f"Date : {date}\n"
                        f"Participants : {participants or 'à compléter'}\n"
                        f"Ordre du jour :\n{ordre}\n\n"
                        "Crée un compte-rendu structuré avec des sections à compléter "
                        "(entre crochets). Inclus : en-tête, liste de présence, "
                        "synthèse par point, décisions prises, actions à mener, "
                        "prochaine réunion, signature."
                    )
                    # generate(user, system=...) : l'ordre était inversé, et la
                    # fonction renvoie un dict — pas une chaîne.
                    res = ai_local.generate(user, system=system)
                    return jsonify({"texte": res["text"], "source": res["backend"]})
                except Exception:
                    pass

            # Fallback générique
            texte = (
                f"COMPTE-RENDU — {label}\n"
                f"Réunion : {titre}\n"
                f"Date : {date}\n"
                f"Participants : {participants or '[à compléter]'}\n\n"
                "─────────────────────────────────────\n"
                "ORDRE DU JOUR\n"
                f"{ordre or '[à compléter]'}\n\n"
                "─────────────────────────────────────\n"
                "DÉROULÉ ET DÉCISIONS\n\n"
                "[Pour chaque point, noter les échanges et décisions prises]\n\n"
                "─────────────────────────────────────\n"
                "ACTIONS À MENER\n"
                "- [Action] — Responsable : [nom] — Échéance : [date]\n\n"
                "─────────────────────────────────────\n"
                "PROCHAINE RÉUNION\n"
                "Date : [à définir] — Objet : [à définir]\n\n"
                "Signatures :\n"
                "Directeur(trice) : ________________\n"
                "Secrétaire de séance : ________________\n"
            )
            return jsonify({"texte": texte, "source": "modele"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    print("[Pousseline] Équipe chargé")
