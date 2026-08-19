#!/usr/bin/env python3
# rescan_patterns.py — boucle de rescan bornee. 0 token.
#
# Les patterns du tour N deviennent les requetes du tour N+1 : ce que le marche
# repete devient ce qu on va rechercher. La boucle est bornee par CONSTRUCTION :
#
#   - 3 tours maximum (TOURS_MAX)
#   - arret des qu un tour n apporte AUCUN cluster neuf
#   - "neuf" = un cluster dont le centroide est a moins de SEUIL_NEUF de tout
#     centroide deja connu. Sans ce test, la boucle re-decouvrirait indefiniment
#     les memes patterns sous des libelles differents et paraitrait productive.

import json, math, sqlite3, subprocess, sys, time
from array import array
from datetime import datetime

DB      = "/home/pamerys/jarvis/jarvis_master.db"
SCRIPTS = "/home/pamerys/jarvis/scripts"
LOG     = "/home/pamerys/jarvis/logs/rescan_patterns.log"
TOURS_MAX   = 3
SEUIL_NEUF  = 0.90     # au-dela, le "nouveau" cluster est l ancien sous un autre nom
SEUIL_CLUST = 0.782    # calibre sur la distribution (p995) le 19/08

def log(m):
    line = f"[{datetime.now():%H:%M:%S}] {m}"
    print(line, flush=True)
    try:
        with open(LOG, "a") as f: f.write(line + "\n")
    except OSError: pass

def cos(a, b):
    n = min(len(a), len(b))
    num = sum(a[i]*b[i] for i in range(n))
    da = math.sqrt(sum(x*x for x in a[:n])); db = math.sqrt(sum(x*x for x in b[:n]))
    return num/(da*db) if da and db else 0.0

def centroides(tour=None):
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    q = "SELECT id,label,tour,centroide FROM patterns_marche"
    if tour is not None: q += f" WHERE tour = {int(tour)}"
    out = []
    for r in c.execute(q):
        v = array("f"); v.frombytes(r["centroide"])
        out.append(dict(id=r["id"], label=r["label"], tour=r["tour"], vec=list(v)))
    c.close(); return out

VIDES = {"les","des","une","un","le","la","de","du","et","ou","pour","avec","dans","sur",
         "que","qui","est","sont","ces","ce","cette","leur","plus","tout","the","of","to",
         "and","for","with","this","that","insuffisant","messages","utilisateurs"}

def requetes_depuis(patterns, n=4):
    """Extrait des mots-cles des labels. Deterministe, aucune inference."""
    import re, unicodedata
    from collections import Counter
    cnt = Counter()
    for p in patterns:
        t = unicodedata.normalize("NFD", p["label"] or "")
        t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn").lower()
        for m in re.findall(r"[a-z0-9]{4,}", t):
            if m not in VIDES: cnt[m] += 1
    return [m for m, _ in cnt.most_common(n)]

def lancer(cmd, minutes=25):
    log(f"  $ {' '.join(cmd)}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=minutes*60)
        if r.returncode != 0:
            log(f"    code {r.returncode} : {(r.stderr or '')[-160:]}")
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        log("    EXPIRE"); return False

def main():
    log(f"=== RESCAN BORNE — {TOURS_MAX} tours maximum ===")
    connus = centroides()
    log(f"patterns deja connus : {len(connus)}")
    if not connus:
        log("aucun pattern de depart — lancer patterns_marche.py d abord."); return 1

    for tour in range(2, TOURS_MAX + 1):
        log(f"\n── TOUR {tour}/{TOURS_MAX} ──")
        reqs = requetes_depuis(connus if tour == 2 else nouveaux, n=4)
        if not reqs:
            log("  aucune requete extractible des patterns -> arret."); break
        log(f"  requetes derivees : {reqs}")

        avant = sqlite3.connect(DB).execute("SELECT COUNT(*) FROM moisson_signaux").fetchone()[0]
        lancer([sys.executable, f"{SCRIPTS}/moisson_multi_source.py", f"--tour={tour}"] + reqs)
        apres = sqlite3.connect(DB).execute("SELECT COUNT(*) FROM moisson_signaux").fetchone()[0]
        log(f"  signaux : {avant} -> {apres} (+{apres-avant})")
        if apres == avant:
            log("  aucun signal neuf -> ARRET (la moisson est seche)."); break

        lancer([sys.executable, f"{SCRIPTS}/patterns_marche.py",
                f"--seuil={SEUIL_CLUST}", f"--tour={tour}"], minutes=40)

        nouveaux = centroides(tour=tour)
        vraiment_neufs = []
        for n_ in nouveaux:
            proche = max((cos(n_["vec"], k["vec"]) for k in connus), default=0.0)
            if proche < SEUIL_NEUF:
                vraiment_neufs.append(n_)
            else:
                log(f"  deja connu (cos {proche:.3f}) : {n_['label'][:64]}")
        log(f"  clusters du tour {tour} : {len(nouveaux)}, dont NEUFS : {len(vraiment_neufs)}")
        if not vraiment_neufs:
            log("  aucun cluster neuf -> ARRET (convergence)."); break
        for n_ in vraiment_neufs:
            log(f"    NEUF : {n_['label'][:88]}")
        connus += vraiment_neufs

    log(f"\n=== FIN — {len(connus)} pattern(s) au total ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
