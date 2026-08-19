#!/usr/bin/env python3
# patterns_marche.py — detection de patterns par clustering d embeddings. 0 token.
#
# Volet C du plan. Deux niveaux, volontairement distincts :
#
#   C1  vectoriser les signaux BRUTS (pas des interpretations generees). Un cluster
#       doit emerger de ce que le marche a REELLEMENT ecrit, pas de ce qu un modele
#       en aurait deduit : interpreter avant de regrouper injecterait le biais du
#       modele dans la geometrie.
#   C2  clusterer, seuil CALIBRE sur la distribution mesuree (jamais choisi a priori).
#   C3  superposition sur les clusters denses seulement : N lectures d un meme pattern,
#       pour verifier qu il tient. Garde-fou repris du 19/08 : si le cos intra des
#       lectures depasse 0,93, elles ne comptent que pour UNE (elles ont collapse).

import json, math, os, sqlite3, sys, time
from array import array
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

sys.path.insert(0, "/home/pamerys/jarvis/scripts")
import dispatch_superposition as D          # reutilise generer() / vectoriser() / Indispo
import urllib.request as _url

# ── CASCADE D EMBEDDINGS (LOI 2 : 0-token, du plus rapide au plus sûr) ────────
# M6/LM Studio est le backend prefere (cable direct, 1,4 ms). Mesure du 19/08 :
# son port 1234 est tombe en cours de run alors que M6 reste joignable (ping 1,4 ms,
# SSH et Ollama ouverts, 4 processus LM Studio vivants mais plus d ecoute HTTP).
# Ollama M6 ne sert PAS de modele d embedding ; Ollama M4 local sert nomic-embed-text
# en 768 d. On bascule donc sur M4 plutot que d attendre un service tombe.
#
# TRACABILITE OBLIGATOIRE : chaque vecteur porte le backend qui l a produit. Comparer
# des vecteurs issus de deux modeles differents n a AUCUN sens geometrique, et rien
# dans les chiffres ne le signalerait.
BACKENDS_EMB = [
    ("M6-lmstudio", "http://10.42.0.230:1234/v1/embeddings",
     "text-embedding-nomic-embed-text-v1.5", "openai"),
    ("M4-ollama",   "http://127.0.0.1:11434/api/embed", "nomic-embed-text", "ollama"),
]
_backend_actif = [None]
# --- POLITIQUE DE REPLI (19/08/2026, apres incident thermique) ---------------
# Par defaut le repli local est INTERDIT. Quand M6 est tombe pendant le volet C,
# toute la generation a bascule sur Ollama CPU local et le M4 est monte de 27 C
# a 94 C — exactement le scenario que la memoire de cette machine documente.
# Le repli CPU n est plus un filet, c est un risque materiel : sans M6 on
# S ARRETE et on le dit, au lieu de cuire le poste de controle en silence.
# Mettre PATTERNS_AUTORISER_LOCAL=1 pour lever ce garde-fou en connaissance de cause.
AUTORISER_LOCAL = os.environ.get("PATTERNS_AUTORISER_LOCAL", "0") == "1"

def _distants(liste):
    return liste if AUTORISER_LOCAL else [b for b in liste if "127.0.0.1" not in b[1]]

def temperature_max():
    """Temperature la plus haute du M4, en degres. 0 si aucun capteur lisible."""
    import glob
    t = 0
    for f in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            v = int(open(f).read().strip()) // 1000
            if 0 < v < 130:
                t = max(t, v)
        except Exception:
            pass
    return t

def _emb_une(url, modele, forme, texte, timeout=60):
    corps = ({"model": modele, "input": texte[:6000]} if forme == "openai"
             else {"model": modele, "input": texte[:6000]})
    req = _url.Request(url, data=json.dumps(corps).encode(),
                       headers={"Content-Type": "application/json"})
    with _url.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    if forme == "openai":
        return d["data"][0]["embedding"]
    e = d.get("embeddings") or ([d["embedding"]] if d.get("embedding") else None)
    if not e:
        raise D.Indispo(d.get("error", "reponse sans embedding"))
    return e[0]

