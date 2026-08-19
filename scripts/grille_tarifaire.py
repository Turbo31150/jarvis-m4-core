#!/usr/bin/env python3
# grille_tarifaire.py — la grille de prix reelle du marche n8n. 0 inference, SQL seul.
#
# Lit les annonces [FOR HIRE] moissonnees et restitue ce que les prestataires
# AFFICHENT. Aucune moyenne inventee : si une annonce ne porte pas de montant
# lisible, elle est comptee dans "prix non affiche", jamais estimee.

import json, re, sqlite3, sys
from collections import Counter
from datetime import datetime, UTC

DB = "/home/pamerys/jarvis/jarvis_master.db"
# Taux indicatifs, dates. Servent UNIQUEMENT a ordonner la liste, jamais a
# presenter un montant converti comme s il etait affiche.
TAUX = {"$": 0.92, "USD": 0.92, "USDC": 0.92, "€": 1.0, "EUR": 1.0,
        "£": 1.17, "GBP": 1.17, "¥": 0.0060, "JPY": 0.0060, "CAD": 0.66, "AUD": 0.60}

def en_euros(brut):
    """Ordre de grandeur en euros, pour trier. None si non convertible."""
    m = re.search(r"([$€£¥]|USD|EUR|GBP|JPY|CAD|AUD|USDC)\s*([\d ,.]+)", brut, re.I)
    if not m: return None
    dev = m.group(1).upper()
    val = m.group(2).strip().replace(" ", "")
    val = val.replace(",", "") if re.match(r"^\d{1,3}(,\d{3})+$", m.group(2).strip()) else val.replace(",", ".")
    try: n = float(val)
    except ValueError: return None
    t = TAUX.get(dev) or TAUX.get(m.group(1))
    return round(n * t) if t else None

def age(d):
    if not d: return None
    try: return (datetime.now(UTC) - datetime.fromisoformat(d + "T00:00:00+00:00")).days
    except Exception: return None

def main():
    max_j = 120
    for a in sys.argv:
        if a.startswith("--max-jours="): max_j = int(a.split("=")[1])
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    try:
        rows = c.execute("SELECT * FROM n8n_jobs WHERE sens='OFFRE' ORDER BY cree_le DESC").fetchall()
    except sqlite3.OperationalError:
        print("table n8n_jobs absente — lancer moisson_n8n_jobs.py d abord"); return

    avec, sans = [], []
    for r in rows:
        prix = json.loads(r["prix"] or "[]")
        (avec if prix else sans).append((r, prix))

    print(f"\n{'='*98}")
    print(f"  GRILLE TARIFAIRE — annonces [FOR HIRE] du forum n8n")
    print(f"  {len(rows)} offres de prestation · {len(avec)} affichent un prix · {len(sans)} n en affichent pas")
    print(f"{'='*98}\n")

    lignes = []
    for r, prix in avec:
        e = next((v for v in (en_euros(p) for p in prix) if v), None)
        lignes.append((e if e is not None else 10**9, r["topic_id"], r, prix))
    lignes.sort()

    print(f"  {'~EUR':>7}  {'affiche':<22} {'j':>4}  {'vues':>5}  prestation")
    print(f"  {'-'*7}  {'-'*22} {'-'*4}  {'-'*5}  {'-'*50}")
    for e, _tid, r, prix in lignes:
        j = age(r["cree_le"])
        if max_j and j is not None and j > max_j: continue
        t = re.sub(r"\[?(FOR HIRE|For Hire|for hire)\]?", "", r["titre"], flags=re.I).strip(" —-:")
        ev = f"{e}" if e < 10**9 else "?"
        print(f"  {ev:>7}  {prix[0][:22]:<22} {(j if j is not None else '?'):>4}  {r['vues']:>5}  {t[:52]}")

    if lignes:
        vals = sorted(e for e, _t, _r, _p in lignes if e < 10**9)
        if vals:
            def q(p): return vals[min(len(vals)-1, int(p*len(vals)))]
            print(f"\n  Repartition des montants affiches (ordre de grandeur en EUR, taux indicatifs) :")
            print(f"    minimum {vals[0]} · median {q(.5)} · haut de fourchette {vals[-1]}  sur {len(vals)} annonces")

    if sans:
        print(f"\n── {len(sans)} offre(s) SANS prix affiche (non estimees) :")
        for r, _ in sans[:8]:
            t = re.sub(r"\[?(FOR HIRE|For Hire|for hire)\]?", "", r["titre"], flags=re.I).strip(" —-:")
            print(f"    {t[:78]}")
    print()
    c.close()

if __name__ == "__main__":
    main()
