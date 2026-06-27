#!/usr/bin/env python3
"""Agent JARVIS — Gestion RDV et agenda (intégration webapp calendar)"""
import sys, requests, sqlite3, json, os
from datetime import datetime

RDV_DB = os.path.expanduser("~/jarvis/rdv.db")
PLANNING_DB = os.path.expanduser("~/jarvis/planning.db")

def get_rdv_today():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(RDV_DB) if os.path.exists(RDV_DB) else None
    if not conn:
        return []
    rows = conn.execute("SELECT * FROM rdv WHERE date=? ORDER BY heure_debut", (today,)).fetchall()
    conn.close()
    return rows

def add_rdv(titre, date, heure="", type_rdv="rdv", desc=""):
    conn = sqlite3.connect(RDV_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS rdv (id INTEGER PRIMARY KEY AUTOINCREMENT, titre TEXT, date TEXT, heure_debut TEXT, heure_fin TEXT, type TEXT, description TEXT)")
    conn.execute("INSERT INTO rdv(titre,date,heure_debut,type,description) VALUES(?,?,?,?,?)",
        (titre, date, heure, type_rdv, desc))
    conn.commit(); conn.close()
    print(f"✅ RDV ajouté: {titre} le {date} à {heure}")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        rdvs = get_rdv_today()
        if rdvs:
            print(f"RDV aujourd'hui ({len(rdvs)}):")
            for r in rdvs: print(f"  {r[4] or '?'}h — {r[1]}")
        else:
            print("Aucun RDV aujourd'hui")
    elif args[0] == "add" and len(args) >= 3:
        add_rdv(args[1], args[2], args[3] if len(args)>3 else "")
