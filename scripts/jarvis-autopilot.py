#!/usr/bin/env python3
"""jarvis-autopilot — agent planifié qui fait trancher le CLUSTER, pas un modèle seul.

    jarvis-autopilot.py --mission "<consigne>"        [--n 5] [--run]
    jarvis-autopilot.py --etat
    jarvis-autopilot.py --install-timer

Principe : chaque tâche est soumise aux backends du cluster via
multi-llm-orchestrate (fan-out parallèle + vote pondéré + quorum). L'autopilote
n'AGIT que si le cluster est réellement d'accord ; sinon il range en to_validate
et le dit. 0 token cloud.

Trois garde-fous, chacun né d'un défaut constaté au sol le 19/08/2026 :

  QUORUM   — M6 (poids 1.5 sur 4.1) rendait HTTP 400 et le vote sortait quand
             même « FORT 1.0 », parce que le score ne comptait que les
             répondants. Sous 2/3 du poids demandé, on refuse d'agir.

  FRAICHEUR— la file `tasks` contient 8,3 M de lignes dont 90 pending datées du
             06/08 visant la machine « M1 », qui n'est plus un nœud de calcul.
             On ignore par défaut ce qui est plus vieux que --max-age jours.

  DRY-RUN  — rien n'est écrit sans --run. Par défaut l'autopilote montre ce
             qu'il ferait.
"""
import argparse, importlib.util, json, os, sqlite3, subprocess, sys, time
from datetime import datetime, timedelta

MASTER = os.path.expanduser("~/jarvis/jarvis_master.db")
LOGDB = os.path.expanduser("~/jarvis/logs/jarvis_logs.db")
ORCH = os.path.expanduser("~/jarvis/scripts/multi-llm-orchestrate.py")
QUORUM_MIN = 0.67
# Concordance minimale entre les backends. Constaté le 19/08/2026 : avec un accord
# de 0.366 (les 3 modèles racontent 3 choses différentes) l'autopilote passait
# quand même en AGIR, et le texte retenu affirmait « le scan a été initié avec
# succès » alors qu'aucun scan n'avait tourné. Le quorum prouve la PRESENCE des
# backends ; seul l'accord prouve qu'ils disent la même chose.
ACCORD_MIN = 0.60


