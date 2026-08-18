#!/usr/bin/env python3
"""
jarvis drill — l'exercice-incendie. Le test qui compte vraiment.

Simule la panne du LLM principal SANS toucher au service : on lance `agent` dans
un sous-process dont l'environnement pointe le hub sur un port mort
(http://127.0.0.1:1). Rien à rollback, aucun risque de laisser l'infra cassée.

Six assertions :
  1. le port est bien mort (la panne est réelle, pas simulée à moitié)
  2. le fallback local retourne une réponse NON VIDE
  3. l'événement agent.fallback_used est tracé au journal
  4. aucun appel cloud (le backend servi est bien local)
  5. la bascule tient dans une borne de temps (~90 s)
  6. retour à NORMAL une fois le hub rétabli

À faire tourner UNE FOIS PAR MOIS. Un chemin de secours jamais exercé est un
chemin de secours qui ne marche pas — autant découvrir la rouille avant le jour J.
"""

import os
import sys
import json
import time
import socket
import subprocess
from pathlib import Path

ROOT = Path(os.environ.get("JARVIS_ROOT", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
import events as journal  # noqa: E402

PORT_MORT = "http://127.0.0.1:1"
BORNE_SECONDES = 90
PROMPT = "Reponds exactement: PONG"

FAILS = []
PASSES = []


def check(label, condition, detail=""):
    (PASSES if condition else FAILS).append(label)
    print(
        f"  {'ok  ' if condition else 'ÉCHEC'} {label}"
        + (f" — {detail}" if detail else "")
    )


def lancer_agent(env_extra, timeout=BORNE_SECONDES + 30):
    env = os.environ.copy()
    env.update(env_extra)
    env["JARVIS_COMMAND_ID"] = f"drill-{int(time.time())}"
    proc = subprocess.run(
        [str(ROOT / "bin" / "jarvis"), "agent", "ask", PROMPT, "--max", "20"],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
    try:
        return json.loads(proc.stdout), env["JARVIS_COMMAND_ID"]
    except ValueError:
        return {"ok": False, "raw": proc.stdout + proc.stderr}, env["JARVIS_COMMAND_ID"]


def main():
    print("🔥 jarvis drill — coupure du LLM principal (aucun service n'est touché)\n")

    # 1. le port est-il réellement mort ?
    mort = False
    try:
        with socket.create_connection(("127.0.0.1", 1), timeout=2):
            mort = False
    except OSError:
        mort = True
    check(
        "1. le port de panne (127.0.0.1:1) est bien fermé",
        mort,
        "" if mort else "quelque chose écoute sur :1, la panne n'est pas réelle",
    )

    # 2 + 5. bascule dans la borne de temps, réponse non vide
    t0 = time.time()
    env, cid = lancer_agent({"JARVIS_HUB": PORT_MORT})
    elapsed = time.time() - t0

    reponse = (env.get("data") or {}).get("response", "") if env.get("ok") else ""
    check(
        "2. le fallback local retourne une réponse non vide",
        bool(reponse.strip()),
        repr(reponse)[:60],
    )
    check(
        f"5. la bascule tient sous {BORNE_SECONDES}s",
        elapsed < BORNE_SECONDES,
        f"{elapsed:.1f}s",
    )

    # 3. trace au journal, corrélée à CE drill
    time.sleep(0.3)
    traces = journal.query(event_type="agent.fallback_used", command_id=cid, limit=5)
    check(
        "3. l'événement agent.fallback_used est tracé",
        bool(traces),
        f"{len(traces)} trace(s) pour {cid[:16]}",
    )

    # 4. aucun appel cloud : le backend servi doit être local
    backend = (env.get("data") or {}).get("backend", "")
    local = any(m in backend for m in ("127.0.0.1", "localhost", "10.42.", "192.168."))
    check("4. aucun appel cloud — backend servi local", local, backend or "(inconnu)")

    degraded = (env.get("meta") or {}).get("degraded_mode")
    check(
        "4b. l'enveloppe signale DEGRADED_LOCAL",
        degraded == "DEGRADED_LOCAL",
        str(degraded),
    )

    # 6. retour à NORMAL une fois le hub rétabli.
    #
    # 3 essais avec backoff : sous forte charge GPU (le daemon de bibliothèque
    # occupe Ollama à ~97 %), le hub met parfois plus longtemps que le timeout
    # et l'agent bascule légitimement en DEGRADED_LOCAL. Un instantané unique
    # transformait cette contention passagère en échec de drill.
    #
    # Ce n'est PAS de la complaisance : après 3 essais espacés, un hub toujours
    # muet est un vrai défaut et l'assertion échoue. On distingue « lent sous
    # charge » de « mort », on ne masque pas le second.
    normal, mode, essais = False, "?", 0
    for essais in range(1, 4):
        env_ok, _ = lancer_agent({})
        mode = (env_ok.get("meta") or {}).get("degraded_mode")
        if env_ok.get("ok") and mode == "NORMAL":
            normal = True
            break
        if essais < 3:
            time.sleep(5 * essais)  # 5s puis 10s
    check(
        "6. retour à NORMAL une fois le hub rétabli",
        normal,
        f"{mode} après {essais} essai(s) — hub muet, pas seulement lent"
        if not normal
        else f"NORMAL (essai {essais})",
    )

    print(f"\n{'=' * 60}")
    print(f"PASS {len(PASSES)}  ·  FAIL {len(FAILS)}")
    if FAILS:
        for f in FAILS:
            print(f"  ✗ {f}")
        print("\n⛔ le chemin de secours souverain n'est PAS prouvé.")
        return 1
    print("✅ exercice-incendie réussi — souveraineté prouvée, pas supposée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
