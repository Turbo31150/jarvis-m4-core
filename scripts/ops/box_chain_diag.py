#!/usr/bin/env python3
"""Diagnostic de la chaîne d'accès complète — remonte du poste jusqu'à l'opérateur.

La sonde DOCSIS ne regarde qu'un maillon. Ici on parcourt les quatre et on
DÉSIGNE celui qui casse, pour ne plus chercher au mauvais endroit :

  1. M1 ↔ box      lien Ethernet   (débit négocié, erreurs/CRC/drops, latence LAN)
  2. box           santé interne   (uptime = reboot, lignes téléphonie)
  3. box ↔ CMTS    voie de retour  (émission, SNR, T3) ← délégué à box_docsis_probe
  4. CMTS ↔ net    chemin          (perte et jitter par saut, via mtr)

Principe : un maillon sain doit être déclaré sain, pour que le maillon fautif
ressorte seul. Un maillon non mesurable est déclaré `unknown`, jamais `ok`.

  --json   sortie machine
Code retour = index du premier maillon fautif (0 = chaîne saine, 9 = indéterminé).
"""

from __future__ import annotations

import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

PROBE = Path(__file__).with_name("box_docsis_probe.py")
IFACE_FALLBACK = "enp42s0"
BOX = "192.168.0.1"

# Un lien Ethernet sain n'a aucune erreur : le moindre CRC est significatif.
JITTER_LAN_MAX_MS = 5.0
JITTER_PATH_SUSPECT_MS = 20.0


def sh(cmd: list[str], timeout: int = 30) -> str:
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def default_iface() -> str:
    m = re.search(r"default via \S+ dev (\S+)", sh(["ip", "route", "show", "default"]))
    return m.group(1) if m else IFACE_FALLBACK


def maillon_lan(iface: str) -> dict:
    """Lien physique poste ↔ box. Le plus souvent innocent, mais l'écarter
    explicitement évite de suspecter la box pour un câble en 100 Mb/s."""
    eth = sh(["ethtool", iface])
    speed = re.search(r"Speed:\s*(\S+)", eth)
    duplex = re.search(r"Duplex:\s*(\S+)", eth)
    link = (
        "yes"
        in (re.search(r"Link detected:\s*(\S+)", eth) or re.match("", "")).group(0)
        if re.search(r"Link detected:", eth)
        else None
    )

    stats = sh(["ip", "-s", "link", "show", iface])
    nums = re.findall(r"\n\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", stats)
    rx = (
        {
            k: int(v)
            for k, v in zip(
                ("bytes", "packets", "errors", "dropped", "missed", "mcast"), nums[0]
            )
        }
        if nums
        else {}
    )
    tx = (
        {
            k: int(v)
            for k, v in zip(
                ("bytes", "packets", "errors", "dropped", "carrier", "collsns"), nums[1]
            )
        }
        if len(nums) > 1
        else {}
    )

    ping = sh(["ping", "-c", "20", "-i", "0.2", "-W", "1", BOX], timeout=40)
    rtts = [float(x) for x in re.findall(r"time=([\d.]+)", ping)]
    loss = re.search(r"(\d+)% packet loss", ping)
    jitter = round(statistics.stdev(rtts), 2) if len(rtts) > 2 else None

    fautes = []
    if speed and speed.group(1) not in ("1000Mb/s", "2500Mb/s", "10000Mb/s"):
        fautes.append(f"lien négocié à {speed.group(1)} (câble ou port dégradé)")
    if duplex and duplex.group(1).lower() != "full":
        fautes.append(f"duplex {duplex.group(1)}")
    err = (
        rx.get("errors", 0)
        + tx.get("errors", 0)
        + rx.get("dropped", 0)
        + tx.get("dropped", 0)
        + tx.get("collsns", 0)
    )
    if err:
        fautes.append(f"{err} erreurs/drops sur l'interface")
    if loss and int(loss.group(1)) > 0:
        fautes.append(f"{loss.group(1)}% de perte vers la box")
    if jitter is not None and jitter > JITTER_LAN_MAX_MS:
        fautes.append(f"jitter LAN {jitter} ms (> {JITTER_LAN_MAX_MS})")

    mesurable = bool(speed or rx)
    return {
        "maillon": "1. M1 ↔ box (Ethernet)",
        "etat": "unknown" if not mesurable else ("fautif" if fautes else "ok"),
        "speed": speed.group(1) if speed else None,
        "duplex": duplex.group(1) if duplex else None,
        "link_detected": link,
        "rx": rx,
        "tx": tx,
        "lan_rtt_ms": round(statistics.mean(rtts), 2) if rtts else None,
        "lan_jitter_ms": jitter,
        "lan_loss_pct": int(loss.group(1)) if loss else None,
        "fautes": fautes,
    }


