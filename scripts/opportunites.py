#!/usr/bin/env python3
"""opportunites.py — moissonneur + qualifieur d'opportunites freelance. 0-token.

CASCADE (ordre impose, du moins cher au plus couteux) :
  1. SQL / cache   : aucune inference. Repond seul dans la majorite des cas.
  2. M6 RJ45       : 10.42.0.230:1234 — GPU deporte, 0 chaleur sur M4. Souvent DOWN.
  3. Remi-ASUS     : 100.113.121.61:11434 — deporte via Tailscale, gemma3:27b NON-thinking.
  4. Ollama local  : 127.0.0.1:11434 — DERNIER recours, chauffe M4. gemma3:4b.
Jamais d'IA facturee au runtime. Jamais de boucle d'inference permanente.

Pourquoi gemma3:27b et pas qwen3.5-9b : mesure du 19/08 — qwen3.5 consomme 100 % de
max_tokens en reasoning_tokens et renvoie un contenu VIDE ; enable_thinking:false et
reasoning_effort sont ignores par cette version de LM Studio. Un modele non-thinking
est donc obligatoire pour de la generation en lot.

Usage :
  opportunites.py status              etat des backends + volumetrie
  opportunites.py score [--top N]     classement 0-token (SQL pur, aucune inference)
  opportunites.py lettre <rowid>      candidature (cache SQL, sinon cascade)
  opportunites.py lot <N>             N candidatures du top, sequentiel, plafonne
  opportunites.py stats               distribution TJM / fraicheur / canaux
"""
import json, sqlite3, sys, time, urllib.request

DB = "/home/pamerys/jarvis/jarvis_master.db"

# (nom, url, modele, deporte?) — l'ordre EST la cascade.
BACKENDS = [
    # Ollama CLOUD en tete : le compute part chez Ollama, donc 0 token Anthropic ET
    # 0 chaleur sur M4 — le vrai "backend deporte" du pattern dispatch-generation-masse.
    # Mesure 19/08 : 1,2 s de latence contre 4 min 48 s sur gemma3:4b local.
    ("OL-cloud",   "http://127.0.0.1:11434/v1/chat/completions",      "gpt-oss:20b-cloud", True),
    ("M6-RJ45",    "http://10.42.0.230:1234/v1/chat/completions",     "qwen/qwen3.5-9b",   True),
    ("Remi-ASUS",  "http://100.113.121.61:11434/v1/chat/completions", "gemma3:27b",        True),
    ("OL1-local",  "http://127.0.0.1:11434/v1/chat/completions",      "gemma3:4b",         False),
]
MAX_LOT = 6          # plafond dur : pas de gros batch synchrone
MAX_TOKENS = 700

SOCLE = """Franck Delmas, architecte IA freelance, Toulouse, remote possible.
Positionnement : DELIVERY TECHNIQUE en sous-traitance.
Competences : agents IA et orchestration multi-agents, RAG, automatisation n8n,
connecteurs sur mesure, MLOps, self-hosting, Docker/Swarm, PostgreSQL, Python.
Preuves MESUREES le 2026-08-19 (les seules citables, re-comptees ce jour) :
319 agents indexes (table agent_index), 5 GPU NVIDIA repartis sur 2 machines
(4 sur la tour : RTX 2060, GTX 1660 SUPER, RTX 3080, GTX 1660 SUPER ; 1 RTX 3050
sur le portable), corpus documentaire de 272 464 chunks FTS5 sur 29 390 sources,
recherche plein texte FTS5 en 4,12 ms, 20 depots publics GitHub sur 176 possedes.
NON REVERIFIES le 19/08, donc a ne pas citer tant qu ils ne le sont pas :
transcription sous 500 ms, debit I/O 12 a 380 Mo/s, requetes RAG 1800 ms a 47 ms.
INTERDIT de citer : 928 agents (code en dur, jamais mesure — vraie valeur 319),
6 GPU (vraie valeur 5, et PAS tous en local), 44 depots (vraie valeur 20 publics),
1000+ agents, 12 GPU, 6 machines, latence <300 ms, +340% ROI, 14h/semaine,
6x plus rapide — chiffres invalides, verifies faux les 18 et 19/08/2026."""


