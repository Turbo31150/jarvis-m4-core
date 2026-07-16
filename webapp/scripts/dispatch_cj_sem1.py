#!/usr/bin/env python3
"""Domino 0-token : cahier-journal semaine 1 MS (4 jours), déporté cloud."""
import sqlite3, requests, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
HERE="/home/pamerys/jarvis/webapp"
TOK=open(HERE+"/.prof_token").read().strip()
c=sqlite3.connect(HERE+"/ecole.db"); c.row_factory=sqlite3.Row
cr=c.execute("SELECT debut,fin,matiere,domaine FROM edt_creneaux WHERE niveau='MS/GS' AND jour=0 ORDER BY debut").fetchall()
edt="\n".join(f"{r['debut']}-{r['fin']} {r['matiere']}"+(f" [{r['domaine']}]" if r['domaine'] else "") for r in cr)
# notions P1 MS réparties sur les 4 jours
p1=[r["notion"] for r in c.execute("SELECT notion,periode FROM banque WHERE niveau='MS'").fetchall() if str(r["periode"]).strip() in ('1','P1','Période 1')]
c.close()
JOURS=[("2026-09-07","lundi"),("2026-09-08","mardi"),("2026-09-10","jeudi"),("2026-09-11","vendredi")]
def emploi_for(i):
    part=p1[i::4] if p1 else []
    return edt+"\n\nNotions de la période 1 à travailler en ateliers ce jour : "+", ".join(part[:4])
def worker(item):
    i,(dt,jn)=item
    body={"date":dt,"niveau":"MS","emploi_du_temps":emploi_for(i)}
    for _ in range(6):
        try:
            r=requests.post("http://127.0.0.1:7777/api/cahier-journal/generer",json=body,headers={"X-Prof-Token":TOK},timeout=180)
            d=r.json()
            if d.get("contenu_md"):
                print(f"✅ {dt} {jn} <{d.get('backend')}> {len(d['contenu_md'])} car",flush=True); return True
            print(f"⚠️ {dt} vide: {d.get('error')}",flush=True)
        except Exception as e:
            print(f"… retry {dt}: {e}",flush=True)
        time.sleep(20)
    return False
items=list(enumerate(JOURS))
with ThreadPoolExecutor(max_workers=4) as ex:
    list(as_completed([ex.submit(worker,it) for it in items]))
print("=== FIN cahier-journal semaine 1 ===",flush=True)
