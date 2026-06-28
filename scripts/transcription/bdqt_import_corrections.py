#!/usr/bin/env python3
"""Importe ~/jarvis.db:voice_corrections (2627) → BDQT corrections.
confidence = min(1.0, 0.5 + hit_count*0.1). Ignore les templates ({site}…)
côté correction exacte mais les garde en alias n'a pas de sens → on filtre.
"""

import os
import sqlite3
import bdqt_core as core

SRC = os.path.expanduser("~/jarvis.db")


def main():
    core.ensure_schema()
    src = sqlite3.connect(SRC)
    dst = core.get_conn()
    rows = src.execute(
        "SELECT source_text,target_text,category,hit_count FROM voice_corrections"
    ).fetchall()
    n = skipped = 0
    for s, t, cat, hc in rows:
        if not s or not t:
            skipped += 1
            continue
        hc = hc or 0
        conf = min(1.0, 0.5 + hc * 0.1)
        dom = "tech" if cat in ("alias", "auto_training") else "general"
        try:
            dst.execute(
                "INSERT OR IGNORE INTO corrections"
                "(source_text,target_text,domain,category,hit_count,confidence) "
                "VALUES(?,?,?,?,?,?)",
                (s, t, dom, cat, hc, conf),
            )
            n += 1
        except Exception:
            skipped += 1
    dst.commit()
    total = dst.execute("SELECT COUNT(*) FROM corrections").fetchone()[0]
    print(f"[import] traités={n} ignorés={skipped} | total corrections en base={total}")
    src.close()
    dst.close()


if __name__ == "__main__":
    main()
