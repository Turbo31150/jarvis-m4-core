#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rapprochement semantique sur les vecteurs produits par m6-dispatch (0 token)."""
import json, math, sqlite3, os, sys, argparse

DB = os.path.expanduser("~/jarvis/data/m6_dispatch.db")

def charge(lot):
    c = sqlite3.connect(DB)
    lignes = []
    for texte, vec in c.execute("SELECT texte, vecteur FROM vecteurs WHERE lot=?", (lot,)):
        parts = texte.split("|", 2)
        if len(parts) < 3: continue
        lignes.append({"type": parts[0], "id": parts[1], "libelle": parts[2],
                       "v": json.loads(vec)})
    c.close()
    return lignes

def cos(a, b):
    s = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(y*y for y in b))
    return s/(na*nb) if na and nb else 0.0

def proches(src, cibles, n=3):
    r = [(cos(src["v"], c["v"]), c) for c in cibles if c["id"] != src["id"]]
    r.sort(key=lambda x: -x[0])
    return r[:n]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lot", default="catalogue-20260819")
    ap.add_argument("--de", default="AGENCE")
    ap.add_argument("--vers", default="FORMATION")
    ap.add_argument("--top", type=int, default=2)
    a = ap.parse_args()
    tout = charge(a.lot)
    src = [x for x in tout if x["type"] == a.de]
    dst = [x for x in tout if x["type"] == a.vers]
    print(f"{len(src)} {a.de} x {len(dst)} {a.vers}\n")
    for s in src:
        print(f"  {s['libelle'][:66]}")
        for sc, c in proches(s, dst, a.top):
            print(f"      {sc:.3f}  {c['libelle'][:74]}")
