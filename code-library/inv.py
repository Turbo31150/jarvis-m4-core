#!/usr/bin/env python3
"""Index inventaire — trier/organiser vite. inv.py [--list|--statut X|--archive]"""
import sqlite3, os, sys, shutil
DB=os.path.join(os.path.dirname(__file__),"inventory.db")
ARCH=os.path.expanduser("~/archives/voice-doublons")
def c(): x=sqlite3.connect(DB); x.row_factory=sqlite3.Row; return x
def lst(statut=None):
    q="SELECT categorie,nom,chemin,taille_mo,statut,note FROM inventaire"
    a=[]
    if statut: q+=" WHERE statut=?"; a=[statut]
    q+=" ORDER BY categorie,statut,taille_mo DESC"
    for r in c().execute(q,a):
        print(f"  [{r['statut']:7}] {r['taille_mo']:6.0f}Mo  {r['nom']}")
        print(f"            {r['chemin']}  — {r['note']}")
def archive():
    conn=c(); os.makedirs(ARCH,exist_ok=True); moved=0; freed=0
    for r in conn.execute("SELECT chemin,taille_mo FROM inventaire WHERE statut='doublon'").fetchall():
        p=r["chemin"]
        if not os.path.exists(p): print(f"  (absent) {p}"); continue
        dest=os.path.join(ARCH,os.path.basename(p.rstrip('/')))
        try:
            shutil.move(p,dest); moved+=1; freed+=r["taille_mo"]
            conn.execute("UPDATE inventaire SET statut='archive',chemin=? WHERE chemin=?",(dest,p))
            print(f"  ✅ archivé {os.path.basename(p)} → {dest}")
        except Exception as e:
            print(f"  ⚠️ {os.path.basename(p)} : {e}")
    conn.commit()
    print(f"\n{moved} dossiers archivés · ~{freed:.0f} Mo libérés · archive : {ARCH}")
if __name__=="__main__":
    a=sys.argv[1:]
    if a and a[0]=="--archive": archive()
    elif a and a[0]=="--statut" and len(a)>1: lst(a[1])
    else: lst()
