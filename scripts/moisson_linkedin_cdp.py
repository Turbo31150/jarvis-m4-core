#!/usr/bin/env python3
# moisson_linkedin_cdp.py — passe LinkedIn SEPAREE et PLAFONNEE. Lecture seule.
#
# Voie distincte de moisson_multi_source.py, conformement au choix "les deux, separes" :
# le moissonneur public ne touche pas au compte, celui-ci l expose. Il est donc bride
# dans le CODE, pas dans une consigne.
#
# PLAFONDS DURS (non contournables par argument) :
#   - 40 pages par jour glissant, compteur persiste dans la base
#   - 20 s minimum entre deux navigations
#   - lecture seule : aucun clic, aucune saisie, aucune interaction emise
#
# ARRET NET SI NON AUTHENTIFIE. Jamais de repli silencieux sur les pages publiques en
# les faisant passer pour du fil connecte : ce sont deux natures de donnees differentes.
#
# Etat mesure le 19/08/2026 : AUCUN profil de cette machine ne porte de cookie LinkedIn
# (browser-os 181 cookies / 0 linkedin ; google-chrome 226 / 0 ; chromium sans fichier).
# Ce script s arrete donc a la verification d authentification, comme prevu.

import json, sqlite3, sys, time, urllib.request
from datetime import datetime, UTC

DB       = "/home/pamerys/jarvis/jarvis_master.db"
LOG      = "/home/pamerys/jarvis/logs/moisson_linkedin.log"
CDP      = "http://127.0.0.1:9100"
MAX_JOUR = 40        # plafond dur
DELAI    = 20        # secondes minimum entre navigations

def log(m):
    line = f"[{datetime.now():%H:%M:%S}] {m}"
    print(line, flush=True)
    try:
        with open(LOG, "a") as f: f.write(line + "\n")
    except OSError: pass

class Arret(Exception):
    """Condition d arret volontaire : on le dit, on ne contourne pas."""

