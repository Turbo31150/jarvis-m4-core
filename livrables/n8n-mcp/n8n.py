#!/usr/bin/env python3
"""n8n.py — Outils MCP pour piloter l'instance n8n locale de JARVIS.

Expose trois fonctions réutilisables par un serveur MCP (ou en CLI) :

    - list_workflows()            : liste les workflows (id, name, active, tags)
    - get_workflow(workflow_id)   : détail complet d'un workflow
    - trigger_workflow(id, payload): déclenche un workflow via son webhook

Conception :
    - Stdlib uniquement (urllib, json, os) — aucun paquet tiers requis.
    - Aucun secret en dur. Le jeton d'API n8n est lu dans la variable
      d'environnement N8N_API_KEY (jamais journalisé ni renvoyé).
    - Aucune exception ne remonte : si n8n est injoignable, on renvoie un
      dict {"ok": False, "error": ..., "hint": ...} avec un message actionnable.

URL par défaut : http://127.0.0.1:5678  (surchargée par N8N_BASE_URL).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

# --- Configuration (aucun secret ici) ---------------------------------------
N8N_BASE_URL: str = os.environ.get("N8N_BASE_URL", "http://127.0.0.1:5678").rstrip("/")
API_V1: str = "/api/v1"
_TIMEOUT: int = int(os.environ.get("N8N_TIMEOUT", "30"))

_DOWN_HINT: str = (
    "n8n semble injoignable. Vérifie que le service tourne "
    f"(curl -s {N8N_BASE_URL}/healthz), qu'il écoute bien sur {N8N_BASE_URL}, "
    "puis relance. Pour l'API REST, exporte un jeton : "
    "export N8N_API_KEY=... (Settings > n8n API dans l'UI)."
)
_AUTH_HINT: str = (
    "Accès refusé par l'API n8n. Le jeton N8N_API_KEY est absent, expiré ou "
    "invalide. Génère-en un dans l'UI n8n (Settings > n8n API) puis "
    "export N8N_API_KEY=<jeton>. Le jeton n'est jamais affiché."
)


def _api_key() -> str:
    """Retourne le jeton n8n depuis l'environnement (chaîne vide si absent)."""
    return os.environ.get("N8N_API_KEY", "").strip()


