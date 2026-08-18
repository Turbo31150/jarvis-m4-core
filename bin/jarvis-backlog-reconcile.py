#!/usr/bin/env python3
"""jarvis-backlog-reconcile.py — ferme la boucle overlay ↔ exécuteur, + prune honnête.

- mode défaut : pour chaque tâche `done` de jarvis_master portant un `uid=<overlay>`,
  marque l'overlay `done` (status_overlay + plan) → le compteur « à faire » BAISSE.
- mode --prune : annule dans l'overlay les report P2 SANS verbe d'action (= observations
  d'audit, pas des tâches) → nettoie le bruit SANS fabriquer de fiches creuses.

Écrit dans status_overlay (persistant, survit à --sync), même mécanisme que jarvis-plan --done.
Usage : jarvis-backlog-reconcile.py [--prune] [--dry|--go]
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
import time

OVERLAY = os.path.expanduser("~/jarvis/data/unified_plan.db")
MASTER = os.path.expanduser("~/jarvis/jarvis_master.db")
LOG = os.path.expanduser("~/jarvis/logs/backlog-drainer.log")

# CONSERVATEUR : ne prune QUE les vrais fragments d'observation (pas les livrables
# nommés type "Content:/domino:/serie:/Bibliothèque:"). Mieux vaut drainer que sur-annuler.
_PREFIX = re.compile(r"^\s*Report\s+\d{4}-\d{2}-\d{2}\s*:\s*", re.I)


def _is_fragment(titre: str) -> bool:
    t = _PREFIX.sub("", titre or "")
    t = re.sub(r"^[^\w]+", "", t).strip()  # retire emoji/puces de tête
    if not t:
        return True
    # livrable nommé → garder
    if re.match(
        r"(content|domino|serie|série|dev|cleanup|git|biblioth|jarvis|ollama)\b",
        t,
        re.I,
    ):
        return False
    if ":" in t[:20]:  # "X : ..." = catégorie nommée → garder
        return False
    # fragment = très court, OU commence en minuscule (mi-phrase), OU pure observation
    if len(t) < 15:
        return True
    if t[0].islower():
        return True
    if re.match(r"(cela|il |ils |elle|pas de|aucun|c'est|on |ce )", t, re.I):
        return True
    return False


def log(msg):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(
                f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}][RECON] {msg}\n"
            )
    except Exception:
        pass


def _set_overlay(con, uids, statut):
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    for uid in uids:
        con.execute(
            "INSERT OR REPLACE INTO status_overlay(uid,statut,updated_at) VALUES(?,?,?)",
            (uid, statut, now),
        )
        con.execute(
            "UPDATE plan SET statut=?, updated_at=? WHERE uid=?", (statut, now, uid)
        )


_MAP = os.path.expanduser("~/jarvis/data/.drained_map.tsv")


def reconcile(go):
    """Ferme la boucle via le mapping uid↔titre : si le titre drainé est done dans
    jarvis_master (quel que soit le consommateur), marque l'overlay uid done.
    Robuste à la concurrence (match par titre, pas par context.uid)."""
    # 1) charge le mapping uid↔titre
    pairs = []
    try:
        for ln in open(_MAP, encoding="utf-8"):
            if "\t" in ln:
                u, t = ln.rstrip("\n").split("\t", 1)
                pairs.append((u, t))
    except FileNotFoundError:
        pass
    if not pairs:
        print("[reconcile] mapping vide (rien de drainé)")
        return
    # 2) titres traités (done/analyzed) dans jarvis_master
    m = sqlite3.connect(f"file:{MASTER}?mode=ro", uri=True)
    done_titles = {
        r[0]
        for r in m.execute(
            "SELECT title FROM tasks WHERE status IN ('done','analyzed')"
        )
    }
    m.close()
    uids = list(dict.fromkeys(u for u, t in pairs if t in done_titles))
    remaining = [(u, t) for u, t in pairs if t not in done_titles]
    if not go:
        print(
            f"[reconcile] DRY : {len(uids)} uid overlay à clôturer (done) · "
            f"{len(remaining)} en cours"
        )
        return
    con = sqlite3.connect(OVERLAY, timeout=15)
    con.execute("PRAGMA busy_timeout=15000")
    already = {
        r[0] for r in con.execute("SELECT uid FROM status_overlay WHERE statut='done'")
    }
    todo = [u for u in uids if u not in already]
    _set_overlay(con, todo, "done")
    con.commit()
    con.close()
    # purge le mapping des traités (garde les en-cours → pas de re-check ni croissance)
    try:
        with open(_MAP, "w", encoding="utf-8") as mf:
            for u, t in remaining:
                mf.write(f"{u}\t{t}\n")
    except Exception:
        pass
    print(
        f"[reconcile] GO : {len(todo)} tâches overlay marquées done · "
        f"{len(remaining)} en cours"
    )
    log(f"reconcile +{len(todo)} done, {len(remaining)} en cours")


def prune(go):
    """annule les report P2 sans verbe d'action (observations, pas des tâches)."""
    con = (
        sqlite3.connect(OVERLAY, timeout=15)
        if go
        else sqlite3.connect(f"file:{OVERLAY}?mode=ro", uri=True)
    )
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT p.uid, p.titre FROM plan p WHERE p.source='report' AND p.priorite='P2' "
        "AND COALESCE((SELECT statut FROM status_overlay o WHERE o.uid=p.uid),p.statut)='todo'"
    ).fetchall()
    victims = [r["uid"] for r in rows if _is_fragment(r["titre"])]
    keep = len(rows) - len(victims)
    print(
        f"[prune] report P2 todo: {len(rows)} · à annuler (sans action): {len(victims)} · gardés (actionnables): {keep}"
    )
    if not go:
        print("[prune] DRY — --go pour annuler")
        con.close()
        return
    con.execute("PRAGMA busy_timeout=15000")
    _set_overlay(con, victims, "cancelled")
    con.commit()
    con.close()
    print(f"[prune] GO : {len(victims)} report P2 annulés (corpus historique)")
    log(f"prune +{len(victims)} cancelled")


def main() -> int:
    go = "--go" in sys.argv
    if "--prune" in sys.argv:
        prune(go)
    else:
        reconcile(go)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
