#!/usr/bin/env python3
# dispatch_superposition.py — simulation massive par superposition + vectorisation
#
# Principe (skill dispatch-generation-masse) : N workers ThreadPool vers un backend
# DEPORTE (M6, cable direct 10.42.0.230). Le compute part sur M6 -> 0 token facture
# et 0 chaleur sur le M4. Plafond reel = M6, pas cette machine.
#
# "Superposition" : pour chaque cible on genere PLUSIEURS etats (angles) en parallele,
# on les vectorise (768d nomic-embed sur M6), puis on mesure leur divergence cosinus.
# Un jeu de variantes trop proches = le modele n'a produit qu'un seul message deguise.
#
# CE SCRIPT N'ENVOIE RIEN. Il ecrit dans SQLite. L'envoi reste une decision humaine.

import json, sqlite3, sys, time, urllib.request, urllib.error
from array import array
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

DB   = "/home/pamerys/jarvis/jarvis_master.db"
LOG  = "/home/pamerys/jarvis/logs/superposition.log"
M6   = "http://10.42.0.230:1234"
GEN  = "qwen/qwen3.5-9b"
EMB  = "text-embedding-nomic-embed-text-v1.5"
def _workers():
    """Lu au niveau module, donc doit tolerer les argv d un IMPORTATEUR.

    Corrige le 19/08 : patterns_marche.py importe ce module et passe --calibrer ;
    un int(sys.argv[1]) nu levait ValueError a l import, cassant un script tiers
    pour une option qui ne le concernait pas."""
    for a in sys.argv[1:]:
        if a.isdigit():
            return max(1, min(16, int(a)))
    return 6

WORKERS = _workers()

_th = __import__("threading")
_lock_msg = _th.Lock()
_lock_cnt = _th.Lock()
def log(m):
    line = f"[{datetime.now():%H:%M:%S}] {m}"
    with _lock_msg:
        print(line, flush=True)
        with open(LOG, "a") as f: f.write(line + "\n")

class Indispo(Exception): pass

