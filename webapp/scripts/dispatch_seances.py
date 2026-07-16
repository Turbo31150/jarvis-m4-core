#!/usr/bin/env python3
import sys; sys.path.insert(0,"/home/pamerys/jarvis/webapp")
"""Domino 0-token : 1 séance par domaine 2026 × MS/GS, déporté cloud."""
import sqlite3, requests, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import banque_annuelle as b
HERE="/home/pamerys/jarvis/webapp"
TOK=open(HERE+"/.prof_token").read().strip()
c=sqlite3.connect(HERE+"/ecole.db"); c.row_factory=sqlite3.Row
# 1 sujet représentatif par (niveau, domaine 2026) = une notion réelle de la banque
tasks=[]
for niv in ("MS","GS"):
    rows=c.execute("SELECT matiere,notion FROM banque WHERE niveau=?",(niv,)).fetchall()
    seen=set()
    for dom in b.DOMAINES_2026:
        for r in rows:
            if b.domaine_2026(r["matiere"])==dom and dom not in seen:
                sujet=f"{r['notion']} ({dom.split(' ')[0].lower()})"
                tasks.append((niv,dom,r["notion"])); seen.add(dom); break
c.close()
def worker(t):
    niv,dom,notion=t
    body={"sujet":f"{notion} — domaine « {dom} »","niveau":niv,"duree":30}
    for _ in range(6):
        try:
            r=requests.post("http://127.0.0.1:7777/api/sequence/generer",json=body,headers={"X-Prof-Token":TOK},timeout=180)
            d=r.json()
            if d.get("contenu_md") and len(d["contenu_md"])>400:
                print(f"✅ {niv}/{dom[:22]}/{notion[:24]} <{d.get('backend')}> {len(d['contenu_md'])}c",flush=True); return True
            print(f"⚠️ {niv}/{notion[:20]} faible: {d.get('error') or len(d.get('contenu_md',''))}",flush=True)
        except Exception as e:
            print(f"… retry {niv}/{notion[:20]}: {e}",flush=True)
        time.sleep(20)
    return False
with ThreadPoolExecutor(max_workers=5) as ex:
    list(as_completed([ex.submit(worker,t) for t in tasks]))
print("=== FIN séances par domaine ===",flush=True)
