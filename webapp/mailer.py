"""Envoi RÉEL des mails parents pour Pousseline (app enseignante).

Comble le manque « les mails étaient rédigés mais jamais envoyés ».
- Config SMTP stockée dans ecole.db table kv (clé 'smtp_config') → hors-Git (ecole.db gitignoré).
- Presets : Gmail (smtp.gmail.com:587 STARTTLS), ou serveur personnalisé.
- Envoi protégé par @require_token (RGPD : serveur sur 0.0.0.0).
- dry_run par défaut tant qu'aucune config valide → ne casse jamais, testable sans creds.
- Chaque envoi est journalisé (table mail_log) pour traçabilité parents.

register(app) branché par server.py. Réversible : retirer de la boucle de server.py.
"""

import json
import smtplib
import sqlite3
import ssl
from email.message import EmailMessage
from email.utils import formataddr, parseaddr

from ecole_schema import ECOLE_DB

CFG_KEY = "smtp_config"

# Presets connus : l'utilisatrice choisit "gmail" et ne renseigne que user+password.
PRESETS = {
    "gmail": {"host": "smtp.gmail.com", "port": 587, "tls": True},
    "outlook": {"host": "smtp.office365.com", "port": 587, "tls": True},
    "orange": {"host": "smtp.orange.fr", "port": 587, "tls": True},
    "free": {"host": "smtp.free.fr", "port": 587, "tls": True},
    "laposte": {"host": "smtp.laposte.net", "port": 465, "tls": True},
}


def _conn():
    c = sqlite3.connect(str(ECOLE_DB))
    c.row_factory = sqlite3.Row
    return c


def _init():
    """Crée mail_log + ajoute eleves.email_parent (idempotent, ne migre rien d'existant)."""
    c = _conn()
    try:
        c.execute(
            """CREATE TABLE IF NOT EXISTS mail_log (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 dest TEXT, sujet TEXT, corps TEXT, eleve_id INTEGER,
                 statut TEXT, erreur TEXT,
                 created_at TEXT DEFAULT (datetime('now'))
               )"""
        )
        cols = [r["name"] for r in c.execute("PRAGMA table_info(eleves)")]
        if "email_parent" not in cols:
            c.execute("ALTER TABLE eleves ADD COLUMN email_parent TEXT")
        c.commit()
    finally:
        c.close()


def _get_cfg():
    c = _conn()
    try:
        r = c.execute("SELECT v FROM kv WHERE k=?", (CFG_KEY,)).fetchone()
        return json.loads(r["v"]) if r and r["v"] else {}
    except Exception:
        return {}
    finally:
        c.close()


def _save_cfg(cfg):
    c = _conn()
    try:
        c.execute(
            "INSERT INTO kv(k,v) VALUES(?,?) "
            "ON CONFLICT(k) DO UPDATE SET v=excluded.v, ts=datetime('now')",
            (CFG_KEY, json.dumps(cfg)),
        )
        c.commit()
    finally:
        c.close()


def _cfg_ready(cfg):
    return bool(
        cfg.get("host") and cfg.get("port") and cfg.get("user") and cfg.get("password")
    )


def _send_smtp(cfg, dest, sujet, corps):
    """Envoi réel. Lève une exception en cas d'échec (capturée par l'appelant)."""
    msg = EmailMessage()
    from_name = cfg.get("from_name") or "L'enseignante"
    msg["From"] = formataddr((from_name, cfg["user"]))
    msg["To"] = dest
    msg["Subject"] = sujet
    msg.set_content(corps)
    port = int(cfg["port"])
    ctx = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(cfg["host"], port, context=ctx, timeout=20) as s:
            s.login(cfg["user"], cfg["password"])
            s.send_message(msg)
    else:
        with smtplib.SMTP(cfg["host"], port, timeout=20) as s:
            if cfg.get("tls", True):
                s.starttls(context=ctx)
            s.login(cfg["user"], cfg["password"])
            s.send_message(msg)


