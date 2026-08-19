#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
m6-dispatch — dispatcher MASSIF PARALLELE vers LM Studio M6 (0 token facture).

Dev sur M4, charge executee sur M6 (10.42.0.230:1234, lien direct ~1,5 ms).

Modes
  bench   courbe de saturation : concurrence croissante, latence p50/p95, debit
  embed   vectorisation d'un corpus (768 dims, nomic-embed-text-v1.5)
  map     superposition : N patterns x M items, tout en parallele

Tout est persiste dans ~/jarvis/data/m6_dispatch.db (idempotent : meme
prompt+modele = pas de re-execution, on relit le cache).
"""
import argparse, hashlib, json, os, sqlite3, statistics, sys, threading, time
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

M6      = os.environ.get("M6_URL", "http://10.42.0.230:1234")
DB      = os.path.expanduser("~/jarvis/data/m6_dispatch.db")
MODEL   = "qwen/qwen3.5-9b"
EMBED   = "text-embedding-nomic-embed-text-v1.5"
_lock   = threading.Lock()


def db():
    c = sqlite3.connect(DB, timeout=60, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS reponses(
      cle TEXT PRIMARY KEY, ts TEXT, modele TEXT, prompt TEXT, contenu TEXT,
      tok_prompt INT, tok_completion INT, tok_reasoning INT, latence_s REAL,
      lot TEXT, item TEXT, pattern TEXT, erreur TEXT);
    CREATE TABLE IF NOT EXISTS vecteurs(
      cle TEXT PRIMARY KEY, ts TEXT, texte TEXT, dim INT, vecteur TEXT, lot TEXT);
    CREATE TABLE IF NOT EXISTS mesures(
      ts TEXT, mode TEXT, concurrence INT, n INT, ok INT, ko INT,
      p50 REAL, p95 REAL, duree_s REAL, req_s REAL, tok_s REAL, detail TEXT);
    CREATE INDEX IF NOT EXISTS i_lot ON reponses(lot);
    """)
    return c


def post(chemin, charge, timeout=600):
    r = urllib.request.Request(M6 + chemin,
        data=json.dumps(charge).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as h:
        return json.loads(h.read())


def cle(*parts):
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:32]


def appel(prompt, modele=MODEL, systeme=None, max_tokens=2000, temp=0.0,
          lot="", item="", pattern="", conn=None, cache=True):
    k = cle(modele, systeme or "", prompt, max_tokens, temp)
    if cache and conn is not None:
        with _lock:
            row = conn.execute(
                "SELECT contenu,latence_s,tok_completion FROM reponses WHERE cle=? AND erreur IS NULL", (k,)
            ).fetchone()
        if row:
            return {"cle": k, "contenu": row[0], "latence_s": row[1],
                    "tok_completion": row[2], "cache": True}
    msgs = ([{"role": "system", "content": systeme}] if systeme else []) + \
           [{"role": "user", "content": prompt}]
    t0 = time.time()
    err = None
    contenu, tp, tc, tr = "", 0, 0, 0
    try:
        d = post("/v1/chat/completions",
                 {"model": modele, "messages": msgs,
                  "max_tokens": max_tokens, "temperature": temp})
        contenu = d["choices"][0]["message"]["content"] or ""
        u = d.get("usage", {}) or {}
        tp, tc = u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
        tr = (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
    except Exception as e:
        err = f"{type(e).__name__}: {e}"[:300]
    lat = round(time.time() - t0, 3)
    if conn is not None:
        with _lock:
            conn.execute(
                "INSERT OR REPLACE INTO reponses VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (k, time.strftime("%F %T"), modele, prompt[:4000], contenu,
                 tp, tc, tr, lat, lot, item, pattern, err))
            conn.commit()
    return {"cle": k, "contenu": contenu, "latence_s": lat, "tok_completion": tc,
            "tok_reasoning": tr, "erreur": err, "cache": False}


def enregistre_mesure(conn, mode, conc, lats, ok, ko, duree, toks, detail=""):
    p50 = round(statistics.median(lats), 2) if lats else 0
    p95 = round(sorted(lats)[int(len(lats) * .95) - 1], 2) if len(lats) >= 2 else (lats[0] if lats else 0)
    row = (time.strftime("%F %T"), mode, conc, ok + ko, ok, ko, p50, p95,
           round(duree, 2), round((ok + ko) / duree, 3) if duree else 0,
           round(toks / duree, 1) if duree else 0, detail)
    with _lock:
        conn.execute("INSERT INTO mesures VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", row)
        conn.commit()
    return row


def mode_bench(a):
    conn = db()
    print(f"BENCH M6 {M6} — modele {a.modele}")
    print(f"{'CONC':>5} {'N':>4} {'OK':>4} {'KO':>4} {'p50 s':>8} {'p95 s':>8} {'req/s':>7} {'tok/s':>8}")
    for conc in [int(x) for x in a.concurrences.split(",")]:
        n = conc * a.par_worker
        prompts = [f"Tache {i}: donne UN mot-cle metier pour l'automatisation n8n. Reponds par un seul mot." for i in range(n)]
        lats, toks, ok, ko = [], 0, 0, 0
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=conc) as ex:
            futs = [ex.submit(appel, p, a.modele, None, a.max_tokens, 0.0,
                              f"bench-c{conc}", str(i), "bench", conn, False)
                    for i, p in enumerate(prompts)]
            for f in as_completed(futs):
                r = f.result()
                lats.append(r["latence_s"]); toks += r.get("tok_completion") or 0
                ok += 0 if r.get("erreur") else 1
                ko += 1 if r.get("erreur") else 0
        d = time.time() - t0
        row = enregistre_mesure(conn, "bench", conc, lats, ok, ko, d, toks, a.modele)
        print(f"{conc:>5} {n:>4} {ok:>4} {ko:>4} {row[6]:>8} {row[7]:>8} {row[9]:>7} {row[10]:>8}")
    conn.close()