def co(ro=False):
    c = sqlite3.connect(f"file:{DB}?mode=ro" if ro else DB, uri=ro, timeout=30)
    if not ro:
        c.execute("""CREATE TABLE IF NOT EXISTS opportunites_lettres (
            rowid_mission INTEGER PRIMARY KEY, titre TEXT, lettre TEXT,
            backend TEXT, genere_le TEXT DEFAULT (datetime('now')))""")
    return c


def sonde(url):
    base = url.rsplit("/v1/", 1)[0]
    for suffixe in ("/v1/models", "/api/tags"):
        try:
            req = urllib.request.Request(base + suffixe, headers={"User-Agent": "jarvis"})
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status == 200:
                    return True
        except Exception:
            continue
    return False


def cmd_status():
    print("CASCADE — du moins cher au plus couteux\n")
    for nom, url, modele, deporte in BACKENDS:
        ok = sonde(url)
        lieu = "deporte (0 chaleur M4)" if deporte else "LOCAL (chauffe M4)"
        print(f"  {'UP  ' if ok else 'DOWN'}  {nom:<10} {modele:<18} {lieu}")
    c = co(ro=True)
    n, f, v = c.execute("""select count(*),
        sum(contrat like '%CONTRACTOR%'),
        sum(valide_jusqu >= date('now'))
        from freework_missions""").fetchone()
    try:
        lettres = c.execute("select count(*) from opportunites_lettres").fetchone()[0]
    except sqlite3.OperationalError:
        lettres = 0
    print(f"\n  missions : {n} · freelance {f} · encore valides {v}")
    print(f"  lettres en cache : {lettres} (0 inference pour les relire)")
    c.close()


def score_sql():
    """Scoring 100 % SQL. Aucune inference — c'est la LOI 2."""
    c = co(ro=True)
    lignes = c.execute("""
      select rowid, titre, url, publie,
             cast(nullif(tjm_min,'') as integer), cast(nullif(tjm_max,'') as integer),
             coalesce(nullif(ville,''), region, '?'), coalesce(nullif(client,''),'?'),
             lower(titre || ' ' || coalesce(description,''))
      from freework_missions
      where contrat like '%CONTRACTOR%' and valide_jusqu >= date('now')""").fetchall()
    c.close()
    out = []
    for rid, titre, url, pub, tmin, tmax, ville, client, blob in lignes:
        s, why = 0, []
        tj = tmin or 0
        if tj >= 700: s, _ = s + 4, why.append("TJM>=700")
        elif tj >= 600: s, _ = s + 3, why.append("TJM>=600")
        elif tj >= 550: s, _ = s + 2, why.append("TJM>=550")
        if pub >= time.strftime("%Y-%m-%d", time.localtime(time.time() - 7 * 86400)):
            s, _ = s + 3, why.append("fraiche<7j")
        if "toulouse" in ville.lower() or "occitanie" in ville.lower():
            s, _ = s + 3, why.append("LOCAL")
        for mot, pts in (("rag", 2), ("agent", 2), ("llm", 2), ("mlops", 2),
                         ("n8n", 3), ("ia générative", 2), ("automatisation", 1)):
            if mot in blob:
                s, _ = s + pts, why.append(mot)
        if "asap" in blob or "démarrage immédiat" in blob:
            s, _ = s + 2, why.append("ASAP")
        if s:
            out.append((s, rid, titre, url, pub, tj, tmax or 0, ville, client, ",".join(dict.fromkeys(why))))
    out.sort(reverse=True)
    return out


def cmd_score(n=20):
    top = score_sql()
    print(f"{len(top)} missions scorees (SQL pur, 0 inference)\n")
    for s, rid, titre, url, pub, tmin, tmax, ville, client, why in top[:n]:
        print(f"  [{s:2}] #{rid:<5} {titre[:50]:50} {tmin or '?':>4}-{tmax or '?':<4} {ville[:14]:14} {pub}")
        print(f"        {why[:74]}")


