#!/usr/bin/env python3
"""dispatch_candidatures.py — generation de masse des candidatures. 0 token, 0 chaleur.

Pattern dispatch-generation-masse : N workers ThreadPool vers un backend DEPORTE.
Le compute part chez Ollama Cloud -> 0 token Anthropic ET 0 chaleur sur M4.
Le plafond reel est le rate-limit cloud, pas la machine.

- SQL d'abord : cible - deja_fait (table opportunites_lettres). Aucun appel inutile.
- Idempotent : INSERT OR REPLACE, relancable a l'infini sans doublon.
- Retry : backend muet -> sleep(25) ; base verrouillee -> sleep(3). 6 essais max.
- Jamais de troncature silencieuse : tout abandon est logue.

Usage : dispatch_candidatures.py [workers] [top_n]
"""
import json, sqlite3, sys, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, "/home/pamerys/jarvis/scripts")
from opportunites import score_sql, BACKENDS, SOCLE, DB   # une seule source de verite

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 6
TOP_N   = int(sys.argv[2]) if len(sys.argv) > 2 else 60
verrou  = threading.Lock()
etat    = {"n": 0}


def log(m):
    with verrou:
        print(m, flush=True)


def infere(prompt):
    dernier = None
    for nom, url, modele, _ in BACKENDS:
        corps = json.dumps({"model": modele,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 700, "temperature": 0.4}).encode()
        try:
            req = urllib.request.Request(url, data=corps,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            txt = (d["choices"][0]["message"].get("content") or "").strip()
            if "</think>" in txt:
                txt = txt.split("</think>")[-1].strip()
            if not txt:            # 200 + contenu vide n'est PAS un succes
                dernier = f"{nom}: contenu vide"
                continue
            return nom, txt
        except Exception as exc:
            dernier = f"{nom}: {str(exc)[:60]}"
            continue
    raise RuntimeError(dernier or "cascade muette")


def worker(item, total):
    s, rid, titre, url, pub, tmin, tmax, ville, client, why = item
    prompt = f"""{SOCLE}

MISSION : {titre}
Client : {client} · Lieu : {ville} · TJM affiche : {tmin or '?'}-{tmax or '?'} EUR/jour

Redige la candidature de Franck Delmas. Contraintes STRICTES :
- Francais, 120 a 160 mots, direct, aucune flatterie.
- Ouvre sur ce que la mission demande, pas sur lui.
- Cite 2 preuves chiffrees du socle, choisies pour CETTE mission.
- N'invente aucun chiffre, aucune reference client, aucune experience non listee.
- Termine par une disponibilite et une proposition d'echange court.
Rends UNIQUEMENT le texte de la candidature."""
    for essai in range(6):
        try:
            backend, txt = infere(prompt)
            c = sqlite3.connect(DB, timeout=60)
            c.execute("""insert or replace into opportunites_lettres
                         (rowid_mission, titre, lettre, backend) values (?,?,?,?)""",
                      (rid, titre, txt, backend))
            c.commit(); c.close()
            with verrou:
                etat["n"] += 1; n = etat["n"]
            log(f"  [{n}/{total} {100*n//total}%] ✅ #{rid} [{s}] {titre[:44]} <{backend}>")
            return True
        except sqlite3.OperationalError:
            time.sleep(3)                     # base verrouillee
        except RuntimeError:
            time.sleep(25)                    # tous les backends muets
        except Exception as exc:
            log(f"  #{rid} essai {essai+1} : {str(exc)[:70]}")
            time.sleep(5)
    log(f"  ⛔ ABANDON #{rid} apres 6 essais — {titre[:50]}")
    return False


def main():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    faites = {r[0] for r in c.execute("select rowid_mission from opportunites_lettres")}
    c.close()
    cibles = [x for x in score_sql()[:TOP_N] if x[1] not in faites]   # SQL d'abord
    if not cibles:
        log("Rien a faire : toutes les candidatures du top sont deja en cache."); return
    log(f"{len(cibles)} candidature(s) a generer · {WORKERS} workers · backend deporte")
    ok = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futurs = [ex.submit(worker, x, len(cibles)) for x in cibles]
        for f in as_completed(futurs):
            ok += bool(f.result())
    log(f"\nTermine : {ok}/{len(cibles)} generees, {len(cibles)-ok} abandonnees")


if __name__ == "__main__":
    main()