def charger_orchestrateur():
    spec = importlib.util.spec_from_file_location("orch", ORCH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def journal(phase, cible, verdict, detail=""):
    os.makedirs(os.path.dirname(LOGDB), exist_ok=True)
    c = sqlite3.connect(LOGDB)
    c.execute("""CREATE TABLE IF NOT EXISTS autopilot_journal(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, phase TEXT,
        cible TEXT, verdict TEXT, detail TEXT)""")
    c.execute("INSERT INTO autopilot_journal(ts,phase,cible,verdict,detail)"
              " VALUES(datetime('now'),?,?,?,?)", (phase, cible, verdict, detail[:2000]))
    c.commit(); c.close()


def taches(n, max_age):
    """File réelle : pending récents seulement. Le reste est du sédiment."""
    limite = (datetime.now() - timedelta(days=max_age)).strftime("%Y-%m-%d")
    c = sqlite3.connect(f"file:{MASTER}?mode=ro", uri=True)
    r = c.execute("""SELECT id, title, COALESCE(context,''), COALESCE(machine,'-'),
                            substr(COALESCE(created_at,''),1,10)
                     FROM tasks WHERE status='pending' AND substr(COALESCE(created_at,''),1,10) >= ?
                     ORDER BY id DESC LIMIT ?""", (limite, n)).fetchall()
    c.close()
    return r


def etat():
    c = sqlite3.connect(f"file:{MASTER}?mode=ro", uri=True)
    print("── File tasks ──")
    for s, k in c.execute("SELECT status,count(*) FROM tasks GROUP BY status ORDER BY 2 DESC LIMIT 6"):
        print(f"  {s:<12} {k}")
    c.close()
    print("\n── Cluster ──")
    m = charger_orchestrateur()
    for nom, url, modele, poids in m.BACKENDS:
        t0 = time.time()
        r = m._ask(nom, url, modele, "ping")
        etat_ = f"OK {len(r['text'])} car." if r["text"] else f"MUET ({r.get('error')})"
        print(f"  {nom:<4} poids {poids}  {int((time.time()-t0)*1000):>6} ms  {etat_}")


def cycle(mission, n, max_age, run):
    m = charger_orchestrateur()
    lot = taches(n, max_age)
    if not lot:
        print(f"Aucune tâche pending de moins de {max_age} jours. Rien à faire.")
        journal("cycle", "-", "VIDE", f"max_age={max_age}")
        return 0
    print(f"── {len(lot)} tâche(s) soumise(s) au cluster ──\n")
    agis = bloques = 0
    for tid, titre, ctx, machine, cree in lot:
        prompt = (f"{mission}\n\nTÂCHE #{tid} (créée le {cree}, cible {machine}) :\n{titre}\n"
                  f"{ctx[:600]}\n\nRéponds en 5 lignes maximum, en français.")
        out = m.orchestrate(prompt)
        v = out["verdict"]
        q = v.get("quorum", 0)
        ok = (v["winner"] and q >= QUORUM_MIN
              and v["agreement"] == "FORT" and v["score"] >= ACCORD_MIN)
        etiquette = "AGIR" if ok else "A VALIDER"
        muets = ",".join(v.get("muets") or []) or "aucun"
        cause = ""
        if not ok and v["winner"]:
            if q < QUORUM_MIN: cause = " ← quorum insuffisant"
            elif v["score"] < ACCORD_MIN: cause = " ← les backends divergent"
            else: cause = " ← accord non FORT"
        print(f"#{tid} [{etiquette}] accord={v['score']} quorum={q} muets={muets}{cause}")
        print(f"   {titre[:78]}")
        if v["winner"]:
            print(f"   → {v['winner']['text'][:220].replace(chr(10),' ')}\n")
        else:
            print("   → aucun backend n'a répondu\n")
        journal("tache", str(tid), etiquette,
                json.dumps({"accord": v["score"], "quorum": q, "muets": v.get("muets")}))
        if ok:
            agis += 1
            if run:
                c = sqlite3.connect(MASTER)
                c.execute("UPDATE tasks SET status='to_validate', agent='autopilot',"
                          " updated_at=datetime('now') WHERE id=?", (tid,))
                c.commit(); c.close()
        else:
            bloques += 1
    print(f"── {agis} retenue(s), {bloques} bloquée(s) (quorum ou divergence) ──")
    if not run:
        print("   DRY-RUN : aucune écriture. Ajoute --run pour appliquer.")
    journal("cycle", mission[:60], f"{agis}/{len(lot)}", f"bloques={bloques} run={run}")
    return 0


UNIT = """[Unit]
Description=JARVIS autopilot — cycle cluster planifie
After=network-online.target

[Service]
Type=oneshot
ExecStart=%s %s --mission "Analyse cette tache et dis en 5 lignes ce qu il faut faire concretement." --n 5 --run
""" % (sys.executable, os.path.abspath(__file__))

TIMER = """[Unit]
Description=JARVIS autopilot toutes les 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
Persistent=true

[Install]
WantedBy=timers.target
"""


def installer():
    d = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(d, exist_ok=True)
    open(f"{d}/jarvis-autopilot.service", "w").write(UNIT)
    open(f"{d}/jarvis-autopilot.timer", "w").write(TIMER)
    for cmd in (["systemctl", "--user", "daemon-reload"],
                ["systemctl", "--user", "enable", "--now", "jarvis-autopilot.timer"]):
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(f"  {' '.join(cmd)} → {r.returncode} {r.stderr.strip()[:80]}")
    print(f"\nUnités écrites dans {d}. Suivi : journalctl --user -u jarvis-autopilot -f")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mission", help="consigne envoyée au cluster pour chaque tâche")
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--max-age", type=int, default=7, help="ignore les tâches plus vieilles (jours)")
    p.add_argument("--run", action="store_true", help="écrit réellement en base")
    p.add_argument("--etat", action="store_true")
    p.add_argument("--install-timer", action="store_true")
    a = p.parse_args()
    if a.etat: return etat()
    if a.install_timer: return installer()
    if not a.mission:
        p.error("--mission requis (ou --etat / --install-timer)")
    return cycle(a.mission, a.n, a.max_age, a.run)


sys.exit(main() or 0)
