#!/usr/bin/env python3
# moisson_multi_source.py — moisson massive des sources PUBLIQUES, 0 token, idempotente.
#
# Sources retenues apres sonde reelle du 19/08 (HTTP 200 sans authentification) :
#   google-trends · hacker-news · github-issues · n8n-forum · stackoverflow · freework
# Ecartees car 403 : reddit, indeed, malt. Aucun contournement n est tente.
#
# LinkedIn n est PAS ici : il a sa passe dediee et plafonnee (moisson_linkedin_cdp.py),
# conformement au choix "les deux, separes".
#
# Idempotence : UNIQUE(source, url_hash). Relancer deux fois ne double jamais la table.

import hashlib, json, re, sqlite3, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, UTC

DB  = "/home/pamerys/jarvis/jarvis_master.db"
LOG = "/home/pamerys/jarvis/logs/moisson_multi.log"
UA  = "Mozilla/5.0 (X11; Linux x86_64) JarvisMoisson/1.0 (+contact via linkedin)"

_th = __import__("threading"); _lock = _th.Lock()

# Nombre de pages a parcourir par source. Le volet C a montre que 428 signaux sur
# 5 sources heterogenes n ont pas la densite pour faire emerger un besoin
# transversal (16/16 clusters mono-source). Les sources paginent : n8n-forum
# nativement, Stack Overflow annonce has_more=True, GitHub expose 4869 issues.
PAGES = 1
RATE_LIMIT_ATTEINT = set()   # sources ayant renvoye 403 : on ARRETE, on ne boucle pas
def log(m):
    line = f"[{datetime.now():%H:%M:%S}] {m}"
    with _lock:
        print(line, flush=True)
        try:
            with open(LOG, "a") as f: f.write(line + "\n")
        except OSError: pass

