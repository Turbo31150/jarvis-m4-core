#!/usr/bin/env python3
"""dispatch_embed_m6.py — vectorisation de masse du board via M6 (LM Studio).

Pattern dispatch-generation-masse : N workers -> backend DÉPORTÉ (M6, câble
direct), UN SEUL écrivain SQLite (coexiste avec l'embedder Rémi en WAL),
idempotent (WHERE embedding IS NULL), retry, log de progression.
0 token facturé, 0 chaleur M4 (le calcul part sur les GPU de M6).

Usage : python3 dispatch_embed_m6.py [workers] [domaine]
        (défaut : 6 workers, domaine biblio-vivante puis souverainete)
"""

import json
import queue
import sqlite3
import struct
import sys
import threading
import time
import urllib.request

DB = "/storage/m1-mirror/databases/board.db"
M6_URL = "http://10.42.0.230:1234/v1/embeddings"
MODEL = "text-embedding-nomic-embed-text-v1.5"
LOG = "/home/pamerys/jarvis/logs/dispatch-embed-m6.log"
LOT = 16  # textes par requête M6
COMMIT_EVERY = 200
MAX_RETRY = 6

write_q: "queue.Queue[tuple]" = queue.Queue(maxsize=2000)
done = threading.Event()
stats = {"ok": 0, "fail": 0, "total": 0}
lock = threading.Lock()


def log(msg: str) -> None:
    line = f"{time.strftime('%FT%T')}\t{msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def embed_lot(texts: list) -> list:
    body = json.dumps({"model": MODEL, "input": texts}).encode()
    req = urllib.request.Request(
        M6_URL, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.load(r)
    return [d["embedding"] for d in data["data"]]


def worker(lots: "queue.Queue[list]") -> None:
    while True:
        try:
            lot = lots.get_nowait()
        except queue.Empty:
            return
        texts = [t[:4000] for (_id, t) in lot]
        for attempt in range(MAX_RETRY):
            try:
                vecs = embed_lot(texts)
                for (cid, _), v in zip(lot, vecs):
                    write_q.put((cid, struct.pack(f"{len(v)}f", *v), len(v)))
                break
            except Exception as e:
                if attempt == MAX_RETRY - 1:
                    with lock:
                        stats["fail"] += len(lot)
                    log(f"ABANDON lot de {len(lot)} après {MAX_RETRY} essais : {e}")
                else:
                    time.sleep(10 * (attempt + 1))


def writer() -> None:
    con = sqlite3.connect(DB, timeout=60)
    con.execute("PRAGMA busy_timeout=30000")
    pending = 0
    while not (done.is_set() and write_q.empty()):
        try:
            cid, blob, dim = write_q.get(timeout=2)
        except queue.Empty:
            continue
        for _ in range(10):
            try:
                con.execute(
                    "UPDATE chunks SET embedding=?, embedding_dim=?, embedding_model=? "
                    "WHERE id=? AND embedding IS NULL",
                    (blob, dim, MODEL, cid),
                )
                break
            except sqlite3.OperationalError:
                time.sleep(3)
        pending += 1
        with lock:
            stats["ok"] += 1
            if stats["ok"] % 1000 == 0:
                pct = 100 * stats["ok"] / max(1, stats["total"])
                log(
                    f"[{stats['ok']}/{stats['total']} {pct:.1f}%] écrits (échecs: {stats['fail']})"
                )
        if pending >= COMMIT_EVERY:
            con.commit()
            pending = 0
    con.commit()
    con.close()


def main() -> None:
    n_workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    domains = [sys.argv[2]] if len(sys.argv) > 2 else ["biblio-vivante", "souverainete"]
    ro = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    ro.row_factory = sqlite3.Row
    for dom in domains:
        rows = ro.execute(
            "SELECT id, text FROM chunks WHERE embedding IS NULL AND domain_id=? ORDER BY id",
            (dom,),
        ).fetchall()
        if not rows:
            log(f"{dom}: rien à embedder")
            continue
        with lock:
            stats["total"] += len(rows)
        log(f"{dom}: {len(rows)} chunks à vectoriser via M6 ({n_workers} workers)")
        lots: "queue.Queue[list]" = queue.Queue()
        for i in range(0, len(rows), LOT):
            lots.put([(r["id"], r["text"]) for r in rows[i : i + LOT]])
        wt = threading.Thread(target=writer, daemon=True)
        done.clear()
        wt.start()
        threads = [
            threading.Thread(target=worker, args=(lots,)) for _ in range(n_workers)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        done.set()
        wt.join()
        log(f"{dom}: terminé — ok={stats['ok']} fail={stats['fail']}")
    ro.close()
    log(f"FIN — écrits={stats['ok']} échecs={stats['fail']}")


if __name__ == "__main__":
    main()
