#!/usr/bin/env python3
"""Dispatch parallèle du remplissage de la banque annuelle (Pousseline).

Fan-out de N workers -> cascade ai_local. En pratique le compute part sur
Ollama cloud (gpt-oss:120b) : déporté = 0 token facturé ET 0 chaleur sur le M4.
Ne génère QUE les cellules manquantes (idempotent, ON CONFLICT en DB).
Retry anti-surchauffe : si le garde-fou 82 °C bloque, la cellule est requeue.

Usage : python3 dispatch_banque.py [workers=6] [--only NIVEAU]
"""

import sys
import time
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, "/home/pamerys/jarvis/webapp")
import ai_local  # noqa: E402
import banque_annuelle as B  # noqa: E402

WORKERS = 6
ONLY = None
args = sys.argv[1:]
for i, a in enumerate(args):
    if a == "--only" and i + 1 < len(args):
        ONLY = args[i + 1]
    elif a.isdigit():
        WORKERS = int(a)

DB = B.ECOLE_DB
LOG = "/home/pamerys/jarvis/webapp/backups/dispatch_banque.log"
_lock = threading.Lock()
_done = 0


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def manquants():
    c = sqlite3.connect(DB)
    have = {
        r[0] for r in c.execute("SELECT niveau||'|'||matiere||'|'||notion FROM banque")
    }
    c.close()
    niveaux = [ONLY] if ONLY else B.NIVEAUX
    cells = []
    for niv in niveaux:
        for cell in B._cells(niv):
            key = f"{cell['niveau']}|{cell['matiere']}|{cell['notion']}"
            if key not in have:
                cells.append(cell)
    return cells


def worker(cell, total):
    global _done
    label = f"{cell['niveau']}/{cell['matiere']}/{cell['notion'][:30]}"
    for attempt in range(6):
        try:
            res = B._generate_cell(
                cell["niveau"], cell["matiere"], cell["notion"], cell["periode"]
            )
            with _lock:
                _done += 1
                pct = 100 * _done // total
                log(f"[{_done}/{total} {pct}%] ✅ {label}  <{res['backend']}>")
            return True
        except ai_local.AIUnavailable:
            time.sleep(25)  # surchauffe/backends KO -> on laisse refroidir
        except sqlite3.OperationalError:
            time.sleep(3)  # DB lock transitoire
        except Exception as e:
            log(f"⚠️  {label} : {type(e).__name__} {e}")
            time.sleep(5)
    log(f"❌ ABANDON après 6 essais : {label}")
    return False


def main():
    cells = manquants()
    total = len(cells)
    if not total:
        log("🎉 Banque complète — 0 cellule manquante.")
        return
    log(
        f"=== DISPATCH BANQUE : {total} paquets · {WORKERS} workers parallèles "
        f"· cible Ollama cloud (0 token, déporté) ==="
    )
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(worker, c, total) for c in cells]
        for _ in as_completed(futs):
            pass
    dt = int(time.time() - t0)
    ok = sum(1 for f in futs if f.result())
    log(f"=== FIN : {ok}/{total} en {dt // 60}m{dt % 60}s ===")


if __name__ == "__main__":
    main()
