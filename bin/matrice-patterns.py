#!/usr/bin/env python3
"""
matrice-patterns.py — detection de patterns par SUPERPOSITION MATRICIELLE
sur la bibliotheque vivante (board.db, FTS5). 0 token, 0 GPU, CPU seul.

Principe : chaque mot-cle projette un vecteur binaire sur l'espace des chunks.
La superposition (intersection) de deux axes revele les zones de co-occurrence
= les patterns. Aucun LLM n'intervient : c'est de l'algebre d'ensembles.

  matrice-patterns.py --axes axes.json --out rapport.json [--workers N] [--top N]
"""
import argparse, json, sqlite3, sys, time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

DB = "/home/pamerys/jarvis/board/board.db"

def echappe(terme: str) -> str:
    """FTS5 : une phrase entre guillemets, guillemets internes doubles."""
    return '"' + terme.replace('"', '""') + '"'

def projette(terme: str, limite: int):
    """Vecteur binaire du terme = ensemble des chunk_id qui le portent."""
    cx = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=30)
    try:
        cur = cx.execute(
            "SELECT c.id, c.source_id, c.domain_id "
            "FROM chunks_fts f JOIN chunks c ON c.rowid = f.rowid "
            "WHERE chunks_fts MATCH ? LIMIT ?",
            (echappe(terme), limite))
        lignes = cur.fetchall()
    except sqlite3.OperationalError as e:
        return terme, set(), {}, f"KO: {e}"
    finally:
        cx.close()
    ids = {l[0] for l in lignes}
    meta = {l[0]: (l[1], l[2]) for l in lignes}
    return terme, ids, meta, None

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--axes", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--limite", type=int, default=6000, help="chunks max par terme")
    p.add_argument("--top", type=int, default=40)
    a = p.parse_args()

    axes = json.load(open(a.axes, encoding="utf-8"))
    termes = [(nom, t) for nom, lst in axes.items() for t in lst]
    print(f"[matrice] {len(axes)} axes · {len(termes)} termes · {a.workers} workers", file=sys.stderr)

    t0 = time.time()
    vecteurs, metas, muets = {}, {}, []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for terme, ids, meta, err in ex.map(lambda x: projette(x[1], a.limite), termes):
            if err:
                muets.append((terme, err)); continue
            vecteurs[terme] = ids
            metas.update(meta)
            if not ids:
                muets.append((terme, "0 occurrence"))
    duree = round(time.time() - t0, 2)
    print(f"[matrice] projection faite en {duree}s", file=sys.stderr)

    # superposition inter-axes : c'est la que naissent les patterns
    noms = list(axes)
    patterns = []
    for i in range(len(noms)):
        for j in range(i + 1, len(noms)):
            for ta in axes[noms[i]]:
                for tb in axes[noms[j]]:
                    va, vb = vecteurs.get(ta, set()), vecteurs.get(tb, set())
                    if not va or not vb:
                        continue
                    inter = va & vb
                    if not inter:
                        continue
                    # Jaccard : evite qu'un terme omnipresent ecrase le classement
                    jac = len(inter) / len(va | vb)
                    patterns.append({
                        "axe_a": noms[i], "terme_a": ta,
                        "axe_b": noms[j], "terme_b": tb,
                        "chunks_a": len(va), "chunks_b": len(vb),
                        "superposition": len(inter),
                        "jaccard": round(jac, 4),
                        "domaines": sorted({metas[c][1] for c in list(inter)[:400] if c in metas}),
                        "sources_distinctes": len({metas[c][0] for c in inter if c in metas}),
                        "echantillon": list(inter)[:5],
                    })
    patterns.sort(key=lambda d: (-d["superposition"], -d["jaccard"]))

    rapport = {
        "genere": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base": DB, "duree_sec": duree,
        "axes": {k: len(v) for k, v in axes.items()},
        "termes_projetes": len(vecteurs),
        "termes_muets": muets,
        "couples_evalues": len(patterns),
        "patterns": patterns[:a.top],
        "couverture_par_terme": {t: len(v) for t, v in sorted(vecteurs.items(), key=lambda x: -len(x[1]))},
    }
    json.dump(rapport, open(a.out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"[matrice] {len(patterns)} couples · rapport -> {a.out}", file=sys.stderr)

if __name__ == "__main__":
    main()
