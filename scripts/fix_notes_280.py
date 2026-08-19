#!/usr/bin/env python3
# fix_notes_280.py — remet les notes d invitation sous la limite LinkedIn (280 c).
#
# POURQUOI ce correctif existe : la consigne "280 caracteres MAXIMUM" placee dans le
# prompt a ete respectee 18 fois sur 45. Un LLM ne compte pas les caracteres — lui
# demander une longueur exacte est une contrainte VERBALE, sans effet mecanique.
# On la remplace par deux contraintes DETERMINISTES :
#   1. budget de tokens serre (le modele ne PEUT physiquement pas depasser de beaucoup)
#   2. troncature a la derniere phrase complete sous 280 (jamais de phrase coupee)
# Resultat garanti par construction, pas espere.

import sqlite3, sys, time
from array import array
sys.path.insert(0, "/home/pamerys/jarvis/scripts")
import dispatch_superposition as D

LIMITE = 280

def tronque_phrase(t, limite=LIMITE):
    """Coupe a la derniere frontiere de phrase sous la limite. Jamais en plein mot."""
    t = " ".join(t.split())
    if len(t) <= limite:
        return t
    coupe = t[:limite]
    for sep in (". ", "! ", "? "):
        i = coupe.rfind(sep)
        if i > limite * 0.5:                       # garde au moins la moitie utile
            return coupe[:i+1].strip()
    if coupe.endswith("."):
        return coupe.strip()
    i = coupe.rfind(" ")                           # repli : dernier mot entier
    return (coupe[:i].rstrip(" ,;:") + ".") if i > 0 else coupe

def main():
    c = sqlite3.connect(D.DB); c.row_factory = sqlite3.Row
    trop = c.execute("""SELECT cible_ref,angle,cible_nom,n_car FROM simulation_superposition
                        WHERE canal='RECRUTEUR' AND n_car > ?""", (LIMITE,)).fetchall()
    c.close()
    if not trop:
        print("Aucune note hors limite."); return
    print(f"{len(trop)} note(s) hors limite a reprendre (budget token serre + troncature)\n")
    ok = 0
    for r in trop:
        cons = D.ANGLES_RECRUTEUR[r["angle"]]
        p = D.prompt_recruteur(r["cible_nom"], cons) + \
            "\n\nCONTRAINTE RENFORCEE : 2 phrases COURTES au total. Va droit au but."
        for essai in range(4):
            try:
                # 88 tokens ~ 300 caracteres en francais : le modele ne peut plus
                # deborder largement, la troncature ne rattrape qu un petit reste.
                txt = D.generer(p, max_tokens=88, temperature=0.6)
                if not txt.strip():
                    raise D.Indispo("vide")
                final = tronque_phrase(txt)
                vec = D.vectoriser(final)
                cel = dict(ref=r["cible_ref"], canal="RECRUTEUR", nom=r["cible_nom"],
                           ent="", angle=r["angle"])
                D.ecrire(cel, final, vec, 0)
                print(f"  {r['cible_ref']:<14} {r['angle']:<9} {r['n_car']:>4}c -> {len(final):>4}c  "
                      f"{'OK' if len(final)<=LIMITE else 'ENCORE TROP'}")
                ok += 1; break
            except D.Indispo:
                time.sleep(20)
            except Exception as e:
                print(f"  ERREUR {r['cible_ref']}|{r['angle']} : {e}"); break
    print(f"\n{ok}/{len(trop)} reprises")
    c = sqlite3.connect(D.DB)
    a, b, mx = c.execute("""SELECT SUM(n_car<=?), COUNT(*), MAX(n_car)
                            FROM simulation_superposition WHERE canal='RECRUTEUR'""", (LIMITE,)).fetchone()
    c.close()
    print(f"conformite finale : {a}/{b} sous {LIMITE}c  (max = {mx}c)")

if __name__ == "__main__":
    main()