def mode_embed(a):
    conn = db()
    textes = [l.strip() for l in open(a.fichier, encoding="utf-8") if l.strip()]
    print(f"VECTORISATION — {len(textes)} textes, lots de {a.taille_lot}, {a.concurrence} en parallele")
    t0, faits, dim = time.time(), 0, 0
    lots = [textes[i:i + a.taille_lot] for i in range(0, len(textes), a.taille_lot)]

    def traite(lot_txt):
        d = post("/v1/embeddings", {"model": a.modele_embed, "input": lot_txt})
        out = []
        for t, e in zip(lot_txt, d["data"]):
            out.append((cle(a.modele_embed, t), time.strftime("%F %T"), t,
                        len(e["embedding"]), json.dumps(e["embedding"]), a.lot))
        return out

    with ThreadPoolExecutor(max_workers=a.concurrence) as ex:
        for f in as_completed([ex.submit(traite, l) for l in lots]):
            try:
                rows = f.result()
            except Exception as e:
                print("  erreur lot:", e); continue
            dim = rows[0][3]; faits += len(rows)
            with _lock:
                conn.executemany("INSERT OR REPLACE INTO vecteurs VALUES(?,?,?,?,?,?)", rows)
                conn.commit()
            print(f"  {faits}/{len(textes)} vectorises", end="\r")
    d = time.time() - t0
    print(f"\n{faits} vecteurs de dimension {dim} en {d:.1f}s ({faits/d:.1f}/s) -> {DB}")
    conn.close()


def mode_map(a):
    """Superposition : chaque item passe par TOUS les patterns, tout en parallele."""
    conn = db()
    items = json.load(open(a.items, encoding="utf-8"))
    patterns = json.load(open(a.patterns, encoding="utf-8"))
    taches = [(i, p) for i in items for p in patterns]
    print(f"SUPERPOSITION — {len(items)} items x {len(patterns)} patterns = {len(taches)} micro-taches")
    print(f"concurrence {a.concurrence} | modele {a.modele}")
    t0, ok, ko, cachees, lats, toks = time.time(), 0, 0, 0, [], 0
    with ThreadPoolExecutor(max_workers=a.concurrence) as ex:
        futs = {}
        for it, pat in taches:
            prompt = pat["gabarit"].format(**it)
            futs[ex.submit(appel, prompt, a.modele, pat.get("systeme"),
                           a.max_tokens, 0.0, a.lot, it.get("id", ""), pat["id"], conn, True)] = (it, pat)
        for f in as_completed(futs):
            it, pat = futs[f]
            r = f.result()
            if r.get("cache"): cachees += 1
            if r.get("erreur"): ko += 1
            else:
                ok += 1; lats.append(r["latence_s"]); toks += r.get("tok_completion") or 0
            print(f"  {ok+ko}/{len(taches)} (cache {cachees}, echecs {ko})", end="\r")
    d = time.time() - t0
    row = enregistre_mesure(conn, "map", a.concurrence, lats, ok, ko, d, toks, a.lot)
    print(f"\n{ok} OK / {ko} KO / {cachees} depuis le cache en {d:.1f}s")
    print(f"p50={row[6]}s p95={row[7]}s | {row[9]} req/s | {row[10]} tok/s")
    print(f"resultats -> sqlite3 {DB} \"SELECT item,pattern,contenu FROM reponses WHERE lot='{a.lot}'\"")
    conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Dispatcher massif parallele vers M6")
    sub = ap.add_subparsers(dest="mode", required=True)

    b = sub.add_parser("bench"); b.set_defaults(f=mode_bench)
    b.add_argument("--concurrences", default="1,2,4,8,16")
    b.add_argument("--par-worker", type=int, default=2)
    b.add_argument("--modele", default=MODEL)
    b.add_argument("--max-tokens", type=int, default=600)

    e = sub.add_parser("embed"); e.set_defaults(f=mode_embed)
    e.add_argument("fichier"); e.add_argument("--taille-lot", type=int, default=32)
    e.add_argument("--concurrence", type=int, default=8)
    e.add_argument("--modele-embed", default=EMBED); e.add_argument("--lot", default="defaut")

    m = sub.add_parser("map"); m.set_defaults(f=mode_map)
    m.add_argument("--items", required=True); m.add_argument("--patterns", required=True)
    m.add_argument("--concurrence", type=int, default=8); m.add_argument("--modele", default=MODEL)
    m.add_argument("--max-tokens", type=int, default=2000); m.add_argument("--lot", default="defaut")

    a = ap.parse_args(); a.f(a)