def vectoriser_cascade(texte):
    """Renvoie (vecteur, nom_backend). Leve Indispo si TOUS les backends sont muets."""
    ordre = _distants(BACKENDS_EMB)
    if _backend_actif[0]:      # on ne re-sonde pas un backend mort a chaque appel
        ordre = sorted(ordre, key=lambda b: b[0] != _backend_actif[0])
    dernier = None
    for nom, url, modele, forme in ordre:
        try:
            v = _emb_une(url, modele, forme, texte)
            if _backend_actif[0] != nom:
                _backend_actif[0] = nom
            return v, nom
        except Exception as e:
            dernier = f"{nom}: {type(e).__name__}"
    raise D.Indispo(f"aucun backend d embedding ({dernier})")

DB  = D.DB
LOG = "/home/pamerys/jarvis/logs/patterns_marche.log"
_th = __import__("threading")
# RLock et non Lock : worker() incremente le compteur sous _lk puis appelle log(),
# qui reprend _lk. Un Lock simple n est PAS reentrant -> le thread se bloque
# lui-meme. Mesure du 19/08 : deadlock exactement au 40e vecteur (ok % 40 == 0),
# arret a 45 (40 + les 5 en vol), 0 connexion reseau, 7 threads endormis.
_lk = _th.RLock()

def log(m):
    line = f"[{datetime.now():%H:%M:%S}] {m}"
    with _lk:
        print(line, flush=True)
        try:
            with open(LOG, "a") as f: f.write(line + "\n")
        except OSError: pass

def cos(a, b):
    n = min(len(a), len(b))
    num = sum(a[i]*b[i] for i in range(n))
    da = math.sqrt(sum(x*x for x in a[:n])); db = math.sqrt(sum(x*x for x in b[:n]))
    return num/(da*db) if da and db else 0.0