def infere(prompt):
    """Cascade. Renvoie (backend, texte). Leve RuntimeError si tout est muet."""
    dernier = None
    for nom, url, modele, _ in BACKENDS:
        corps = json.dumps({"model": modele,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": MAX_TOKENS, "temperature": 0.4}).encode()
        try:
            req = urllib.request.Request(url, data=corps,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=240) as r:
                d = json.load(r)
            txt = d["choices"][0]["message"]["content"].strip()
            if "</think>" in txt:
                txt = txt.split("</think>")[-1].strip()
            # Un modele thinking peut rendre 200 + contenu VIDE : ce n'est PAS un succes.
            if not txt:
                dernier = f"{nom}: reponse vide (thinking a consomme le budget)"
                continue
            return nom, txt
        except Exception as exc:
            dernier = f"{nom}: {exc}"
            continue
    raise RuntimeError(f"toute la cascade est muette — {dernier}")


def cmd_lettre(rid, silencieux=False):
    c = co()
    cache = c.execute("select lettre, backend from opportunites_lettres where rowid_mission=?",
                      (rid,)).fetchone()
    if cache:                                    # SQL AVANT inference — LOI 2
        if not silencieux:
            print(f"[backend: cache · 0 inference]\n\n{cache[0]}")
        c.close()
        return cache[0]
    m = c.execute("""select titre, coalesce(nullif(client,''),'?'),
                            coalesce(nullif(ville,''), region, '?'),
                            nullif(tjm_min,''), nullif(tjm_max,''), url
                     from freework_missions where rowid=?""", (rid,)).fetchone()
    if not m:
        print(f"mission #{rid} introuvable"); c.close(); return None
    titre, client, ville, tmin, tmax, url = m
    prompt = f"""{SOCLE}

MISSION : {titre}
Client : {client} · Lieu : {ville} · TJM affiche : {tmin or '?'}-{tmax or '?'} EUR/jour

Redige la candidature de Franck. Contraintes STRICTES :
- Francais, 120 a 160 mots, direct, aucune flatterie.
- Ouvre sur ce que la mission demande, pas sur lui.
- Cite 2 preuves chiffrees du socle, choisies pour CETTE mission.
- N'invente aucun chiffre, aucune reference client, aucune experience non listee.
- Termine par une disponibilite et une proposition d'echange court.
Rends UNIQUEMENT le texte de la candidature."""
    try:
        backend, txt = infere(prompt)
    except RuntimeError as e:
        print(f"⛔ {e}"); c.close(); return None
    c.execute("""insert or replace into opportunites_lettres
                 (rowid_mission, titre, lettre, backend) values (?,?,?,?)""",
              (rid, titre, txt, backend))
    c.commit(); c.close()
    if not silencieux:
        print(f"[backend: {backend}]\n\n{txt}\n\n{url}")
    return txt


def cmd_lot(n):
    n = min(n, MAX_LOT)                          # plafond dur, pas de batch massif
    top = score_sql()[:n]
    print(f"generation de {len(top)} candidature(s) — plafond {MAX_LOT}, sequentiel\n")
    ok = 0
    for s, rid, titre, *_ in top:
        print(f"  #{rid} [{s}] {titre[:56]}", flush=True)
        if cmd_lettre(rid, silencieux=True):
            ok += 1
        time.sleep(1)
    print(f"\n{ok}/{len(top)} generees. Relire avec : opportunites.py lettre <rowid>")


def cmd_stats():
    c = co(ro=True)
    for libelle, sql in (
        ("TJM (freelance, valides)",
         """select count(*), min(cast(tjm_min as integer)), max(cast(tjm_max as integer))
            from freework_missions where contrat like '%CONTRACTOR%'
              and valide_jusqu>=date('now') and tjm_min not in ('','None')"""),
        ("publiees ces 7 jours",
         """select count(*) from freework_missions
            where contrat like '%CONTRACTOR%' and publie >= date('now','-7 day')"""),
        ("Occitanie / Toulouse",
         """select count(*) from freework_missions where contrat like '%CONTRACTOR%'
              and valide_jusqu>=date('now')
              and (lower(ville) like '%toulouse%' or lower(region) like '%occitanie%')"""),
    ):
        print(f"  {libelle:28} {c.execute(sql).fetchone()}")
    c.close()


if __name__ == "__main__":
    a = sys.argv[1:] or ["status"]
    cmd = a[0]
    if cmd == "status":  cmd_status()
    elif cmd == "score": cmd_score(int(a[a.index("--top") + 1]) if "--top" in a else 20)
    elif cmd == "lettre" and len(a) > 1: cmd_lettre(int(a[1]))
    elif cmd == "lot":   cmd_lot(int(a[1]) if len(a) > 1 else 3)
    elif cmd == "stats": cmd_stats()
    else: print(__doc__)
