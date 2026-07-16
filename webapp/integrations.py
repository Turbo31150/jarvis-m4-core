#!/usr/bin/env python3
"""Module Intégrations & API — tableau de bord de toutes les connexions de Pousseline.

Teste en réel l'état de chaque API/ressource et le retourne pour la vue « Intégrations ».
Lecture seule, on-demand (aucun timer). Ne révèle jamais les clés — seulement leur présence
et si le service répond. Aide à voir d'un coup ce qui est branché / à configurer.

- GET /api/integrations/etat : liste [{nom, categorie, etat, detail}] (etat: ok|cle_invalide|a_config|absent)
"""

import os
from flask import jsonify
import requests


def _ollama_local():
    try:
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
        n = len(r.json().get("models", [])) if r.ok else 0
        return (
            ("ok", f"{n} modèles (CPU, hors-ligne)")
            if r.ok
            else ("a_config", "hors service")
        )
    except requests.exceptions.RequestException:
        return ("absent", "Ollama non lancé")


def _ollama_cloud():
    k = os.environ.get("OLLAMA_API_KEY", "")
    if not k:
        return ("a_config", "clé absente")
    try:
        r = requests.post(
            "https://ollama.com/api/chat",
            headers={"Authorization": f"Bearer {k}"},
            json={
                "model": os.environ.get("OLLAMA_CLOUD_MODEL", "gpt-oss:120b"),
                "stream": False,
                "messages": [{"role": "user", "content": "ok"}],
            },
            timeout=25,
        )
        return (
            ("ok", "gpt-oss:120b (déporté, gratuit)")
            if r.ok
            else ("cle_invalide", f"HTTP {r.status_code}")
        )
    except requests.exceptions.RequestException:
        return ("a_config", "injoignable")


def _m1():
    host = os.environ.get("M1_HOST", "http://10.42.0.1:1234")
    try:
        r = requests.get(f"{host}/v1/models", timeout=3)
        return (
            ("ok", "LM Studio (câble direct)") if r.ok else ("a_config", "hors service")
        )
    except requests.exceptions.RequestException:
        return ("absent", "hors ligne (câble/réseau)")


def _gemini():
    k = os.environ.get("GEMINI_API_KEY", "")
    if not k:
        return ("a_config", "clé absente")
    try:
        r = requests.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            params={"key": k},
            timeout=15,
        )
        if r.ok:
            return ("ok", "Google Gemini (quota gratuit)")
        if r.status_code in (400, 403):
            return ("cle_invalide", "clé à renouveler (Google AI Studio)")
        return ("a_config", f"HTTP {r.status_code}")
    except requests.exceptions.RequestException:
        return ("a_config", "injoignable")


def _systeme_io():
    return (
        "ok" if os.environ.get("SYSTEME_IO_API_KEY") else "a_config",
        "ventes/formations"
        if os.environ.get("SYSTEME_IO_API_KEY")
        else "clé à configurer",
    )


def _cache():
    from pathlib import Path

    p = Path(__file__).resolve().parent / "ecole.db"
    return (
        ("ok", "réponses IA mémorisées (0 token)")
        if p.exists()
        else ("a_config", "base absente")
    )


CHECKS = [
    ("Cache IA (SQL)", "IA locale", _cache),
    ("Ollama local", "IA locale", _ollama_local),
    ("M1 LM Studio", "IA déportée", _m1),
    ("Ollama cloud", "IA déportée", _ollama_cloud),
    ("Google Gemini", "IA déportée", _gemini),
    ("systeme.io", "Business", _systeme_io),
]


def register(app):
    try:
        from prof_routes import require_token
    except Exception:

        def require_token(f):
            return f

    @app.route("/api/integrations/etat")
    @require_token
    def api_integrations():
        out = []
        for nom, cat, fn in CHECKS:
            try:
                etat, detail = fn()
            except Exception as e:
                etat, detail = "a_config", str(e)[:60]
            out.append({"nom": nom, "categorie": cat, "etat": etat, "detail": detail})
        return jsonify({"ok": True, "integrations": out})

    print("[integrations] module chargé (/api/integrations/etat)")
