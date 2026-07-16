#!/usr/bin/env python3
import sys; sys.path.insert(0,"/home/pamerys/jarvis/webapp")
"""Élargit la base de séances : jusqu'à 3 notions/domaine/niveau non couvertes."""
import sqlite3, requests, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import banque_annuelle as b
HERE="/home/pamerys/jarvis/webapp"; TOK=open(HERE+"/.prof_token").read().strip()
c=sqlite3.connect(HERE+"/ecole.db"); c.row_factory=sqlite3.Row
done={r[0] for r in c.execute("SELECT sujet FROM sequences WHERE sujet IS NOT NULL")}
tasks=[]
for niv in ("MS","GS"):
    rows=c.execute("SELECT matiere,notion FROM banque WHERE niveau=?",(niv,)).fetchall()
    per_dom={d:0 for d in b.DOMAINES_2026}
    for r in rows:
        dom=b.domaine_2026(r["matiere"]); sujet=f"{r['notion']} — domaine « {dom} »"
        if per_dom[dom]>=3: continue
        if any(r["notion"] in s for s in done): continue
        tasks.append((niv,dom,r["notion"])); per_dom[dom]+=1
c.close()
print(f"{len(tasks)} séances à générer",flush=True)
def worker(t):
    niv,dom,notion=t; body={"sujet":f"{notion} — domaine « {dom} »","niveau":niv,"duree":30}
    for _ in range(6):
        try:
            d=requests.post("http://127.0.0.1:7777/api/sequence/generer",json=body,headers={"X-Prof-Token":TOK},timeout=180).json()
            if d.get("contenu_md") and len(d["contenu_md"])>400:
                print(f"✅ {niv}/{dom.split(' ')[0]}/{notion[:22]} {len(d['contenu_md'])}c",flush=True); return True
            print(f"⚠️ {niv}/{notion[:18]}: {d.get('error') or 'faible'}",flush=True)
        except Exception as e: print(f"… {niv}/{notion[:18]}: {e}",flush=True)
        time.sleep(20)
    return False
with ThreadPoolExecutor(max_workers=6) as ex:
    list(as_completed([ex.submit(worker,t) for t in tasks]))
print("=== FIN élargissement séances ===",flush=True)
