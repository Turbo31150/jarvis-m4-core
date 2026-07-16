#!/usr/bin/env python3
import sys; sys.path.insert(0,"/home/pamerys/jarvis/webapp")
"""3 mois d'avance MS (Sept-Nov 2026), auto-améliorant :
bibliothèque d'abord (cache via route) -> log -> score -> correction -> KB."""
import sqlite3, requests, time, json, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
import banque_annuelle as b
HERE="/home/pamerys/jarvis/webapp"; TOK=open(HERE+"/.prof_token").read().strip()
DB=HERE+"/ecole.db"
c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
jours=json.loads(c.execute("SELECT v FROM kv WHERE k='calendrier_sept_nov_2026'").fetchone()[0])
cr=c.execute("SELECT debut,fin,matiere,domaine FROM edt_creneaux WHERE niveau='MS/GS' AND jour=0 ORDER BY debut").fetchall()
edt="\n".join(f"{r['debut']}-{r['fin']} {r['matiere']}"+(f" [{r['domaine']}]" if r['domaine'] else "") for r in cr)
rows=c.execute("SELECT matiere,notion,periode FROM banque WHERE niveau='MS'").fetchall()
def notions(per): return [r["notion"] for r in rows if str(r["periode"]).strip() in per]
P1=notions(('1','P1','Période 1')); P2=notions(('2','P2','Période 2'))
c.close()
TOUSS=dt.date(2026,10,17)
def week_notions(d, idx):
    per=P1 if dt.date.fromisoformat(d)<TOUSS else P2
    if not per: per=P1 or P2
    return per[idx::4][:4] if per else []
def score(txt):
    if not txt: return 0
    t=txt.lower(); s=0
    for kw in ("objectif","activité","matériel","déroul","différenci","observ"):
        if kw in t: s+=15
    if len(txt)>=1500: s+=10
    return min(s,100)
def kb_log(cible,backend,sc,ok,retries,note):
    cc=sqlite3.connect(DB)
    for _ in range(5):
        try: cc.execute("INSERT INTO generation_kb(tache,cible,backend,score,ok,retries,note) VALUES('cahier-journal-3mois-MS',?,?,?,?,?,?)",(cible,backend,sc,ok,retries,note)); cc.commit(); break
        except sqlite3.OperationalError: time.sleep(2)
    cc.close()
def gen(dt_iso, strict, notions_j):
    emploi=edt+"\n\nNotions de la semaine (à travailler en ateliers) : "+", ".join(notions_j)
    if strict: emploi+="\n\nSTRUCTURE IMPÉRATIVE pour CHAQUE créneau : Objectif — Activités — Matériel — Organisation — Différenciation — Observations à compléter."
    r=requests.post("http://127.0.0.1:7777/api/cahier-journal/generer",json={"date":dt_iso,"niveau":"MS","emploi_du_temps":emploi},headers={"X-Prof-Token":TOK},timeout=200)
    return r.json()
def worker(item):
    idx,dt_iso=item; nj=week_notions(dt_iso,idx%4); retries=0
    for attempt in range(6):
        try:
            d=gen(dt_iso, attempt>0, nj); txt=d.get("contenu_md",""); sc=score(txt); bk=d.get("backend","?")
            if txt and sc>=60:
                kb_log(dt_iso,bk,sc,1,retries,"ok"); print(f"✅ {dt_iso} score={sc} <{bk}> {len(txt)}c",flush=True); return True
            retries+=1
            if not txt: print(f"… {dt_iso} vide {d.get('error')}",flush=True); time.sleep(20); continue
            print(f"↻ {dt_iso} score={sc} faible → correction",flush=True)  # score bas → retry strict
        except Exception as e:
            print(f"… {dt_iso}: {e}",flush=True); time.sleep(20)
    kb_log(dt_iso,"?",sc if 'sc' in dir() else 0,0,retries,"échec après 6"); print(f"❌ {dt_iso} abandon",flush=True); return False
items=list(enumerate(jours))
print(f"→ {len(items)} journées à générer (auto-améliorant)",flush=True)
with ThreadPoolExecutor(max_workers=6) as ex:
    list(as_completed([ex.submit(worker,it) for it in items]))
print("=== FIN 3 mois MS ===",flush=True)