# ── compteur journalier persiste ──────────────────────────────────────────────
def schema(c):
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""CREATE TABLE IF NOT EXISTS moisson_linkedin_quota (
        jour TEXT PRIMARY KEY, pages INTEGER DEFAULT 0, dernier_appel TEXT)""")

def quota_restant():
    c = sqlite3.connect(DB, timeout=30); schema(c)
    jour = datetime.now(UTC).strftime("%Y-%m-%d")
    r = c.execute("SELECT pages FROM moisson_linkedin_quota WHERE jour=?", (jour,)).fetchone()
    c.close()
    return MAX_JOUR - (r[0] if r else 0)

def consommer():
    c = sqlite3.connect(DB, timeout=30); schema(c)
    jour = datetime.now(UTC).strftime("%Y-%m-%d")
    c.execute("""INSERT INTO moisson_linkedin_quota (jour,pages,dernier_appel)
                 VALUES (?,1,datetime('now'))
                 ON CONFLICT(jour) DO UPDATE SET pages=pages+1, dernier_appel=datetime('now')""",
              (jour,))
    c.commit(); c.close()

# ── pilotage CDP, strictement en lecture ──────────────────────────────────────
def cdp_cibles():
    try:
        with urllib.request.urlopen(CDP + "/json/list", timeout=8) as r:
            return json.load(r)
    except Exception as e:
        raise Arret(f"CDP {CDP} injoignable : {e}")

def cdp_fermer(target_id):
    """Referme un onglet ouvert par ce script. Ne ferme JAMAIS un onglet preexistant."""
    try:
        with urllib.request.urlopen(CDP + "/json/close/" + target_id, timeout=8) as r:
            r.read()
        return True
    except Exception:
        return False

def cdp_nouvel_onglet(url):
    try:
        req = urllib.request.Request(CDP + "/json/new?url=" + urllib.parse.quote(url, safe=""),
                                     method="PUT")
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r)
    except Exception as e:
        raise Arret(f"ouverture d onglet refusee : {e}")

def cdp_naviguer(ws_url, url, timeout=30):
    """Navigation EXPLICITE via Page.navigate.

    Le parametre ?url= de PUT /json/new est ignore par ce build de BrowserOS
    (mesure le 19/08 : l onglet reste sur about:blank). On ne suppose donc rien
    de l URL demandee a la creation : on navigue explicitement et on attend
    Page.loadEventFired."""
    import websocket
    ws = websocket.create_connection(ws_url, timeout=timeout, suppress_origin=True)
    try:
        ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        ws.send(json.dumps({"id": 2, "method": "Page.navigate", "params": {"url": url}}))
        fin, charge = time.time() + timeout, False
        while time.time() < fin:
            try:
                msg = json.loads(ws.recv())
            except Exception:
                break
            if msg.get("method") == "Page.loadEventFired":
                charge = True
                break
            if msg.get("id") == 2 and (msg.get("result") or {}).get("errorText"):
                raise Arret(f"navigation refusee : {msg['result']['errorText']}")
        return charge
    finally:
        ws.close()

def cdp_evaluer(ws_url, expression, timeout=25):
    """Execute une expression JS en lecture. Aucun clic, aucune saisie."""
    import websocket
    # suppress_origin : depuis Chrome 111 le navigateur REJETTE tout handshake
    # WebSocket portant un header Origin (403 "Rejected an incoming WebSocket
    # connection ... use --remote-allow-origins"). websocket-client en envoie un
    # par defaut. On le supprime plutot que de relancer Chrome avec un drapeau
    # qui affaiblirait sa protection pour toutes les autres pages.
    ws = websocket.create_connection(ws_url, timeout=timeout, suppress_origin=True)
    try:
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                            "params": {"expression": expression, "returnByValue": True,
                                       "awaitPromise": True}}))
        fin = time.time() + timeout
        while time.time() < fin:
            msg = json.loads(ws.recv())
            if msg.get("id") == 1:
                res = (msg.get("result") or {}).get("result") or {}
                if "value" in res:
                    return res["value"]
                raise Arret(f"evaluation sans valeur : {msg.get('result')}")
        raise Arret("evaluation expiree")
    finally:
        ws.close()

def verifier_authentification():
    """Ouvre /feed et regarde OU on atterrit. Redirection vers /login = non connecte.

    L onglet ouvert ici est TOUJOURS referme, y compris en cas d erreur : ce script
    ne doit laisser aucune trace dans le navigateur de l utilisateur."""
    log("verification de l authentification LinkedIn...")
    onglet = cdp_nouvel_onglet("https://www.linkedin.com/feed/")
    tid = onglet.get("id")
    ws  = onglet.get("webSocketDebuggerUrl")
    consommer()
    try:
        if not ws:
            raise Arret("onglet sans webSocketDebuggerUrl")
        charge = cdp_naviguer(ws, "https://www.linkedin.com/feed/")
        log(f"  navigation explicite : {'chargee' if charge else 'pas de loadEvent (on lit quand meme)'}")
        time.sleep(4)   # laisse la redirection cote client s effectuer
        try:
            etat = cdp_evaluer(ws, "JSON.stringify({url: location.href, titre: document.title})")
        except Arret:
            raise
        except Exception as e:
            raise Arret(f"pilotage CDP impossible : {type(e).__name__} {e}")
        try:
            d = json.loads(etat)
        except Exception:
            raise Arret(f"reponse illisible : {etat!r}")
        url = d.get("url", "")
        log(f"  atterri sur : {url[:90]}")
        if any(m in url for m in ("/login", "/uas/login", "/checkpoint", "/authwall", "/signup")):
            raise Arret("profil NON authentifie sur LinkedIn (redirection vers la page de "
                        "connexion). Connecte-toi manuellement dans le navigateur, puis relance.")
        if "/feed" not in url:
            raise Arret(f"atterrissage inattendu ({url[:70]}) — on n interprete pas, on s arrete.")
        log("  authentifie.")
        return ws
    finally:
        if tid and cdp_fermer(tid):
            log("  onglet de verification referme.")

def main():
    log("=== MOISSON LINKEDIN (CDP, lecture seule, plafonnee) ===")
    reste = quota_restant()
    log(f"quota du jour : {reste}/{MAX_JOUR} pages restantes")
    if reste <= 0:
        log("PLAFOND ATTEINT — arret. Reprise demain."); return 1
    try:
        cibles = cdp_cibles()
        pages = [t for t in cibles if t.get("type") == "page"]
        log(f"CDP joignable : {len(cibles)} cible(s), {len(pages)} page(s)")
        verifier_authentification()
    except Arret as e:
        log(f"ARRET : {e}")
        log("Aucune donnee ecrite. Le moissonneur public (moisson_multi_source.py) reste "
            "disponible et ne depend pas d une session.")
        return 2
    log("authentifie — la moisson du fil pourrait demarrer ici (non atteint aujourd hui).")
    return 0

if __name__ == "__main__":
    import urllib.parse
    sys.exit(main())
