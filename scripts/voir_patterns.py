#!/usr/bin/env python3
# voir_patterns.py — restitution lisible des patterns. 0 inference, SQL seul.

import json, sqlite3, sys
from collections import Counter
DB = "/home/pamerys/jarvis/jarvis_master.db"

# Sources d OFFRES (la demande solvable) vs sources de PROBLEMES (la difficulte reelle).
# Un pattern qui melange les deux est le seul qui porte un signal commercial : quelqu un
# paie pour resoudre ce que d autres n arrivent pas a faire.
OFFRES = {"remoteok", "arbeitnow", "remotive", "jobicy", "hn-hiring", "freework"}

def main():
    tour, detail, top = 1, "--detail" in sys.argv, 0
    for a in sys.argv:
        if a.startswith("--tour="): tour = int(a.split("=")[1])
        if a.startswith("--top="):  top  = int(a.split("=")[1])

    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    rows = c.execute("SELECT * FROM patterns_marche WHERE tour=? ORDER BY taille DESC",
                     (tour,)).fetchall()
    if not rows:
        print("aucun pattern pour ce tour."); return

    def utile(r): return not (r["label"] or "").upper().startswith("INSUFFISANT")
    ok   = [r for r in rows if utile(r)]
    muet = [r for r in rows if not utile(r)]

    print(f"\n{'='*94}")
    print(f"  PATTERNS DE MARCHE — tour {tour}")
    print(f"  {len(rows)} groupes · {len(ok)} exploitables · {len(muet)} sans conclusion")
    print(f"  Corpus : {c.execute('SELECT COUNT(*) FROM moisson_signaux').fetchone()[0]} signaux, "
          f"{c.execute('SELECT COUNT(*) FROM moisson_vecteurs').fetchone()[0]} vectorises")
    print(f"{'='*94}\n")

    aff = ok[:top] if top else ok
    for i, r in enumerate(aff, 1):
        src = json.loads(r["sources"] or "{}")
        drap = []
        if r["collapse"]: drap.append("ANGLES COLLAPSES")
        if len(src) == 1: drap.append("MONO-SOURCE")
        if r["cohesion"] and r["cohesion"] < 0.30: drap.append("cohesion faible")
        n_off = sum(v for k, v in src.items() if k in OFFRES)
        n_pb  = sum(v for k, v in src.items() if k not in OFFRES)
        croise = n_off > 0 and n_pb > 0
        marque = "€ DEMANDE↔PROBLEME" if croise else ""
        print(f"┌─ [{i}] {r['taille']} signaux · {len(src)} sources · "
              f"cohesion {r['cohesion']:.3f}"
              + (f"  {marque}" if marque else "")
              + (f"  ⚠ {' · '.join(drap)}" if drap else ""))
        print(f"│  {r['label']}")
        if croise:
            off = {k: v for k, v in src.items() if k in OFFRES}
            pb  = {k: v for k, v in src.items() if k not in OFFRES}
            print(f"│  OFFRES   ({n_off}) : {off}")
            print(f"│  PROBLEME ({n_pb}) : {pb}")
        else:
            print(f"│  {src}")
        if detail:
            for a, t in json.loads(r["lectures"] or "{}").items():
                if not t.strip().upper().startswith("INSUFFISANT"):
                    print(f"│    {a:<9}: {t[:140]}")
            for m in json.loads(r["membres"] or "[]")[:4]:
                q = c.execute("SELECT source,titre FROM moisson_signaux WHERE id=?", (m,)).fetchone()
                if q: print(f"│      · [{q[0]:<13}] {q[1][:66]}")
        print("└" + "─"*92 + "\n")

    if muet:
        print(f"── {len(muet)} groupe(s) sans conclusion (le modele a refuse d inventer) :")
        for r in muet[:6]:
            print(f"   {r['taille']} signaux · {json.loads(r['sources'] or '{}')}")
        print()

    # Lecture d ensemble : quelles sources se croisent le plus souvent ?
    paires = Counter()
    for r in ok:
        s = sorted(json.loads(r["sources"] or "{}"))
        for x in range(len(s)):
            for y in range(x+1, len(s)):
                paires[(s[x], s[y])] += 1
    if paires:
        print("── Croisements de sources les plus frequents (un vrai signal de marche")
        print("   relie une DEMANDE et un PROBLEME, pas deux fois le meme canal) :")
        for (a, b), n in paires.most_common(6):
            print(f"   {n:>2}x  {a} ↔ {b}")
    mono = [r for r in ok if len(json.loads(r["sources"] or "{}")) == 1]
    if mono:
        print(f"\n⚠ {len(mono)}/{len(ok)} patterns sont mono-source : ils refletent la facon")
        print("  d ecrire d un site, pas une tendance. A confirmer ailleurs avant usage.")
    print()
    c.close()

if __name__ == "__main__":
    main()
