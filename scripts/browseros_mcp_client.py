#!/usr/bin/env python3
"""
browseros_mcp_client.py — Client MCP HTTP pour BrowserOS

Connecte au serveur MCP BrowserOS (port 9000 ou 9239) et expose toutes ses
capacités (40+ connecteurs : Gmail, Slack, GitHub, LinkedIn, Notion, Linear,
Google Calendar/Drive/Sheets, etc.).

Utilise le protocole JSON-RPC 2.0 sur HTTP.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from typing import Any

MCP_URL = os.environ.get("BROWSEROS_MCP_URL", "http://127.0.0.1:9003/mcp")
log = logging.getLogger("browseros-mcp")


class BrowserOSMCP:
    """Client minimal pour serveur MCP BrowserOS (HTTP JSON-RPC)."""

    def __init__(self, url: str = MCP_URL):
        self.url = url
        self.req_id = 0
        self.session_id: str | None = None

    def _rpc(
        self, method: str, params: dict | None = None, timeout: float = 30.0
    ) -> Any:
        self.req_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.req_id,
            "method": method,
            "params": params or {},
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        req = urllib.request.Request(
            self.url, data=body, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            sid = r.headers.get("Mcp-Session-Id")
            if sid:
                self.session_id = sid
            raw = r.read().decode()
            # Peut être SSE ou JSON brut
            for line in raw.splitlines():
                line = line.strip()
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data:"):
                    line = line[5:].strip()
                try:
                    data = json.loads(line)
                    if "error" in data:
                        raise RuntimeError(f"MCP error: {data['error']}")
                    if "result" in data:
                        return data["result"]
                except json.JSONDecodeError:
                    continue
            return None

    def initialize(self) -> dict:
        """Handshake MCP initial."""
        return self._rpc(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}},
                "clientInfo": {"name": "jarvis-li-watcher", "version": "2.0"},
            },
        )

    def list_tools(self) -> list[dict]:
        """Liste les outils MCP disponibles (53+ outils BrowserOS attendus)."""
        result = self._rpc("tools/list")
        return result.get("tools", []) if result else []

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        """Invoque un outil MCP."""
        return self._rpc("tools/call", {"name": name, "arguments": arguments or {}})

    def health(self) -> bool:
        """Test de joignabilité."""
        try:
            self.initialize()
            return True
        except Exception as e:
            log.debug(f"MCP health failed: {e}")
            return False


# ─── Helpers LinkedIn via BrowserOS MCP ──────────────────────────────────
def linkedin_open_inbox(mcp: BrowserOSMCP) -> dict:
    """Ouvre LinkedIn messaging via outil BrowserOS."""
    return mcp.call_tool("navigate", {"url": "https://www.linkedin.com/messaging/"})


def linkedin_get_inbox(mcp: BrowserOSMCP) -> str:
    """Récupère le texte de la page (incluant inbox)."""
    res = mcp.call_tool("get_page_text", {})
    if isinstance(res, dict):
        return (
            res.get("content", [{}])[0].get("text", "")
            if "content" in res
            else str(res)
        )
    return str(res)


# ─── CLI test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    import sys

    mcp = BrowserOSMCP()
    if not mcp.health():
        print(f"❌ MCP unreachable: {MCP_URL}")
        sys.exit(1)

    print(f"✅ MCP OK: {MCP_URL}")
    tools = mcp.list_tools()
    print(f"\n=== Outils MCP disponibles ({len(tools)}) ===")
    for t in tools[:50]:
        name = t.get("name", "?")
        desc = (t.get("description") or "")[:80]
        print(f"  • {name:35} — {desc}")
