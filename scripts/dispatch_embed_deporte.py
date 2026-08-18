#!/usr/bin/env python3
"""Dispatch de masse pour la vectorisation — recette dispatch-generation-masse.

Règle centrale : le compute part sur un backend DÉPORTÉ. C'est ce qui manquait
aux batchs `board.py embed` du 2026-08-18, qui tapaient l'Ollama LOCAL et ont
poussé M4 à 95 °C. Ici M4 ne fait que du réseau et du SQL.
"""
import json, sqlite3, struct, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

DB = "/home/pamerys/jarvis/databases/board.db"
# Backends déportés, par ordre de préférence. Jamais 127.0.0.1 : c'est la ligne
# qui sépare « 0 chaleur » de « 95 °C ».
BACKENDS = [
    ("M6-direct", "http://10.42.0.230:1234/v1/embeddings", "text-embedding-nomic-embed-text-v1.5"),
    ("Remi-ASUS", "http://100.113.121.61:11434/v1/embeddings", "nomic-embed-text:latest"),
]
WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 4
verrou_log = __import__("threading").Lock()

def log(m):
    with verrou_log:
        print(m, flush=True)

def vecteur(texte):
    """Renvoie (nom_backend, blob) — bascule au backend suivant s'il est muet."""
    dernier = None
    for nom, url, modele in BACKENDS:
        corps = json.dumps({"model": modele, "input": texte[:8000]}).encode()
        req = urllib.request.Request(url, data=corps,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                v = json.load(r)["data"][0]["embedding"]
            return nom, struct.pack(f"{len(v)}f", *v)
        except Exception as exc:
            dernier = f"{nom}: {exc}"
            continue
    raise RuntimeError(f"tous les backends déportés muets — {dernier}")

def manquants():
    """SQL d'abord : cible − déjà fait. 0 token."""
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    r = c.execute("select rowid, text from chunks where embedding is null").fetchall()
    c.close()
    return r

def worker(item, total, compteur):
    rid, texte = item
    for essai in range(6):
        try:
            nom, blob = vecteur(texte)
            c = sqlite3.connect(DB, timeout=60)
            # Idempotent : relançable sans doublon ni écrasement d'un vecteur déjà posé.
            c.execute("update chunks set embedding=? where rowid=? and embedding is null",
                      (blob, rid))
            c.commit(); c.close()
            n = compteur()
            log(f"  [{n}/{total} {100*n//total}%] ✅ chunk {rid} <{nom}>")
            return True
        except sqlite3.OperationalError:
            time.sleep(3)                      # base verrouillée
        except RuntimeError:
            time.sleep(25)                     # backends déportés indisponibles
        except Exception as exc:
            log(f"  chunk {rid} essai {essai+1} : {exc}")
            time.sleep(5)
    log(f"  ⛔ ABANDON chunk {rid} après 6 essais")   # jamais de troncature silencieuse
    return False

def main():
    cellules = manquants()
    total = len(cellules)
    if not total:
        log("Rien à faire : aucun chunk sans embedding."); return
    log(f"{total} chunk(s) à vectoriser · {WORKERS} workers · backends déportés uniquement")
    etat = {"n": 0}
    verrou = __import__("threading").Lock()
    def inc():
        with verrou:
            etat["n"] += 1; return etat["n"]
    ok = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futurs = [ex.submit(worker, c, total, inc) for c in cellules]
        for f in as_completed(futurs):
            ok += bool(f.result())
    log(f"Terminé : {ok}/{total} réussis, {total-ok} abandonnés")

if __name__ == "__main__":
    main()