def maillon_box(r: dict) -> dict:
    if not r.get("ok"):
        return {
            "maillon": "2. box (santé interne)",
            "etat": "unknown",
            "fautes": [r.get("reason", "sonde indisponible")],
        }
    fautes = []
    if r.get("rebooted_recently"):
        fautes.append(f"redémarrage il y a {r.get('uptime_min')} min")
    if r.get("phone_lines_down"):
        fautes.append(f"{r['phone_lines_down']} ligne(s) téléphonie déconnectée(s)")
    return {
        "maillon": "2. box (santé interne)",
        "etat": "fautif" if fautes else "ok",
        "uptime_min": r.get("uptime_min"),
        "fautes": fautes,
    }


def maillon_retour(r: dict) -> dict:
    if not r.get("ok"):
        return {
            "maillon": "3. box ↔ CMTS (voie de retour)",
            "etat": "unknown",
            "fautes": [r.get("reason", "sonde indisponible")],
        }
    fautes = list(r.get("reasons", []))
    # Un reboot seul n'incrimine pas la voie de retour : il est déjà porté par le
    # maillon 2. Ici on ne retient que ce qui touche l'émission/réception.
    fautes = [f for f in fautes if "reboot" not in f]
    return {
        "maillon": "3. box ↔ CMTS (voie de retour)",
        "etat": "fautif" if fautes else "ok",
        "upstream_max_dbmv": r.get("upstream_max_dbmv"),
        "snr_min_db": r.get("downstream_snr_min_db"),
        "t3": r.get("log", {}).get("t3_timeout"),
        "fautes": fautes,
    }


def maillon_chemin() -> dict:
    out = sh(["mtr", "-r", "-c", "20", "-n", "--no-dns", "8.8.8.8"], timeout=120)
    if not out:
        return {
            "maillon": "4. CMTS ↔ Internet (chemin)",
            "etat": "unknown",
            "fautes": ["mtr indisponible"],
        }
    sauts = []
    for ln in out.splitlines():
        m = re.match(
            r"\s*(\d+)\.\|--\s+(\S+)\s+([\d.]+)%\s+\d+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+([\d.]+)",
            ln,
        )
        if m:
            sauts.append(
                {
                    "n": int(m.group(1)),
                    "host": m.group(2),
                    "loss_pct": float(m.group(3)),
                    "stdev_ms": float(m.group(4)),
                }
            )

    # Un saut final à 100% est souvent un routeur muet à l'ICMP, pas une panne :
    # ne l'incriminer que si la destination elle-même ne répond pas.
    dest_ok = (
        bool(sauts) and any(s["loss_pct"] < 100 for s in sauts[-1:]) or "???" not in out
    )
    fautes, premier = [], None
    for s in sauts:
        if s["stdev_ms"] > JITTER_PATH_SUSPECT_MS:
            premier = premier or s
    if premier:
        fautes.append(
            f"jitter {premier['stdev_ms']} ms dès le saut {premier['n']} ({premier['host']})"
            + (" — premier équipement opérateur" if premier["n"] == 2 else "")
        )
    return {
        "maillon": "4. CMTS ↔ Internet (chemin)",
        "etat": "fautif" if fautes else ("ok" if sauts else "unknown"),
        "sauts": sauts,
        "destination_joignable": dest_ok,
        "fautes": fautes,
    }


