#!/usr/bin/env python3
"""
JARVIS Action CLI — Notice utilisation commandes détectées par mots-clés
==========================================================================

3 modes :
  1. match    : user input → meilleure action SQL match (fuzzy)
  2. exec     : run command template + log success/error
  3. learn    : enrichi trigger_keywords avec nouvelle variante
  4. sync     : export SQL → page Notion catalogue

Apprentissage continu :
- Chaque exec incrémente success_count + last_executed_at
- Chaque match avec phrase nouvelle → propose ajout trigger_keywords
- learn confirme ajout définitif (idempotent)

Usage :
  ./jarvis_action.py match "publie sur les 5 réseaux"
  ./jarvis_action.py exec autopilot_e2e_m5
  ./jarvis_action.py learn publish_mirra_multi "balance partout sur les sociaux"
  ./jarvis_action.py sync
  ./jarvis_action.py stats
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

DB = os.environ.get("JARVIS_DB", "/home/pamerys/jarvis/jarvis_master.db")
NOTION_PAGE = "36e6e907-1cc0-811e-a93c-c3b9cf71273d"
CATALOGUE_URL = f"https://www.notion.so/{NOTION_PAGE.replace('-', '')}"


def _conn():
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    c = sqlite3.connect(DB, timeout=120)
    c.execute("PRAGMA busy_timeout=120000")
    c.row_factory = sqlite3.Row
    return c


def _tokenize(text: str) -> set[str]:
    """lowercase + accents stripped + split"""
    t = text.lower()
    repl = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")
    t = t.translate(repl)
    return set(re.findall(r"[a-z0-9]+", t))


def cmd_match(user_input: str, top: int = 3) -> list[dict]:
    """Retourne top N actions matching user input par overlap mots-clés."""
    user_tokens = _tokenize(user_input)
    if not user_tokens:
        return []
    con = _conn()
    rows = con.execute(
        "SELECT id, action_name, category, trigger_keywords, command_template, success_count, notes FROM action_validation"
    ).fetchall()
    con.close()

    scored = []
    for r in rows:
        try:
            keys = json.loads(r["trigger_keywords"] or "[]")
        except json.JSONDecodeError:
            keys = []
        key_tokens = set()
        for k in keys:
            key_tokens |= _tokenize(k)
        if not key_tokens:
            continue
        overlap = user_tokens & key_tokens
        if not overlap:
            continue
        # Score: overlap_count + log(success_count+1) * 0.3
        import math

        score = len(overlap) + math.log1p(r["success_count"]) * 0.3
        scored.append(
            {
                "score": score,
                "action_name": r["action_name"],
                "category": r["category"],
                "command": r["command_template"],
                "success_count": r["success_count"],
                "matched": sorted(overlap),
                "keys": keys[:5],
            }
        )
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top]


def cmd_exec(action_name: str, dry_run: bool = False) -> int:
    """Récupère command template + l'affiche (pas d'exec auto pour safety)."""
    con = _conn()
    row = con.execute(
        "SELECT * FROM action_validation WHERE action_name = ?", (action_name,)
    ).fetchone()
    if not row:
        print(f"❌ Action inconnue: {action_name}", file=sys.stderr)
        con.close()
        return 1
    print(f"🎯 Action : {action_name}")
    print(f"📁 Catégorie : {row['category']}")
    print(f"💻 Commande : {row['command_template']}")
    if row["notes"]:
        print(f"📝 Notes : {row['notes']}")
    print(f"✓ Exécutée {row['success_count']}× (dernière : {row['last_executed_at']})")
    if dry_run:
        print(
            '\n[DRY_RUN] — pas d\'exécution. Lance: bash -c "$(./jarvis_action.py exec X --print)"'
        )
        con.close()
        return 0
    # Increment success_count + update last_executed_at
    con.execute(
        "UPDATE action_validation SET success_count = success_count + 1, last_executed_at = ? WHERE action_name = ?",
        (datetime.now(timezone.utc).isoformat(), action_name),
    )
    con.commit()
    con.close()
    print("\n✅ Logged exec — success_count += 1")
    return 0


def cmd_learn(action_name: str, new_keyword: str) -> int:
    """Ajoute un mot-clé/phrase à trigger_keywords d'une action."""
    con = _conn()
    row = con.execute(
        "SELECT trigger_keywords FROM action_validation WHERE action_name = ?",
        (action_name,),
    ).fetchone()
    if not row:
        print(f"❌ Action inconnue: {action_name}", file=sys.stderr)
        con.close()
        return 1
    try:
        keys = json.loads(row["trigger_keywords"] or "[]")
    except json.JSONDecodeError:
        keys = []
    new_keyword = new_keyword.strip().lower()
    if new_keyword in [k.lower() for k in keys]:
        print(f"⚠️  Keyword '{new_keyword}' déjà présent")
        con.close()
        return 0
    keys.append(new_keyword)
    con.execute(
        "UPDATE action_validation SET trigger_keywords = ? WHERE action_name = ?",
        (json.dumps(keys, ensure_ascii=False), action_name),
    )
    con.commit()
    con.close()
    print(f"✅ Keyword '{new_keyword}' ajouté à {action_name} ({len(keys)} keys total)")
    return 0


