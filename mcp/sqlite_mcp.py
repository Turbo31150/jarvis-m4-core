#!/usr/bin/env python3
"""
sqlite_mcp.py — Serveur MCP SQLite stdio natif haute performance (0 dépendance externe).
"""
import sys, json, sqlite3, os, argparse

parser = argparse.ArgumentParser()
parser.add_argument("--db-path", required=True)
args = parser.parse_args()
DB_PATH = os.path.expanduser(args.db_path)

def execute_query(sql):
    if not os.path.exists(DB_PATH):
        return f"Erreur: Base {DB_PATH} introuvable"
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute(sql)
        if sql.strip().upper().startswith("SELECT") or sql.strip().upper().startswith("PRAGMA"):
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
            con.close()
            return json.dumps({"columns": cols, "rows": rows[:100]}, indent=2, ensure_ascii=False)
        else:
            con.commit()
            changes = con.total_changes
            con.close()
            return f"Exécuté avec succès ({changes} modifications)."
    except Exception as e:
        return f"Erreur SQL: {e}"

def list_tables():
    if not os.path.exists(DB_PATH):
        return []
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        con.close()
        return tables
    except Exception:
        return []

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            req = json.loads(line)
        except Exception:
            continue

        method = req.get("method")
        msg_id = req.get("id")

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": f"sqlite-{os.path.basename(DB_PATH)}", "version": "1.0.0"}
                }
            }
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "query",
                            "description": f"Exécute une requête SQL en lecture/écriture sur la base {os.path.basename(DB_PATH)}.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"sql": {"type": "string", "description": "Requête SQL"}},
                                "required": ["sql"]
                            }
                        },
                        {
                            "name": "list_tables",
                            "description": f"Liste les tables de la base {os.path.basename(DB_PATH)}.",
                            "inputSchema": {"type": "object", "properties": {}}
                        }
                    ]
                }
            }
        elif method == "tools/call":
            params = req.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            if name == "query":
                out = execute_query(args.get("sql", ""))
            elif name == "list_tables":
                out = json.dumps(list_tables())
            else:
                out = f"Outil inconnu: {name}"

            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": out}]}
            }
        else:
            resp = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Method not found"}}

        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
