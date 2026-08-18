#!/usr/bin/env python3
"""route.py "<intent>" → département + cible (lit org_routing). 0-token."""
import sqlite3,sys,re
q=" ".join(sys.argv[1:]).lower()
con=sqlite3.connect("/home/turbo/jarvis/jarvis.db")
for intent,dept,target in con.execute("SELECT intent,dept,target FROM org_routing"):
    if re.search(intent,q): print(f"{dept} → {target}"); break
else: print("dept.infra → jarvis_master (défaut)")
