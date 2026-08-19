#!/usr/bin/env python3
# moisson_freework.py — missions FreeWork via JSON-LD JobPosting. 0 token.
#
# FreeWork publie sur chaque fiche un bloc <script type="application/ld+json">
# de type JobPosting : titre, datePosted, validThrough, jobLocation, baseSalary,
# employmentType, hiringOrganization. C est une donnee STRUCTUREE et datee —
# infiniment plus fiable que du parsing HTML, et elle porte la date de VALIDITE,
# donc on sait si la mission est encore ouverte au lieu de le deviner.

import json, re, sqlite3, sys, time, urllib.parse, urllib.request
from datetime import datetime, UTC

DB = "/home/pamerys/jarvis/jarvis_master.db"
UA = "Mozilla/5.0 (X11; Linux x86_64) JarvisMoisson/1.0"
BASE = "https://www.free-work.com"

REQUETES = ["intelligence artificielle", "n8n", "llm", "rag", "automatisation",
            "mlops", "agent ia", "data engineer", "ia generative", "python ia"]

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def texte(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    for a, b in (("&amp;","&"),("&lt;","<"),("&gt;",">"),("&quot;",'"'),
                 ("&#039;","'"),("&#39;","'"),("&nbsp;"," ")):
        s = s.replace(a, b)
    return " ".join(s.split())

# Le TJM n est PAS dans le JSON-LD : FreeWork y met currency=EUR et unitText=DAY
# mais laisse minValue/maxValue vides. Le montant reel est dans le HTML, sous la
# forme "570-800 €⁄j" (noter le U+2044 FRACTION SLASH, pas un slash normal) et
# dans le blob Nuxt sous "contractor","570-800 €". On le lit donc a la main.
TJM_RE = re.compile(r"(\d{3,4})\s*[-–—]\s*(\d{3,4})\s*€\s*[/⁄]?\s*j|(\d{3,4})\s*€\s*[/⁄]\s*j", re.I)

def lire_tjm(h):
    m = TJM_RE.search(h)
    if not m:
        return "", ""
    if m.group(1):
        return m.group(1), m.group(2)
    return m.group(3), m.group(3)

def fiche(url):
    """Extrait le JobPosting. None si la page n en porte pas."""
    try:
        h = get(url)
    except Exception:
        return None
    tmin, tmax = lire_tjm(h)
    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', h, re.S):
        try:
            d = json.loads(m.group(1))
        except Exception:
            continue
        if d.get("@type") != "JobPosting":
            continue
        bs = d.get("baseSalary") or {}
        v  = bs.get("value") or {}
        loc = d.get("jobLocation") or {}
        addr = (loc.get("address") or {}) if isinstance(loc, dict) else {}
        org = d.get("hiringOrganization") or {}
        et = d.get("employmentType")
        return dict(
            titre = texte(d.get("title") or "")[:300],
            url = url,
            publie = (d.get("datePosted") or "")[:10],
            valide_jusqu = (d.get("validThrough") or "")[:10],
            tjm_min = v.get("minValue") or tmin,
            tjm_max = v.get("maxValue") or tmax,
            devise = bs.get("currency") or "",
            unite = v.get("unitText") or "",
            ville = addr.get("addressLocality") or "",
            region = addr.get("addressRegion") or "",
            contrat = ",".join(et) if isinstance(et, list) else (et or ""),
            client = org.get("name","") if isinstance(org, dict) else "",
            description = texte(d.get("description") or "")[:3000],
        )
    return None

def schema(c):
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""CREATE TABLE IF NOT EXISTS freework_missions (
        url TEXT PRIMARY KEY, titre TEXT, publie TEXT, valide_jusqu TEXT,
        tjm_min TEXT, tjm_max TEXT, devise TEXT, unite TEXT,
        ville TEXT, region TEXT, contrat TEXT, client TEXT,
        description TEXT, moissonne_le TEXT)""")

def main():
    pages = 3
    for a in sys.argv:
        if a.startswith("--pages="): pages = int(a.split("=")[1])

    c = sqlite3.connect(DB, timeout=60); schema(c)
    connus = {r[0] for r in c.execute("SELECT url FROM freework_missions")}
    print(f"deja en base : {len(connus)}")

    # 1. collecte des URLs de fiches
    urls = set()
    for q in REQUETES:
        for p in range(1, pages + 1):
            try:
                h = get(f"{BASE}/fr/tech-it/jobs?query={urllib.parse.quote(q)}&page={p}")
            except Exception as e:
                print(f"  liste '{q[:18]}' p{p} : {e}"); break
            trouves = set(re.findall(r'href="(/fr/tech-it/job-mission/[^"]+)"', h))
            if not trouves: break
            urls |= {BASE + u for u in trouves}
            time.sleep(1.5)
        print(f"  '{q[:22]:<22}' -> cumul {len(urls)} URLs")

    neuves = [u for u in urls if u not in connus]
    print(f"\n{len(urls)} fiches vues, {len(neuves)} nouvelles a lire\n")

    n_ok = n_tjm = 0
    for i, u in enumerate(neuves, 1):
        f = fiche(u)
        if not f:
            continue
        c.execute("""INSERT INTO freework_missions
            (url,titre,publie,valide_jusqu,tjm_min,tjm_max,devise,unite,
             ville,region,contrat,client,description,moissonne_le)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
            ON CONFLICT(url) DO UPDATE SET
              valide_jusqu=excluded.valide_jusqu, tjm_min=excluded.tjm_min,
              tjm_max=excluded.tjm_max, moissonne_le=excluded.moissonne_le""",
            (f["url"], f["titre"], f["publie"], f["valide_jusqu"], str(f["tjm_min"]),
             str(f["tjm_max"]), f["devise"], f["unite"], f["ville"], f["region"],
             f["contrat"], f["client"], f["description"]))
        n_ok += 1
        if f["tjm_min"] or f["tjm_max"]: n_tjm += 1
        if n_ok % 20 == 0:
            c.commit(); print(f"  ... {n_ok}/{len(neuves)}", flush=True)
        time.sleep(0.9)
    c.commit()
    tot = c.execute("SELECT COUNT(*) FROM freework_missions").fetchone()[0]
    c.close()
    print(f"\n{n_ok} fiche(s) lue(s), {n_tjm} avec un TJM affiche")
    print(f"base : {tot} missions")

if __name__ == "__main__":
    main()
