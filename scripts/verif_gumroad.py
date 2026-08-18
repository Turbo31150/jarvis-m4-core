#!/usr/bin/env python3
"""Vérifie que chaque produit Gumroad référencé existe vraiment.

Un lien présent dans une page de vente ne prouve pas que le produit est publié
et payable. Envoyer du trafic vers un lien mort brûle l'audience — on sonde
donc les 66 slugs avant toute promotion.

Massivement parallèle et sans coût : ce sont de simples requêtes HTTP, aucune
inférence. La mémoire consommée est négligeable, ce qui compte sur une machine
déjà à 92 % de RAM.

Usage : python3 verif_gumroad.py [concurrence]
"""

import json
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

INVENTAIRE = Path("/home/pamerys/jarvis/data/gumroad_inventaire.json")
SORTIE = Path("/home/pamerys/jarvis/data/gumroad_verif.json")
CONCURRENCE = int(sys.argv[1]) if len(sys.argv) > 1 else 12
UA = "Mozilla/5.0 (X11; Linux x86_64) verif-inventaire/1.0"


def sonder(produit):
    slug = produit["slug"]
    url = f"https://gumroad.com/l/{slug}"
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            corps = r.read(20000).decode("utf-8", "replace")
            code = r.status
            final = r.geturl()
    except urllib.error.HTTPError as e:
        return {**produit, "http": e.code, "verdict": "MORT"}
    except Exception as e:
        return {
            **produit,
            "http": 0,
            "verdict": "INJOIGNABLE",
            "erreur": type(e).__name__,
        }

    # Gumroad renvoie 200 sur des pages « produit introuvable » : le code seul
    # ne suffit pas, on cherche un signe d'achat réel dans la page.
    bas = corps.lower()
    achetable = any(
        m in bas
        for m in (
            "add to cart",
            "ajouter au panier",
            "i want this",
            "je le veux",
            '"price"',
        )
    )
    introuvable = any(
        m in bas
        for m in (
            "page not found",
            "introuvable",
            "no longer available",
            "n'existe plus",
        )
    )
    if introuvable:
        verdict = "MORT"
    elif achetable:
        verdict = "PUBLIE"
    else:
        verdict = "DOUTEUX"
    return {**produit, "http": code, "url_finale": final, "verdict": verdict}


def main():
    if not INVENTAIRE.exists():
        print(f"❌ inventaire absent : {INVENTAIRE}")
        sys.exit(1)
    produits = json.loads(INVENTAIRE.read_text("utf-8"))
    print(
        f"sondage de {len(produits)} produits · {CONCURRENCE} en parallèle", flush=True
    )

    res = []
    with ThreadPoolExecutor(max_workers=CONCURRENCE) as ex:
        futs = {ex.submit(sonder, p): p for p in produits}
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            res.append(r)
            print(f"[{i}/{len(produits)}] {r['verdict']:12} {r['slug']}", flush=True)

    SORTIE.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    compte = {}
    for r in res:
        compte[r["verdict"]] = compte.get(r["verdict"], 0) + 1
    print("\n=== BILAN ===")
    for v, n in sorted(compte.items(), key=lambda x: -x[1]):
        print(f"  {n:3}  {v}")
    morts = [r["slug"] for r in res if r["verdict"] in ("MORT", "INJOIGNABLE")]
    if morts:
        print(f"\nÀ ne PAS promouvoir ({len(morts)}) : {', '.join(morts[:15])}")
    print(f"\ndétail : {SORTIE}")


if __name__ == "__main__":
    main()
