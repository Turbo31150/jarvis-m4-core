#!/usr/bin/env python3
"""MCP server for safe discovery of the JARVIS shared document roots.

This server is deliberately read-only. It can inventory, search, inspect, and
prepare conversion plans; it cannot run requests, execute commands, or alter a
file. That separation makes it suitable for a private OpenAI tunnel.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from catalog import CatalogError, SOURCES, is_text_file, iter_files, redact, resolve

app = Server("jarvis-common")
MAX_FILE_BYTES = 1_000_000


def text(payload: object) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]


def tool(name: str, description: str, properties: dict, required: list[str] | None = None) -> Tool:
    return Tool(
        name=name,
        description=description,
        inputSchema={"type": "object", "properties": properties, "required": required or []},
        annotations={"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    )


@app.list_tools()
async def list_tools() -> list[Tool]:
    source = {"type": "string", "enum": sorted(SOURCES), "description": "Racine JARVIS à consulter."}
    return [
        tool("list_sources", "Lister les sources JARVIS et leurs règles d'accès.", {}),
        tool("list_files", "Inventorier les fichiers d'une source non restreinte.", {"source": source, "path": {"type": "string", "default": ""}, "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 100}}, ["source"]),
        tool("search_text", "Rechercher du texte dans des fichiers textuels non sensibles.", {"source": source, "query": {"type": "string", "minLength": 2}, "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20}}, ["source", "query"]),
        tool("inspect_file", "Lire un fichier textuel autorisé, avec secrets masqués.", {"source": source, "path": {"type": "string"}, "max_chars": {"type": "integer", "minimum": 100, "maximum": 20000, "default": 8000}}, ["source", "path"]),
        tool("plan_conversion", "Préparer une conversion sans écrire de fichier.", {"source": source, "path": {"type": "string"}, "target_format": {"type": "string", "enum": ["markdown", "json", "text", "html", "csv"]}}, ["source", "path", "target_format"]),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "list_sources":
            return text({"sources": [{"name": s.name, "description": s.description, "available": s.path.is_dir(), "access": "restricted" if s.restricted else "read_only"} for s in SOURCES.values()]})

        source_name = arguments["source"]
        if name == "list_files":
            root = resolve(source_name, arguments.get("path", ""))
            if root.is_file():
                paths = [root]
            else:
                paths = list(iter_files(root))
            limit = min(arguments.get("limit", 100), 200)
            source_root = resolve(source_name)
            return text({"source": source_name, "files": [{"path": str(path.relative_to(source_root)), "bytes": path.stat().st_size, "text": is_text_file(path)} for path in paths[:limit]], "truncated": len(paths) > limit})

        if name == "search_text":
            root = resolve(source_name)
            needle = arguments["query"].casefold()
            limit = min(arguments.get("limit", 20), 50)
            matches = []
            for path in iter_files(root):
                if not is_text_file(path) or path.stat().st_size > MAX_FILE_BYTES:
                    continue
                try:
                    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                        if needle in line.casefold():
                            matches.append({"path": str(path.relative_to(root)), "line": number, "snippet": redact(line.strip())[:500]})
                            if len(matches) >= limit:
                                return text({"source": source_name, "matches": matches, "truncated": True})
                except OSError:
                    continue
            return text({"source": source_name, "matches": matches, "truncated": False})

        if name == "inspect_file":
            path = resolve(source_name, arguments["path"])
            if not is_text_file(path):
                raise CatalogError("Seuls les fichiers textuels autorisés peuvent être inspectés.")
            if path.stat().st_size > MAX_FILE_BYTES:
                raise CatalogError("Fichier trop volumineux pour une inspection MCP.")
            value = path.read_text(encoding="utf-8", errors="replace")
            maximum = min(arguments.get("max_chars", 8000), 20000)
            return text({"source": source_name, "path": arguments["path"], "content": redact(value[:maximum]), "truncated": len(value) > maximum})

        if name == "plan_conversion":
            path = resolve(source_name, arguments["path"])
            target = arguments["target_format"]
            if not is_text_file(path):
                raise CatalogError("La conversion planifiée est limitée aux formats textuels autorisés.")
            return text({"source": source_name, "input": arguments["path"], "target_format": target, "mode": "plan_only", "steps": ["Lire et valider le fichier source", "Parser selon son format détecté", f"Produire une prévisualisation {target}", "Demander une validation explicite avant toute écriture"], "writes_performed": False})

        return text({"error": f"Outil inconnu : {name}"})
    except (CatalogError, KeyError, OSError) as error:
        return text({"error": str(error)})


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