def _request(
    path: str,
    method: str = "GET",
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Appelle l'API n8n. Ne lève jamais : renvoie un dict normalisé.

    Retour : {"ok": bool, "status": int, "data"|"error": ..., "hint"?: str}
    """
    url = f"{N8N_BASE_URL}{path}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    key = _api_key()
    if key:
        headers["X-N8N-API-KEY"] = key

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw) if raw else {}
            return {"ok": True, "status": resp.status, "data": parsed}
    except urllib.error.HTTPError as exc:
        # Réponse HTTP d'erreur (401/403/404/500...) — message actionnable.
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:  # noqa: BLE001 — lecture best-effort du corps d'erreur
            detail = ""
        out: dict[str, Any] = {
            "ok": False,
            "status": exc.code,
            "error": f"HTTP {exc.code}: {exc.reason}",
            "detail": detail,
        }
        if exc.code in (401, 403):
            out["hint"] = _AUTH_HINT
        elif exc.code == 404:
            out["hint"] = (
                "Ressource introuvable. Vérifie l'identifiant du workflow "
                "(list_workflows) ou le chemin du webhook."
            )
        return out
    except urllib.error.URLError as exc:
        # n8n éteint / port fermé / DNS — on n'a jamais crashé.
        return {
            "ok": False,
            "status": 0,
            "error": f"Connexion échouée: {exc.reason}",
            "hint": _DOWN_HINT,
        }
    except (TimeoutError, OSError) as exc:
        return {"ok": False, "status": 0, "error": f"Réseau: {exc}", "hint": _DOWN_HINT}
    except json.JSONDecodeError as exc:
        return {"ok": False, "status": 0, "error": f"Réponse n8n illisible: {exc}"}


# --- API publique (outils MCP) ----------------------------------------------
def list_workflows() -> dict[str, Any]:
    """Liste les workflows n8n.

    Retour : {"ok": True, "count": int, "workflows": [{id, name, active, tags}]}
             ou {"ok": False, "error": ..., "hint": ...} si n8n est down.
    """
    res = _request(f"{API_V1}/workflows")
    if not res["ok"]:
        return res
    payload = res["data"]
    items = payload.get("data", payload) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return {
            "ok": False,
            "status": res["status"],
            "error": "Format de réponse inattendu.",
        }
    workflows = [
        {
            "id": wf.get("id"),
            "name": wf.get("name"),
            "active": wf.get("active"),
            "tags": [t.get("name") for t in wf.get("tags", []) if isinstance(t, dict)],
        }
        for wf in items
        if isinstance(wf, dict)
    ]
    return {"ok": True, "count": len(workflows), "workflows": workflows}


def get_workflow(workflow_id: str) -> dict[str, Any]:
    """Retourne le détail complet d'un workflow (nodes, connexions, settings).

    Args:
        workflow_id: identifiant n8n du workflow (voir list_workflows).
    """
    wid = str(workflow_id).strip()
    if not wid:
        return {"ok": False, "status": 0, "error": "workflow_id manquant."}
    res = _request(f"{API_V1}/workflows/{wid}")
    if not res["ok"]:
        return res
    return {"ok": True, "workflow": res["data"]}


def trigger_workflow(
    workflow_id: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Déclenche un workflow via son webhook.

    n8n déclenche les workflows par webhook, pas par l'API REST /workflows.
    `workflow_id` doit donc être le CHEMIN du webhook (le "path" du node
    Webhook), pas forcément l'id interne. On tente d'abord /webhook/<path>
    (production) puis /webhook-test/<path> (mode test de l'éditeur).

    Args:
        workflow_id: chemin du webhook (ex. "mon-workflow" pour
            http://127.0.0.1:5678/webhook/mon-workflow).
        payload: corps JSON transmis au workflow (optionnel).
    """
    path = str(workflow_id).strip().lstrip("/")
    if not path:
        return {
            "ok": False,
            "status": 0,
            "error": "workflow_id (chemin webhook) manquant.",
        }

    body = payload if payload is not None else {}
    prod = _request(f"/webhook/{path}", method="POST", data=body)
    if prod["ok"]:
        return {"ok": True, "mode": "production", "result": prod["data"]}

    # Si le webhook prod n'existe pas (404), essaie le webhook de test.
    if prod.get("status") == 404:
        test = _request(f"/webhook-test/{path}", method="POST", data=body)
        if test["ok"]:
            return {"ok": True, "mode": "test", "result": test["data"]}
        prod = test  # remonter l'erreur la plus parlante

    prod.setdefault(
        "hint",
        "Le workflow doit être ACTIF et contenir un node Webhook dont le "
        "'path' correspond à workflow_id. En mode test, ouvre l'éditeur et "
        "clique 'Listen for test event' avant de déclencher.",
    )
    return prod


# --- CLI de vérification (ne déclenche rien sans argument explicite) ---------
def _main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Outils n8n pour JARVIS (MCP/CLI).")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list", help="Lister les workflows")
    g = sub.add_parser("get", help="Détail d'un workflow")
    g.add_argument("id")
    t = sub.add_parser("trigger", help="Déclencher un workflow (webhook)")
    t.add_argument("id", help="Chemin du webhook")
    t.add_argument("--payload", default="{}", help="Corps JSON (défaut: {})")
    args = ap.parse_args()

    if args.cmd == "list":
        out = list_workflows()
    elif args.cmd == "get":
        out = get_workflow(args.id)
    elif args.cmd == "trigger":
        try:
            data = json.loads(args.payload)
        except json.JSONDecodeError as exc:
            out = {"ok": False, "error": f"--payload JSON invalide: {exc}"}
        else:
            out = trigger_workflow(args.id, data)
    else:
        ap.print_help()
        return
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
