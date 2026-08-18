#!/usr/bin/env python3
"""
jarvis-linkedin — pilotage de la campagne LinkedIn, cascade 0-token.

LOI D'OR RESPECTEE :
  SQL/cache AVANT toute inference · fallback ordonne · on-demand seulement
  (aucune boucle, aucun daemon) · NE PUBLIE NI N'ENVOIE JAMAIS RIEN.

Topologie reelle (2026-08-18) : M4 (ici) + M6 (cable direct) + Ollama local.
M1 = SSD USB-C, pas un noeud.  M2/M3 = detruites.

  jarvis-linkedin etat                 etat de campagne (0 inference)
  jarvis-linkedin backends             sonde les backends 0-token
  jarvis-linkedin draft <id>           redige un message pour une cible
  jarvis-linkedin draft --accepted     idem pour toutes les cibles ACCEPTE sans DM (max 6)
  jarvis-linkedin draft <id> --force   ignore le cache
"""
import os, sys, json, sqlite3, hashlib, urllib.request, datetime

DB     = os.path.expanduser("~/jarvis/jarvis_master.db")
TABLE  = "campagne_linkedin_20260818"
DRAFTS = os.path.expanduser("~/jarvis/campagnes/linkedin-toulouse-20260818/drafts")
MAX_LOT, MAX_TOKENS = 6, 320

# fallback ordonne : le moins cher / le plus proche d'abord
BACKENDS = [
    ("M6-cable",   "http://10.42.0.230:1234/v1/chat/completions",  "qwen/qwen3.5-9b"),
    ("hub-cascade","http://127.0.0.1:18800/v1/chat/completions",   "jarvis-quality"),
    ("ollama-M4",  "http://127.0.0.1:11434/v1/chat/completions",   "qwen2.5:7b"),
]

class AIUnavailable(Exception): pass

def db(ro=False):
    c = sqlite3.connect(f"file:{DB}?mode=ro" if ro else DB, uri=True)
    c.row_factory = sqlite3.Row
    return c

# ---------- cache SQL : lu AVANT toute inference ----------
def cache_get(key):
    try:
        with db(ro=True) as c:
            r = c.execute("SELECT text FROM ai_cache WHERE k=?", (key,)).fetchone()
            return r["text"] if r else None
    except Exception:
        return None

def cache_put(key, txt):
    try:
        with db() as c:
            c.execute("INSERT OR REPLACE INTO ai_cache(k,text,created_at) VALUES(?,?,datetime('now'))", (key, txt))
    except Exception as e:
        print(f"  [avert] cache non ecrit : {e}", file=sys.stderr)

def ask(prompt, force=False):
    """Retourne (texte, backend). cache -> M6 -> hub -> ollama."""
    key = "linkedin:" + hashlib.sha256(prompt.encode()).hexdigest()[:32]
    if not force:
        hit = cache_get(key)
        if hit:
            return hit, "cache"
    last = ""
    for name, url, model in BACKENDS:
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                           "max_tokens": MAX_TOKENS, "temperature": 0.5}).encode()
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                txt = json.load(r)["choices"][0]["message"]["content"].strip()
            if txt:
                cache_put(key, txt)
                return txt, name
            last = "reponse vide"
        except Exception as e:
            last = f"{type(e).__name__}"
            continue
    raise AIUnavailable(f"aucun backend 0-token n'a repondu (dernier: {last})")

# ---------- commandes ----------
def cmd_backends():
    print("Backends 0-token (ordre de cascade) :")
    for name, url, model in BACKENDS:
        base = url.rsplit("/v1/", 1)[0] + "/v1/models"
        try:
            with urllib.request.urlopen(base, timeout=6) as r:
                n = len(json.load(r).get("data", []))
            print(f"  [OK]   {name:<13} {model:<22} ({n} modele(s))")
        except Exception as e:
            print(f"  [DOWN] {name:<13} {model:<22} {type(e).__name__}")

def cmd_etat():
    with db(ro=True) as c:
        print("== Campagne LinkedIn — etat (0 inference) ==")
        for r in c.execute(f"SELECT canal,statut,COUNT(*) n FROM {TABLE} GROUP BY 1,2 ORDER BY 1,2"):
            print(f"  {r['canal']:<10} {r['statut']:<12} {r['n']}")
        print("\n-- en attente de reponse (invites) --")
        for r in c.execute(f"SELECT nom,entreprise,substr(invite_le,1,10) d FROM {TABLE} WHERE statut='INVITE' ORDER BY invite_le DESC LIMIT 8"):
            print(f"  · {r['nom']:<26} {(r['entreprise'] or '')[:28]:<30} {r['d'] or ''}")
        n = c.execute(f"SELECT COUNT(*) n FROM {TABLE} WHERE statut='ACCEPTE' AND (dm_le IS NULL OR dm_le='')").fetchone()["n"]
        print(f"\n-- A RELANCER : {n} cible(s) ACCEPTE sans message --")
        if n: print("   -> jarvis-linkedin draft --accepted")

