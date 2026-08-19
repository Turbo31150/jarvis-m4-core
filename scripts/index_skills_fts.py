#!/usr/bin/env python3
# index_skills_fts.py — index FTS5 de TOUS les skills et agents, 0 token.
#
# POURQUOI : jarvis-plan.py ne lit que ~/.claude/skills (1 016 dossiers) alors que la
# cascade skillmp installe dans ~/.claude/plugins/local/skillsmp/skills (38 746 SKILL.md).
# Resultat mesure le 19/08 : 2,6 % de visibilite, et donc _ready_cmd() n a JAMAIS pu
# apparier un seul skill — 11 360 des 12 792 entrees de `plan` tombent sur le fallback
# pauvre {"ready_cmd": "dominos <slug>"}. Cet index ferme l angle mort.
#
# Ne lit que l en-tete de chaque fichier (frontmatter + premieres lignes) : lire 38 746
# fichiers en entier coûterait des minutes pour rien.

import os, re, sqlite3, sys, time

HOME = os.path.expanduser("~")
DB   = os.path.join(HOME, "jarvis", "jarvis_master.db")

RACINES = [
    ("skill", os.path.join(HOME, ".claude", "skills")),
    ("skill", os.path.join(HOME, ".claude", "plugins", "local", "skillsmp", "skills")),
    ("agent", os.path.join(HOME, ".claude", "agents")),
]
ENTETE_MAX = 6000        # octets lus par fichier : le frontmatter tient tres large dedans


def lire_entete(chemin, n=ENTETE_MAX):
    try:
        with open(chemin, "r", encoding="utf-8", errors="replace") as f:
            return f.read(n)
    except OSError:
        return ""


def parse(txt, chemin, kind):
    """Extrait name / description / corps utile. Tolere l absence de frontmatter."""
    nom = desc = ""
    corps = txt
    if txt.startswith("---"):
        fin = txt.find("\n---", 3)
        if fin != -1:
            fm, corps = txt[3:fin], txt[fin + 4:]
            m = re.search(r"^name:\s*(.+)$", fm, re.M)
            if m:
                nom = m.group(1).strip().strip("\"'")
            # description peut etre sur plusieurs lignes ou entre quotes
            m = re.search(r"^description:\s*(.+?)(?=^\w+:|\Z)", fm, re.M | re.S)
            if m:
                desc = " ".join(m.group(1).split()).strip().strip("\"'")
    if not nom:
        # repli : nom du dossier parent (SKILL.md) ou du fichier (agent .md)
        nom = (os.path.basename(os.path.dirname(chemin)) if os.path.basename(chemin) == "SKILL.md"
               else os.path.splitext(os.path.basename(chemin))[0])
    if not desc:
        # premiere ligne de prose du corps, titres markdown ecartes
        for l in corps.splitlines():
            l = l.strip()
            if l and not l.startswith("#"):
                desc = l[:400]
                break
    # le corps sert au FTS : on garde un extrait, pas le fichier entier
    return nom, desc, " ".join(corps.split())[:1500]


def schema(c):
    c.execute("PRAGMA journal_mode=WAL")
    # table normale : porte la cle unique (chemin) et permet l idempotence
    c.execute("""CREATE TABLE IF NOT EXISTS skills_index (
        chemin TEXT PRIMARY KEY, kind TEXT, racine TEXT, slug TEXT,
        nom TEXT, description TEXT, extrait TEXT, mtime REAL, indexe_le TEXT)""")
    # FTS5 externe : indexe le contenu de skills_index via rowid
    c.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS skills_index_fts
        USING fts5(slug, nom, description, extrait,
                   content='skills_index', content_rowid='rowid',
                   tokenize='unicode61 remove_diacritics 2')""")


def collecter():
    """Parcourt les racines. Retourne la liste des fichiers a indexer."""
    out = []
    for kind, racine in RACINES:
        if not os.path.isdir(racine):
            print(f"  racine absente, ignoree : {racine}", file=sys.stderr)
            continue
        n0 = len(out)
        for dirpath, dirnames, filenames in os.walk(racine):
            dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__")]
            for fn in filenames:
                if kind == "skill" and fn != "SKILL.md":
                    continue
                if kind == "agent" and not fn.endswith(".md"):
                    continue
                out.append((kind, racine, os.path.join(dirpath, fn)))
        print(f"  {racine} -> {len(out)-n0} fichier(s)")
    return out


def main():
    plein = "--full" in sys.argv
    t0 = time.time()
    c = sqlite3.connect(DB, timeout=60)
    schema(c)

    connus = {} if plein else {r[0]: r[1] for r in c.execute("SELECT chemin, mtime FROM skills_index")}
    print(f"index existant : {len(connus)} entree(s)")
    print("collecte des fichiers :")
    fichiers = collecter()
    print(f"total sur disque : {len(fichiers)}")

    n_new = n_maj = n_skip = 0
    lot = []
    for kind, racine, chemin in fichiers:
        try:
            mt = os.path.getmtime(chemin)
        except OSError:
            continue
        if chemin in connus:
            if abs(connus[chemin] - mt) < 1:          # inchange -> on ne relit pas
                n_skip += 1
                continue
            n_maj += 1
        else:
            n_new += 1
        nom, desc, extrait = parse(lire_entete(chemin), chemin, kind)
        slug = (os.path.basename(os.path.dirname(chemin)) if os.path.basename(chemin) == "SKILL.md"
                else os.path.splitext(os.path.basename(chemin))[0])
        lot.append((chemin, kind, racine, slug, nom, desc, extrait, mt))
        if len(lot) >= 2000:
            ecrire(c, lot); lot = []
            print(f"  ... {n_new+n_maj} ecrites", flush=True)
    if lot:
        ecrire(c, lot)

    # rebuild du FTS : moins cher et plus sûr que de maintenir des triggers sur 39k lignes
    c.execute("INSERT INTO skills_index_fts(skills_index_fts) VALUES('rebuild')")
    c.commit()
    tot = c.execute("SELECT COUNT(*) FROM skills_index").fetchone()[0]
    par = dict(c.execute("SELECT kind, COUNT(*) FROM skills_index GROUP BY kind").fetchall())
    c.close()
    print(f"\nindex : {tot} entrees ({par})  — {n_new} nouvelles, {n_maj} maj, {n_skip} inchangees")
    print(f"duree : {time.time()-t0:.1f}s")


def ecrire(c, lot):
    c.executemany("""INSERT INTO skills_index
        (chemin,kind,racine,slug,nom,description,extrait,mtime,indexe_le)
        VALUES (?,?,?,?,?,?,?,?,datetime('now'))
        ON CONFLICT(chemin) DO UPDATE SET
          kind=excluded.kind, racine=excluded.racine, slug=excluded.slug,
          nom=excluded.nom, description=excluded.description, extrait=excluded.extrait,
          mtime=excluded.mtime, indexe_le=excluded.indexe_le""", lot)
    c.commit()


if __name__ == "__main__":
    main()
