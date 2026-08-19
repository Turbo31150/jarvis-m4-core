#!/usr/bin/env python3
# precharge_taches.py — remplit `plan.preloaded` avec un contexte REEL, 0 token par defaut.
#
# AVANT (mesure du 19/08) : 11 360 des 12 792 entrees valaient
#     {"ready_cmd": "dominos <slug>"}                        -> 84 caracteres, inexploitable
# Aucun skill ni agent n avait jamais ete apparie, faute d index (cf. index_skills_fts.py).
#
# APRES : 5 champs, tous derives de donnees reelles —
#     skill   : meilleur appariement FTS5 sur 40 073 entrees, avec score bm25
#     agent   : famille resolue via skillsmp_affectation, sinon via le nom des agents
#     cli     : binaire ~/.local/bin ou script ~/jarvis/scripts reellement present
#     prompt  : consigne construite par gabarit (deterministe). --prompt-llm pour M6.
#     command : ligne shell executable telle quelle
#
# Un champ qui ne peut pas etre etabli vaut null. JAMAIS une valeur plausible inventee :
# un `cli` qui n existe pas sur le disque est pire que pas de `cli` du tout.

import json, os, re, sqlite3, sys, unicodedata

HOME = os.path.expanduser("~")
DB   = os.path.join(HOME, "jarvis", "jarvis_master.db")
BINS = [os.path.join(HOME, ".local", "bin"), os.path.join(HOME, "jarvis", "bin"),
        os.path.join(HOME, "jarvis", "scripts")]

VIDES = {  # mots qui ne discriminent rien dans ce corpus : ils noieraient le score bm25
 "auto","le","la","les","de","des","du","un","une","et","ou","a","au","aux","en","pour",
 "par","sur","avec","dans","ce","cette","ces","son","sa","ses","leur","est","sont","que",
 "qui","quoi","dont","plus","tout","tous","toute","si","ne","pas","the","of","to","and",
 "jarvis","tache","taches","faire","mettre","verifier","relancer","lancer",
 # vocabulaire de STRUCTURE des SKILL.md : present dans presque tous les fichiers,
 # donc nul pouvoir discriminant. Sans ce filtre, "triggers" appariait /vue-dd-rum
 # a une tache domino simplement parce que sa description dit "Triggers on mentions".
 "use","this","skill","when","user","asks","triggers","trigger","says","want","wants",
 "should","operator","workflow","tool","tools","agent","agents","build","run","launch",
}


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower()


def mots_cles(titre, n=6):
    """Mots significatifs du titre, pour une requete FTS5 sûre (aucun caractere special)."""
    bruts = re.findall(r"[a-z0-9]{4,}", norm(titre))   # 3 lettres = bruit (cf. "pre")
    vus, out = set(), []
    for m in bruts:
        if m in VIDES or m in vus:
            continue
        vus.add(m); out.append(m)
        if len(out) >= n:
            break
    return out


_cache_cli = None
def trouve_cli(mots):
    """Un binaire/script REELLEMENT present dont le nom recoupe un mot-cle."""
    global _cache_cli
    if _cache_cli is None:
        _cache_cli = []
        for d in BINS:
            if os.path.isdir(d):
                for f in os.listdir(d):
                    p = os.path.join(d, f)
                    if os.path.isfile(p) and (os.access(p, os.X_OK) or f.endswith((".py", ".sh"))):
                        _cache_cli.append((norm(f), p))
    for m in mots:
        if len(m) < 4:
            continue
        for nom, p in _cache_cli:
            if m in nom:
                return p
    return None


def apparie_skill(c, mots):
    """Meilleur skill/agent — classe par RECOUVREMENT lexical, pas par bm25.

    Calibrage mesure sur 400 titres tires au hasard (19/08) : le score bm25 ne
    discrimine PAS. Un score de -21,57 donnait /content-perf-harvester pour une tache
    d embeddings (recouvrement 0, faux), tandis que -16,77 donnait un appariement juste.
    Le nombre de mots-cles du titre reellement presents dans le skill, lui, separe :
    recouvrement 0 -> 13 % des cas, tous visiblement faux ; recouvrement >= 2 -> 43 %,
    tous justes a l inspection.

    On recupere donc les 25 meilleurs candidats bm25 puis on les RE-CLASSE par
    recouvrement. Recouvrement 0 => on ne propose RIEN : un mauvais aiguillage coûte
    plus cher a l agent qu une case vide.
    """
    if not mots:
        return None
    q = " OR ".join(mots)
    try:
        rows = c.execute("""
            SELECT s.slug, s.kind, s.nom, s.description, bm25(skills_index_fts) sc
            FROM skills_index_fts f JOIN skills_index s ON s.rowid=f.rowid
            WHERE skills_index_fts MATCH ?
            ORDER BY bm25(skills_index_fts) LIMIT 25""", (q,)).fetchall()
    except sqlite3.OperationalError:
        return None
    if not rows:
        return None

    DESC_MAX = 300   # meme borne au calcul et au stockage : sans quoi on annonce un
                     # recouvrement calcule sur un texte que l on ne conserve pas.
    best = None
    for slug, kind, nom, desc, sc in rows:
        d = (desc or "")[:DESC_MAX]
        b_slug, b_nom, b_desc = norm(slug), norm(nom or ""), norm(d)
        # pondere par EMPLACEMENT : un mot dans le slug identifie l outil,
        # le meme mot noye dans une description ne prouve presque rien.
        pts, trouves = 0, []
        for w in mots:
            if w in b_slug:   pts += 3; trouves.append(w)
            elif w in b_nom:  pts += 2; trouves.append(w)
            elif w in b_desc: pts += 1; trouves.append(w)
        if best is None or (pts, -sc) > (best[0], -best[4]):
            best = (pts, slug, kind, nom, sc, d, trouves)
    pts, slug, kind, nom, sc, d, trouves = best
    if pts < 3:
        return None      # sous 3 points : aucun mot dans le slug et au plus 2 dans le
                         # texte -> on s abstient plutot que d aiguiller a faux.
    return {"slug": slug, "kind": kind, "nom": nom, "desc": d,
            "score": round(sc, 2), "points": pts, "mots_trouves": trouves,
            "sur": len(mots),
            # paliers calibres sur 500 titres (19/08) : >=7 pts = plusieurs mots dans le
            # slug, juste a l inspection ; 5-6 = juste aussi ; 3-4 = souvent juste mais
            # parfois un homonyme isole ("masked", "term") -> l agent doit verifier.
            "confiance": "forte" if pts >= 7 else "bonne" if pts >= 5 else "indicative"}


