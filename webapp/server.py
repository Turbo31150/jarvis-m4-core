#!/usr/bin/env python3
"""JARVIS WebApp Dashboard — Flask backend, port 7777."""

import json
import os
import sqlite3
import subprocess
import time
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=".")

# ── Module Logiciels (cockpit unique : lance Gén.5/Biblio Manuels/… via Wine) ──
import sys as _sys

_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import logiciels as _logiciels

    _logiciels.register(app)
except Exception as _e:  # pragma: no cover
    print(f"[logiciels] module non chargé: {_e}")

# ── Module Espace Prof (élèves, exercices différenciés, corrections, séquences) ──
try:
    import prof_routes as _prof_routes

    _prof_routes.register(app)
    print("[JARVIS] Espace Prof chargé (/api/eleves, /api/exercice/*, …)")
except Exception as _e:  # pragma: no cover
    print(f"[prof_routes] module non chargé: {_e}")

# ── Module Outils Classe (problèmes maths, rituels, comportement, ceintures) ──
try:
    import outils_classe as _outils_classe

    _outils_classe.register(app)
except Exception as _e:  # pragma: no cover
    print(f"[outils_classe] module non chargé: {_e}")

# ── Module Ressources (supports pédagogiques imprimables PDF) ──
try:
    import ressources as _ressources

    _ressources.register(app)
except Exception as _e:  # pragma: no cover
    print(f"[ressources] module non chargé: {_e}")

# ── Modules gestion d'année (sorties, équipe, automatisations) ──
for _modname in (
    "sorties",
    "equipe",
    "automations",
    "export_pdf",
    "edt",
    "groupes",
    "appel",
    "ateliers",
    "carnet",
    "eleves_import",
    "bibliotheque",
    "mailer",
    "banque_annuelle",
    "systeme_io",
    "documents",
    "documents_io",
    "autosave",
    "admin",
    "adaptatif",
    "integrations",
):
    try:
        _m = __import__(_modname)
        _m.register(app)
    except Exception as _e:  # pragma: no cover
        print(f"[{_modname}] module non chargé: {_e}")

# ── GARDE DE SÉCURITÉ GLOBAL ─────────────────────────────────────────────
# RGPD : le serveur écoute sur 0.0.0.0 (LAN + téléphone). SANS ce garde, n'importe
# quel appareil du réseau lirait les données élèves (sorties, mails, logs) ou
# exécuterait /api/open, /api/run-cmd, /api/logiciels sans token. On exige donc le
# token X-Prof-Token sur TOUTES les routes /api/ (sauf localhost, exempté).
import hmac as _hmac

try:
    from prof_routes import PROF_TOKEN as _PROF_TOKEN
except Exception:  # pragma: no cover
    _PROF_TOKEN = ""


@app.before_request
def _require_token_global():
    p = request.path
    if not p.startswith("/api/"):
        return None  # /, manifest, sw.js, icons, /prof, static : publics
    if request.remote_addr in ("127.0.0.1", "::1"):
        return None  # localhost exempté (front same-origin, curl, monitoring)
    sent = request.headers.get("X-Prof-Token", "")
    if _PROF_TOKEN and _hmac.compare_digest(sent, _PROF_TOKEN):
        return None
    return jsonify({"error": "non autorisé", "need_token": True}), 401


# ── paths ──────────────────────────────────────────────────────────────
BASE = Path("/home/pamerys/jarvis")
THERMAL_JSON = BASE / "logs" / "thermal-status.json"
BUDGET_DB = BASE / "budget" / "budget.db"
PLANNING_DB = BASE / "planning.db"
NOTES_DB = BASE / "webapp" / "notes.db"
DOCUMENTS = Path("/home/pamerys/Documents")

M1 = "http://192.168.1.85:1234"
M2 = "http://192.168.1.26:1234"


