#!/usr/bin/env python3
"""
perplexity_mcp.py — Serveur MCP & Connecteur Personnalisé JARVIS ↔ Perplexity AI
Permet aux agents (Claude Code, Manus, Antigravity) d'effectuer des recherches sémantiques web
et des synthèses documentaires haute fidélité via l'API Perplexity / Sonar.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from typing import Any

ENV_FILE = os.path.expanduser("~/.config/jarvis/perplexity.env")
API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")

if not API_KEY and os.path.exists(ENV_FILE):
    for line in open(ENV_FILE):
        line = line.strip()
        if line.startswith("PERPLEXITY_API_KEY="):
            API_KEY = line.split("=", 1)[1].strip()

TOOLS: list[dict[str, Any]] = [
    {
        "name": "perplexity_search",
        "description": "Effectue une recherche en direct sur le web avec citations et raisonnement (modèles Sonar).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "La requête de recherche en langage naturel"},
                "model": {
                    "type": "string",
                    "description": "sonar | sonar-pro | sonar-reasoning (défaut sonar)",
                    "default": "sonar"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "perplexity_deep_research",
        "description": "Recherche approfondie multi-sources avec raisonnement poussé (sonar-reasoning / deep research).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Sujet complexe d'investigation ou de benchmark"}
            },
            "required": ["topic"]
        }
    }
]

def query_perplexity(prompt: str, model: str = "sonar") -> dict[str, Any]:
    if not API_KEY:
        return {
            "ok": False,
            "error": "Clé PERPLEXITY_API_KEY non configurée dans l'environnement ou ~/.config/jarvis/perplexity.env",
            "fallback_info": "Mode local actif. Utilisez Board OS (88k chunks) ou mistral-rag en local."
        }
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Tu es un assistant de recherche précis, technique et concis."},
            {"role": "user", "content": prompt}
        ]
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            citations = data.get("citations", [])
            return {"ok": True, "answer": content, "citations": citations}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def dispatch(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "perplexity_search":
        return query_perplexity(args.get("query", ""), model=args.get("model", "sonar"))
    if name == "perplexity_deep_research":
        return query_perplexity(f"Effectue une recherche approfondie et structurée sur : {args.get('topic', '')}", model="sonar-reasoning")
    return {"ok": False, "error": f"Outil inconnu : {name}"}

def _send(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()

def main():
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
            _send({
                "jsonrpc": "2.0",
                "id": mid,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "jarvis-perplexity", "version": "1.0.0"}
                }
            })
        elif method == "tools/list":
            _send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            params = msg.get("params", {})
            try:
                out = dispatch(params.get("name", ""), params.get("arguments") or {})
            except Exception as e:
                out = {"ok": False, "error": str(e)}
            _send({
                "jsonrpc": "2.0",
                "id": mid,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False, indent=2)}],
                    "isError": not out.get("ok", True)
                }
            })
        elif mid is not None:
            _send({
                "jsonrpc": "2.0",
                "id": mid,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            })

if __name__ == "__main__":
    main()
