#!/usr/bin/env python3
# ouvrir_missions.py — ouvre dans le navigateur les missions qui meritent une candidature.
#
# Critere : encore VALIDE (validThrough non depasse), contrat freelance quand c est
# indique, et un mot-cle du positionnement dans le titre. Trie par TJM decroissant.
# N ouvre rien sans --go : par defaut il liste, c est tout.

import os, sqlite3, subprocess, sys
from datetime import datetime, UTC

DB = "/home/pamerys/jarvis/jarvis_master.db"
MOTS = ("ia", "ai", "n8n", "llm", "rag", "agent", "automat", "mlops", "data",
        "genai", "generative", "python")

def main():
    go = "--go" in sys.argv
    maxi = 8
    tjm_min = 0
    ville = None
    for a in sys.argv:
        if a.startswith("--max="):  maxi = int(a.split("=")[1])
        if a.startswith("--tjm="):  tjm_min = int(a.split("=")[1])
        if a.startswith("--ville="): ville = a.split("=")[1].lower()

    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    auj = datetime.now(UTC).strftime("%Y-%m-%d")
    rows = c.execute("SELECT * FROM freework_missions").fetchall()
    ret = []
    for r in rows:
        t = (r["titre"] or "").lower()
        if not any(m in t for m in MOTS):
            continue
        if r["valide_jusqu"] and r["valide_jusqu"] < auj:
            continue                                   # mission expiree
        if ville and ville not in (r["ville"] or "").lower():
            continue
        try: tj = int(r["tjm_max"] or r["tjm_min"] or 0)
        except ValueError: tj = 0
        if tjm_min and tj < tjm_min:
            continue
        ret.append((tj, r))
    ret.sort(key=lambda x: -x[0])

    print(f"\n  {len(ret)} mission(s) valide(s) et pertinente(s)"
          + (f", TJM >= {tjm_min}" if tjm_min else "")
          + (f", ville {ville}" if ville else "") + "\n")
    print(f"  {'TJM':>11}  {'valide→':<11} {'ville':<16} mission")
    print(f"  {'-'*11}  {'-'*11} {'-'*16} {'-'*46}")
    for tj, r in ret[:maxi]:
        aff = (f"{r['tjm_min']}-{r['tjm_max']}" if r["tjm_min"] != r["tjm_max"]
               else r["tjm_min"]) or "non affiche"
        print(f"  {aff:>11}  {r['valide_jusqu'] or '?':<11} {(r['ville'] or '?')[:16]:<16} {r['titre'][:46]}")
        if not go:
            print(f"  {'':>11}  {r['url'][:88]}")
    if not go:
        print(f"\n  (ajouter --go pour les ouvrir dans le navigateur)\n")
        return
    print(f"\n  ouverture de {min(maxi,len(ret))} onglet(s)...")
    env = dict(os.environ, DISPLAY=":0", XDG_RUNTIME_DIR="/run/user/1000")
    for tj, r in ret[:maxi]:
        subprocess.Popen(["xdg-open", r["url"]], env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"    {r['titre'][:64]}")
        import time; time.sleep(2.5)
    c.close()

if __name__ == "__main__":
    main()
