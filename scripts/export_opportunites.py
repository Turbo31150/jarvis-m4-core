#!/usr/bin/env python3
# export_opportunites.py — extrait les patterns commercialement exploitables. 0 inference.
#
# Un pattern est retenu s il croise une source d OFFRES (quelqu un paie) et une source
# de PROBLEMES (quelqu un bloque), et si sa cohesion tient. Le reste est du support
# technique ou du bruit de plateforme — utile a savoir, pas a vendre.

import json, sqlite3, sys
from collections import Counter

DB = "/home/pamerys/jarvis/jarvis_master.db"
OFFRES = {"remoteok", "arbeitnow", "remotive", "jobicy", "hn-hiring", "freework"}

def main():
    tour = 2
    coh_min = 0.30
    for a in sys.argv:
        if a.startswith("--tour="): tour = int(a.split("=")[1])
        if a.startswith("--coh="):  coh_min = float(a.split("=")[1])

    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    rows = c.execute("SELECT * FROM patterns_marche WHERE tour=? ORDER BY taille DESC",
                     (tour,)).fetchall()
    retenus, ecartes = [], []
    for r in rows:
        src = json.loads(r["sources"] or "{}")
        off = {k: v for k, v in src.items() if k in OFFRES}
        pb  = {k: v for k, v in src.items() if k not in OFFRES}
        lab = (r["label"] or "")
        if lab.upper().startswith("INSUFFISANT"):
            ecartes.append((r, "le modele n a pas conclu")); continue
        if not off or not pb:
            ecartes.append((r, "pas de croisement offre/probleme")); continue
        if (r["cohesion"] or 0) < coh_min:
            ecartes.append((r, f"cohesion {r['cohesion']:.3f} < {coh_min}")); continue
        retenus.append((r, off, pb))

    print(f"\n{'='*94}")
    print(f"  OPPORTUNITES — tour {tour} · {len(retenus)} retenues sur {len(rows)} patterns")
    print(f"  Critere : croise OFFRES et PROBLEMES, cohesion >= {coh_min}, conclusion emise")
    print(f"{'='*94}\n")

    for i, (r, off, pb) in enumerate(retenus, 1):
        lectures = json.loads(r["lectures"] or "{}")
        stack = lectures.get("STACK", "")
        urg   = lectures.get("URGENCE", "")
        faux  = lectures.get("FAUX", "")
        print(f"┌─ [{i}] {r['taille']} signaux · cohesion {r['cohesion']:.3f}")
        print(f"│  BESOIN   : {r['label']}")
        if stack and not stack.upper().startswith("INSUFFISANT"):
            print(f"│  STACK    : {stack[:150]}")
        if urg and not urg.upper().startswith("INSUFFISANT"):
            print(f"│  URGENCE  : {urg[:150]}")
        if faux and not faux.upper().startswith("INSUFFISANT"):
            print(f"│  CONTROLE : {faux[:150]}")
        print(f"│  qui PAIE     : {off}")
        print(f"│  qui BLOQUE   : {pb}")
        ids = json.loads(r["membres"] or "[]")
        for m in ids[:3]:
            q = c.execute("SELECT source,titre,url FROM moisson_signaux WHERE id=?", (m,)).fetchone()
            if q:
                tag = "€" if q[0] in OFFRES else "?"
                print(f"│    {tag} [{q[0]:<12}] {q[1][:62]}")
        print("└" + "─"*92 + "\n")

    if ecartes:
        raisons = Counter(m for _, m in ecartes)
        print(f"── {len(ecartes)} pattern(s) ecarte(s), et pourquoi :")
        for m, n in raisons.most_common():
            print(f"   {n:>3}x  {m}")
    print()
    c.close()

if __name__ == "__main__":
    main()