def _post(path, payload, timeout=240):
    req = urllib.request.Request(M6 + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise Indispo(str(e))

def generer(prompt, max_tokens=420, temperature=0.75):
    # /v1/completions avec <think></think> pre-ferme : qwen3.5-9b part en
    # reasoning-runaway sur /v1/chat/completions (content vide, tout le budget
    # passe dans reasoning_content). Parade deja validee dans lm-ask.sh.
    d = _post("/v1/completions", {
        "model": GEN,
        "prompt": f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n<think></think>\n\n",
        "temperature": temperature, "max_tokens": max_tokens,
        "stop": ["<|im_end|>"],
    })
    return (d.get("choices") or [{}])[0].get("text", "").strip()

def vectoriser(texte):
    d = _post("/v1/embeddings", {"model": EMB, "input": texte[:6000]}, timeout=120)
    return d["data"][0]["embedding"]

# --- FAITS AUTORISES -------------------------------------------------------
# Rien hors de cette liste ne peut apparaitre dans un message genere.
# Chaque ligne est verifiee. Pas de client, pas de reference, pas de chiffre marketing.
FAITS = """- je suis architecte IA independant, base a Toulouse
- je fais tourner les modeles en local (GPU perso, LM Studio et Ollama), pas dans le cloud
- j exploite n8n auto-heberge, avec des workflows en production chez moi
- je construis des bases documentaires interrogeables en local (recherche plein texte)
- l EU AI Act est en phase d application stricte depuis le 1er aout 2026"""

INTERDITS = """INTERDITS ABSOLUS (le message est rejete sinon) :
- ne cite AUCUN client, AUCUNE reference, AUCUN projet passe : je n en fournis pas
- n invente AUCUN chiffre (ni %, ni euros, ni nombre de machines, ni delai chiffre non fourni)
- ne parle PAS de moi a la troisieme personne : ecris a la PREMIERE personne
- pas de formule creuse ("je me permets de vous contacter", "n hesitez pas")
- pas d emoji, pas de hashtag"""

ANGLES_STARTUP = {
 "SIGNAL":      "Ouvre en citant le fait observe ci-dessus, textuellement et sans l embellir. Une seule phrase sur ce que je fais. Termine par une proposition concrete et modeste.",
 "SOUVERAINETE":"Angle donnees : ce que change le fait de garder les modeles et les donnees sur leur propre infrastructure. Relie au fait observe. Reste factuel, aucune peur vendue.",
 "ECHEANCE":    "Angle temps : propose un livrable borne dans le temps, court. Ne chiffre AUCUN prix. Relie au fait observe.",
 "PAIR":        "Ecris d ingenieur a ingenieur. Technique, sobre, zero posture commerciale. Relie au fait observe.",
 "QUESTION":    "Ouvre par UNE question precise sur leur situation, deduite du fait observe. Ne pitche pas. Deux phrases maximum sur moi.",
}
ANGLES_MISSION = {
 "SIGNAL":      "Candidature. Reprends l intitule de la mission tel quel. Dis en quoi ce que je fais recoupe le besoin, et dis aussi honnetement ce qui ne recoupe pas.",
 "SOUVERAINETE":"Candidature sous l angle de l execution locale des modeles. Sois honnete si la mission est orientee cloud : ne pretends pas le contraire.",
 "ECHEANCE":    "Candidature sous l angle de la disponibilite immediate et d un premier livrable borne.",
 "PAIR":        "Candidature d ingenieur a ingenieur, sur le fond technique de la mission uniquement.",
 "QUESTION":    "Candidature qui ouvre par une question technique precise sur la mission, montrant que je l ai lue.",
}
ANGLES_RECRUTEUR = {
 "PAIR":     "Note d invitation LinkedIn. Je ne dispose d AUCUNE information sur cette personne : n en invente pas, reste general et honnete. Dis qui je suis en une ligne et pourquoi je me connecte.",
 "DISPO":    "Note d invitation LinkedIn axee disponibilite. Aucune information sur la personne : n en invente pas.",
 "QUESTION": "Note d invitation LinkedIn ouvrant sur une question generale au metier de recruteur tech. Aucune information sur la personne : n en invente pas.",
}

def prompt_startup(nom, entreprise, preuve, consigne):
    qui = nom if nom and "identifi" not in nom and "ecosyst" not in nom else "l equipe"
    return f"""Ecris un message LinkedIn en francais, adresse a {qui} chez {entreprise}.

FAIT OBSERVE SUR CETTE ENTREPRISE (seule source autorisee a son sujet) :
{preuve}

CE QUE JE PEUX DIRE DE MOI (seuls faits autorises) :
{FAITS}

CONSIGNE D ANGLE : {consigne}

{INTERDITS}

Longueur : 90 mots maximum. Reponds UNIQUEMENT par le message, sans preambule ni guillemets."""

def prompt_mission(auteur, intitule, extrait, fit, consigne):
    return f"""Ecris un message de candidature LinkedIn en francais, adresse a {auteur}.

LA MISSION (seule source autorisee) :
Intitule : {intitule}
Extrait  : {extrait or "(pas d extrait)"}
Mon evaluation honnete du fit : {fit}

CE QUE JE PEUX DIRE DE MOI (seuls faits autorises) :
{FAITS}

CONSIGNE D ANGLE : {consigne}

{INTERDITS}
- si mon evaluation du fit signale un ecart, DIS-LE dans le message : ne le masque pas

Longueur : 110 mots maximum. Reponds UNIQUEMENT par le message, sans preambule ni guillemets."""

def prompt_recruteur(nom, consigne):
    return f"""Ecris une note d invitation LinkedIn en francais, adressee a {nom}, recruteur tech.

CE QUE JE PEUX DIRE DE MOI (seuls faits autorises) :
{FAITS}

CONSIGNE D ANGLE : {consigne}

{INTERDITS}
- je ne sais RIEN de cette personne ni de son entreprise : ne fais AUCUNE supposition

Contrainte dure : 280 caracteres MAXIMUM (limite LinkedIn). Reponds UNIQUEMENT par la note."""

def schema():
    c = sqlite3.connect(DB, timeout=30); c.execute("PRAGMA journal_mode=WAL")
    c.execute("""CREATE TABLE IF NOT EXISTS simulation_superposition (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cible_ref TEXT NOT NULL, canal TEXT NOT NULL,
        cible_nom TEXT, cible_entreprise TEXT, angle TEXT NOT NULL,
        texte TEXT, n_car INTEGER, embedding BLOB, dim INTEGER,
        backend TEXT, latence_ms INTEGER, cree_le TEXT,
        UNIQUE(cible_ref, angle))""")
    c.commit(); c.close()

def cellules():
    """Les trous : (cible x angle) attendus MOINS ce qui est deja en base."""
    c = sqlite3.connect(DB, timeout=30); c.row_factory = sqlite3.Row
    faits = {r[0] for r in c.execute(
        "SELECT cible_ref||'|'||angle FROM simulation_superposition WHERE texte IS NOT NULL AND TRIM(texte)<>''")}
    out = []
    for r in c.execute("""SELECT id,nom,entreprise,preuve_besoin FROM campagne_linkedin_20260818
                          WHERE canal='STARTUP' AND TRIM(COALESCE(preuve_besoin,''))<>''"""):
        for a, cons in ANGLES_STARTUP.items():
            ref = f"campagne:{r['id']}"
            if f"{ref}|{a}" not in faits:
                out.append(dict(ref=ref, canal="STARTUP", nom=r["nom"], ent=r["entreprise"], angle=a,
                                prompt=prompt_startup(r["nom"], r["entreprise"], r["preuve_besoin"], cons)))
    for r in c.execute("SELECT id,auteur,intitule,extrait,fit FROM moisson_missions_linkedin"):
        for a, cons in ANGLES_MISSION.items():
            ref = f"mission:{r['id']}"
            if f"{ref}|{a}" not in faits:
                out.append(dict(ref=ref, canal="MISSION", nom=r["auteur"], ent=r["intitule"], angle=a,
                                prompt=prompt_mission(r["auteur"], r["intitule"], r["extrait"], r["fit"], cons)))
    for r in c.execute("""SELECT id,nom FROM campagne_linkedin_20260818
                          WHERE canal='RECRUTEUR' AND statut='A_INVITER'"""):
        for a, cons in ANGLES_RECRUTEUR.items():
            ref = f"campagne:{r['id']}"
            if f"{ref}|{a}" not in faits:
                out.append(dict(ref=ref, canal="RECRUTEUR", nom=r["nom"], ent="", angle=a,
                                prompt=prompt_recruteur(r["nom"], cons)))
    c.close(); return out

def ecrire(cel, texte, vec, ms):
    blob = array("f", vec).tobytes()
    for essai in range(6):
        try:
            c = sqlite3.connect(DB, timeout=30)
            c.execute("""INSERT INTO simulation_superposition
                (cible_ref,canal,cible_nom,cible_entreprise,angle,texte,n_car,embedding,dim,backend,latence_ms,cree_le)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(cible_ref,angle) DO UPDATE SET
                  texte=excluded.texte, n_car=excluded.n_car, embedding=excluded.embedding,
                  dim=excluded.dim, backend=excluded.backend, latence_ms=excluded.latence_ms,
                  cree_le=excluded.cree_le""",
                (cel["ref"], cel["canal"], cel["nom"], cel["ent"], cel["angle"], texte, len(texte),
                 blob, len(vec), "M6:qwen3.5-9b+nomic768", ms, datetime.now().isoformat(timespec="seconds")))
            c.commit(); c.close(); return
        except sqlite3.OperationalError:
            time.sleep(3)
    raise RuntimeError("SQLite verrouillee apres 6 essais")

def worker(cel, total, compteur):
    for essai in range(5):
        try:
            t0 = time.time()
            txt = generer(cel["prompt"])
            if not txt.strip():
                raise Indispo("generation vide")
            vec = vectoriser(txt)
            ms = int((time.time() - t0) * 1000)
            ecrire(cel, txt, vec, ms)
            n = compteur()
            log(f"[{n}/{total} {100*n//total}%] OK {cel['ref']:<14} {cel['angle']:<13} "
                f"{len(txt):>4}c {ms:>6}ms  {cel['ent'][:26]}")
            return True
        except Indispo as e:
            log(f"  M6 indispo ({e}) -> pause 25s, essai {essai+2}/5 sur {cel['ref']}|{cel['angle']}")
            time.sleep(25)
        except Exception as e:
            log(f"  ERREUR {cel['ref']}|{cel['angle']} : {type(e).__name__} {e}")
            time.sleep(3)
    log(f"  ABANDON apres 5 essais : {cel['ref']}|{cel['angle']}")   # jamais de troncature silencieuse
    return False

def main():
    schema()
    cels = cellules()
    if not cels:
        log("file vide — rien a generer, tout est deja en base."); return
    par_canal = {}
    for c in cels: par_canal[c["canal"]] = par_canal.get(c["canal"], 0) + 1
    log(f"=== SUPERPOSITION — {len(cels)} cellules a generer, {WORKERS} workers vers M6 ===")
    log(f"    repartition : {par_canal}")
    n = [0]
    def inc():
        with _lock_cnt:
            n[0] += 1
            return n[0]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(worker, c, len(cels), inc) for c in cels]
        ok = sum(1 for f in as_completed(futs) if f.result())
    log(f"=== FIN — {ok}/{len(cels)} reussies en {time.time()-t0:.0f}s ===")

if __name__ == "__main__":
    main()
