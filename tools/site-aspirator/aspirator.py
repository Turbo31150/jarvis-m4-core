#!/usr/bin/env python3
"""aspirator.py — Orchestrateur : avale un site page par page via CDP, mémorise
localement le code source + la navigation, journalise la série d'actions, adapte
le protocole à la structure détectée, puis génère un rapport.

Prérequis : un Chrome lancé en CDP (comme cdp-inspect / notebooklm-aspire) :
  google-chrome --user-data-dir=/tmp/aspire --remote-debugging-port=9223 \
                --remote-allow-origins='*' <url>

Usage :
  aspirator.py aspire [url] [--depth N] [--max-pages M] [--out DIR] [--shots]
  aspirator.py report <session_dir>

Env : CDP_URL (défaut http://127.0.0.1:9223)
"""

import os
import time
import argparse
from collections import deque

from siteaspirator import cdp as cdpmod, protocol, capture, memory, report

BASE = os.getenv("CDP_URL", "http://127.0.0.1:9223")


def aspire(args):
    c = cdpmod.CDP(base=BASE)
    if args.url:
        c.navigate(args.url, wait=2.0)
    start = c.evl("location.href") or (args.url or "about:blank")
    session = "session-" + memory.slugify(start)[:40]
    mem = memory.Memory(args.out, session)

    # série d'actions : file d'attente (url, profondeur)
    queue = deque([(start, 0)])
    seen = set()
    print(f"[aspire] départ={start}  depth<={args.depth}  max={args.max_pages}")

    while queue and len(seen) < args.max_pages:
        url, depth = queue.popleft()
        if url in seen:
            continue
        seen.add(url)

        try:
            if url != start or args.url:
                c.navigate(url, wait=2.0)
            typ, strat, sig = protocol.detect(c)
            mem.log("detect", url=url, type=typ, signals=sig)

            if strat.get("settle"):
                time.sleep(strat["settle"])

            cap = capture.capture_page(c, strat)
            shot = c.screenshot_png() if args.shots else None
            slug = mem.save_page(url, cap, shot=shot)
            mem.log(
                "captured",
                url=url,
                type=typ,
                slug=slug,
                nodes=cap["dom"].get("nodes", 0),
                links=len(cap["links"]),
            )
            print(
                f"  ✓ [{typ:9}] {len(seen):>3}/{args.max_pages}  "
                f"{cap['dom'].get('nodes', 0):>6} nœuds  {url[:70]}"
            )
        except Exception as e:
            # une page qui échoue ne tue pas la session : on journalise et on continue
            mem.log("error", url=url, error=str(e)[:200])
            print(
                f"  ✗ [erreur  ] {len(seen):>3}/{args.max_pages}  {type(e).__name__}: {url[:60]}"
            )
            c.reconnect()
            continue

        if depth < args.depth:
            for link in cap["links"]:
                if link not in seen:
                    queue.append((link, depth + 1))

    out = mem.flush()
    rep = report.build(out)
    print(f"[aspire] {len(seen)} page(s) → {out}")
    print(f"[rapport] {rep['md']}")
    c.close()


def aspire_tabs(args):
    """Avale TOUT le groupe d'onglets ouverts, mappé par targetId (uid stable de l'onglet)."""
    tabs = cdpmod.CDP.list_tabs(BASE)
    if not tabs:
        print("[tabs] aucun onglet CDP")
        return
    session = "session-tabs-" + memory.slugify(BASE)[:24]
    mem = memory.Memory(args.out, session)
    mapping = []
    print(f"[tabs] {len(tabs)} onglet(s) à avaler")

    for i, tab in enumerate(tabs, 1):
        url, tid = tab["url"], tab["id"]
        try:
            c = cdpmod.CDP(base=BASE, target=tab)
            typ, strat, sig = protocol.detect(c)
            cap = capture.capture_page(c, strat, fast=True)
            cap["tab"] = {"targetId": tid, "title": tab["title"], "type": tab["type"]}
            shot = c.screenshot_png() if args.shots else None
            slug = mem.save_page(url or f"tab-{tid}", cap, shot=shot)
            c.close()
            mapping.append(
                {
                    "n": i,
                    "targetId": tid,
                    "url": url,
                    "title": tab["title"],
                    "type": typ,
                    "slug": slug,
                    "nodes": cap["dom"].get("nodes", 0),
                }
            )
            mem.log(
                "tab_captured",
                n=i,
                targetId=tid,
                url=url,
                type=typ,
                nodes=cap["dom"].get("nodes", 0),
            )
            print(
                f"  ✓ [{typ:9}] {i:>2}/{len(tabs)}  uid={tid[:12]}  "
                f"{cap['dom'].get('nodes', 0):>6} nœuds  {(tab['title'] or url)[:55]}"
            )
        except Exception as e:
            mem.log("tab_error", n=i, targetId=tid, url=url, error=str(e)[:200])
            print(
                f"  ✗ [erreur  ] {i:>2}/{len(tabs)}  uid={tid[:12]}  "
                f"{type(e).__name__}: {(tab['title'] or url)[:45]}"
            )

    # mappage uid ↔ onglet, écrit en clair
    import json as _json

    (mem.root / "mappage_uid.json").write_text(
        _json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    out = mem.flush()
    rep = report.build(out)
    print(f"[tabs] {len(mapping)}/{len(tabs)} onglet(s) avalés → {out}")
    print(f"[tabs] mappage uid → {out}/mappage_uid.json")
    print(f"[rapport] {rep['md']}")


def main():
    ap = argparse.ArgumentParser(description="Aspirateur de site via CDP")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("aspire", help="avale un site page par page")
    a.add_argument(
        "url", nargs="?", default=None, help="URL de départ (sinon onglet courant)"
    )
    a.add_argument("--depth", type=int, default=1, help="profondeur de suivi des liens")
    a.add_argument("--max-pages", type=int, default=10, help="nombre max de pages")
    a.add_argument("--out", default=os.path.expanduser("~/jarvis/data/aspirations"))
    a.add_argument("--shots", action="store_true", help="capture PNG par page")
    a.set_defaults(func=aspire)

    t = sub.add_parser(
        "tabs", help="avale TOUT le groupe d'onglets ouverts (mappage uid)"
    )
    t.add_argument("--out", default=os.path.expanduser("~/jarvis/data/aspirations"))
    t.add_argument("--shots", action="store_true", help="capture PNG par onglet")
    t.set_defaults(func=aspire_tabs)

    r = sub.add_parser("report", help="(re)génère le rapport d'une session")
    r.add_argument("session_dir")
    r.set_defaults(func=lambda args: print(report.build(args.session_dir)))

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
