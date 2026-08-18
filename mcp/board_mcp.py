#!/usr/bin/env python3
"""MCP stdio — Board OS JARVIS (Bibliothèque Vivante + table ronde).

Outils :
  board_domains  : liste les domaines indexés (SQL pur, 0 token)
  board_search   : recherche FTS5 dans les chunks (SQL pur, 0 token)
  board_ask      : interroge un domaine via board.py (backend M6, 0 token facturé)
  table_ronde    : débat multi-moteurs via jarvis-table-ronde
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys

BOARD_DIR = "/home/pamerys/jarvis/board"
BOARD_DB = f"{BOARD_DIR}/board.db"
JARVIS_BOARD = "/home/pamerys/.local/bin/jarvis-board"
TABLE_RONDE = "/home/pamerys/.local/bin/jarvis-table-ronde"

TOOLS = [
    {
        "name": "board_domains",
        "description": "Liste les domaines du Board OS (0 token, lecture SQLite).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "board_search",
        "description": (
            "Recherche plein texte (FTS5) dans la Bibliothèque Vivante. "
            "0 token : aucune inférence, uniquement SQL. À utiliser AVANT toute inférence."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Requête FTS5"},
                "domain": {
                    "type": "string",
                    "description": "Filtre domaine (optionnel)",
                },
                "k": {"type": "integer", "default": 8},
            },
            "required": ["query"],
        },
    },
    {
        "name": "board_ask",
        "description": (
            "Interroge le conseil d'experts du domaine (backend LM Studio M6, 0 token facturé). "
            "Réponse sourcée avec citations [n] depuis le corpus."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Domaine cible (cf. board_domains)",
                },
                "question": {"type": "string"},
            },
            "required": ["domain", "question"],
        },
    },
    {
        "name": "table_ronde",
        "description": (
            "Table ronde multi-moteurs : sonde l'état des moteurs, ou lance un débat "
            "en 3 tours (avis indépendants → critique croisée → synthèse). Moteur muet = signalé, jamais simulé."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["sonde", "debat"],
                    "default": "sonde",
                },
                "sujet": {
                    "type": "string",
                    "description": "Sujet du débat (requis si action=debat)",
                },
            },
        },
    },
]


def _run(cmd: list[str], timeout: int = 240) -> str:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=BOARD_DIR
        )
        return (r.stdout + r.stderr).strip() or "(sortie vide)"
    except subprocess.TimeoutExpired:
        return f"TIMEOUT après {timeout}s : {' '.join(cmd)}"
    except Exception as exc:  # noqa: BLE001
        return f"ERREUR {type(exc).__name__}: {exc}"


def board_domains() -> str:
    db = sqlite3.connect(f"file:{BOARD_DB}?mode=ro", uri=True)
    rows = db.execute("select id, display_name from domains order by id").fetchall()
    db.close()
    return "\n".join(f"{i} — {n}" for i, n in rows)


def board_search(query: str, domain: str | None = None, k: int = 8) -> str:
    db = sqlite3.connect(f"file:{BOARD_DB}?mode=ro", uri=True)
    sql = (
        "select c.domain_id, snippet(chunks_fts, -1, '«', '»', '…', 24) "
        "from chunks_fts join chunks c on c.rowid = chunks_fts.rowid "
        "where chunks_fts match ?"
    )
    params: list = [query]
    if domain:
        sql += " and c.domain_id = ?"
        params.append(domain)
    sql += " order by rank limit ?"
    params.append(k)
    try:
        rows = db.execute(sql, params).fetchall()
    except sqlite3.Error as exc:
        return f"ERREUR FTS5 : {exc}"
    finally:
        db.close()
    if not rows:
        return "Aucun résultat dans la Bibliothèque Vivante."
    return "\n\n".join(f"[{i}] ({d}) {s}" for i, (d, s) in enumerate(rows, 1))


def dispatch(name: str, args: dict) -> str:
    if name == "board_domains":
        return board_domains()
    if name == "board_search":
        return board_search(args["query"], args.get("domain"), int(args.get("k", 8)))
    if name == "board_ask":
        return _run([JARVIS_BOARD, "ask", args["domain"], args["question"]])
    if name == "table_ronde":
        action = args.get("action", "sonde")
        if action == "debat":
            sujet = args.get("sujet")
            if not sujet:
                return "ERREUR : 'sujet' requis pour action=debat."
            return _run([TABLE_RONDE, "debat", sujet], timeout=600)
        return _run([TABLE_RONDE, "sonde"], timeout=60)
    return f"Outil inconnu : {name}"


def reply(mid, result=None, error=None) -> None:
    msg = {"jsonrpc": "2.0", "id": mid}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method, mid = req.get("method"), req.get("id")
        if method == "initialize":
            reply(
                mid,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "jarvis-board", "version": "1.0.0"},
                },
            )
        elif method == "tools/list":
            reply(mid, {"tools": TOOLS})
        elif method == "tools/call":
            p = req.get("params", {})
            out = dispatch(p.get("name", ""), p.get("arguments") or {})
            reply(mid, {"content": [{"type": "text", "text": out}]})
        elif mid is not None:
            reply(
                mid, error={"code": -32601, "message": f"Méthode inconnue : {method}"}
            )


if __name__ == "__main__":
    main()
