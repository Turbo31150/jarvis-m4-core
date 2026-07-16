#!/usr/bin/env python3
"""Recherche dans la bibliothèque de code (SQL avant compute).
Usage: python3 lib.py <requête>   |   python3 lib.py --list   |   python3 lib.py --show <nom>"""
import sqlite3, os, sys, textwrap
DB = os.path.join(os.path.dirname(__file__), "code_library.db")

def _c(): 
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def search(q):
    c=_c()
    try:
        rows=c.execute("""SELECT p.* FROM patterns_fts f JOIN patterns p ON p.id=f.rowid
                          WHERE patterns_fts MATCH ? ORDER BY rank LIMIT 8""",(q,)).fetchall()
    except sqlite3.OperationalError:
        rows=c.execute("SELECT * FROM patterns WHERE triggers LIKE ? OR description LIKE ? LIMIT 8",
                       (f"%{q}%",f"%{q}%")).fetchall()
    if not rows: print(f"(aucun pattern pour « {q} »)"); return
    for r in rows:
        print(f"\n▸ {r['nom']}  [{r['categorie']}/{r['langage']}]")
        print(f"  {r['description']}")
        print(f"  quand: {r['quand_utiliser']}")
        print(f"  → détail : lib.py --show {r['nom']}")

def show(nom):
    c=_c(); r=c.execute("SELECT * FROM patterns WHERE nom=?",(nom,)).fetchone()
    if not r: print("introuvable"); return
    print(f"\n═══ {r['nom']} ═══  [{r['categorie']}/{r['langage']}]  (source: {r['source']})")
    print(f"\n{r['description']}\nQuand: {r['quand_utiliser']}\n\n--- code ---\n{r['code']}\n")

def lst():
    c=_c()
    for r in c.execute("SELECT nom,categorie,description FROM patterns ORDER BY categorie,nom"):
        print(f"  {r['nom']:32} [{r['categorie']:9}] {r['description'][:50]}")

if __name__=="__main__":
    a=sys.argv[1:]
    if not a or a[0]=="--list": lst()
    elif a[0]=="--show" and len(a)>1: show(a[1])
    else: search(" ".join(a))
