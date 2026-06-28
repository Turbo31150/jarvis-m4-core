#!/usr/bin/env python3
"""Module Logiciels — cockpit unique de l'app école.

Registre JSON de logiciels (Wine / natifs / web) lançables depuis la PWA.
register(app) branche les routes /api/logiciels* sur le serveur Flask existant.
Réversible : supprimer l'import dans server.py suffit.
"""

import json
import os
import subprocess
from pathlib import Path

BASE = Path("/home/pamerys/jarvis/webapp")
LOG_DIR = BASE / "logiciels"  # installeurs + données
REGISTRY = LOG_DIR / "registry.json"
PREFIX = Path.home() / ".wine-ecole"  # préfixe Wine dédié (32 bits)
DISPLAY = os.environ.get("DISPLAY", ":0")

# Registre par défaut (créé au premier lancement, puis éditable)
DEFAULT = [
    {
        "id": "generation5",
        "nom": "Génération 5",
        "icon": "🎓",
        "categorie": "Pédagogie",
        "type": "wine",
        "exe": "",
        "installer": "",
        "url": "https://www.generation5.fr/",
        "statut": "a_telecharger",
        "note": "Télécharger le titre exact depuis generation5.fr puis l'installer ici.",
    },
    {
        "id": "biblio_manuels",
        "nom": "Biblio Manuels (Belin)",
        "icon": "📚",
        "categorie": "Manuels",
        "type": "wine",
        "exe": "",
        "installer": "/home/pamerys/jarvis/webapp/logiciels/install_biblio_manuels.exe",
        "url": "",
        "statut": "installable",
        "note": "Manuels numériques Belin (Adobe AIR). Installeur déjà récupéré du Drive.",
    },
    {
        "id": "readwrite",
        "nom": "Read&Write",
        "icon": "🗣️",
        "categorie": "Accessibilité",
        "type": "wine",
        "exe": "",
        "installer": "",
        "url": "",
        "statut": "a_copier",
        "note": "Aide à la lecture (Texthelp). À copier depuis le Drive de Claire.",
    },
    {
        "id": "photofiltre",
        "nom": "PhotoFiltre",
        "icon": "🖼️",
        "categorie": "Image",
        "type": "wine",
        "exe": "",
        "installer": "",
        "url": "",
        "statut": "a_copier",
        "note": "Retouche d'images. Installeur photofiltre11.4.1_fr_setup.exe dans le Drive.",
    },
]


def _load():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not REGISTRY.exists():
        REGISTRY.write_text(json.dumps(DEFAULT, ensure_ascii=False, indent=2))
    return json.loads(REGISTRY.read_text())


def _save(data):
    REGISTRY.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def _wine_env():
    env = {
        **os.environ,
        "WINEPREFIX": str(PREFIX),
        "WINEARCH": "win32",
        "DISPLAY": DISPLAY,
        "WINEDEBUG": "-all",
    }
    return env


def _wine_ready():
    return bool(subprocess.run(["which", "wine"], capture_output=True).stdout.strip())


def _enrich(app):
    """Calcule le statut réel (exe présent ?) sans modifier le registre."""
    a = dict(app)
    exe = a.get("exe", "")
    inst = a.get("installer", "")
    if exe and os.path.exists(exe):
        a["statut"] = "pret"
    elif inst and os.path.exists(inst):
        a["statut"] = "installable"
    a["wine_ready"] = _wine_ready()
    return a


def register(app):
    from flask import jsonify, request

    @app.route("/api/logiciels")
    def api_logiciels():
        return jsonify([_enrich(x) for x in _load()])

    @app.route("/api/logiciels/launch", methods=["POST"])
    def api_logiciels_launch():
        d = request.get_json(force=True)
        lid = d.get("id", "")
        item = next((x for x in _load() if x["id"] == lid), None)
        if not item:
            return jsonify({"ok": False, "error": "inconnu"}), 404
        typ = item.get("type")
        if typ == "web" and item.get("url"):
            return jsonify({"ok": True, "open_url": item["url"]})
        if typ == "native":
            tgt = item.get("exe") or item.get("url")
            subprocess.Popen(["xdg-open", tgt], env={**os.environ, "DISPLAY": DISPLAY})
            return jsonify({"ok": True})
        # wine
        exe = item.get("exe", "")
        if not exe or not os.path.exists(exe):
            return jsonify(
                {"ok": False, "error": "exe absent — installer d'abord"}
            ), 400
        if not _wine_ready():
            return jsonify({"ok": False, "error": "Wine pas encore prêt"}), 503
        subprocess.Popen(
            ["wine", exe], env=_wine_env(), cwd=os.path.dirname(exe) or None
        )
        return jsonify({"ok": True})

    @app.route("/api/logiciels/install", methods=["POST"])
    def api_logiciels_install():
        d = request.get_json(force=True)
        lid = d.get("id", "")
        item = next((x for x in _load() if x["id"] == lid), None)
        if not item:
            return jsonify({"ok": False, "error": "inconnu"}), 404
        inst = item.get("installer", "")
        if not inst or not os.path.exists(inst):
            return jsonify({"ok": False, "error": "installeur absent"}), 400
        if not _wine_ready():
            return jsonify({"ok": False, "error": "Wine pas encore prêt"}), 503
        PREFIX.mkdir(parents=True, exist_ok=True)
        log = LOG_DIR / f"install-{lid}.log"
        with open(log, "w") as fh:
            subprocess.Popen(
                ["wine", inst],
                env=_wine_env(),
                stdout=fh,
                stderr=fh,
                cwd=os.path.dirname(inst) or None,
            )
        return jsonify({"ok": True, "log": str(log)})

    return app