def prompt_for(row):
    canal = row["canal"]
    role  = "recruteur tech" if canal == "RECRUTEUR" else "decideur en startup"
    return f"""Tu rediges un message LinkedIn court, en francais, pour Franck Delmas,
architecte infrastructure IA a Toulouse. Il deploie des infras d'inference qui
tournent entierement en local (cluster GPU, orchestration multi-noeuds, aucune
donnee envoyee a un fournisseur externe).

DESTINATAIRE : {row['nom']} — {row['fonction'] or 'fonction inconnue'} chez {row['entreprise'] or '?'} ({role}).
CE QU'ON SAIT DE SON BESOIN : {(row['preuve_besoin'] or 'aucun signal documente')[:400]}

REGLES ABSOLUES :
- Ecris a la PREMIERE PERSONNE : c'est Franck qui parle ("je", "j'ai construit").
  Ne parle JAMAIS de Franck a la 3e personne, ne le presente pas comme un tiers.
- 5 phrases maximum. Ton pair-a-pair, jamais demandeur d'emploi.
- Ouvrir sur SON probleme concret, pas sur Franck.
- Aucun chiffre invente : ne cite ni nombre de GPU, ni nombre d'agents, ni latence.
- INTERDIT ABSOLU : ne jamais pretendre qu'il a deja des clients, des references,
  qu'il a "aide d'autres structures", ni citer un cas client. Il n'en a aucun de
  publiable. Parler UNIQUEMENT de ce qu'il a construit lui-meme.
- Ne jamais inventer de fait sur le destinataire au-dela de ce qui est fourni ci-dessus.
- Finir par une porte de sortie ("sinon, ca ne coute rien de m'oublier").
- Pas de CV, pas de piece jointe, pas de lien.
Rends UNIQUEMENT le message, sans commentaire ni titre."""

def cmd_draft(args):
    force = "--force" in args
    ids = [a for a in args if a.isdigit()]
    with db(ro=True) as c:
        if "--accepted" in args:
            rows = c.execute(f"SELECT * FROM {TABLE} WHERE statut='ACCEPTE' AND (dm_le IS NULL OR dm_le='') ORDER BY id LIMIT {MAX_LOT}").fetchall()
        elif ids:
            q = ",".join("?" * len(ids))
            rows = c.execute(f"SELECT * FROM {TABLE} WHERE id IN ({q})", ids).fetchall()
        else:
            print("usage: jarvis-linkedin draft <id> | --accepted [--force]"); return 1
    if not rows:
        print("Aucune cible correspondante. (Personne n'a encore accepte ?)"); return 0
    if len(rows) > MAX_LOT:
        print(f"Lot plafonne a {MAX_LOT}."); rows = rows[:MAX_LOT]
    os.makedirs(DRAFTS, exist_ok=True)
    for r in rows:
        print(f"\n─── #{r['id']} {r['nom']} — {r['entreprise'] or '?'} ───")
        try:
            txt, backend = ask(prompt_for(r), force=force)
        except AIUnavailable as e:
            print(f"  [KO] {e}"); continue
        slug = "".join(ch if ch.isalnum() else "_" for ch in (r["nom"] or "sans_nom")).lower()
        path = os.path.join(DRAFTS, f"{r['id']:03d}_{slug}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# BROUILLON — {r['nom']} ({r['entreprise']})\n"
                    f"# backend: {backend} · genere: {datetime.datetime.now():%Y-%m-%d %H:%M}\n"
                    f"# RIEN N'A ETE ENVOYE. Relire, puis copier-coller a la main.\n\n{txt}\n")
        print(f"  backend : {backend}")
        print(f"  fichier : {path}\n")
        print("  " + txt.replace("\n", "\n  "))
    print("\nAucun message n'a ete envoye. Relis les brouillons avant de copier.")
    return 0

def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"): print(__doc__); return 0
    if a[0] == "etat":     return cmd_etat()
    if a[0] == "backends": return cmd_backends()
    if a[0] == "draft":    return cmd_draft(a[1:])
    print(f"commande inconnue: {a[0]}"); print(__doc__); return 1

if __name__ == "__main__":
    sys.exit(main() or 0)