_cache_fam = None
def famille_de(c, slug):
    global _cache_fam
    if _cache_fam is None:
        _cache_fam = {}
        try:
            for s, f in c.execute("SELECT slug, famille FROM skillsmp_affectation WHERE famille IS NOT NULL"):
                _cache_fam.setdefault(s, f)
        except sqlite3.OperationalError:
            pass
    return _cache_fam.get(slug)


def construire(c, titre, source):
    mots = mots_cles(titre)
    sk   = apparie_skill(c, mots)
    fam  = famille_de(c, sk["slug"]) if sk else None
    cli  = trouve_cli(mots)

    skill = f"/{sk['slug']}" if sk and sk["kind"] == "skill" else None
    agent = (sk["slug"] if sk and sk["kind"] == "agent"
             else (f"squad-{fam}-integrateur" if fam else None))

    # commande : la plus concrete d abord, jamais inventee
    if skill:
        command = f"Skill: {skill}"
    elif agent:
        command = f"Agent: {agent}"
    elif cli:
        command = cli
    else:
        command = None

    prompt = None
    if sk:
        prompt = (f"Objectif : {titre.strip()[:180]}. "
                  f"Outil apparie : {sk['slug']} ({sk['kind']}), confiance {sk['confiance']} "
                  f"({sk['points']} pts, mots retrouves : {','.join(sk['mots_trouves'])}). "
                  f"Verifie que l outil correspond avant de l executer ; s il ne correspond pas, "
                  f"dis-le et n execute rien.")

    return {"skill": skill, "agent": agent, "cli": cli, "prompt": prompt,
            "command": command,
            "confiance": sk["confiance"] if sk else None,
            "appariement": f"{sk['points']}pts:{','.join(sk['mots_trouves'])}" if sk else None,
            "source": source}


def stats(c, libelle):
    tot = c.execute("SELECT COUNT(*) FROM plan").fetchone()[0]
    sk  = c.execute("SELECT COUNT(*) FROM plan WHERE preloaded LIKE '%\"skill\": \"/%'").fetchone()[0]
    ag  = c.execute("SELECT COUNT(*) FROM plan WHERE preloaded LIKE '%\"agent\": \"%' AND preloaded NOT LIKE '%\"agent\": null%'").fetchone()[0]
    cl  = c.execute("SELECT COUNT(*) FROM plan WHERE preloaded LIKE '%\"cli\": \"/%'").fetchone()[0]
    ln  = c.execute("SELECT ROUND(AVG(LENGTH(preloaded))) FROM plan").fetchone()[0]
    print(f"  {libelle:<8} total={tot}  skill={sk} ({100*sk//max(tot,1)}%)  "
          f"agent={ag}  cli={cl}  longueur_moy={ln}c")


def main():
    rescan = "--rescan" in sys.argv
    limite = None
    for a in sys.argv:
        if a.startswith("--limit="):
            limite = int(a.split("=")[1])

    c = sqlite3.connect(DB, timeout=60)
    c.execute("PRAGMA journal_mode=WAL")
    if not c.execute("SELECT name FROM sqlite_master WHERE name='skills_index_fts'").fetchone():
        sys.exit("skills_index_fts absent — lancer d abord index_skills_fts.py")

    print("AVANT :"); stats(c, "plan")
    if not rescan:
        print("\n(dry-run — ajouter --rescan pour ecrire)")
        rows = c.execute("SELECT id,titre,source FROM plan LIMIT 5").fetchall()
        for i, t, s in rows:
            print(f"\n  {t[:80]}\n    -> {json.dumps(construire(c,t,s), ensure_ascii=False)[:230]}")
        return

    q = "SELECT id,titre,source FROM plan" + (f" LIMIT {limite}" if limite else "")
    rows = c.execute(q).fetchall()
    print(f"\nrescan de {len(rows)} entrees...")
    lot, n = [], 0
    for i, t, s in rows:
        lot.append((json.dumps(construire(c, t, s), ensure_ascii=False), i))
        if len(lot) >= 1000:
            c.executemany("UPDATE plan SET preloaded=? WHERE id=?", lot); c.commit()
            n += len(lot); lot = []
            print(f"  ... {n}", flush=True)
    if lot:
        c.executemany("UPDATE plan SET preloaded=? WHERE id=?", lot); c.commit(); n += len(lot)
    print(f"  {n} entrees mises a jour\n")
    print("APRES :"); stats(c, "plan")
    c.close()


if __name__ == "__main__":
    main()
