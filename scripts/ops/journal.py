#!/usr/bin/env python3
"""
jarvis events — lecture du journal opérationnel, filtrable par ID de corrélation.

Nommé journal.py et non events.py délibérément : un module `events.py` dans
scripts/ops/ masquerait scripts/lib/events.py selon l'ordre de sys.path, et on
lirait le journal avec le mauvais module.
"""

import os
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(os.environ.get("JARVIS_ROOT", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
import events as journal  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        prog="jarvis events", description="Lecture du journal opérationnel JARVIS"
    )
    parser.add_argument(
        "--type", dest="event_type", help="Filtrer par type (ex: agent.fallback_used)"
    )
    parser.add_argument("--command-id", help="Filtrer par ID de corrélation")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    evts = journal.query(
        event_type=args.event_type, command_id=args.command_id, limit=args.limit
    )

    if args.json:
        print(json.dumps(evts, indent=2, ensure_ascii=False))
        return 0

    if not evts:
        print(
            "aucun événement (filtres appliqués : "
            f"type={args.event_type or '*'}, command_id={args.command_id or '*'})"
        )
        return 0

    print(f"{len(evts)} événement(s), du plus récent au plus ancien :\n")
    for e in evts:
        cid = (e.get("command_id") or "-")[:8]
        extras = {
            k: v
            for k, v in e.items()
            if k
            not in (
                "event_id",
                "schema_version",
                "ts",
                "ts_iso",
                "type",
                "command_id",
                "pid",
                "host",
            )
        }
        detail = " ".join(f"{k}={str(v)[:40]}" for k, v in extras.items())
        print(f"  {e.get('ts_iso', '?')}  {e.get('type', '?'):26} [{cid}] {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