def register(app):
    from flask import jsonify, request

    _init()

    try:
        from prof_routes import require_token
    except Exception:  # pragma: no cover

        def require_token(f):
            return f

    def _body():
        return request.get_json(force=True, silent=True) or {}

    @app.route("/api/mail/config", methods=["GET"])
    @require_token
    def mail_config_get():
        cfg = _get_cfg()
        return jsonify(
            {
                "host": cfg.get("host", ""),
                "port": cfg.get("port", 587),
                "user": cfg.get("user", ""),
                "from_name": cfg.get("from_name", ""),
                "tls": cfg.get("tls", True),
                "configured": _cfg_ready(cfg),
                "password_set": bool(cfg.get("password")),
                "presets": sorted(PRESETS.keys()),
            }
        )

    @app.route("/api/mail/config", methods=["POST"])
    @require_token
    def mail_config_set():
        d = _body()
        cfg = _get_cfg()
        preset = str(d.get("preset", "")).lower().strip()
        if preset in PRESETS:
            cfg.update(PRESETS[preset])
        for k in ("host", "from_name", "user"):
            if d.get(k) is not None:
                cfg[k] = str(d[k])[:200]
        if d.get("port"):
            cfg["port"] = int(d["port"])
        if "tls" in d:
            cfg["tls"] = bool(d["tls"])
        # mot de passe : on n'écrase pas s'il est vide (permet de modifier sans le retaper)
        if d.get("password"):
            cfg["password"] = str(d["password"])
        _save_cfg(cfg)
        return jsonify({"ok": True, "configured": _cfg_ready(cfg)})

    @app.route("/api/mail/send", methods=["POST"])
    @require_token
    def mail_send():
        d = _body()
        sujet = str(d.get("sujet", ""))[:300].strip()
        corps = str(d.get("corps", ""))[:20000].strip()
        eleve_id = d.get("eleve_id")
        dest = str(d.get("dest", "")).strip()
        # destinataire : explicite, sinon email_parent de l'élève
        if not dest and eleve_id:
            c = _conn()
            try:
                r = c.execute(
                    "SELECT email_parent FROM eleves WHERE id=?", (eleve_id,)
                ).fetchone()
                if r and r["email_parent"]:
                    dest = r["email_parent"].strip()
            finally:
                c.close()
        if not parseaddr(dest)[1] or "@" not in dest:
            return jsonify({"error": "Adresse destinataire manquante ou invalide"}), 400
        if not sujet or not corps:
            return jsonify({"error": "Sujet et corps requis"}), 400

        cfg = _get_cfg()
        dry = bool(d.get("dry_run")) or not _cfg_ready(cfg)
        statut, erreur = "envoye", None
        if dry:
            statut = "brouillon"  # pas de config → on n'envoie pas, on trace
        else:
            try:
                _send_smtp(cfg, dest, sujet, corps)
            except Exception as e:
                statut, erreur = "echec", str(e)[:500]

        c = _conn()
        try:
            cur = c.execute(
                "INSERT INTO mail_log(dest,sujet,corps,eleve_id,statut,erreur) "
                "VALUES(?,?,?,?,?,?)",
                (dest, sujet, corps, eleve_id, statut, erreur),
            )
            c.commit()
            mid = cur.lastrowid
        finally:
            c.close()

        if statut == "echec":
            return jsonify({"error": f"Échec d'envoi : {erreur}", "id": mid}), 502
        return jsonify(
            {
                "ok": True,
                "id": mid,
                "statut": statut,
                "dry_run": dry,
                "dest": dest,
                "info": "Aucune config SMTP : enregistré en brouillon, non envoyé."
                if dry
                else "Mail envoyé.",
            }
        )

    @app.route("/api/mail/test", methods=["POST"])
    @require_token
    def mail_test():
        cfg = _get_cfg()
        if not _cfg_ready(cfg):
            return jsonify(
                {"error": "Configure d'abord le SMTP (host/user/password)"}
            ), 400
        try:
            _send_smtp(
                cfg,
                cfg["user"],
                "Test Pousseline ✅",
                "Ceci est un mail de test envoyé depuis ton app Pousseline. "
                "Si tu le reçois, l'envoi automatique des mails parents fonctionne.",
            )
        except Exception as e:
            return jsonify({"error": str(e)[:500]}), 502
        return jsonify({"ok": True, "info": f"Mail de test envoyé à {cfg['user']}"})

    @app.route("/api/mail/log", methods=["GET"])
    @require_token
    def mail_log_list():
        c = _conn()
        try:
            rows = [
                dict(r)
                for r in c.execute(
                    "SELECT id,dest,sujet,eleve_id,statut,erreur,created_at "
                    "FROM mail_log ORDER BY id DESC LIMIT 100"
                )
            ]
        finally:
            c.close()
        return jsonify(rows)

    print("[mailer] module chargé (/api/mail/config|send|test|log)")