def schema(c):
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""CREATE TABLE IF NOT EXISTS moisson_vecteurs (
        signal_id INTEGER PRIMARY KEY, embedding BLOB, dim INTEGER,
        backend TEXT, vectorise_le TEXT)""")
    cols = {r[1] for r in c.execute("PRAGMA table_info(moisson_vecteurs)")}
    if "backend" not in cols:
        c.execute("ALTER TABLE moisson_vecteurs ADD COLUMN backend TEXT")
    c.execute("""CREATE TABLE IF NOT EXISTS patterns_marche (
        id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT, taille INTEGER,
        sources TEXT, membres TEXT, cohesion REAL, centroide BLOB,
        lectures TEXT, cos_intra_lectures REAL, collapse INTEGER DEFAULT 0,
        tour INTEGER DEFAULT 1, cree_le TEXT)""")

# ── C1 : vectorisation des signaux bruts ─────────────────────────────────────
def vectoriser_signaux(limite=None):
    c = sqlite3.connect(DB, timeout=60); schema(c); c.row_factory = sqlite3.Row
    q = """SELECT s.id, s.source, s.titre, s.extrait FROM moisson_signaux s
           LEFT JOIN moisson_vecteurs v ON v.signal_id = s.id
           WHERE v.signal_id IS NULL"""
    if limite: q += f" LIMIT {limite}"
    todo = [dict(r) for r in c.execute(q)]
    c.close()
    if not todo:
        log("tous les signaux sont deja vectorises."); return 0
    log(f"C1 — vectorisation de {todo and len(todo)} signal(aux) sur M6...")
    ok = [0]
    def worker(s):
        txt = f"{s['titre']} — {s['extrait'] or ''}".strip()[:2000]
        for _ in range(4):
            try:
                v, bk = vectoriser_cascade(txt)
                cc = sqlite3.connect(DB, timeout=60)
                cc.execute("""INSERT INTO moisson_vecteurs (signal_id,embedding,dim,backend,vectorise_le)
                              VALUES (?,?,?,?,datetime('now'))
                              ON CONFLICT(signal_id) DO UPDATE SET
                                embedding=excluded.embedding, dim=excluded.dim,
                                backend=excluded.backend""",
                           (s["id"], array("f", v).tobytes(), len(v), bk))
                cc.commit(); cc.close()
                with _lk:
                    ok[0] += 1
                    if ok[0] % 40 == 0: log(f"  ... {ok[0]}/{len(todo)}")
                return True
            except D.Indispo:
                time.sleep(15)
            except sqlite3.OperationalError:
                time.sleep(2)
        log(f"  ABANDON signal {s['id']}")      # jamais de perte silencieuse
        return False
    # 24 workers et non 6 : debit MESURE sur M6 le 19/08 —
    #   1 worker 1,6/s · 6 workers 7,5/s · 12 workers 7,2/s · 24 workers 34,3/s
    # M6 encaisse le parallelisme (4 GPU), contrairement a Ollama local qui
    # SERIALISE (6 appels paralleles = 5,3 s chacun, aucun gain). Le M4 ne fait
    # qu emettre des requetes HTTP : il ne chauffe pas.
    n_workers = int(os.environ.get("PATTERNS_WORKERS", "24"))
    log(f"C1 — {n_workers} workers vers {'M6' if not AUTORISER_LOCAL else 'la cascade'}")
    with ThreadPoolExecutor(max_workers=n_workers) as ex:
        list(as_completed([ex.submit(worker, s) for s in todo]))
    log(f"C1 — {ok[0]}/{len(todo)} vectorises")
    return ok[0]

def charger():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    rows = c.execute("""SELECT s.id,s.source,s.titre,s.extrait,v.embedding,v.backend
                        FROM moisson_signaux s JOIN moisson_vecteurs v ON v.signal_id=s.id""").fetchall()
    # Refus de melanger : deux modeles d embedding placent le meme texte a des endroits
    # differents. Un cluster calcule sur un melange serait du bruit presente comme un
    # resultat. On garde le backend majoritaire et on DIT combien on ecarte.
    from collections import Counter
    cnt = Counter(r["backend"] or "?" for r in rows)
    c.close()
    if len(cnt) > 1:
        major = cnt.most_common(1)[0][0]
        ecartes = sum(v for k, v in cnt.items() if k != major)
        log(f"  ATTENTION — {len(cnt)} backends d embedding en base {dict(cnt)}. "
            f"On garde '{major}', on ECARTE {ecartes} vecteur(s) : melanger deux modeles "
            f"invaliderait la geometrie.")
        rows = [r for r in rows if (r["backend"] or "?") == major]
    out = []
    for r in rows:
        a = array("f"); a.frombytes(r["embedding"])
        out.append(dict(id=r["id"], source=r["source"], titre=r["titre"],
                        extrait=r["extrait"], vec=list(a)))
    return out

# ── C2 : calibration puis clustering ─────────────────────────────────────────
def distribution(items, ech=250):
    import random
    n = len(items)
    paires = [(i, j) for i in range(n) for j in range(i+1, n)]
    if len(paires) > 20000:
        paires = paires[::max(1, len(paires)//20000)]
    sims = sorted(cos(items[i]["vec"], items[j]["vec"]) for i, j in paires)
    def q(p): return sims[min(len(sims)-1, int(p*len(sims)))]
    return dict(n=len(sims), p50=q(.50), p90=q(.90), p95=q(.95), p99=q(.99),
                p995=q(.995), maxi=sims[-1])

def clusterer(items, seuil, methode="average"):
    """Agglomeratif. average-link par defaut ; single-link disponible pour comparaison.

    POURQUOI PAS single-link. Mesure du 19/08 sur 428 signaux propres : le single-link
    CHAINE. A proche de B, B proche de C, donc A et C atterrissent ensemble meme sans
    rien de commun. Resultat : a p95 (0,602) un seul cluster absorbait 393 des 428
    signaux, et meme a p995 le plus gros en gardait 36. Un tel cluster n est pas un
    pattern, c est le corpus entier avec une etiquette.

    average-link exige que la similarite MOYENNE entre les deux groupes depasse le
    seuil, ce qui casse les chaines. Implemente via scipy si present, sinon repli
    sur une agglomeration average en Python pur (O(n^3) mais n reste petit ici)."""
    if methode == "average":
        try:
            return _clusterer_average(items, seuil)
        except ImportError:
            log("  scipy absent -> average-link en Python pur")
            return _clusterer_average_pur(items, seuil)
    return _clusterer_single(items, seuil)

def _clusterer_average(items, seuil):
    import numpy as np
    from scipy.cluster.hierarchy import linkage, fcluster
    from scipy.spatial.distance import pdist
    X = np.array([i["vec"] for i in items], dtype="float32")
    X /= (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)
    d = pdist(X, metric="cosine")                 # distance = 1 - cos
    Z = linkage(d, method="average")
    lab = fcluster(Z, t=1.0 - seuil, criterion="distance")
    g = {}
    for i, l in enumerate(lab):
        g.setdefault(int(l), []).append(i)
    return [v for v in g.values() if len(v) >= 2]

def _clusterer_average_pur(items, seuil):
    groupes = [[i] for i in range(len(items))]
    sim = {}
    def s(a, b):
        k = (min(a, b), max(a, b))
        if k not in sim:
            sim[k] = cos(items[a]["vec"], items[b]["vec"])
        return sim[k]
    while True:
        best, bi, bj = seuil, None, None
        for x in range(len(groupes)):
            for y in range(x + 1, len(groupes)):
                m = sum(s(a, b) for a in groupes[x] for b in groupes[y]) / (len(groupes[x])*len(groupes[y]))
                if m >= best:
                    best, bi, bj = m, x, y
        if bi is None:
            break
        groupes[bi] += groupes.pop(bj)
    return [g for g in groupes if len(g) >= 2]

def _clusterer_single(items, seuil):
    """Single-link par union-find. Conserve pour comparaison, PAS pour la production."""
    n = len(items)
    parent = list(range(n))
    def trouve(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def unir(a, b):
        ra, rb = trouve(a), trouve(b)
        if ra != rb: parent[rb] = ra
    for i in range(n):
        for j in range(i+1, n):
            if cos(items[i]["vec"], items[j]["vec"]) >= seuil:
                unir(i, j)
    groupes = {}
    for i in range(n):
        groupes.setdefault(trouve(i), []).append(i)
    return [g for g in groupes.values() if len(g) >= 2]

def centrer_par_source(items):
    """Retire l effet de PLATEFORME pour laisser l effet de CONTENU.

    Mesure du 19/08 : 16 clusters sur 16 etaient mono-source, et la matrice de
    similarite montre que la diagonale (interne a une source) domine partout le
    hors-diagonale — freework 0,681 contre 0,393-0,481 ; n8n-forum 0,569 contre
    0,456-0,504. Autrement dit l embedding capture d abord la FACON D ECRIRE du
    site, ensuite le sujet. Un cluster mono-source n est donc pas un signal de
    marche, c est un signal de site.

    Correction standard : soustraire a chaque vecteur le centroide de SA source,
    puis renormer. Ce qui reste est ce qui distingue un message des autres messages
    DU MEME SITE — donc du contenu, plus du style de plateforme.
    Aucune inference : algebre seule, 0 token et 0 chaleur."""
    from collections import defaultdict
    par = defaultdict(list)
    for i, it in enumerate(items):
        par[it["source"]].append(i)
    out = [dict(it) for it in items]
    for src, idx in par.items():
        dim = len(items[idx[0]]["vec"])
        cent = [sum(items[i]["vec"][k] for i in idx)/len(idx) for k in range(dim)]
        for i in idx:
            v = [items[i]["vec"][k] - cent[k] for k in range(dim)]
            n = math.sqrt(sum(x*x for x in v)) or 1.0
            out[i]["vec"] = [x/n for x in v]
    return out

def cohesion(items, idx):
    if len(idx) < 2: return 1.0
    s = [cos(items[a]["vec"], items[b]["vec"])
         for x, a in enumerate(idx) for b in idx[x+1:]]
    return sum(s)/len(s)

# ── C3 : superposition sur les clusters denses ───────────────────────────────
ANGLES_PATTERN = {
 "BESOIN":   "Quel BESOIN concret ces messages expriment-ils ? Une phrase.",
 "STACK":    "Quelle STACK TECHNIQUE precise est en jeu ? Une phrase. Si aucune n est nommee, dis-le.",
 "URGENCE":  "Ces messages traduisent-ils une URGENCE ou une exploration tranquille ? Une phrase, justifiee par le texte.",
 "FAUX":     "Ces messages forment-ils un vrai theme commun, ou sont-ils regroupes par hasard ? Reponds franchement, une phrase.",
}

# ── CASCADE DE GENERATION (meme raison que pour les embeddings) ──────────────
BACKENDS_GEN = [
    # qwen3-4b EN TETE : la qualification produit 4 phrases courtes, pas de la
    # redaction fine. Mesure du 19/08 : le 4B repond en 2,7 s la ou le 9B, charge
    # a 32768 de contexte, prend des dizaines de secondes pour le meme resultat.
    ("M6-lmstudio", "http://10.42.0.230:1234/v1/completions", "qwen/qwen3-4b", "lmstudio"),
    ("M6-lms-9b",   "http://10.42.0.230:1234/v1/completions", "qwen/qwen3.5-9b", "lmstudio"),
    ("M4-ollama",   "http://127.0.0.1:11434/api/generate",    "qwen2.5:7b",      "ollama"),
    ("M4-ollama-s", "http://127.0.0.1:11434/api/generate",    "gemma3:4b",       "ollama"),
]
_gen_actif = [None]

def generer_cascade(prompt, max_tokens=110, temperature=0.5):
    ordre = _distants(BACKENDS_GEN)
    if _gen_actif[0]:
        ordre = sorted(ordre, key=lambda b: b[0] != _gen_actif[0])
    dernier = None
    for nom, url, modele, forme in ordre:
        try:
            if forme == "lmstudio":
                # <think></think> pre-ferme : qwen3.5-9b part sinon en reasoning-runaway
                corps = {"model": modele,
                         "prompt": f"<|im_start|>user\n{prompt}<|im_end|>\n"
                                   f"<|im_start|>assistant\n<think></think>\n\n",
                         "temperature": temperature, "max_tokens": max_tokens,
                         "stop": ["<|im_end|>"]}
            else:
                corps = {"model": modele, "prompt": prompt, "stream": False,
                         "keep_alive": "5m",
                         "options": {"temperature": temperature, "num_predict": max_tokens}}
            req = _url.Request(url, data=json.dumps(corps).encode(),
                               headers={"Content-Type": "application/json"})
            with _url.urlopen(req, timeout=180) as r:
                d = json.load(r)
            txt = ((d.get("choices") or [{}])[0].get("text", "") if forme == "lmstudio"
                   else d.get("response", "")).strip()
            # qwen3-4b reemet parfois la balise fermante en tete malgre le
            # <think></think> pre-ferme : on la retire plutot que de la laisser
            # polluer le label d un pattern.
            for marq in ("</think>", "<think></think>", "<think>"):
                if txt.startswith(marq):
                    txt = txt[len(marq):].strip()
            if not txt:
                raise D.Indispo("reponse vide")
            if _gen_actif[0] != nom:
                _gen_actif[0] = nom
                log(f"  generation via {nom} ({modele})")
            return txt
        except Exception as e:
            dernier = f"{nom}: {type(e).__name__}"
    raise D.Indispo(f"aucun backend de generation ({dernier})")

def lire_pattern(membres, angle, consigne):
    extraits = "\n".join(f"- {m['titre'][:130]}" for m in membres[:12])
    p = (f"Voici {len(membres)} messages publics collectes sur des forums techniques "
         f"et des sites d offres :\n\n{extraits}\n\n"
         f"{consigne}\n\n"
         f"CONTRAINTES : appuie-toi UNIQUEMENT sur les messages ci-dessus. "
         f"N invente aucun chiffre, aucun nom d entreprise, aucun detail absent. "
         f"Si les messages ne permettent pas de repondre, ecris exactement : "
         f"INSUFFISANT. Reponds en francais, une seule phrase, 30 mots maximum.")
    return generer_cascade(p, max_tokens=110, temperature=0.5)

def _une_lecture(membres, angle, consigne):
    """Une lecture + son vecteur. Isolee pour etre parallelisable."""
    for _ in range(3):
        try:
            t = lire_pattern(membres, angle, consigne).strip()
            if not t:
                raise D.Indispo("vide")
            return angle, t, vectoriser_cascade(t)[0]
        except D.Indispo:
            time.sleep(8)
        except Exception as e:
            log(f"    lecture {angle} : {type(e).__name__}")
            return angle, None, None
    return angle, None, None

def qualifier(items, idx, tour):
    """Les 4 angles sont demandes EN PARALLELE.

    Mesure du 19/08 : en sequentiel, les 4 GPU de M6 restaient a 0-1 %
    d utilisation pendant toute la qualification — une requete a la fois sur un
    parc qui encaisse 34 requetes/s a 24 workers. Le goulot n etait pas M6,
    c etait la boucle."""
    membres = [items[i] for i in idx]
    lectures, vecs = {}, []
    with ThreadPoolExecutor(max_workers=4) as ex:
        for f in as_completed([ex.submit(_une_lecture, membres, a, c)
                               for a, c in ANGLES_PATTERN.items()]):
            angle, t, v = f.result()
            if t:
                lectures[angle] = t
                vecs.append(v)
    # cos intra des lectures : si les angles disent la meme chose, le pattern est net ;
    # au-dela de 0,93 ils ont COLLAPSE et ne valent qu une seule lecture (garde-fou 19/08)
    ci = 0.0
    if len(vecs) > 1:
        s = [cos(vecs[a], vecs[b]) for a in range(len(vecs)) for b in range(a+1, len(vecs))]
        ci = sum(s)/len(s)
    # Le label prend la premiere lecture QUI DIT QUELQUE CHOSE. Un "INSUFFISANT."
    # en tete masquerait des angles informatifs derriere lui. Si les 4 angles disent
    # INSUFFISANT, le label le dit aussi — c est un resultat, pas un echec : cela
    # signifie que le cluster ne porte pas de besoin identifiable.
    def _informative(t):
        return t and not t.strip().upper().startswith("INSUFFISANT")
    label = next((lectures[a] for a in ("BESOIN", "STACK", "URGENCE", "FAUX")
                  if _informative(lectures.get(a))), None)
    if label is None:
        label = "INSUFFISANT — les 4 angles refusent de conclure sur ce groupe"
    n_insuf = sum(1 for v in lectures.values() if not _informative(v))
    dim = len(membres[0]["vec"])
    cent = array("f", [sum(m["vec"][k] for m in membres)/len(membres) for k in range(dim)]).tobytes()
    from collections import Counter
    return dict(label=label[:400], taille=len(membres), n_insuffisant=n_insuf,
                sources=json.dumps(dict(Counter(m["source"] for m in membres))),
                membres=json.dumps([m["id"] for m in membres]),
                cohesion=round(cohesion(items, idx), 4), centroide=cent,
                lectures=json.dumps(lectures, ensure_ascii=False),
                cos_intra=round(ci, 4), collapse=1 if ci > 0.93 else 0, tour=tour)

def main():
    # Sonde d entree : M6 doit repondre AVANT de lancer quoi que ce soit.
    if not AUTORISER_LOCAL:
        try:
            import urllib.request as _u
            _u.urlopen("http://10.42.0.230:1234/v1/models", timeout=6).read()
            log("M6 joignable — la generation et les embeddings partent sur GPU distant")
        except Exception as e:
            log(f"ARRET : M6 injoignable ({type(e).__name__}). Le repli CPU local est "
                f"desactive (incident thermique du 19/08 : 94 C). Repare M6, ou relance "
                f"avec PATTERNS_AUTORISER_LOCAL=1 en sachant que le M4 va chauffer.")
            return 2
    t0 = temperature_max()
    if t0 >= 85:
        log(f"ARRET : le M4 est deja a {t0} C avant de commencer. Laisse-le refroidir.")
        return 3
    log(f"temperature M4 au demarrage : {t0} C")
    tour = 1
    for a in sys.argv:
        if a.startswith("--tour="): tour = int(a.split("=")[1])
    calibrer_seul = "--calibrer" in sys.argv
    seuil = None
    for a in sys.argv:
        if a.startswith("--seuil="): seuil = float(a.split("=")[1])

    vectoriser_signaux()
    items = charger()
    log(f"C2 — {len(items)} signaux vectorises charges")
    if len(items) < 4:
        log("trop peu de signaux pour clusteriser."); return

    if "--centrer" in sys.argv:
        items = centrer_par_source(items)
        log("C2 — vecteurs CENTRES par source (l effet de plateforme est retire)")
    d = distribution(items)
    log(f"C2 — distribution des similarites ({d['n']} paires) :")
    for k in ("p50", "p90", "p95", "p99", "p995", "maxi"):
        log(f"       {k:<5} = {d[k]:.4f}")
    if calibrer_seul:
        log("(--calibrer : on s arrete la, aucun cluster ecrit)")
        for s in (d["p90"], d["p95"], d["p99"], d["p995"]):
            g = clusterer(items, s)
            log(f"       seuil {s:.3f} -> {len(g)} cluster(s), "
                f"{sum(len(x) for x in g)} signaux groupes, plus gros = {max((len(x) for x in g), default=0)}")
        return

    if seuil is None:
        seuil = d["p99"]      # calibre sur la distribution reelle, pas devine
        log(f"C2 — seuil retenu : p99 = {seuil:.4f}")
    groupes = clusterer(items, seuil, methode="average")
    log(f"C2 — methode : average-link (single-link chaine : a 0,60 il absorbait "
        f"395 des 428 signaux dans un seul groupe)")
    groupes.sort(key=len, reverse=True)
    log(f"C2 — {len(groupes)} cluster(s) de 2+ membres, "
        f"{sum(len(g) for g in groupes)} signaux groupes sur {len(items)}")

    denses = [g for g in groupes if len(g) >= 3]
    # --multi : ne qualifier que les clusters MULTI-SOURCES.
    # Mesure du 19/08 : un cluster mono-source refletent la facon d ecrire du site,
    # pas un besoin du marche (a 428 signaux, 16/16 clusters etaient mono-source et
    # aucun ne portait de signal). A 1855 signaux les multi-sources apparaissent et
    # ce sont les seuls interessants : le cluster RAG melange 5 offres d emploi et
    # 5 issues techniques — la demande solvable rejoint le probleme reel.
    # --croise : ne garder que les clusters qui melangent une source d OFFRES et une
    # source de PROBLEMES. C est le seul croisement qui porte un signal COMMERCIAL —
    # une demande solvable adossee a une difficulte technique reelle. Mesure du 19/08 :
    # avec 91 offres dans le corpus, 3 clusters sur 33 croisaient ; avec 2241 offres,
    # 80 sur 621. Le rendement vient du corpus, pas de l algorithme.
    OFFRES = {"remoteok", "arbeitnow", "remotive", "jobicy", "hn-hiring", "freework"}
    if "--croise" in sys.argv:
        tmax = 40
        for a in sys.argv:
            if a.startswith("--taille-max="):
                tmax = int(a.split("=")[1])
        avant = len(denses)
        gardes = []
        trop_gros = 0
        for g in denses:
            srcs = {items[i]["source"] for i in g}
            if not (srcs & OFFRES and srcs - OFFRES):
                continue
            if len(g) > tmax:
                trop_gros += 1        # un groupe trop large ne produit pas une lecture nette
                continue
            gardes.append(g)
        denses = gardes
        log(f"C3 — filtre --croise : {len(denses)} clusters OFFRE<->PROBLEME retenus "
            f"sur {avant} denses ({trop_gros} ecartes car > {tmax} signaux)")
    if "--multi" in sys.argv:
        avant = len(denses)
        denses = [g for g in denses
                  if len({items[i]["source"] for i in g}) > 1]
        log(f"C3 — filtre --multi : {len(denses)} clusters multi-sources retenus "
            f"sur {avant} denses ({avant-len(denses)} mono-source ecartes)")
    denses.sort(key=len, reverse=True)
    log(f"C3 — qualification par superposition de {len(denses)} cluster(s) dense(s) (>=3)...")
    c = sqlite3.connect(DB, timeout=60); schema(c)
    # REPRENABLE (19/08) : on n efface plus le tour. Un DELETE en tete rendait tout
    # arret coûteux — la generation CPU locale a fait monter le M4 a 94 C et il a
    # fallu couper a 11/33 ; relancer aurait tout refait. On saute desormais les
    # clusters deja qualifies, identifies par leur liste de membres exacte.
    deja = {r[0] for r in c.execute(
        "SELECT membres FROM patterns_marche WHERE tour=?", (tour,))}
    a_faire, saute = [], 0
    for g in denses:
        if json.dumps([items[i]["id"] for i in g]) in deja:
            saute += 1
        else:
            a_faire.append(g)
    log(f"C3 — {len(a_faire)} cluster(s) a qualifier, {saute} deja fait(s)")

    # 6 clusters x 4 angles = 24 requetes simultanees sur M6 : exactement le regime
    # ou le debit a ete mesure au maximum (34/s). Le M4 n emet que du HTTP.
    n_par = int(os.environ.get("PATTERNS_CLUSTERS_PAR", "6"))
    log(f"C3 — {n_par} clusters en parallele x 4 angles = {n_par*4} requetes simultanees")
    n = 0
    _wl = _th.Lock()
    with ThreadPoolExecutor(max_workers=n_par) as ex:
        for f in as_completed([ex.submit(qualifier, items, g, tour) for g in a_faire]):
            tc = temperature_max()
            if tc >= 85:
                log(f"ARRET THERMIQUE : M4 a {tc} C, {n} pattern(s) conserves."); break
            try:
                r = f.result()
            except Exception as e:
                log(f"  cluster en echec : {type(e).__name__} {e}"); continue
            with _wl:
                cc = sqlite3.connect(DB, timeout=60)
                cc.execute("""INSERT INTO patterns_marche
                    (label,taille,sources,membres,cohesion,centroide,lectures,
                     cos_intra_lectures,collapse,tour,cree_le)
                    VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'))""",
                    (r["label"], r["taille"], r["sources"], r["membres"], r["cohesion"],
                     r["centroide"], r["lectures"], r["cos_intra"], r["collapse"], r["tour"]))
                cc.commit(); cc.close(); n += 1
                log(f"  [{n}/{len(a_faire)}] {r['taille']} sig  coh={r['cohesion']:.3f}  "
                    f"insuf={r['n_insuffisant']}/4  {r['label'][:70]}")
    c.close()
    log(f"C3 — {n} pattern(s) ecrits, {saute} deja qualifie(s) et sautes (tour {tour})")

if __name__ == "__main__":
    main()
