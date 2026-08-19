#!/usr/bin/env python3
"""board-purifier — ramene board.db a UN SEUL espace vectoriel (LM Studio M6).

    board-purifier.py [--workers 8] [--limit N] [--etat]

Pourquoi : le corpus contenait deux moteurs melanges — 122 224 chunks Ollama
(cosinus 1.0000 contre Ollama) et 65 861 LM Studio (0.9998). Un corpus vectoriel
n'admet qu'un seul moteur, prefixe compris ; 0,93 n'est pas « assez proche »,
c'est un autre espace, et la recherche semantique y devient du bruit SANS erreur.

Trois choses apprises au sol le 19/08/2026, encodees ici :

  MODELE SERVI — LM Studio IGNORE le nom demande sur /v1/embeddings et renvoie
      toujours le modele d'embedding charge. On enregistre donc le nom qu'il
      RENVOIE (data.model), jamais celui qu'on demande. Sinon la colonne ment.

  TRONCATURE  — le modele coupe vers 4 000 caracteres : le vecteur d'un chunk de
      1,6 Mo est identique a celui de ses 4 000 premiers caracteres (cos 1.0000),
      et la fin du texte n'y est pas (0,7720). On marque embedding_tronque=1
      plutot que de faire croire que le chunk entier est represente.

  8 WORKERS   — mesure : 8 -> 27,7 chunks/s, 4 -> 23,7, 12 -> 25,0.
      L'optimum n'est pas le maximum.
"""
import argparse, json, math, os, sqlite3, struct, sys, threading, time, urllib.request
import queue as Q

DB = os.path.expanduser("~/jarvis/databases/board.db")
URL = "http://10.42.0.230:1234/v1/embeddings"
MODELE = "text-embedding-nomic-embed-text-v1.5"
PREFIXE = "search_document: "
SEUIL_TRONC = 4000

CONFORME = "embedding IS NOT NULL AND embedding_model = ?"
A_FAIRE = "embedding IS NULL OR embedding_model IS NULL OR embedding_model <> ?"


def etat():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    print("── board.db ──")
    for lot, sql in (("deja conformes", CONFORME), ("a traiter", A_FAIRE)):
        n = c.execute(f"SELECT count(*) FROM chunks WHERE {sql}", (MODELE,)).fetchone()[0]
        print(f"  {lot:<16} {n}")
    for m, n in c.execute("SELECT COALESCE(embedding_model,'(null)'),count(*) FROM chunks "
                          "WHERE embedding IS NOT NULL GROUP BY 1 ORDER BY 2 DESC"):
        print(f"    {m:<40} {n}")
    c.close()


def embed(texte):
    """Renvoie (vecteur, modele_servi). Le modele servi vient du serveur.

    On coupe a SEUIL_TRONC AVANT l'envoi. Ce n'est pas une degradation : le
    modele tronque de toute facon vers 4 000 caracteres — prouve le 19/08, le
    vecteur d'un chunk de 1,6 Mo est identique a celui de ses 4 000 premiers
    caracteres (cos 1.0000) et n'en contient pas la fin (0,7720). Envoyer le
    texte entier produisait donc EXACTEMENT le meme vecteur en payant la
    bande passante et le temps de tokenisation."""
    corps = json.dumps({"model": MODELE, "input": PREFIXE + texte[:SEUIL_TRONC]}).encode()
    req = urllib.request.Request(URL, data=corps, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    return d["data"][0]["embedding"], d.get("model") or MODELE


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--etat", action="store_true")
    a = p.parse_args()
    if a.etat:
        return etat()

    lec = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    sql = f"SELECT id, text FROM chunks WHERE {A_FAIRE} ORDER BY length(text)"
    lot = lec.execute(sql + (f" LIMIT {a.limit}" if a.limit else ""), (MODELE,)).fetchall()
    lec.close()
    total = len(lot)
    if not total:
        print("Rien a traiter."); return
    print(f"── {total} chunks · {a.workers} workers · {URL} · prefixe '{PREFIXE.strip()}'")

    entree = Q.Queue()
    for r in lot:
        entree.put(r)
    sortie = Q.Queue()
    compte = {"ok": 0, "ko": 0, "tronq": 0}
    verrou = threading.Lock()
    t0 = time.time()

    def bosseur():
        while True:
            try:
                cid, texte = entree.get_nowait()
            except Q.Empty:
                return
            try:
                v, servi = embed(texte)
                blob = struct.pack(f"<{len(v)}f", *v)
                tronq = 1 if len(texte) > SEUIL_TRONC else 0
                sortie.put((blob, len(v), servi, tronq, cid))
                with verrou:
                    compte["ok"] += 1
                    compte["tronq"] += tronq
            except Exception:
                with verrou:
                    compte["ko"] += 1
            finally:
                entree.task_done()

    fils = [threading.Thread(target=bosseur, daemon=True) for _ in range(a.workers)]
    for f in fils:
        f.start()

    # Un SEUL ecrivain : SQLite n'aime pas les ecritures concurrentes.
    ecr = sqlite3.connect(DB)
    ecr.execute("PRAGMA journal_mode=WAL")
    tampon, dernier = [], time.time()
    while any(f.is_alive() for f in fils) or not sortie.empty():
        try:
            tampon.append(sortie.get(timeout=1))
        except Q.Empty:
            pass
        if len(tampon) >= 200 or (tampon and time.time() - dernier > 10):
            ecr.executemany("UPDATE chunks SET embedding=?, embedding_dim=?, "
                            "embedding_model=?, embedding_tronque=? WHERE id=?", tampon)
            ecr.commit()
            tampon.clear(); dernier = time.time()
            fait = compte["ok"] + compte["ko"]
            d = time.time() - t0
            print(f"  {fait}/{total} — {compte['ok']} ok, {compte['ko']} echecs, "
                  f"{compte['tronq']} tronques — {fait/d:.1f} chunks/s", flush=True)
    if tampon:
        ecr.executemany("UPDATE chunks SET embedding=?, embedding_dim=?, "
                        "embedding_model=?, embedding_tronque=? WHERE id=?", tampon)
        ecr.commit()
    ecr.close()
    d = time.time() - t0
    print(f"\n✓ {compte['ok']}/{total} vectorises · {compte['ko']} echecs · "
          f"{compte['tronq']} marques tronques · {d/60:.1f} min · {compte['ok']/d:.1f} chunks/s")


main()
