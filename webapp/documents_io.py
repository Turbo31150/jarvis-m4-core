#!/usr/bin/env python3
"""Module Documents I/O — consulter / ouvrir / modifier / enregistrer les fichiers
de ~/Documents DIRECTEMENT dans l'app (navigateur), sans dépendre de xdg-open
(cassé : Chrome --app avale les PDF, evince s'ouvre sur un display fantôme, et
rien ne marche depuis le PWA Android). Ici tout passe par HTTP → marche partout.

Routes :
- GET  /api/file?path=…          : sert le fichier (inline pour PDF/image/texte,
                                    téléchargement pour le reste) → CONSULTER/OUVRIR
- GET  /api/file-content?path=…  : renvoie le texte d'un fichier éditable → MODIFIER
- POST /api/file-save {path,text} : écrit le fichier (backup .bak) → ENREGISTRER

Sécurité : confinement strict à quelques racines (anti-traversal via resolve() +
is_relative_to), exécutables refusés, écriture limitée aux extensions texte,
protégé par le token prof (localhost exempté par le garde global de server.py).
RGPD : aucune donnée élève exposée hors des racines autorisées.
"""

import mimetypes
from pathlib import Path
from flask import jsonify, request, send_file, abort

# Racines autorisées (mêmes que /api/open)
ALLOWED = [
    (Path.home() / "Documents").resolve(),
    (Path.home() / "jarvis" / "webapp").resolve(),
    (Path.home() / "Téléchargements").resolve(),
]

# Exécutables / scripts : jamais servis ni écrits (anti-RCE)
DENY = {".desktop", ".sh", ".py", ".appimage", ".jar", ".bin", ".run", ".exe", ".so"}

# Fichiers texte éditables dans l'app (consultables ET modifiables)
TEXTE = {
    ".md",
    ".txt",
    ".csv",
    ".json",
    ".html",
    ".htm",
    ".xml",
    ".yaml",
    ".yml",
    ".log",
    ".ini",
    ".conf",
    ".tex",
    ".rst",
    ".org",
    ".markdown",
}
# Affichables directement par le navigateur (inline)
INLINE = TEXTE | {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp"}

MAX_EDIT = 3 * 1024 * 1024  # 3 Mo : garde-fou édition texte


def _resoudre(path: str):
    """Résout un chemin dans les racines autorisées, sinon None (anti-traversal)."""
    if not path:
        return None
    try:
        target = Path(path).resolve()
    except Exception:
        return None
    if not any(target.is_relative_to(r) for r in ALLOWED):
        return None
    if target.suffix.lower() in DENY:
        return None
    return target


def register(app):
    try:
        from prof_routes import require_token
    except Exception:

        def require_token(f):
            return f

    @app.route("/api/file")
    @require_token
    def api_file():
        target = _resoudre(request.args.get("path", ""))
        if not target or not target.is_file():
            abort(404)
        mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        inline = target.suffix.lower() in INLINE
        # texte → forcer un charset UTF-8 pour l'affichage correct des accents
        if target.suffix.lower() in TEXTE and mime.startswith("text"):
            mime += "; charset=utf-8"
        return send_file(
            str(target),
            mimetype=mime,
            as_attachment=not inline,
            download_name=target.name,
        )

    @app.route("/api/file-content")
    @require_token
    def api_file_content():
        target = _resoudre(request.args.get("path", ""))
        if not target or not target.is_file():
            return jsonify({"ok": False, "error": "introuvable"}), 404
        editable = target.suffix.lower() in TEXTE
        if not editable:
            return jsonify(
                {
                    "ok": True,
                    "editable": False,
                    "nom": target.name,
                    "url": f"/api/file?path={target}",
                }
            )
        try:
            if target.stat().st_size > MAX_EDIT:
                return jsonify({"ok": False, "error": "fichier trop volumineux"}), 413
            text = target.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return jsonify({"ok": False, "error": str(e)}), 500
        return jsonify(
            {
                "ok": True,
                "editable": True,
                "nom": target.name,
                "path": str(target),
                "text": text,
            }
        )

    @app.route("/api/file-save", methods=["POST"])
    @require_token
    def api_file_save():
        d = request.get_json(force=True, silent=True) or {}
        target = _resoudre(d.get("path", ""))
        if not target:
            return jsonify({"ok": False, "error": "chemin non autorisé"}), 403
        if target.suffix.lower() not in TEXTE:
            return jsonify({"ok": False, "error": "type non éditable"}), 403
        text = d.get("text", "")
        if not isinstance(text, str):
            return jsonify({"ok": False, "error": "contenu invalide"}), 400
        try:
            # backup avant écrasement (une seule copie de secours)
            if target.exists():
                target.with_suffix(target.suffix + ".bak").write_bytes(
                    target.read_bytes()
                )
            target.write_text(text, encoding="utf-8")
        except OSError as e:
            return jsonify({"ok": False, "error": str(e)}), 500
        return jsonify({"ok": True, "octets": len(text.encode("utf-8"))})

    print("[documents_io] module chargé (/api/file, /api/file-content, /api/file-save)")
