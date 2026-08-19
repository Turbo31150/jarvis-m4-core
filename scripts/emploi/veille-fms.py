#!/usr/bin/env python3
"""Veille des offres FMS (entreprise adaptée) — Toulouse. 0 token, lecture seule.
État persistant SQLite. Alerte Telegram uniquement sur changement."""
import re, json, sqlite3, sys, os, urllib.request
from datetime import datetime

URL = "https://fms-ea.nicoka.com/public/jobs/"
DB  = os.path.expanduser("~/jarvis/data/veille_emploi.db")
UA  = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151.0 Safari/537.36"
VILLES = ("toulouse",)

def fetch() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")

def parse(html: str) -> list[dict]:
    out = []
    for b in html.split('class="job-title"')[1:]:
        mu = re.search(r'href="([^"]*/public/jobs/([0-9a-f-]+))"', b)
        mt = re.search(r'class="text-primary"[^>]*>([^<]+)<', b)
        mv = re.search(r'job-info-ville"[^>]*>(?:<[^>]+>)*\s*([^<]+)<', b)
        mc = re.search(r'job-info[^"]*"><i class="fas fa-book[^>]*></i>([^<]+)<', b)
        if not (mu and mt):
            continue
        out.append({"ref": mu.group(2), "url": mu.group(1), "titre": mt.group(1).strip(),
                    "ville": (mv.group(1).strip() if mv else ""),
                    "contrat": (mc.group(1).strip() if mc else "")})
    return out

def db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS offres(
        ref TEXT PRIMARY KEY, titre TEXT, ville TEXT, contrat TEXT, url TEXT,
        vue_le TEXT, disparue_le TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS runs(ts TEXT, total INT, ciblees INT, nouvelles INT, disparues INT)""")
    return c

def telegram(msg: str) -> bool:
    tok = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not tok:
        env = os.path.expanduser("~/.config/jarvis/telegram.env")
        if os.path.exists(env):
            for l in open(env):
                if "=" in l and "TOKEN" in l.split("=")[0].upper():
                    tok = l.split("=", 1)[1].strip().strip('"\'')
                    break
    if not tok:
        return False
    data = json.dumps({"chat_id": "2010747443", "text": msg,
                       "parse_mode": "HTML", "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage",
                                 data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=15)
        return True
    except Exception as e:
        print(f"  telegram KO: {e}", file=sys.stderr)
        return False

def main():
    notify = "--notify" in sys.argv
    ts = datetime.now().isoformat(timespec="seconds")
    offres = parse(fetch())
    if not offres:
        print("ALERTE: 0 offre parsée — structure du site probablement changée", file=sys.stderr)
        sys.exit(2)
    cibles = [o for o in offres if any(v in o["ville"].lower() for v in VILLES)]
    c = db()
    connues = {r[0] for r in c.execute("SELECT ref FROM offres WHERE disparue_le IS NULL")}
    actuelles = {o["ref"] for o in cibles}
    nouvelles = [o for o in cibles if o["ref"] not in connues]
    disparues = connues - actuelles

    for o in nouvelles:
        c.execute("INSERT OR REPLACE INTO offres VALUES(?,?,?,?,?,?,NULL)",
                  (o["ref"], o["titre"], o["ville"], o["contrat"], o["url"], ts))
    for r in disparues:
        c.execute("UPDATE offres SET disparue_le=? WHERE ref=?", (ts, r))
    c.execute("INSERT INTO runs VALUES(?,?,?,?,?)", (ts, len(offres), len(cibles), len(nouvelles), len(disparues)))
    c.commit()

    print(f"[{ts}] {len(offres)} offres · {len(cibles)} Toulouse · {len(nouvelles)} nouvelle(s) · {len(disparues)} retirée(s)")
    for o in cibles:
        mark = "NOUVEAU " if o["ref"] in {n['ref'] for n in nouvelles} else "        "
        print(f"  {mark}{o['titre']} — {o['contrat']} — {o['url']}")

    if (nouvelles or disparues) and notify:
        m = "<b>VEILLE FMS TOULOUSE</b>\n"
        for o in nouvelles:
            m += f"\nNOUVELLE OFFRE\n<b>{o['titre']}</b> ({o['contrat']})\n{o['url']}\n"
        for r in disparues:
            row = c.execute("SELECT titre FROM offres WHERE ref=?", (r,)).fetchone()
            m += f"\nRetiree : {row[0] if row else r}\n"
        m += f"\n{len(cibles)} offre(s) Toulouse sur {len(offres)} publiees."
        print("  telegram:", "envoye" if telegram(m) else "ECHEC")
    c.close()

if __name__ == "__main__":
    main()
