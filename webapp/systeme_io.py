#!/usr/bin/env python3
"""Intégration OPTIONNELLE de systeme.io dans Pousseline.

Désactivée par défaut : rien ne se connecte tant que l'utilisatrice ne l'active
pas explicitement (toggle + clé API stockés en local dans ecole.db/kv, hors-Git).
Conçu comme socle extensible : un proxy générique vers l'API REST systeme.io
permet d'ajouter de nouveaux outils (contacts, tags, tunnels, emails…) sans
réécrire l'authentification à chaque fois — il suffit d'exposer une route qui
appelle `_call(method, path, ...)`.

register(app) branché par server.py. Protégé par le garde global @before_request
(token sur tout /api/ hors localhost). Réversible : retirer de la boucle server.py.
"""

import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

from flask import jsonify, request

ECOLE_DB = str(Path(__file__).resolve().parent / "ecole.db")
API_BASE = "https://api.systeme.io"  # API REST publique (clé X-API-Key)
CFG_KEY = "systeme_io_config"


def _conn():
    c = sqlite3.connect(ECOLE_DB)
    c.row_factory = sqlite3.Row
    return c


def _get_cfg():
    try:
        with _conn() as c:
            r = c.execute("SELECT v FROM kv WHERE k=?", (CFG_KEY,)).fetchone()
            return json.loads(r["v"]) if r and r["v"] else {}
    except Exception:
        return {}


def _save_cfg(cfg):
    with _conn() as c:
        c.execute(
            "INSERT INTO kv(k,v) VALUES(?,?) "
            "ON CONFLICT(k) DO UPDATE SET v=excluded.v, ts=datetime('now')",
            (CFG_KEY, json.dumps(cfg)),
        )
        c.commit()


def _enabled(cfg=None):
    cfg = cfg if cfg is not None else _get_cfg()
    return bool(cfg.get("enabled")) and bool(cfg.get("api_key"))


def _call(method, path, params=None, body=None, timeout=20):
    """Appel générique à l'API systeme.io. Lève RuntimeError si désactivé/erreur.

    method : GET/POST/PATCH/DELETE ; path : ex. '/api/contacts'.
    Renvoie (status_code, parsed_json|texte).
    """
    cfg = _get_cfg()
    if not _enabled(cfg):
        raise RuntimeError("systeme.io désactivé (active-le et renseigne la clé API)")
    url = API_BASE + path
    if params:
        from urllib.parse import urlencode

        url += ("&" if "?" in url else "?") + urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("X-API-Key", cfg["api_key"])
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(raw)
            except Exception:
                return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def register(app):
    @app.route("/api/systeme/config", methods=["GET"])
    def systeme_config_get():
        cfg = _get_cfg()
        return jsonify(
            {
                "enabled": bool(cfg.get("enabled")),
                "key_set": bool(cfg.get("api_key")),
                "ready": _enabled(cfg),
            }
        )

    @app.route("/api/systeme/config", methods=["POST"])
    def systeme_config_set():
        d = request.get_json(force=True, silent=True) or {}
        cfg = _get_cfg()
        if "enabled" in d:
            cfg["enabled"] = bool(d["enabled"])
        # la clé n'est écrasée que si une nouvelle valeur non vide est fournie
        if d.get("api_key"):
            cfg["api_key"] = str(d["api_key"]).strip()[:200]
        if d.get("clear_key"):
            cfg.pop("api_key", None)
        _save_cfg(cfg)
        return jsonify(
            {"ok": True, "enabled": bool(cfg.get("enabled")), "ready": _enabled(cfg)}
        )

    @app.route("/api/systeme/ping", methods=["POST"])
    def systeme_ping():
        """Teste la clé : un appel léger à l'API. Ne modifie rien."""
        try:
            status, payload = _call("GET", "/api/contacts", params={"limit": 10})
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 400
        ok = 200 <= status < 300
        return jsonify(
            {
                "ok": ok,
                "status": status,
                "info": "Clé valide, connexion établie."
                if ok
                else "Clé refusée ou API injoignable.",
            }
        )

    @app.route("/api/systeme/proxy", methods=["POST"])
    def systeme_proxy():
        """Proxy générique (socle des futurs outils). Body : {method, path, params, json}."""
        d = request.get_json(force=True, silent=True) or {}
        method = str(d.get("method", "GET")).upper()
        path = str(d.get("path", ""))
        if not path.startswith("/api/"):
            return jsonify({"error": "path doit commencer par /api/"}), 400
        if method not in ("GET", "POST", "PATCH", "DELETE"):
            return jsonify({"error": "méthode non autorisée"}), 400
        try:
            status, payload = _call(
                method, path, params=d.get("params"), body=d.get("json")
            )
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"status": status, "data": payload})

    print("[Pousseline] Module systeme.io (OPTIONNEL, désactivé par défaut) chargé")
