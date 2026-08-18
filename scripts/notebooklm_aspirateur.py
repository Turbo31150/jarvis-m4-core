#!/usr/bin/env python3
"""
notebooklm_aspirateur.py — Aspiration locale complète de NotebookLM via CDP.

Pilote un Chrome déjà authentifié (port 9222) pour extraire, sans API Google :
  - la liste de tous les notebooks du compte
  - pour chaque notebook : titre, sources, notes, résumés affichés

Tout est stocké en local dans SQLite (souverain, 0 token, réutilisable hors ligne).

Usage :
    notebooklm_aspirateur.py --list              # inventorie les notebooks
    notebooklm_aspirateur.py --all               # aspire tout le compte
    notebooklm_aspirateur.py --url <url>         # aspire un notebook précis

Prérequis : Chrome lancé avec --remote-debugging-port=9222 ET session Google active.
"""

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime

CDP = "http://127.0.0.1:9222"
DB = os.path.expanduser("~/jarvis/data/notebooklm_local.db")
TIMEOUT = 30


# ---------------------------------------------------------------- CDP minimal
def _http(path):
    with urllib.request.urlopen(f"{CDP}{path}", timeout=5) as r:
        return json.load(r)


def cdp_pages():
    return [t for t in _http("/json") if t.get("type") == "page"]


def cdp_eval(ws_url, expression, await_promise=True):
    """Évalue du JS dans l'onglet et renvoie le résultat sérialisé."""
    try:
        from websocket import create_connection  # websocket-client
    except ImportError:
        sys.exit("Manque websocket-client :  pip install --user websocket-client")

    ws = create_connection(ws_url, timeout=TIMEOUT)
    try:
        ws.send(
            json.dumps(
                {
                    "id": 1,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": expression,
                        "returnByValue": True,
                        "awaitPromise": await_promise,
                    },
                }
            )
        )
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == 1:
                result = msg.get("result", {}).get("result", {})
                if "value" in result:
                    return result["value"]
                # exceptionDetails => remonter l'erreur telle quelle
                return {"error": msg.get("result", {}).get("exceptionDetails")}
    finally:
        ws.close()


def navigate(ws_url, url):
    from websocket import create_connection

    ws = create_connection(ws_url, timeout=TIMEOUT)
    try:
        ws.send(
            json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": url}})
        )
        ws.recv()
    finally:
        ws.close()


# ---------------------------------------------------------------- extraction
# NotebookLM est une SPA Angular : on lit le DOM rendu, pas le HTML source.
JS_LIST_NOTEBOOKS = r"""
(() => {
  const out = [];
  document.querySelectorAll('a[href*="/notebook/"]').forEach(a => {
    const href = a.getAttribute('href') || '';
    const m = href.match(/\/notebook\/([0-9a-f-]{36})/i);
    if (!m) return;
    const title = (a.innerText || a.textContent || '').trim().split('\n')[0];
    if (!out.some(o => o.id === m[1])) out.push({id: m[1], title: title, href: href});
  });
  return JSON.stringify(out);
})()
"""

JS_DUMP_NOTEBOOK = r"""
(() => {
  const txt = el => (el ? (el.innerText || el.textContent || '').trim() : '');
  // Titres de sources : NotebookLM les rend dans la colonne de gauche.
  const sources = [];
  document.querySelectorAll(
    'source-list-item, [class*="source-item"], [role="listitem"]'
  ).forEach(el => {
    const t = txt(el);
    if (t && t.length < 300 && !sources.includes(t)) sources.push(t);
  });
  return JSON.stringify({
    title: txt(document.querySelector('h1')) || document.title,
    url: location.href,
    sources: sources,
    body: txt(document.body).slice(0, 200000)
  });
})()
"""


# ---------------------------------------------------------------- stockage
SCHEMA = """
CREATE TABLE IF NOT EXISTS notebooks (
    id           TEXT PRIMARY KEY,
    titre        TEXT,
    url          TEXT,
    aspire_le    TEXT,
    nb_sources   INTEGER
);
CREATE TABLE IF NOT EXISTS sources (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    notebook_id  TEXT,
    intitule     TEXT,
    UNIQUE(notebook_id, intitule)
);
CREATE TABLE IF NOT EXISTS contenus (
    notebook_id  TEXT PRIMARY KEY,
    texte        TEXT,
    aspire_le    TEXT
);
"""


def db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def enregistrer(conn, data, nb_id):
    now = datetime.now().isoformat(timespec="seconds")
    srcs = data.get("sources", [])
    conn.execute(
        "INSERT OR REPLACE INTO notebooks VALUES (?,?,?,?,?)",
        (nb_id, data.get("title"), data.get("url"), now, len(srcs)),
    )
    for s in srcs:
        conn.execute(
            "INSERT OR IGNORE INTO sources (notebook_id, intitule) VALUES (?,?)",
            (nb_id, s),
        )
    conn.execute(
        "INSERT OR REPLACE INTO contenus VALUES (?,?,?)",
        (nb_id, data.get("body", ""), now),
    )
    conn.commit()


# ---------------------------------------------------------------- pilotage
def onglet():
    pages = cdp_pages()
    if not pages:
        sys.exit("Aucun onglet CDP. Lance Chrome avec --remote-debugging-port=9222.")
    return pages[0]["webSocketDebuggerUrl"]


def verifier_auth(ws):
    url = cdp_eval(ws, "location.href", await_promise=False)
    if isinstance(url, str) and "accounts.google.com" in url:
        sys.exit(
            "NON AUTHENTIFIE : Chrome est sur la page de connexion Google.\n"
            "Connecte-toi dans cette fenetre, puis relance."
        )


def aspirer_un(conn, ws, url):
    nb_id = url.rstrip("/").split("/")[-1].split("?")[0]
    navigate(ws, url)
    time.sleep(8)  # laisser la SPA rendre
    verifier_auth(ws)
    raw = cdp_eval(ws, JS_DUMP_NOTEBOOK)
    if not isinstance(raw, str):
        print(f"  !! extraction vide pour {nb_id}")
        return None
    data = json.loads(raw)
    enregistrer(conn, data, nb_id)
    print(
        f"  OK {data.get('title', '(sans titre)')[:60]} — {len(data.get('sources', []))} sources, "
        f"{len(data.get('body', ''))} caracteres"
    )
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="inventorier les notebooks")
    ap.add_argument("--all", action="store_true", help="aspirer tout le compte")
    ap.add_argument("--url", help="aspirer un notebook precis")
    args = ap.parse_args()

    ws = onglet()
    conn = db()

    if args.url:
        aspirer_un(conn, ws, args.url)
        return

    # Inventaire depuis la page d'accueil
    navigate(ws, "https://notebooklm.google.com/")
    time.sleep(8)
    verifier_auth(ws)
    raw = cdp_eval(ws, JS_LIST_NOTEBOOKS)
    notebooks = json.loads(raw) if isinstance(raw, str) else []
    print(f"{len(notebooks)} notebook(s) detecte(s)")
    for n in notebooks:
        print(f"  - {n['id']}  {n['title'][:60]}")

    if args.all:
        for n in notebooks:
            print(f"\nAspiration {n['id']}")
            aspirer_un(conn, ws, f"https://notebooklm.google.com/notebook/{n['id']}")
        tot = conn.execute("SELECT count(*) FROM notebooks").fetchone()[0]
        print(f"\nTermine — {tot} notebook(s) en base : {DB}")


if __name__ == "__main__":
    main()