# ── helpers ────────────────────────────────────────────────────────────
def db_conn(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_notes_db():
    with db_conn(NOTES_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nom       TEXT NOT NULL,
                prenom    TEXT NOT NULL,
                classe    TEXT NOT NULL,
                matiere   TEXT NOT NULL,
                note      REAL NOT NULL,
                coeff     REAL NOT NULL DEFAULT 1,
                date_ajout TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


init_notes_db()


# ── /api/status ────────────────────────────────────────────────────────
@app.route("/api/status")
def api_status():
    result = {
        "m1": {"status": "down", "latency_ms": None, "host": "192.168.1.85"},
        "m2": {"status": "down", "latency_ms": None, "host": "192.168.1.26"},
        "gpu": {"temp": 0, "state": "UNKNOWN", "fan_rpm": 0},
        "timestamp": datetime.now().isoformat(),
    }

    # Ping M1 with 1s timeout
    for name, base in (("m1", M1), ("m2", M2)):
        try:
            start = time.time()
            r = requests.get(f"{base}/v1/models", timeout=1)
            latency_ms = round((time.time() - start) * 1000, 2)
            if r.status_code == 200:
                result[name]["status"] = "up"
                result[name]["latency_ms"] = latency_ms
        except Exception:
            pass

    # Read GPU thermal data
    try:
        data = json.loads(THERMAL_JSON.read_text())
        result["gpu"] = {
            "temp": data.get("gpu_temp", 0),
            "state": data.get("state", "UNKNOWN"),
            "fan_rpm": data.get("fan_rpm", 0),
        }
    except Exception:
        pass

    return jsonify(result)


# ── /api/budget ────────────────────────────────────────────────────────
@app.route("/api/budget", methods=["GET"])
def get_budget():
    with db_conn(BUDGET_DB) as conn:
        rows = conn.execute(
            "SELECT * FROM transactions ORDER BY date DESC LIMIT 200"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/budget", methods=["POST"])
def add_budget():
    d = request.get_json(force=True)
    required = ("type", "categorie", "montant", "description")
    if not all(k in d for k in required):
        return jsonify({"error": "Missing fields"}), 400
    today = datetime.now().strftime("%Y-%m-%d")
    with db_conn(BUDGET_DB) as conn:
        conn.execute(
            "INSERT INTO transactions (type,categorie,montant,description,date) VALUES (?,?,?,?,?)",
            (d["type"], d["categorie"], float(d["montant"]), d["description"], today),
        )
        conn.commit()
    return jsonify({"ok": True})


# ── /api/planning ──────────────────────────────────────────────────────
@app.route("/api/planning", methods=["GET"])
def get_planning():
    # ?cat=pro|perso : ne renvoyer qu'un des deux plannings (pro = Espace prof, perso = vie perso)
    cat = (request.args.get("cat") or "").strip().lower()
    with db_conn(PLANNING_DB) as conn:
        # filet : garantir la colonne categorie même sur une base ancienne
        cols = [r[1] for r in conn.execute("PRAGMA table_info(cours)")]
        if "categorie" not in cols:
            conn.execute("ALTER TABLE cours ADD COLUMN categorie TEXT DEFAULT 'pro'")
            conn.commit()
        if cat in ("pro", "perso"):
            rows = conn.execute(
                "SELECT * FROM cours WHERE COALESCE(categorie,'pro')=? ORDER BY jour,heure",
                (cat,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM cours ORDER BY jour,heure").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/planning", methods=["POST"])
def add_planning():
    d = request.get_json(force=True)
    required = ("jour", "heure", "duree", "titre")
    if not all(k in d for k in required):
        return jsonify({"error": "Missing fields"}), 400
    cat = str(d.get("categorie", "pro")).lower()
    if cat not in ("pro", "perso"):
        cat = "pro"
    with db_conn(PLANNING_DB) as conn:
        conn.execute(
            "INSERT INTO cours (jour,heure,duree,titre,salle,categorie) VALUES (?,?,?,?,?,?)",
            (d["jour"], d["heure"], d["duree"], d["titre"], d.get("salle", ""), cat),
        )
        conn.commit()
    return jsonify({"ok": True})


@app.route("/api/planning/<int:cid>", methods=["DELETE"])
def del_planning(cid):
    with db_conn(PLANNING_DB) as conn:
        conn.execute("DELETE FROM cours WHERE id=?", (cid,))
        conn.commit()
    return jsonify({"ok": True})


# ── /api/notes ─────────────────────────────────────────────────────────
@app.route("/api/notes", methods=["GET"])
def get_notes():
    classe = request.args.get("classe")
    with db_conn(NOTES_DB) as conn:
        if classe:
            rows = conn.execute(
                "SELECT * FROM notes WHERE classe=? ORDER BY nom,prenom", (classe,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM notes ORDER BY classe,nom,prenom"
            ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/notes", methods=["POST"])
def add_note():
    d = request.get_json(force=True)
    required = ("nom", "prenom", "classe", "matiere", "note", "coeff")
    if not all(k in d for k in required):
        return jsonify({"error": "Missing fields"}), 400
    n = float(d["note"])
    if not (0 <= n <= 20):
        return jsonify({"error": "Note must be 0-20"}), 400
    with db_conn(NOTES_DB) as conn:
        conn.execute(
            "INSERT INTO notes (nom,prenom,classe,matiere,note,coeff) VALUES (?,?,?,?,?,?)",
            (d["nom"], d["prenom"], d["classe"], d["matiere"], n, float(d["coeff"])),
        )
        conn.commit()
    return jsonify({"ok": True})


# ── /api/cluster ───────────────────────────────────────────────────────
@app.route("/api/cluster")
def api_cluster():
    result = {}
    for name, base in (("M1", M1), ("M2", M2)):
        try:
            r = requests.get(f"{base}/v1/models", timeout=3)
            models = [m["id"] for m in r.json().get("data", [])]
            result[name] = {"status": "up", "models": models[:6]}
        except Exception as e:
            result[name] = {"status": "down", "error": str(e)}
    return jsonify(result)


# ── /api/jarvis-ask ────────────────────────────────────────────────────
MODE_MODELS = {
    "cours": "qwen3.5-35b-a3b",
    "recherche": "qwen3.5-35b-a3b",
    "code": "claudegpt-debugger",
    "trading": "qwen3.5-27b-claude-4.6-opus-distilled",
}
DEFAULT_MODEL = "qwen3.5-35b-a3b"


@app.route("/api/jarvis-ask", methods=["POST"])
def jarvis_ask():
    d = request.get_json(force=True)
    question = d.get("question", "").strip()
    mode = d.get("mode", "cours").lower()
    if not question:
        return jsonify({"error": "Empty question"}), 400
    model = MODE_MODELS.get(mode, DEFAULT_MODEL)
    system_prompts = {
        "cours": "Tu es un assistant pédagogique expert. Réponds en français, de façon claire et structurée pour une enseignante.",
        "recherche": "Tu es un assistant de recherche académique. Synthétise et cite des sources.",
        "code": "Tu es un expert développeur. Fournis du code commenté, fonctionnel.",
        "trading": "Tu es un analyste financier. Fournis des analyses précises avec chiffres.",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompts.get(mode, system_prompts["cours"]),
            },
            {"role": "user", "content": question},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }
    try:
        r = requests.post(f"{M2}/v1/chat/completions", json=payload, timeout=60)
        answer = r.json()["choices"][0]["message"]["content"]
        return jsonify({"answer": answer, "model": model})
    except Exception:
        # Fallback to M1
        try:
            r = requests.post(f"{M1}/v1/chat/completions", json=payload, timeout=60)
            answer = r.json()["choices"][0]["message"]["content"]
            return jsonify({"answer": answer, "model": model + " (M1)"})
        except Exception as e2:
            return jsonify({"error": str(e2)}), 503


# ── /api/docs ──────────────────────────────────────────────────────────
@app.route("/api/docs")
def api_docs():
    tree = []
    if not DOCUMENTS.exists():
        return jsonify([])
    for item in sorted(DOCUMENTS.iterdir()):
        node = {
            "name": item.name,
            "path": str(item),
            "type": "dir" if item.is_dir() else "file",
            "children": [],
        }
        if item.is_dir():
            try:
                for child in sorted(item.iterdir()):
                    node["children"].append(
                        {
                            "name": child.name,
                            "path": str(child),
                            "type": "dir" if child.is_dir() else "file",
                        }
                    )
            except PermissionError:
                pass
        tree.append(node)
    return jsonify(tree)


# ── /api/open ──────────────────────────────────────────────────────────
# Répertoires autorisés à l'ouverture (anti path-traversal / exécution arbitraire)
_OPEN_ALLOWED = [
    (Path.home() / "Documents").resolve(),
    (Path.home() / "jarvis" / "webapp").resolve(),
    (Path.home() / "Téléchargements").resolve(),
]


def _display():
    """Retourne un display X dont le socket existe VRAIMENT.

    Le service hérite DISPLAY=:0 (unit + env) mais M4 tourne en réalité sur :1
    (seul socket /tmp/.X11-unix/X1). On ne garde le DISPLAY hérité que si son
    socket existe, sinon on prend le premier socket réel — sans quoi evince /
    xdg-open s'ouvrent sur un écran fantôme et rien ne s'affiche.
    """
    try:
        displays = [":" + s.name[1:] for s in sorted(Path("/tmp/.X11-unix").glob("X*"))]
    except OSError:
        displays = []
    env_disp = os.environ.get("DISPLAY")
    if env_disp and env_disp in displays:
        return env_disp
    return displays[0] if displays else (env_disp or ":0")


@app.route("/api/open")
def api_open():
    path = request.args.get("path", "")
    if not path:
        return jsonify({"error": "Missing path"}), 400
    try:
        target = Path(path).resolve()
    except Exception:
        return jsonify({"error": "Invalid path"}), 400
    # confinement réel (pas de bypass par préfixe : /home/x-evil ne matche plus /home/x)
    if not any(target.is_relative_to(root) for root in _OPEN_ALLOWED):
        return jsonify({"error": "Chemin non autorisé"}), 403
    # ne jamais ouvrir un exécutable/script via xdg-open (RCE)
    _DENY_SUFFIX = {
        ".desktop",
        ".sh",
        ".py",
        ".appimage",
        ".jar",
        ".bin",
        ".run",
        ".exe",
    }
    if target.suffix.lower() in _DENY_SUFFIX:
        return jsonify({"error": "Type de fichier non autorisé"}), 403
    if not target.is_file() and not target.is_dir():
        return jsonify({"error": "Not found"}), 404
    env = {**os.environ, "DISPLAY": _display()}
    # Chrome tourne en mode --app (kiosk) et "avale" les PDF sans les afficher :
    # on les ouvre avec une visionneuse dédiée. Le reste passe par xdg-open.
    cmd = ["xdg-open", str(target)]
    if target.is_file() and target.suffix.lower() == ".pdf":
        import shutil

        viewer = shutil.which("evince") or shutil.which("okular")
        if viewer:
            cmd = [viewer, str(target)]
    # start_new_session : détache le process de gvfs/service (sinon meurt avec la requête)
    subprocess.Popen(cmd, env=env, start_new_session=True)
    return jsonify({"ok": True})


# ── /api/service-status ────────────────────────────────────────────────
@app.route("/api/service-status")
def api_service_status():
    name = request.args.get("name", "")
    if not name:
        return jsonify({"error": "Missing name"}), 400
    r = subprocess.run(
        ["systemctl", "--user", "is-active", name], capture_output=True, text=True
    )
    return jsonify({"active": r.stdout.strip() == "active", "state": r.stdout.strip()})


# ── /api/run-cmd ───────────────────────────────────────────────────────
CMD_MAP = {
    "restart-widget": ["systemctl", "--user", "restart", "jarvis-voice-widget"],
    "git-push": [
        "bash",
        "-c",
        "cd /home/pamerys/jarvis && git add -A && git commit -m 'auto-push' && git push 2>&1",
    ],
    "backup": ["systemctl", "--user", "start", "jarvis-backup"],
}


@app.route("/api/run-cmd", methods=["POST"])
def api_run_cmd():
    d = request.get_json(force=True)
    cmd_key = d.get("cmd", "")
    if cmd_key not in CMD_MAP:
        return jsonify({"error": "Unknown command"}), 400
    try:
        r = subprocess.run(CMD_MAP[cmd_key], capture_output=True, text=True, timeout=30)
        return jsonify({"ok": True, "output": (r.stdout + r.stderr).strip()[:500]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── serve index.html ───────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# ── PWA (installable + synchro Android) ──────────────────────────────
@app.route("/manifest.json")
def pwa_manifest():
    return send_from_directory(
        ".", "manifest.json", mimetype="application/manifest+json"
    )


@app.route("/sw.js")
def pwa_sw():
    resp = send_from_directory(".", "sw.js", mimetype="application/javascript")
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.route("/icon-192.png")
def pwa_icon192():
    return send_from_directory(".", "icon-192.png", mimetype="image/png")


@app.route("/icon-512.png")
def pwa_icon512():
    return send_from_directory(".", "icon-512.png", mimetype="image/png")


@app.route("/ca.crt")
def pwa_ca():
    # Certificat racine à installer une fois sur le téléphone Android
    return send_from_directory(
        "certs",
        "ca.crt",
        mimetype="application/x-x509-ca-cert",
        as_attachment=True,
        download_name="JARVIS-M4-Root-CA.crt",
    )


# ── RDV Calendrier ───────────────────────────────────────────────────
def _rdv_conn():
    import sqlite3 as _s

    path = os.path.expanduser("~/jarvis/rdv.db")
    c = _s.connect(path)
    c.row_factory = _s.Row
    c.execute("""CREATE TABLE IF NOT EXISTS rdv (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL, date TEXT NOT NULL,
        heure_debut TEXT, heure_fin TEXT,
        type TEXT DEFAULT 'rdv', description TEXT,
        created_at TEXT DEFAULT (datetime('now')))""")
    c.commit()
    return c


@app.route("/api/rdv", methods=["GET"])
def api_rdv_get():
    from datetime import datetime as _dt

    y = request.args.get("year", str(_dt.now().year))
    m = str(request.args.get("month", _dt.now().month)).zfill(2)
    c = _rdv_conn()
    rows = c.execute(
        "SELECT * FROM rdv WHERE strftime('%Y',date)=? AND strftime('%m',date)=? ORDER BY date,heure_debut",
        (str(y), m),
    ).fetchall()
    c.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/rdv", methods=["POST"])
def api_rdv_add():
    d = request.json or {}
    c = _rdv_conn()
    c.execute(
        "INSERT INTO rdv(titre,date,heure_debut,heure_fin,type,description) VALUES(?,?,?,?,?,?)",
        (
            d.get("titre", ""),
            d.get("date", ""),
            d.get("heure_debut", ""),
            d.get("heure_fin", ""),
            d.get("type", "rdv"),
            d.get("description", ""),
        ),
    )
    c.commit()
    c.close()
    return jsonify({"ok": True})


@app.route("/api/rdv/<int:rid>", methods=["DELETE"])
def api_rdv_del(rid):
    c = _rdv_conn()
    c.execute("DELETE FROM rdv WHERE id=?", (rid,))
    c.commit()
    c.close()
    return jsonify({"ok": True})


@app.route("/api/voice-record", methods=["POST"])
def api_voice():
    import subprocess

    try:
        subprocess.Popen(
            ["bash", os.path.expanduser("~/jarvis/scripts/voice_widget.sh")]
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ── TODO LIST ────────────────────────────────────────────────────────
def _todo_conn():
    import sqlite3 as _s

    path = os.path.expanduser("~/jarvis/todo.db")
    c = _s.connect(path)
    c.row_factory = _s.Row
    c.execute("""CREATE TABLE IF NOT EXISTS todo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL, categorie TEXT DEFAULT 'général',
        priorite TEXT DEFAULT 'normal', statut TEXT DEFAULT 'todo',
        cli TEXT, deadline TEXT, notes TEXT,
        created_at TEXT DEFAULT (datetime('now')))""")
    c.commit()
    return c


@app.route("/api/todo", methods=["GET"])
def api_todo_get():
    cat = request.args.get("cat", "")
    c = _todo_conn()
    q = (
        "SELECT * FROM todo"
        + (" WHERE categorie=?" if cat else "")
        + " ORDER BY CASE priorite WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 ELSE 4 END, created_at"
    )
    rows = c.execute(q, (cat,) if cat else ()).fetchall()
    c.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/todo", methods=["POST"])
def api_todo_add():
    d = request.json or {}
    c = _todo_conn()
    c.execute(
        "INSERT INTO todo(titre,categorie,priorite,cli,deadline,notes) VALUES(?,?,?,?,?,?)",
        (
            d.get("titre", ""),
            d.get("categorie", "général"),
            d.get("priorite", "normal"),
            d.get("cli", ""),
            d.get("deadline", ""),
            d.get("notes", ""),
        ),
    )
    c.commit()
    c.close()
    return jsonify({"ok": True})


@app.route("/api/todo/<int:tid>", methods=["PATCH"])
def api_todo_update(tid):
    d = request.json or {}
    c = _todo_conn()
    if "statut" in d:
        c.execute("UPDATE todo SET statut=? WHERE id=?", (d["statut"], tid))
    c.commit()
    c.close()
    return jsonify({"ok": True})


@app.route("/api/todo/<int:tid>", methods=["DELETE"])
def api_todo_del(tid):
    c = _todo_conn()
    c.execute("DELETE FROM todo WHERE id=?", (tid,))
    c.commit()
    c.close()
    return jsonify({"ok": True})


# ── AGENTS LIST ───────────────────────────────────────────────────────
@app.route("/api/agents")
def api_agents():
    agents = [
        {
            "nom": "jarvis-ask",
            "desc": "Assistant IA multi-mode (cours/code/trading/compress)",
            "cli": "jarvis-ask 'question' --cours",
            "categorie": "IA",
            "icon": "🤖",
        },
        {
            "nom": "jarvis-concours",
            "desc": "Préparation concours MAMS oral 2 juin 2026",
            "cli": "jarvis-concours 'question jury'",
            "categorie": "Concours",
            "icon": "🎓",
        },
        {
            "nom": "jarvis-admin",
            "desc": "Démarches admin MDPH/DALO/CAF/Académie",
            "cli": "jarvis-admin 'ma question'",
            "categorie": "Admin",
            "icon": "🏛️",
        },
        {
            "nom": "jarvis-rdv",
            "desc": "Gestion agenda et RDV (sync dashboard)",
            "cli": "jarvis-rdv | jarvis-rdv add 'Titre' '2026-06-02'",
            "categorie": "Agenda",
            "icon": "📅",
        },
        {
            "nom": "notes_eleves",
            "desc": "Notes élèves SQLite — ajouter/moyennes/bulletin/export CSV",
            "cli": "notes_eleves ajouter 'Dupont' 'Marie' '6A' 'Maths' 15",
            "categorie": "Pédagogie",
            "icon": "📊",
        },
        {
            "nom": "obs-cours",
            "desc": "Enregistrement OBS automatique pour les cours",
            "cli": "obs-cours start | stop | status",
            "categorie": "Cours",
            "icon": "🎥",
        },
        {
            "nom": "push-all",
            "desc": "Push GitHub de tous les repos (BASE-SQL3 + machine-m4)",
            "cli": "push-all",
            "categorie": "Système",
            "icon": "📤",
        },
        {
            "nom": "dashboard",
            "desc": "Dashboard terminal JARVIS (météo/planning/budget/cluster)",
            "cli": "python3 ~/jarvis/scripts/dashboard.py",
            "categorie": "Système",
            "icon": "🖥️",
        },
        {
            "nom": "backup-now",
            "desc": "Backup quotidien docs + DBs avec rotation 7j",
            "cli": "bash ~/jarvis/scripts/backup-daily.sh",
            "categorie": "Système",
            "icon": "💾",
        },
        {
            "nom": "windows-data",
            "desc": "Accès données importées depuis Windows (concours/démarches)",
            "cli": "ls ~/Documents/Windows-Import/",
            "categorie": "Données",
            "icon": "📁",
        },
        {
            "nom": "jarvis-thermal-agent",
            "desc": "Agent thermique GPU — contrôle OC selon température",
            "cli": "systemctl --user status jarvis-thermal-agent",
            "categorie": "Système",
            "icon": "🌡️",
        },
        {
            "nom": "arrange_windows",
            "desc": "Organisation automatique fenêtres terminaux (Super+T)",
            "cli": "python3 /usr/local/bin/arrange_windows.py auto",
            "categorie": "Bureau",
            "icon": "🪟",
        },
        {
            "nom": "budget",
            "desc": "Gestion budget mensuel enseignante (revenus/dépenses/rapport)",
            "cli": "python3 ~/jarvis/budget/budget_enseignante.py rapport",
            "categorie": "Budget",
            "icon": "💰",
        },
        {
            "nom": "jarvis-router",
            "desc": "Routeur multi-agents M1+M2 par mots-clés (transcription→IA)",
            "cli": "python3 ~/jarvis/multiagent/jarvis-router.py",
            "categorie": "IA",
            "icon": "🔀",
        },
        {
            "nom": "gemini-ask",
            "desc": "Gemini 2.5 Pro via Google One (gratuit)",
            "cli": "bash ~/jarvis/scripts/gemini-ask.sh 'question'",
            "categorie": "IA",
            "icon": "💎",
        },
    ]
    return jsonify(agents)


# ── KEYWORDS / TRIGGERS ───────────────────────────────────────────────
@app.route("/api/keywords")
def api_keywords():
    kws = {
        "cours": {
            "agents": ["jarvis-ask --cours", "notes_eleves", "obs-cours"],
            "desc": "Pédagogie, exercices, leçons",
            "color": "green",
        },
        "concours": {
            "agents": ["jarvis-concours", "jarvis-ask --cours"],
            "desc": "MAMS, jury, oral, préparation",
            "color": "orange",
        },
        "budget": {
            "agents": ["budget", "push-all"],
            "desc": "Dépenses, revenus, finances",
            "color": "blue",
        },
        "trading": {
            "agents": ["jarvis-ask --trading"],
            "desc": "Crypto, MEXC, analyse marché",
            "color": "purple",
        },
        "admin": {
            "agents": ["jarvis-admin", "jarvis-rdv"],
            "desc": "MDPH, DALO, CAF, démarches",
            "color": "red",
        },
        "rdv": {
            "agents": ["jarvis-rdv"],
            "desc": "Calendrier, rendez-vous, agenda",
            "color": "teal",
        },
        "code": {
            "agents": ["jarvis-ask --code"],
            "desc": "Développement, debug, scripts",
            "color": "yellow",
        },
        "backup": {
            "agents": ["backup-now", "push-all"],
            "desc": "Sauvegarde, GitHub, archivage",
            "color": "gray",
        },
        "médical": {
            "agents": ["jarvis-admin"],
            "desc": "Santé, RQTH, médecin, ordonnance",
            "color": "pink",
        },
    }
    return jsonify(kws)


@app.route("/api/system")
def api_system():
    """Audit système complet — score JARVIS, J-X MAMS, services, disque."""
    from datetime import date as _date
    import shutil

    result: dict = {
        "mams_days": ((_date(2026, 6, 2) - _date.today()).days),
        "score": 0,
        "max": 0,
        "items": [],
        "disk_pct": 0,
        "services": {},
    }

    def _check(name: str, ok: bool, detail: str = "") -> None:
        result["max"] += 1
        status = "ok" if ok else "ko"
        if ok:
            result["score"] += 1
        result["items"].append({"name": name, "status": status, "detail": detail})

    # Services
    for svc in ["jarvis-webapp", "jarvis-voice-widget", "jarvis-thermal-agent"]:
        try:
            import subprocess as _sp

            r = _sp.run(
                ["systemctl", "--user", "is-active", f"{svc}.service"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            active = r.stdout.strip() == "active"
        except Exception:
            active = False
        result["services"][svc] = "up" if active else "down"
        _check(svc, active, "active" if active else "inactif")

    # Disk
    usage = shutil.disk_usage("/home")
    disk_pct = int(usage.used * 100 / usage.total)
    result["disk_pct"] = disk_pct
    _check("disque /home", disk_pct < 85, f"{disk_pct}%")

    # GPU
    try:
        data = json.loads(THERMAL_JSON.read_text())
        temp = data.get("gpu_temp", 0)
        _check("gpu_temp", temp < 90, f"{temp}°C")
    except Exception:
        _check("gpu_temp", False, "thermal JSON absent")

    # Cluster M2 (quick check)
    try:
        r = requests.get(f"{M2}/v1/models", timeout=1)
        _check("cluster_m2", r.status_code == 200, "UP")
    except Exception:
        _check("cluster_m2", False, "DOWN")

    # SQLite todo
    TODO_DB = BASE / "todo.db"
    try:
        with db_conn(TODO_DB) as conn:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM todo WHERE statut='todo'"
            ).fetchone()[0]
        _check("todo_db", True, f"{cnt} tâches actives")
    except Exception:
        _check("todo_db", False, "inaccessible")

    result["score_pct"] = (
        int(result["score"] * 100 / result["max"]) if result["max"] else 0
    )
    return jsonify(result)


if __name__ == "__main__":
    import ssl as _ssl
    import threading as _th
    from werkzeug.serving import make_server as _mk

    _certdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs")
    _crt = os.path.join(_certdir, "server.crt")
    _key = os.path.join(_certdir, "server.key")

    # HTTPS:8443 (téléphone Android — PWA installable + offline) si certs présents
    if os.path.exists(_crt) and os.path.exists(_key):
        _ctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_SERVER)
        _ctx.load_cert_chain(_crt, _key)
        _https = _mk("0.0.0.0", 8443, app, ssl_context=_ctx)
        _th.Thread(target=_https.serve_forever, daemon=True).start()
        print("[JARVIS] HTTPS actif sur https://0.0.0.0:8443 (PWA Android)")

    # HTTP:7777 (PC/localhost — contexte sécurisé via localhost)
    app.run(host="0.0.0.0", port=7777, debug=False)
