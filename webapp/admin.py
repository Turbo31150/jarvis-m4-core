#!/usr/bin/env python3
"""Module Dashboard Admin — état consolidé de Pousseline en un coup d'œil.

Regroupe (demandé par l'audit) : backends IA (up/down + modèle actif), bases de
données, dernières sauvegardes, thermique. Lecture seule, on-demand (aucun timer →
0 risque thermique). Aide la prof non-technique à voir si tout va bien.

- GET /api/admin/etat : JSON agrégé pour l'encart Admin de l'onglet Système.
"""

import sqlite3
from pathlib import Path
from flask import jsonify

BASE = Path(__file__).resolve().parent


def _cpu_temp():
    try:
        t = int(Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip())
        return round(t / 1000)
    except (OSError, ValueError):
        return None


def _base_info(nom):
    p = BASE / nom
    if not p.exists():
        return {"nom": nom, "present": False}
    try:
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        n = con.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]
        con.close()
    except sqlite3.Error:
        n = None
    return {
        "nom": nom,
        "present": True,
        "ko": max(1, p.stat().st_size // 1024),
        "tables": n,
    }


def _backends():
    """État des backends IA sans bloquer : réutilise la sonde d'ai_local."""
    out = []
    try:
        import ai_local

        for label, url in (
            ("M1 (LM Studio)", ai_local.M1),
            ("M2 (LM Studio)", ai_local.M2),
        ):
            up = ai_local._up(url)
            out.append(
                {
                    "nom": label,
                    "up": up,
                    "modele": ai_local._pick_chat_model(url) if up else None,
                }
            )
        out.append(
            {
                "nom": "Ollama local",
                "up": ai_local._up(ai_local.OLLAMA),
                "modele": "CPU (gemma3/qwen)",
            }
        )
        out.append(
            {
                "nom": "Ollama cloud",
                "up": True,
                "modele": getattr(ai_local, "OLLAMA_CLOUD_MODEL", "gpt-oss:120b"),
            }
        )
    except Exception as e:  # pragma: no cover
        out.append({"nom": "cascade IA", "up": False, "modele": f"erreur: {e}"})
    return out


def register(app):
    try:
        from prof_routes import require_token
    except Exception:

        def require_token(f):
            return f

    @app.route("/api/admin/etat")
    @require_token
    def api_admin_etat():
        bdir = BASE / "backups"
        snaps = sorted(bdir.glob("ecole-*.db")) if bdir.exists() else []
        return jsonify(
            {
                "ok": True,
                "cpu_temp": _cpu_temp(),
                "backends": _backends(),
                "bases": [_base_info("ecole.db"), _base_info("notes.db")],
                "sauvegardes": {
                    "total": len(snaps),
                    "derniere": snaps[-1].name if snaps else None,
                },
            }
        )

    print("[admin] module chargé (/api/admin/etat)")