def cmd_stats() -> int:
    """Affiche stats globales du catalogue."""
    con = _conn()
    total = con.execute("SELECT COUNT(*) FROM action_validation").fetchone()[0]
    cats = con.execute(
        "SELECT category, COUNT(*) c FROM action_validation GROUP BY category ORDER BY c DESC"
    ).fetchall()
    top = con.execute(
        "SELECT action_name, success_count FROM action_validation WHERE success_count > 0 ORDER BY success_count DESC LIMIT 10"
    ).fetchall()
    kw = con.execute("SELECT COUNT(*) FROM keyword_actions").fetchone()[0]
    try:
        domino = con.execute(
            "SELECT trigger_event, chain_name, status FROM domino_triggers ORDER BY id DESC LIMIT 5"
        ).fetchall()
    except sqlite3.OperationalError:
        domino = []
    con.close()
    print(
        f"📊 JARVIS Catalogue — {total} actions / {len(cats)} catégories / {kw} keywords"
    )
    print(f"📋 Page Notion : {CATALOGUE_URL}\n")
    print("Top catégories :")
    for c in cats[:8]:
        print(f"  {c['category']:<22s} {c['c']}")
    print("\nTop actions exécutées :")
    for r in top:
        print(f"  {r['action_name']:<30s} {r['success_count']}×")
    if domino:
        print("\nDomino chains récents :")
        for d in domino:
            print(
                f"  {d['trigger_event']:<35s} → {d['chain_name']:<25s} [{d['status']}]"
            )
    return 0


NOTION_TOKEN_PATH = os.path.expanduser("~/.config/notion/api_key")


def _notion_token() -> str:
    if os.path.exists(NOTION_TOKEN_PATH):
        return open(NOTION_TOKEN_PATH).read().strip()
    return os.environ.get("NOTION_TOKEN", "")


def cmd_sync(parent_page: str = NOTION_PAGE) -> int:
    """Push catalogue stats vers Notion via REST API."""
    import urllib.request
    import urllib.error

    token = _notion_token()
    if not token:
        print(
            "❌ Pas de token. Crée ~/.config/notion/api_key (chmod 600)",
            file=sys.stderr,
        )
        return 1

    con = _conn()
    total = con.execute("SELECT COUNT(*) FROM action_validation").fetchone()[0]
    cats = con.execute(
        "SELECT category, COUNT(*) c FROM action_validation GROUP BY category ORDER BY c DESC"
    ).fetchall()
    top = con.execute(
        "SELECT action_name, success_count FROM action_validation ORDER BY success_count DESC LIMIT 8"
    ).fetchall()
    kw = con.execute("SELECT COUNT(*) FROM keyword_actions").fetchone()[0]
    con.close()

    blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"🔄 Sync {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        },
                    }
                ]
            },
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"Total: {total} actions / {len(cats)} catégories / {kw} keywords"
                        },
                    }
                ]
            },
        },
    ]
    for c in cats[:5]:
        blocks.append(
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"{c['category']}: {c['c']}"},
                        }
                    ]
                },
            }
        )
    for r in top[:5]:
        blocks.append(
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"{r['action_name']}: {r['success_count']}×"
                            },
                        }
                    ]
                },
            }
        )

    req = urllib.request.Request(
        f"https://api.notion.com/v1/blocks/{parent_page.replace('-', '')}/children",
        method="PATCH",
        data=json.dumps({"children": blocks}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"✅ Sync OK — {len(blocks)} blocks → {CATALOGUE_URL}")
            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        if "Could not find" in body or "not been shared" in body:
            print("❌ Intégration pas ajoutée à la page Notion.\n")
            print("   Setup manuel requis (1 fois) :")
            print(f"   1. Ouvre la page : {CATALOGUE_URL}")
            print("   2. Click ⋮ menu (top right) → Connections → Add connections")
            print("   3. Sélectionne ton intégration Personal")
            print("   4. Relance : python3 ~/jarvis/scripts/jarvis_action.py sync")
        else:
            print(f"❌ {e.code}: {body}")
        return 1
    except Exception as e:
        print(f"❌ {type(e).__name__}: {e}")
        return 1


def main():
    p = argparse.ArgumentParser(description="JARVIS Action CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("match", help="Match user input → top actions")
    m.add_argument("input", nargs="+")
    m.add_argument("-n", "--top", type=int, default=3)

    e = sub.add_parser("exec", help="Display + log execution of action")
    e.add_argument("action_name")
    e.add_argument("--dry-run", action="store_true")

    l = sub.add_parser("learn", help="Add new trigger keyword to action")
    l.add_argument("action_name")
    l.add_argument("keyword", nargs="+")

    sub.add_parser("stats", help="Show catalogue stats")
    sub.add_parser("sync", help="Sync info to Notion catalogue")

    args = p.parse_args()

    if args.cmd == "match":
        text = " ".join(args.input)
        results = cmd_match(text, top=args.top)
        if not results:
            print(f"❌ Aucun match pour : {text}")
            return 1
        print(f"🎯 Top {len(results)} matches pour : {text}\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['action_name']} ({r['category']}) — score {r['score']:.1f}")
            print(f"   matched : {', '.join(r['matched'])}")
            print(f"   cmd     : {r['command'][:90]}")
            print(f"   exec    : {r['success_count']}×")
            print()
        return 0
    elif args.cmd == "exec":
        return cmd_exec(args.action_name, dry_run=args.dry_run)
    elif args.cmd == "learn":
        return cmd_learn(args.action_name, " ".join(args.keyword))
    elif args.cmd == "stats":
        return cmd_stats()
    elif args.cmd == "sync":
        return cmd_sync()


if __name__ == "__main__":
    sys.exit(main())
