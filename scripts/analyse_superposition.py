#!/usr/bin/env python3
# analyse_superposition.py — mesure la superposition, 0 inference, 0 token.
#
# Deux questions, une seule methode : la geometrie des embeddings.
#
#  1. COLLAPSE INTRA-CIBLE : les N angles d une meme cible ont-ils vraiment produit
#     N messages distincts, ou un seul message reformule ? Similarite cosinus haute
#     entre angles = superposition effondree, le choix d angle n a servi a rien.
#
#  2. TEMPLATE INTER-CIBLE : le message ecrit pour l entreprise A ressemble-t-il a
#     celui ecrit pour B ? Similarite haute = la "personnalisation" est cosmetique.
#     C est le test decisif : il distingue un vrai sur-mesure d un publipostage.

import sqlite3, math, sys
from array import array
from collections import defaultdict

DB = "/home/pamerys/jarvis/jarvis_master.db"

def cos(a, b):
    n = min(len(a), len(b))
    num = sum(a[i]*b[i] for i in range(n))
    da = math.sqrt(sum(x*x for x in a[:n])); db = math.sqrt(sum(x*x for x in b[:n]))
    return num/(da*db) if da and db else 0.0

def charger():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    rows = c.execute("""SELECT cible_ref,canal,cible_nom,cible_entreprise,angle,texte,n_car,embedding,dim
                        FROM simulation_superposition WHERE embedding IS NOT NULL""").fetchall()
    c.close()
    out = []
    for r in rows:
        v = array("f"); v.frombytes(r["embedding"])
        out.append(dict(ref=r["cible_ref"], canal=r["canal"], nom=r["cible_nom"],
                        ent=r["cible_entreprise"], angle=r["angle"], texte=r["texte"],
                        n_car=r["n_car"], vec=list(v)))
    return out

def barre(x, lo=0.5, hi=1.0, w=22):
    p = max(0.0, min(1.0, (x-lo)/(hi-lo)))
    n = int(p*w); return "#"*n + "."*(w-n)

