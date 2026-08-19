#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
board-vectorise — complete les embeddings manquants de la bibliotheque vivante.

N'ecrit QUE dans les lignes ou embedding IS NULL : jamais d'ecrasement.
Interruptible et reprenable : relancer reprend la ou on s'est arrete.
Format ecrit : BLOB float32 little-endian, 768 valeurs (identique a l'existant).
"""
import argparse, json, os, sqlite3, struct, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

DB    = os.path.expanduser("~/jarvis/board/board.db")
M6    = os.environ.get("M6_URL", "http://10.42.0.230:1234")
MODEL = "text-embedding-nomic-embed-text-v1.5"
DIM   = 768
MAXC  = 6000   # caracteres max envoyes (ctx du modele = 2048 tokens)



SSH = ("ssh -o BatchMode=yes -o ConnectTimeout=6 -o StrictHostKeyChecking=no "
       "-o UserKnownHostsFile=/dev/null -i /home/pamerys/.ssh/id_ed25519 turbo@10.42.0.230")


def sante_m6():
    """Retourne (ram_dispo_Mo, temp_gpu_max) ou (None, None) si injoignable."""
    import subprocess
    try:
        r = subprocess.run(
            SSH.split() + ["free -m | awk 'NR==2{print $7}'; "
                           "nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader"],
            capture_output=True, text=True, timeout=25)
        l = [x.strip() for x in r.stdout.strip().splitlines() if x.strip()]
        return int(l[0]), max(int(x) for x in l[1:])
    except Exception:
        return None, None


SEUIL_RAM_MO = 1200
SEUIL_TEMP_C = 85


def embed(textes, timeout=180):
    corps = json.dumps({"model": MODEL, "input": textes}).encode()
    req = urllib.request.Request(M6 + "/v1/embeddings", data=corps,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as h:
        d = json.loads(h.read())
    return [e["embedding"] for e in d["data"]]


def blob(vec):
    return struct.pack(f"<{len(vec)}f", *vec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lot", type=int, default=32, help="textes par requete")
    ap.add_argument("--concurrence", type=int, default=3)
    ap.add_argument("--paquet", type=int, default=480, help="chunks par transaction")
    ap.add_argument("--max", type=int, default=0, help="0 = tout")
    ap.add_argument("--domaine", default=None)
    a = ap.parse_args()

    c = sqlite3.connect(DB, timeout=120)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")

    where = "embedding IS NULL" + (" AND domain_id=?" if a.domaine else "")
    args = (a.domaine,) if a.domaine else ()
    reste = c.execute(f"SELECT COUNT(*) FROM chunks WHERE {where}", args).fetchone()[0]
    total = min(reste, a.max) if a.max else reste
    print(f"{reste} chunks sans embedding" + (f" (domaine {a.domaine})" if a.domaine else ""))
    print(f"a traiter : {total} | lots de {a.lot} | {a.concurrence} en parallele\n")

    faits, echecs, t0 = 0, 0, time.time()
    while faits < total:
        n = min(a.paquet, total - faits)
        ram, temp = sante_m6()
        if ram is not None:
            if ram < SEUIL_RAM_MO:
                print(f"\n  ⛔ ARRET : RAM M6 tombee a {ram} Mo (< {SEUIL_RAM_MO}). "
                      f"Relancer plus tard reprendra ici.")
                break
            if temp and temp > SEUIL_TEMP_C:
                print(f"\n  ⏸  PAUSE 60 s : GPU M6 a {temp} C (> {SEUIL_TEMP_C})")
                time.sleep(60)
        rows = c.execute(
            f"SELECT id, text FROM chunks WHERE {where} LIMIT ?", args + (n,)).fetchall()
        if not rows:
            break
        paquets = [rows[i:i+a.lot] for i in range(0, len(rows), a.lot)]

        def traite(p):
            textes = [(t or "")[:MAXC] or " " for _, t in p]
            return [(blob(v), DIM, MODEL, i) for (i, _), v in zip(p, embed(textes))]

        maj = []
        with ThreadPoolExecutor(max_workers=a.concurrence) as ex:
            for f in as_completed([ex.submit(traite, p) for p in paquets]):
                try:
                    maj.extend(f.result())
                except Exception as e:
                    echecs += a.lot
                    print(f"\n  [echec lot] {type(e).__name__}: {str(e)[:110]}")

        if maj:
            c.executemany(
                "UPDATE chunks SET embedding=?, embedding_dim=?, embedding_model=? "
                "WHERE id=? AND embedding IS NULL", maj)
            c.commit()
        faits += len(rows)
        d = time.time() - t0
        print(f"\r  {faits}/{total}  ({faits/d:.0f}/s, {echecs} echecs, "
              f"reste ~{(total-faits)/max(faits/d,0.01)/60:.0f} min)   ", end="", flush=True)

    d = time.time() - t0
    print(f"\n\ntermine : {faits} traites, {echecs} echecs, en {d/60:.1f} min")
    r = c.execute("SELECT COUNT(*) FROM chunks WHERE embedding IS NULL").fetchone()[0]
    print(f"chunks encore sans embedding : {r}")
    c.close()


if __name__ == "__main__":
    main()