def main() -> int:
    iface = default_iface()
    p = subprocess.run(
        [sys.executable, str(PROBE)], capture_output=True, text=True, timeout=220
    )
    try:
        r = (
            json.loads(p.stdout)
            if p.stdout.strip()
            else {"ok": False, "reason": "sonde muette"}
        )
    except json.JSONDecodeError:
        r = {"ok": False, "reason": "sortie sonde illisible"}

    chaine = [maillon_lan(iface), maillon_box(r), maillon_retour(r), maillon_chemin()]
    fautifs = [i for i, m in enumerate(chaine, 1) if m["etat"] == "fautif"]
    inconnus = [i for i, m in enumerate(chaine, 1) if m["etat"] == "unknown"]

    # Le premier maillon fautif dans l'ordre physique n'est PAS la cause racine :
    # une voie de retour saturée fait tomber la téléphonie DOCSIS (maillon 2) et
    # jitter le chemin (maillon 4). Désigner le 2 enverrait chercher au mauvais
    # endroit — exactement ce que cet outil doit éviter.
    # Ordre de causalité : 3 (retour) > 1 (lien local) > 2 (box) > 4 (chemin).
    CAUSALITE = [3, 1, 2, 4]
    EXPLIQUE = {3: [2, 4]}  # une voie de retour saturée explique ces symptômes

    if fautifs:
        racine = next(i for i in CAUSALITE if i in fautifs)
        consequences = [i for i in fautifs if i in EXPLIQUE.get(racine, [])]
        autres = [i for i in fautifs if i != racine and i not in consequences]
        verdict = f"cause racine : maillon {racine} — {chaine[racine - 1]['maillon']}"
        if consequences:
            verdict += f" ; symptôme(s) induit(s) : maillon(s) {consequences}"
        if autres:
            verdict += f" ; à examiner séparément : maillon(s) {autres}"
        rc = racine
    elif inconnus:
        rc, verdict = 9, f"indéterminé — maillon(s) non mesurable(s) : {inconnus}"
    else:
        rc, verdict = 0, "chaîne saine de bout en bout"

    if "--json" in sys.argv:
        print(
            json.dumps(
                {
                    "iface": iface,
                    "chaine": chaine,
                    "verdict": verdict,
                    "maillons_fautifs": fautifs,
                    "rc": rc,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return rc

    icone = {"ok": "✅", "fautif": "⛔", "unknown": "❔"}
    print(f"CHAÎNE D'ACCÈS — interface {iface}\n")
    for m in chaine:
        print(f"{icone[m['etat']]} {m['maillon']}")
        for f in m["fautes"]:
            print(f"      · {f}")
        if m["maillon"].startswith("1.") and m["etat"] == "ok":
            print(
                f"      · {m['speed']} {m['duplex']}, 0 erreur, "
                f"RTT {m['lan_rtt_ms']} ms (jitter {m['lan_jitter_ms']} ms)"
            )
        if m["maillon"].startswith("3.") and m["etat"] == "ok":
            print(
                f"      · émission {m['upstream_max_dbmv']} dBmV, SNR {m['snr_min_db']} dB"
            )
    print(f"\n→ {verdict}")
    # Condition explicite plutôt qu'une liste de combinaisons : le foyer est
    # disculpé dès lors que son seul maillon (le lien local) est sain et que le
    # défaut siège au-delà de la box.
    if chaine[0]["etat"] == "ok" and 3 in fautifs:
        print(
            "  Le foyer est hors de cause : lien local sain, défaut en amont de la box."
        )
        print("  → action utile : dominos box-escalade-operateur --run")
    return rc


if __name__ == "__main__":
    sys.exit(main())