def get(url, timeout=25, accept="application/json"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def jget(url, **kw):
    return json.loads(get(url, **kw))

# Libelles de navigation : ils passent tous les tests de forme (chaine non vide,
# insertion reussie, code 0) et ne portent AUCUNE information. Sans ce filtre, ils
# formaient le cluster le plus dense du corpus et le pipeline aurait presente des
# boutons de site comme un "pattern de marche".
BRUIT = ("voir cette offre", "voir l offre", "voir l'offre", "en savoir plus", "postuler",
         "lire la suite", "read more", "see more", "view job", "apply now", "voir plus",
         "offres", "toutes les offres", "deposez votre cv", "next", "suivant")

def utile(titre, mini=25):
    """Un signal doit porter de l information, pas un libelle de navigation."""
    t = " ".join((titre or "").split())
    if len(t) < mini:
        return False
    return t.lower().strip(" .:-") not in BRUIT

def sig(url, titre):
    """Empreinte d unicite : url ET titre.

    Ne jamais hacher l URL seule. Le flux RSS Google Trends repete le MEME <link>
    (l URL du flux lui-meme) sur ses 10 items : hacher l URL faisait s ecraser
    9 tendances sur 10 dans le ON CONFLICT, sans la moindre erreur. Perte
    silencieuse — mesuree le 19/08 : 10 items vus, 1 seul en base."""
    return hashlib.sha256(f"{url or ''}||{titre or ''}".encode()).hexdigest()[:32]

def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = (s.replace("&amp;","&").replace("&lt;","<").replace("&gt;",">")
          .replace("&quot;",'"').replace("&#39;","'").replace("&nbsp;"," "))
    return " ".join(s.split())

# ── collecteurs : chacun renvoie une liste de dicts homogenes ──────────────────

def c_google_trends(mots):
    out = []
    for geo in ("FR",):
        xml = get(f"https://trends.google.fr/trending/rss?geo={geo}", accept="application/rss+xml")
        for bloc in re.findall(r"<item>(.*?)</item>", xml, re.S):
            t = re.search(r"<title>(.*?)</title>", bloc, re.S)
            l = re.search(r"<link>(.*?)</link>", bloc, re.S)
            n = re.search(r"<ht:approx_traffic>(.*?)</ht:approx_traffic>", bloc, re.S)
            if not t: continue
            titre = strip_html(t.group(1))
            out.append(dict(source="google-trends", url=strip_html(l.group(1)) if l else "",
                            titre=titre, extrait=f"trafic approx {strip_html(n.group(1))}" if n else "",
                            auteur=f"geo:{geo}", date_src=""))
    return out

def c_hacker_news(mots):
    ids = jget("https://hacker-news.firebaseio.com/v0/topstories.json")[:60*PAGES]
    out = []
    for i in ids:
        try:
            it = jget(f"https://hacker-news.firebaseio.com/v0/item/{i}.json", timeout=12)
        except Exception:
            continue
        if not it or it.get("type") != "story":
            continue
        titre = it.get("title", "")
        if mots and not any(m in titre.lower() for m in mots):
            continue
        out.append(dict(source="hacker-news",
                        url=it.get("url") or f"https://news.ycombinator.com/item?id={i}",
                        titre=titre, extrait=f"{it.get('score',0)} pts / {it.get('descendants',0)} comm.",
                        auteur=it.get("by",""),
                        date_src=datetime.fromtimestamp(it.get("time",0), UTC).isoformat() if it.get("time") else ""))
    return out

def c_github_issues(mots):
    out = []
    for q in ("n8n self-hosted help", "ollama local llm deploy help",
              "rag local embeddings help", "docker swarm production issue",
              "langchain rag production issue", "vector database self hosted help"):
        for page in range(1, PAGES + 1):
            if "github-issues" in RATE_LIMIT_ATTEINT:
                return out                      # arret NET, pas de reessai en boucle
            try:
                d = jget(f"https://api.github.com/search/issues?per_page=25&page={page}"
                         "&sort=created&order=desc&q="
                         + urllib.parse.quote(q + " state:open"))
            except Exception as e:
                if "403" in str(e) or "rate limit" in str(e).lower():
                    RATE_LIMIT_ATTEINT.add("github-issues")
                    log(f"  github : RATE-LIMIT atteint (page {page}, requete '{q[:28]}') "
                        f"-> arret de la source, {len(out)} signaux conserves")
                    return out
                log(f"  github '{q[:28]}' p{page} : {e}"); break
            items = d.get("items", [])
            if not items:
                break
            for it in items:
                out.append(dict(source="github-issues", url=it.get("html_url",""),
                                titre=it.get("title",""),
                                extrait=(it.get("body") or "")[:400].replace("\n"," "),
                                auteur=(it.get("user") or {}).get("login",""),
                                date_src=it.get("created_at","")))
            time.sleep(6)   # 10 req/min sans authentification : 6 s de marge
    return out

def c_n8n_forum(mots):
    out = []
    topics = []
    for page in range(PAGES):
        try:
            d = jget(f"https://community.n8n.io/latest.json?page={page}")
        except Exception as e:
            log(f"  n8n-forum p{page} : {e}"); break
        t = (d.get("topic_list") or {}).get("topics", [])
        if not t:
            break
        topics += t
        time.sleep(1.5)
    for t in topics:
        out.append(dict(source="n8n-forum",
                        url=f"https://community.n8n.io/t/{t.get('slug','')}/{t.get('id','')}",
                        titre=t.get("title",""),
                        extrait=f"{t.get('posts_count',0)} msg / {t.get('views',0)} vues"
                                f"{' [SANS REPONSE]' if t.get('posts_count',0)<=1 else ''}",
                        auteur="", date_src=t.get("created_at","")))
    return out

def c_stackoverflow(mots):
    out = []
    for tag in ("n8n", "ollama", "llama-index", "langchain", "rag", "vector-database",
                "huggingface-transformers", "self-hosted"):
      for page in range(1, PAGES + 1):
        try:
            d = jget("https://api.stackexchange.com/2.3/questions?site=stackoverflow&pagesize=25"
                     f"&page={page}&order=desc&sort=creation&tagged={tag}&filter=withbody")
        except Exception as e:
            log(f"  stackoverflow '{tag}' p{page} : {e}"); break
        if not d.get("items"):
            break
        for it in d.get("items", []):
            out.append(dict(source="stackoverflow", url=it.get("link",""),
                            titre=strip_html(it.get("title","")),
                            extrait=(strip_html(it.get("body",""))[:400]
                                     + (" [SANS REPONSE]" if it.get("answer_count",0)==0 else "")),
                            auteur=(it.get("owner") or {}).get("display_name",""),
                            date_src=datetime.fromtimestamp(it.get("creation_date",0), UTC).isoformat()))
        time.sleep(1.5)
        if not d.get("has_more"):
            break
      # fin des pages pour ce tag
    return out

def c_freework(mots):
    out = []
    for q in ("intelligence artificielle", "n8n", "llm", "automatisation", "rag",
              "mlops", "data engineer", "devops"):
        try:
            html = get("https://www.free-work.com/fr/tech-it/jobs?query=" + urllib.parse.quote(q),
                       accept="text/html")
        except Exception as e:
            log(f"  freework '{q}' : {e}"); continue
        # Corrige le 19/08. L ancienne regex acceptait (?:job|mission), donc elle
        # capturait aussi /fr/tech-it/jobs/paris (filtres de ville) et le second <a>
        # de chaque carte, dont le texte est "Voir cette offre". Resultat mesure :
        # 26 des 39 signaux freework etaient du texte de bouton, et le cluster le plus
        # dense de tout le corpus (13 membres, cohesion 0,914) etait fait de 10 fois
        # "Voir cette offre". Seul /job-mission/ designe une vraie offre.
        vus = set()
        for m in re.finditer(r'<a[^>]+href="(/fr/tech-it/job-mission/[^"]+)"[^>]*>(.*?)</a>',
                             html, re.S):
            url, titre = m.group(1), strip_html(m.group(2))
            if url in vus or len(titre) < 15:
                continue
            vus.add(url)
            out.append(dict(source="freework", url="https://www.free-work.com"+url,
                            titre=titre[:200], extrait=f"recherche: {q}", auteur="", date_src=""))
        time.sleep(3)
    return out

# google-trends N EST PLUS dans le set par defaut : mesure du 19/08, le flux FR
# generaliste ne remonte que du divertissement (GTA 6, matchs, personnalites) et
# ses 11 signaux etaient tous sous le seuil du filtre qualite. Reste accessible
# explicitement via --sources=google-trends.

# ── COLLECTEURS D OFFRES ET MISSIONS ──────────────────────────────────────────
# Mesure du 19/08 : sur 33 patterns qualifies, seuls 3 croisaient une DEMANDE
# (offre d emploi) avec un PROBLEME technique. Cause chiffree : 1589 signaux de
# problemes (SO+GitHub+HN) contre 89 offres. Un croisement demande/probleme est
# le seul qui porte un signal commercial — d ou ces sources supplementaires.

def c_remoteok(mots):
    d = jget("https://remoteok.com/api")
    out = []
    for it in d[1:] if isinstance(d, list) else []:   # [0] = mention legale
        titre = strip_html(it.get("position") or "")
        if not titre: continue
        tags = ",".join(it.get("tags") or [])
        if mots and not any(m in (titre+tags).lower() for m in mots): continue
        out.append(dict(source="remoteok", url=it.get("url") or it.get("apply_url") or "",
                        titre=f"{titre} — {it.get('company','')}".strip(" —"),
                        extrait=(strip_html(it.get("description") or "")[:400] or tags),
                        auteur=it.get("company",""), date_src=it.get("date","")))
    return out

def c_arbeitnow(mots):
    out = []
    for page in range(1, PAGES + 1):
        try:
            d = jget(f"https://www.arbeitnow.com/api/job-board-api?page={page}")
        except Exception as e:
            log(f"  arbeitnow p{page} : {e}"); break
        items = d.get("data") or []
        if not items: break
        for it in items:
            titre = strip_html(it.get("title") or "")
            if not titre: continue
            blob = (titre + " " + " ".join(it.get("tags") or [])).lower()
            if mots and not any(m in blob for m in mots): continue
            out.append(dict(source="arbeitnow", url=it.get("url",""),
                            titre=f"{titre} — {it.get('company_name','')}".strip(" —"),
                            extrait=strip_html(it.get("description") or "")[:400],
                            auteur=it.get("company_name",""),
                            date_src=str(it.get("created_at",""))))
        time.sleep(1.5)
    return out

def c_remotive(mots):
    out = []
    for q in ("AI", "machine learning", "automation", "data engineer", "LLM", "devops"):
        try:
            d = jget("https://remotive.com/api/remote-jobs?limit=40&search="
                     + urllib.parse.quote(q))
        except Exception as e:
            log(f"  remotive '{q}' : {e}"); continue
        for it in d.get("jobs") or []:
            out.append(dict(source="remotive", url=it.get("url",""),
                            titre=f"{strip_html(it.get('title',''))} — {it.get('company_name','')}".strip(" —"),
                            extrait=strip_html(it.get("description") or "")[:400],
                            auteur=it.get("company_name",""),
                            date_src=it.get("publication_date","")))
        time.sleep(2)
    return out

def c_jobicy(mots):
    out = []
    for tag in ("python", "devops", "data-science", "engineering"):
        try:
            d = jget(f"https://jobicy.com/api/v2/remote-jobs?count=50&tag={tag}")
        except Exception as e:
            log(f"  jobicy '{tag}' : {e}"); continue
        for it in d.get("jobs") or []:
            out.append(dict(source="jobicy", url=it.get("url",""),
                            titre=f"{strip_html(it.get('jobTitle',''))} — {it.get('companyName','')}".strip(" —"),
                            extrait=strip_html(it.get("jobExcerpt") or "")[:400],
                            auteur=it.get("companyName",""), date_src=it.get("pubDate","")))
        time.sleep(1.5)
    return out

def c_hn_hiring(mots):
    """Fils « Who is hiring » de Hacker News, via l index Algolia.

    Chaque commentaire de ces fils EST une offre : c est du recrutement direct,
    sans intermediaire, souvent avec la stack nommee."""
    out = []
    for q in ("hiring AI engineer", "hiring machine learning", "hiring automation",
              "hiring data engineer", "hiring LLM"):
        for page in range(min(PAGES, 5)):
            try:
                d = jget("https://hn.algolia.com/api/v1/search?tags=comment&hitsPerPage=50"
                         f"&page={page}&query=" + urllib.parse.quote(q))
            except Exception as e:
                log(f"  hn-hiring '{q[:22]}' p{page} : {e}"); break
            hits = d.get("hits") or []
            if not hits: break
            for h in hits:
                txt = strip_html(h.get("comment_text") or "")
                if len(txt) < 90: continue
                out.append(dict(source="hn-hiring",
                                url=f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                                titre=txt[:150], extrait=txt[:400],
                                auteur=h.get("author",""), date_src=h.get("created_at","")))
            time.sleep(1.5)
    return out

COLLECTEURS = {
    "hacker-news": c_hacker_news,
    "github-issues": c_github_issues, "n8n-forum": c_n8n_forum,
    "stackoverflow": c_stackoverflow, "freework": c_freework,
    # sources d OFFRES : le cote "demande solvable" du corpus
    "remoteok": c_remoteok, "arbeitnow": c_arbeitnow, "remotive": c_remotive,
    "jobicy": c_jobicy, "hn-hiring": c_hn_hiring,
}
COLLECTEURS_OPTIONNELS = {"google-trends": c_google_trends}

def schema(c):
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""CREATE TABLE IF NOT EXISTS moisson_signaux (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL, url_hash TEXT NOT NULL, url TEXT,
        titre TEXT, extrait TEXT, auteur TEXT, date_src TEXT,
        tour INTEGER DEFAULT 1, requete TEXT,
        recolte_le TEXT, UNIQUE(source, url_hash))""")
    c.execute("CREATE INDEX IF NOT EXISTS ix_moisson_source ON moisson_signaux(source)")

def ecrire(rows, tour, requete):
    avant_filtre = len(rows)
    rows = [r for r in rows if utile(r.get("titre"))]
    if avant_filtre != len(rows):
        log(f"    filtre qualite : {avant_filtre - len(rows)} libelle(s) de navigation ecarte(s)")
    if not rows: return 0, 0
    c = sqlite3.connect(DB, timeout=60); schema(c)
    avant = c.execute("SELECT COUNT(*) FROM moisson_signaux").fetchone()[0]
    c.executemany("""INSERT INTO moisson_signaux
        (source,url_hash,url,titre,extrait,auteur,date_src,tour,requete,recolte_le)
        VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))
        ON CONFLICT(source,url_hash) DO UPDATE SET
          extrait=excluded.extrait, recolte_le=excluded.recolte_le""",
        [(r["source"], sig(r["url"], r["titre"]), r["url"], r["titre"], r["extrait"],
          r["auteur"], r["date_src"], tour, requete) for r in rows])
    c.commit()
    apres = c.execute("SELECT COUNT(*) FROM moisson_signaux").fetchone()[0]
    c.close()
    return apres - avant, len(rows)

def main():
    mots = [a.lower() for a in sys.argv[1:] if not a.startswith("--")]
    tour = 1
    global PAGES
    for a in sys.argv:
        if a.startswith("--tour="):  tour = int(a.split("=")[1])
        if a.startswith("--pages="): PAGES = max(1, min(20, int(a.split("=")[1])))
    seules = None
    for a in sys.argv:
        if a.startswith("--sources="): seules = set(a.split("=")[1].split(","))

    tous = {**COLLECTEURS, **COLLECTEURS_OPTIONNELS}
    cibles = ({k: v for k, v in tous.items() if k in seules} if seules else dict(COLLECTEURS))
    log(f"=== MOISSON — {len(cibles)} source(s), {PAGES} page(s)/source, tour {tour}"
        f"{', filtre: ' + ','.join(mots) if mots else ''} ===")
    t0 = time.time(); tot_new = tot_vus = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(f, mots): n for n, f in cibles.items()}
        for fut in as_completed(futs):
            nom = futs[fut]
            try:
                rows = fut.result()
            except Exception as e:
                log(f"  {nom:<16} ECHEC : {type(e).__name__} {e}")   # jamais silencieux
                continue
            new, vus = ecrire(rows, tour, " ".join(mots))
            tot_new += new; tot_vus += vus
            log(f"  {nom:<16} {vus:>4} vus, {new:>4} nouveaux")
    log(f"=== FIN — {tot_vus} signaux vus, {tot_new} nouveaux, {time.time()-t0:.0f}s ===")

if __name__ == "__main__":
    main()
