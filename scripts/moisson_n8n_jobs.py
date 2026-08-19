#!/usr/bin/env python3
# moisson_n8n_jobs.py — la categorie Jobs du forum n8n, avec extraction des PRIX.
#
# Pourquoi une source dediee. Le moissonneur generaliste lisait /latest.json et
# classait n8n-forum du cote "problemes". C etait faux : la categorie Jobs (id=13,
# 684 sujets) contient des annonces de prestation PAYEE, dans les deux sens —
# [HIRING] quelqu un cherche et paie, [FOR HIRE] quelqu un propose et affiche son tarif.
# Les [FOR HIRE] donnent la grille tarifaire reelle du marche, ce qu aucune etude ne donne.
#
# Les prix sont extraits du TITRE et du CORPS, jamais devines. Une annonce sans
# montant lisible est marquee "prix non affiche" — on ne l estime pas.

import json, re, sqlite3, sys, time, urllib.request
from datetime import datetime, UTC

DB  = "/home/pamerys/jarvis/jarvis_master.db"
CAT = "https://community.n8n.io/c/jobs/13.json"
UA  = "Mozilla/5.0 (X11; Linux x86_64) JarvisMoisson/1.0"

# Devises et formats rencontres reellement : $150, USD 350-650, JPY 132,000, 6,000/mo, 300 fixed
# Un nombre = chiffres, avec des separateurs de milliers a EXACTEMENT 3 chiffres.
# Sans cette contrainte, "USD 75, 24-hour turnaround" donnait le montant "75, 24" :
# la virgule de la phrase etait lue comme un separateur de milliers.
_NB = r"\d{1,3}(?:[ ,.]\d{3})*(?:\.\d{1,2})?"
MONTANT = re.compile(
    rf"(?:(?P<sym>[$€£¥])\s?(?P<v1>{_NB})"
    rf"|(?P<dev>USD|EUR|GBP|JPY|CAD|AUD|USDC)\s?(?P<v2>{_NB})"
    rf"|(?P<v3>{_NB})\s?(?P<dev2>USD|EUR|GBP|JPY|usd|eur))"
    rf"(?:\s?[-–—]\s?(?P<v4>{_NB}))?",
    re.I)
PERIODE = re.compile(r"/\s?(mo|month|hr|hour|day|week|yr|year)\b|per\s+(month|hour|day|week)", re.I)

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    for a, b in (("&amp;","&"),("&lt;","<"),("&gt;",">"),("&quot;",'"'),("&#39;","'"),
                 ("&nbsp;"," "),("&#x2F;","/")):
        s = s.replace(a, b)
    return " ".join(s.split())

def extraire_prix(texte):
    """Retourne la liste des montants lisibles. Vide si aucun — jamais d estimation."""
    out = []
    for m in MONTANT.finditer(texte or ""):
        brut = m.group(0).strip()
        # ecarte les faux positifs : annees, versions, nombres nus sans devise
        if not (m.group("sym") or m.group("dev") or m.group("dev2")):
            continue
        val = (m.group("v1") or m.group("v2") or m.group("v3") or "").replace(" ", "")
        try:
            n = float(val.replace(",", "").replace(".", "") if val.count(",") or val.count(".") > 1
                      else val.replace(",", ""))
        except ValueError:
            continue
        if n < 20 or n > 2_000_000:      # hors de toute plage de prestation credible
            continue
        per = PERIODE.search(texte[max(0, m.start()-10): m.end()+18])
        out.append(brut + (f" {per.group(0).strip()}" if per else ""))
    vus, uniq = set(), []
    for x in out:
        k = x.lower().replace(" ", "")
        if k not in vus:
            vus.add(k); uniq.append(x)
    return uniq[:6]

def sens(titre):
    t = (titre or "").lower()
    if "[for hire]" in t or "for hire" in t:      return "OFFRE"     # propose ses services
    if any(k in t for k in ("[hiring]", "hiring:", "hiring ", "looking to hire",
                            "seeking", "looking for", "need ", "wanted")):
        return "DEMANDE"                                             # cherche un prestataire
    return "?"

def schema(c):
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""CREATE TABLE IF NOT EXISTS n8n_jobs (
        topic_id INTEGER PRIMARY KEY, titre TEXT, url TEXT, sens TEXT,
        prix TEXT, corps TEXT, auteur TEXT, cree_le TEXT, dernier_le TEXT,
        reponses INTEGER, vues INTEGER, moissonne_le TEXT)""")

def main():
    pages = 12
    detail = "--detail" in sys.argv
    for a in sys.argv:
        if a.startswith("--pages="): pages = int(a.split("=")[1])

    c = sqlite3.connect(DB, timeout=60); schema(c)
    connus = {r[0] for r in c.execute("SELECT topic_id FROM n8n_jobs")}
    print(f"deja en base : {len(connus)} annonces")

    sujets, page = [], 0
    while page < pages:
        try:
            d = get(f"{CAT}?page={page}")
        except Exception as e:
            print(f"  page {page} : {e}"); break
        lot = (d.get("topic_list") or {}).get("topics") or []
        if not lot:
            break
        sujets += lot
        print(f"  page {page} : {len(lot)} sujets (cumul {len(sujets)})")
        page += 1
        time.sleep(1.2)

    n_new = n_prix = 0
    for t in sujets:
        tid = t.get("id")
        titre = strip_html(t.get("title") or "")
        url = f"https://community.n8n.io/t/{t.get('slug','')}/{tid}"
        s = sens(titre)
        corps = ""
        # Le detail coute une requete par sujet : reserve aux annonces qui affichent
        # un sens clair, et seulement si --detail. Sinon on lit le titre seul.
        if detail and s != "?" and tid not in connus:
            try:
                dd = get(f"https://community.n8n.io/t/{tid}.json", timeout=20)
                posts = (dd.get("post_stream") or {}).get("posts") or []
                if posts:
                    corps = strip_html(posts[0].get("cooked") or "")[:2500]
                time.sleep(0.8)
            except Exception:
                pass
        prix = extraire_prix(titre + " " + corps)
        if prix: n_prix += 1
        c.execute("""INSERT INTO n8n_jobs
            (topic_id,titre,url,sens,prix,corps,auteur,cree_le,dernier_le,reponses,vues,moissonne_le)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
            ON CONFLICT(topic_id) DO UPDATE SET
              prix=excluded.prix, corps=CASE WHEN excluded.corps<>'' THEN excluded.corps ELSE n8n_jobs.corps END,
              dernier_le=excluded.dernier_le, reponses=excluded.reponses, vues=excluded.vues""",
            (tid, titre, url, s, json.dumps(prix, ensure_ascii=False), corps,
             "", (t.get("created_at") or "")[:10], (t.get("last_posted_at") or "")[:10],
             max(0, (t.get("posts_count") or 1) - 1), t.get("views") or 0))
        if tid not in connus: n_new += 1
    c.commit()
    tot = c.execute("SELECT COUNT(*) FROM n8n_jobs").fetchone()[0]
    par = dict(c.execute("SELECT sens, COUNT(*) FROM n8n_jobs GROUP BY sens").fetchall())
    c.close()
    print(f"\n{len(sujets)} sujets vus · {n_new} nouveaux · {n_prix} avec un prix lisible")
    print(f"base : {tot} annonces {par}")

if __name__ == "__main__":
    main()