def main():
    data = charger()
    if not data:
        print("Aucune variante vectorisee en base."); return
    par_cible = defaultdict(list)
    for d in data: par_cible[d["ref"]].append(d)

    print(f"\n{'='*78}")
    print(f"  SUPERPOSITION — {len(data)} variantes / {len(par_cible)} cibles / dim 768 (M6 nomic)")
    print(f"{'='*78}\n")

    # ---- 1. COLLAPSE INTRA-CIBLE ------------------------------------------
    print("1. COLLAPSE INTRA-CIBLE — les angles produisent-ils des messages distincts ?")
    print("   (cos moyen entre angles d une meme cible ; plus BAS = plus distinct)\n")
    print(f"   {'cible':<16} {'canal':<10} {'n':>2}  {'cos moy':>7}  {'max':>6}  divergence")
    print(f"   {'-'*16} {'-'*10} {'-'*2}  {'-'*7}  {'-'*6}  {'-'*22}")
    stats_intra, collapses = [], []
    for ref, grp in sorted(par_cible.items()):
        if len(grp) < 2: continue
        sims = []
        for i in range(len(grp)):
            for j in range(i+1, len(grp)):
                s = cos(grp[i]["vec"], grp[j]["vec"])
                sims.append((s, grp[i]["angle"], grp[j]["angle"]))
        moy = sum(s for s,_,_ in sims)/len(sims)
        mx  = max(sims, key=lambda t: t[0])
        stats_intra.append(moy)
        ent = (grp[0]["ent"] or grp[0]["nom"] or "")[:14]
        print(f"   {ent:<16} {grp[0]['canal']:<10} {len(grp):>2}  {moy:>7.3f}  {mx[0]:>6.3f}  {barre(moy)}")
        if mx[0] > 0.93:
            collapses.append((ent, mx[1], mx[2], mx[0]))
    if stats_intra:
        print(f"\n   cos intra moyen global : {sum(stats_intra)/len(stats_intra):.3f}")
    if collapses:
        print(f"\n   [!] {len(collapses)} paire(s) d angles quasi identiques (cos > 0.93) :")
        for e,a1,a2,s in sorted(collapses, key=lambda t:-t[3])[:10]:
            print(f"       {e:<16} {a1} ~ {a2}  cos={s:.3f}  -> l angle n a rien change")
    else:
        print("\n   Aucune paire d angles au-dessus de 0.93 : la superposition tient.")

    # ---- 2. TEMPLATE INTER-CIBLE ------------------------------------------
    print(f"\n\n2. TEMPLATE INTER-CIBLE — la personnalisation est-elle reelle ?")
    print("   (a angle EGAL, cos entre cibles differentes ; HAUT = publipostage)\n")
    par_angle = defaultdict(list)
    for d in data: par_angle[(d["canal"], d["angle"])].append(d)
    print(f"   {'canal':<10} {'angle':<13} {'n':>3}  {'cos inter':>9}  lecture")
    print(f"   {'-'*10} {'-'*13} {'-'*3}  {'-'*9}  {'-'*30}")
    for (canal, angle), grp in sorted(par_angle.items()):
        if len(grp) < 2: continue
        sims = [cos(grp[i]["vec"], grp[j]["vec"])
                for i in range(len(grp)) for j in range(i+1, len(grp))]
        moy = sum(sims)/len(sims)
        verdict = ("PUBLIPOSTAGE" if moy > 0.90 else
                   "tres proche"  if moy > 0.85 else
                   "proche"       if moy > 0.78 else "personnalise")
        print(f"   {canal:<10} {angle:<13} {len(grp):>3}  {moy:>9.3f}  {verdict}")

    # ---- 3. ECART INTRA vs INTER ------------------------------------------
    print(f"\n\n3. VERDICT — l ecart entre les deux mesures")
    intra = sum(stats_intra)/len(stats_intra) if stats_intra else 0
    inter_all = []
    for (canal, angle), grp in par_angle.items():
        if len(grp) < 2: continue
        inter_all += [cos(grp[i]["vec"], grp[j]["vec"])
                      for i in range(len(grp)) for j in range(i+1, len(grp))]
    inter = sum(inter_all)/len(inter_all) if inter_all else 0
    print(f"   cos intra-cible (angles differents, meme cible)  : {intra:.3f}")
    print(f"   cos inter-cible (meme angle, cibles differentes) : {inter:.3f}")
    d = intra - inter
    print(f"   ecart                                            : {d:+.3f}")
    print()
    if d > 0.04:
        print("   > La cible pese PLUS que l angle : deux messages pour la meme entreprise")
        print("     se ressemblent davantage que deux messages du meme angle. C est le signe")
        print("     que le contenu suit reellement la preuve de besoin -> personnalisation reelle.")
    elif d < -0.04:
        print("   > L angle pese PLUS que la cible : la consigne de style domine le contenu.")
        print("     Les messages sont formates, pas personnalises. A corriger avant tout envoi.")
    else:
        print("   > Angle et cible pesent autant : ni template pur, ni sur-mesure franc.")

    # ---- 4. SELECTION -----------------------------------------------------
    print(f"\n\n4. SELECTION PAR CENTROIDE — la variante la plus representative par cible")
    print("   (celle dont l embedding est le plus proche du barycentre de ses angles)\n")
    for ref, grp in sorted(par_cible.items(), key=lambda kv: kv[1][0]["canal"]):
        if len(grp) < 2: continue
        dim = len(grp[0]["vec"])
        cent = [sum(g["vec"][i] for g in grp)/len(grp) for i in range(dim)]
        best = max(grp, key=lambda g: cos(g["vec"], cent))
        far  = min(grp, key=lambda g: cos(g["vec"], cent))
        ent = (grp[0]["ent"] or grp[0]["nom"] or "")[:22]
        print(f"   {grp[0]['canal']:<10} {ent:<24} centre={best['angle']:<13} "
              f"atypique={far['angle']:<13} ({best['n_car']}c)")

    print()

if __name__ == "__main__":
    main()
