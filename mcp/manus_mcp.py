#!/usr/bin/env python3
"""Serveur MCP JARVIS ↔ Manus API v2 (stdio, JSON-RPC 2.0).

Souverain : aucune dépendance tierce, la clé ne quitte jamais la machine.
Clé lue dans ~/.config/jarvis/manus.env (chmod 600) ou $MANUS_API_KEY.

Surface couverte : les 31 endpoints /v2/* (task, agent, project, skill,
connector, file, webhook, website, browser, usage) + un appel générique.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ENV_FILE = Path.home() / ".config" / "jarvis" / "manus.env"
BASE = "https://api.manus.ai/v2"
TIMEOUT = 120


def _load_env() -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env()
API_KEY = os.environ.get("MANUS_API_KEY", "")
DEFAULT_PROFILE = os.environ.get("MANUS_AGENT_PROFILE", "manus-1.6")

# endpoint -> méthode HTTP (source : open.manus.ai/docs/llms.txt, v2)
ENDPOINTS: dict[str, str] = {
    "agent.detail": "GET",
    "agent.list": "GET",
    "agent.update": "POST",
    "browser.onlineList": "GET",
    "connector.list": "GET",
    "file.detail": "GET",
    "file.delete": "POST",
    "file.upload": "POST",
    "project.list": "GET",
    "project.create": "POST",
    "skill.list": "GET",
    "task.detail": "GET",
    "task.list": "GET",
    "task.listMessages": "GET",
    "task.create": "POST",
    "task.sendMessage": "POST",
    "task.stop": "POST",
    "task.delete": "POST",
    "task.update": "POST",
    "task.confirmAction": "POST",
    "usage.availableCredits": "GET",
    "usage.list": "GET",
    "usage.teamLog": "GET",
    "usage.teamStatistic": "GET",
    "webhook.list": "GET",
    "webhook.publicKey": "GET",
    "webhook.create": "POST",
    "webhook.delete": "POST",
    "website.listCheckpoints": "GET",
    "website.status": "GET",
    "website.publish": "POST",
    "website.update": "POST",
}


def call(
    endpoint: str, params: dict[str, Any] | None = None, method: str | None = None
) -> dict[str, Any]:
    """Appelle un endpoint Manus v2. GET → query string, POST → body JSON."""
    if not API_KEY:
        return {"ok": False, "error": f"MANUS_API_KEY absente ({ENV_FILE})"}
    params = {k: v for k, v in (params or {}).items() if v is not None}
    verb = (method or ENDPOINTS.get(endpoint, "POST")).upper()
    url = f"{BASE}/{endpoint}"
    data = None
    if verb == "GET":
        if params:
            url += "?" + urllib.parse.urlencode(params, doseq=True)
    else:
        data = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=verb,
        headers={
            "x-manus-api-key": API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "jarvis-manus-mcp/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"ok": False, "http": exc.code, "body": body[:2000]}
    except Exception as exc:  # réseau, DNS, timeout
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"ok": False, "body": body[:2000]}


def _obj(**props: Any) -> dict[str, Any]:
    return {"type": "object", "properties": props}


_S = {"type": "string"}
_I = {"type": "integer"}

TOOLS: list[dict[str, Any]] = [
    {
        "name": "manus_task_create",
        "description": "Crée une tâche Manus (agent autonome). Retourne task_id et l'URL de suivi.",
        "inputSchema": {
            **_obj(
                prompt={**_S, "description": "Consigne donnée à l'agent Manus"},
                agent_profile={
                    **_S,
                    "description": f"Profil agent (défaut {DEFAULT_PROFILE})",
                },
                mode={**_S, "description": "chat | agent"},
                project_id=_S,
                connectors={"type": "array", "items": _S},
            ),
            "required": ["prompt"],
        },
    },
    {
        "name": "manus_task_send",
        "description": "Envoie un message de suivi dans une tâche existante. Astuce : task_id='agent-default-main_task' parle à l'agent IM par défaut.",
        "inputSchema": {
            **_obj(task_id=_S, prompt=_S, connectors={"type": "array", "items": _S}),
            "required": ["task_id", "prompt"],
        },
    },
    {
        "name": "manus_task_messages",
        "description": "Lit les messages d'une tâche (polling de la réponse de l'agent).",
        "inputSchema": {
            **_obj(task_id=_S, limit=_I, order={**_S, "description": "asc | desc"}),
            "required": ["task_id"],
        },
    },
    {
        "name": "manus_task_detail",
        "description": "État détaillé d'une tâche (statut, événements d'attente, livrables).",
        "inputSchema": {**_obj(task_id=_S), "required": ["task_id"]},
    },
    {
        "name": "manus_task_list",
        "description": "Liste les tâches. scope='agent_subtask' + agent_id pour les sous-tâches d'un agent.",
        "inputSchema": _obj(scope=_S, agent_id=_S, project_id=_S, limit=_I),
    },
    {
        "name": "manus_task_stop",
        "description": "Arrête une tâche en cours.",
        "inputSchema": {**_obj(task_id=_S), "required": ["task_id"]},
    },
    {
        "name": "manus_task_confirm",
        "description": "Répond à un événement d'attente (validation, choix de navigateur via client_id...).",
        "inputSchema": {
            **_obj(task_id=_S, action=_S, client_id=_S, payload={"type": "object"}),
            "required": ["task_id"],
        },
    },
    {
        "name": "manus_agents",
        "description": "Liste les agents personnalisés du compte Manus.",
        "inputSchema": _obj(),
    },
    {
        "name": "manus_connectors",
        "description": "Liste les connecteurs installés (Slack, HubSpot, Zoom, Meta Ads, MCP...).",
        "inputSchema": _obj(),
    },
    {
        "name": "manus_skills",
        "description": "Liste les skills disponibles côté Manus.",
        "inputSchema": _obj(),
    },
    {
        "name": "manus_credits",
        "description": "Crédits Manus restants — à sonder AVANT de lancer une tâche coûteuse.",
        "inputSchema": _obj(),
    },
    {
        "name": "manus_webhook_create",
        "description": "Enregistre un webhook Manus (notifications temps réel vers JARVIS).",
        "inputSchema": {
            **_obj(url=_S, events={"type": "array", "items": _S}),
            "required": ["url"],
        },
    },
    {
        "name": "manus_webhook_list",
        "description": "Liste les webhooks enregistrés.",
        "inputSchema": _obj(),
    },
    {
        "name": "manus_call",
        "description": (
            "Appel générique de n'importe quel endpoint Manus v2 "
            "(échappatoire : " + ", ".join(sorted(ENDPOINTS)) + ")."
        ),
        "inputSchema": {
            **_obj(
                endpoint=_S,
                params={"type": "object"},
                method={**_S, "description": "GET | POST (auto sinon)"},
            ),
            "required": ["endpoint"],
        },
    },
]

_MAP = {
    "manus_task_detail": ("task.detail", None),
    "manus_task_list": ("task.list", None),
    "manus_task_stop": ("task.stop", None),
    "manus_task_confirm": ("task.confirmAction", None),
    "manus_agents": ("agent.list", None),
    "manus_connectors": ("connector.list", None),
    "manus_skills": ("skill.list", None),
    "manus_credits": ("usage.availableCredits", None),
    "manus_webhook_create": ("webhook.create", None),
    "manus_webhook_list": ("webhook.list", None),
}


def dispatch(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "manus_task_create":
        return call(
            "task.create",
            {
                "message": {"content": args["prompt"]},
                "agent_profile": args.get("agent_profile", DEFAULT_PROFILE),
                "mode": args.get("mode"),
                "project_id": args.get("project_id"),
                "connectors": args.get("connectors"),
            },
        )
    if name == "manus_task_send":
        return call(
            "task.sendMessage",
            {
                "task_id": args["task_id"],
                "message": {"content": args["prompt"]},
                "connectors": args.get("connectors"),
            },
        )
    if name == "manus_task_messages":
        return call(
            "task.listMessages",
            {
                "task_id": args["task_id"],
                "limit": args.get("limit", 20),
                "order": args.get("order", "desc"),
            },
        )
    if name == "manus_call":
        return call(args["endpoint"], args.get("params"), args.get("method"))
    if name in _MAP:
        return call(_MAP[name][0], args)
    return {"ok": False, "error": f"outil inconnu: {name}"}


def _send(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        method, mid = msg.get("method"), msg.get("id")
        if method == "initialize":
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": mid,
                    "result": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "jarvis-manus", "version": "1.0.0"},
                    },
                }
            )
        elif method == "tools/list":
            _send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            params = msg.get("params", {})
            try:
                out = dispatch(params.get("name", ""), params.get("arguments") or {})
            except Exception as exc:  # ne jamais tuer le serveur
                out = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": mid,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(out, ensure_ascii=False, indent=2),
                            }
                        ],
                        "isError": not out.get("ok", True),
                    },
                }
            )
        elif mid is not None:
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": mid,
                    "error": {"code": -32601, "message": f"method not found: {method}"},
                }
            )


if __name__ == "__main__":
    main()
