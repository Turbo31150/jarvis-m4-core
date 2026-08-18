#!/usr/bin/env python3
"""dispatch_skillsmp_fr — mots-cles FRANCAIS en masse pour le catalogue SkillsMP.

Applique le pattern `dispatch-generation-masse` : N workers ThreadPool vers un
backend DEPORTE (ollama-cloud via ai_local) => 0 token Anthropic, 0 chaleur M4.

Remplit skillsmp_skills.mots_cles_fr, que l'etage `fr` du pipeline SkillsMP
aurait du produire — sauf que skillmp-pipeline.py n'existe pas sur M4 (il est
reste sur le disque M1). D'ou 4,5 % de couverture seulement.

Idempotent : ne traite que les lignes vides, relançable sans doublon.
Usage : dispatch_skillsmp_fr.py [workers] [limite]
"""
import os, sys, time, sqlite3, threading, unicodedata
sys.path.insert(0, "/home/pamerys/jarvis/webapp")
import ai_local

DB      = os.path.expanduser("~/jarvis/jarvis_master.db")
LOG     = os.path.expanduser("~/jarvis/logs/dispatch_skillsmp_fr.log")
WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 6
LIMITE  = int(sys.argv[2]) if len(sys.argv) > 2 else 0   # 0 = tout

_lock  = threading.Lock()
_stats = {"ok": 0, "vide": 0, "abandon": 0}

def log(msg):
    ligne = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    with _lock:
        print(ligne, flush=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(ligne + "\n")

def manquants():
    """SQL d'abord (0 token) : cible - deja fait."""
    cx = sqlite3.connect(DB, timeout=60)
    q = ("SELECT url, COALESCE(nom,''), COALESCE(description,'') FROM skillsmp_skills "
         "WHERE (mots_cles_fr IS NULL OR mots_cles_fr='') "
         "AND description IS NOT NULL AND LENGTH(description)>30")
    if LIMITE:
        q += f" LIMIT {LIMITE}"
    rows = cx.execute(q).fetchall()
    cx.close()
    return rows

PROMPT = (
    "Voici la description d'un outil logiciel (« skill ») destine a un agent IA.\n"
    "Donne EXACTEMENT 6 mots-cles en FRANCAIS qui permettraient de le retrouver "
    "par recherche. Uniquement des noms communs ou expressions courtes, separes "
    "par des virgules. Aucune phrase, aucune explication, aucune numerotation.\n\n"
    "Nom : {nom}\nDescription : {desc}\n\nMots-cles francais :"
)

def nettoie(txt):
    """Le modele bavarde parfois : on ne garde que la liste."""
    if not txt:
        return ""
    t = str(txt).strip().splitlines()
    t = [l for l in t if l.strip()]
    if not t:
        return ""
    ligne = max(t, key=lambda l: l.count(","))          # la ligne la plus "liste"
    ligne = ligne.split(":")[-1]                        # coupe un eventuel prefixe
    mots = []
    for m in ligne.split(","):
        m = m.strip().strip("-•*0123456789.[]\"' ").lower()
        if 2 <= len(m) <= 40 and not m.startswith(("voici", "les mots", "bien sur")):
            mots.append(m)
    return ", ".join(list(dict.fromkeys(mots))[:6])   # dedoublonne en gardant l'ordre

def worker(row, total):
    url, nom, desc = row
    for essai in range(6):
        try:
            res = ai_local.generate(
                PROMPT.format(nom=nom[:120], desc=desc[:600]),
                cache=True,          # descriptions publiques : aucun PII
            )
            txt = res.get("text", "") if isinstance(res, dict) else str(res)
            mots = nettoie(txt)
            if not mots:
                with _lock: _stats["vide"] += 1
                return False
            cx = sqlite3.connect(DB, timeout=60)
            cx.execute("PRAGMA busy_timeout=60000")
            cx.execute("UPDATE skillsmp_skills SET mots_cles_fr=? WHERE url=?", (mots, url))
            cx.commit(); cx.close()
            with _lock:
                _stats["ok"] += 1
                n = _stats["ok"]
            if n % 25 == 0:
                fait = sum(_stats.values())
                log(f"[{fait}/{total} {100*fait/total:.1f}%] ok={_stats['ok']} "
                    f"vide={_stats['vide']} abandon={_stats['abandon']} "
                    f"| {nom[:40]} -> {mots[:60]}")
            return True
        except ai_local.AIUnavailable:
            time.sleep(25)                    # garde-fou thermique / backends KO
        except sqlite3.OperationalError:
            time.sleep(3)                     # verrou DB (dump en cours)
        except Exception as e:
            if essai >= 2:
                log(f"ABANDON {url} : {type(e).__name__}: {str(e)[:120]}")
                with _lock: _stats["abandon"] += 1
                return False
            time.sleep(2)
    log(f"ABANDON {url} : 6 essais epuises")   # jamais de troncature silencieuse
    with _lock: _stats["abandon"] += 1
    return False

def main():
    from concurrent.futures import ThreadPoolExecutor, as_completed
    # Ne jamais ecrire pendant un `.backup` : le dump repartirait en boucle.
    while any("driver.sh" in l for l in os.popen("pgrep -af 'driver.sh --dry-run' 2>/dev/null").read().splitlines()):
        log("dump SQL en cours — attente 60 s avant d'ecrire dans jarvis_master.db")
        time.sleep(60)
    cells = manquants()
    total = len(cells)
    log(f"=== DEPART — {total} skills sans mots-cles FR, {WORKERS} workers, backend deporte ===")
    if not total:
        log("rien a faire"); return
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(worker, c, total) for c in cells]
        for _ in as_completed(futs):
            pass
    d = time.time() - t0
    log(f"=== FIN — ok={_stats['ok']} vide={_stats['vide']} abandon={_stats['abandon']} "
        f"en {d/60:.1f} min ({total/max(d,1):.1f} items/s) ===")

if __name__ == "__main__":
    main()
