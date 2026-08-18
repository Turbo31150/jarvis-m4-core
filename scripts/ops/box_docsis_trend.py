#!/usr/bin/env python3
"""Échantillonne la voie de retour DOCSIS dans le temps pour tester la dérive thermique.

Hypothèse à valider : « quand la box chauffe, elle coupe ». La box n'expose aucune
température, donc on ne la mesure pas — on mesure sa **conséquence** :

  la puissance d'émission d'un modem câble dérive vers le haut quand son étage
  d'amplification chauffe. À 48 dBmV il n'existe plus de marge : quelques dB de
  dérive suffisent à faire décrocher le ranging (T3) puis réinitialiser la MAC.

Deux signaux croisés :
  · intrinsèque — upstream vs uptime : si la puissance monte à mesure que le modem
    accumule des heures de fonctionnement, l'échauffement est en cause.
  · contextuel  — températures M1 (proxy d'ambiance de la pièce, imparfait et
    signalé comme tel : M1 chauffe la pièce, il n'est pas dans la box).

  --sample    un échantillon → data/box_trend.jsonl   (appelé par timer)
  --analyse   lit l'historique et conclut, ou dit franchement qu'il est trop court
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PROBE = Path(__file__).with_name("box_docsis_probe.py")
TREND = Path.home() / "jarvis" / "data" / "box_trend.jsonl"

# En dessous, toute "corrélation" serait du bruit : on refuse de conclure.
MIN_SAMPLES = 8
# Écart de puissance considéré comme une dérive réelle et non du pas de mesure
# (le firmware ne rapporte l'émission que par pas de 1 dB).
DRIFT_SIGNIFICANT = 1.5


def local_temps() -> dict:
    """Températures M1 — proxy d'ambiance uniquement, jamais la température box."""
    try:
        out = subprocess.run(
            ["sensors"], capture_output=True, text=True, timeout=10
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return {}
    # Ne garder que la LECTURE de chaque ligne (avant la parenthèse) : sinon on
    # capte les seuils `(crit = +90.8°C)` et les `low = +0.0°C`, ce qui écrasait
    # le max à 90 °C et tirait la moyenne à 18 °C — corrélation en pur bruit.
    # Les jc42 (barrettes DDR) sont passifs : ils suivent l'air du boîtier, donc
    # meilleur proxy d'ambiance que Tctl/GPU qui dépendent de la charge.
    ddr = [
        float(m.group(1))
        for ln in out.splitlines()
        if (m := re.match(r"\s*temp\d+:\s*\+(\d+\.\d)°C", ln))
    ]
    cpu = re.search(r"Tctl:\s*\+(\d+\.\d)°C", out)
    vals = ddr
    return {
        "ambient_proxy_max_c": max(vals) if vals else None,
        "ambient_proxy_mean_c": round(sum(vals) / len(vals), 1) if vals else None,
        "cpu_tctl_c": float(cpu.group(1)) if cpu else None,
    }


def sample() -> int:
    p = subprocess.run(
        [sys.executable, str(PROBE)], capture_output=True, text=True, timeout=200
    )
    if not p.stdout.strip():
        return 3
    try:
        r = json.loads(p.stdout)
    except json.JSONDecodeError:
        return 3
    if not r.get("ok"):
        return 3

    row = {
        "ts": r.get("ts"),
        "uptime_min": r.get("uptime_min"),
        "upstream_max_dbmv": r.get("upstream_max_dbmv"),
        "snr_min_db": r.get("downstream_snr_min_db"),
        "t3": r.get("log", {}).get("t3_timeout"),
        "mac_reinit": r.get("log", {}).get("mac_reinit"),
        "severity": r.get("severity"),
        **local_temps(),
    }
    TREND.parent.mkdir(parents=True, exist_ok=True)
    with TREND.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False))
    return 0


def load() -> list[dict]:
    if not TREND.exists():
        return []
    rows = []
    for ln in TREND.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            try:
                rows.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    return rows


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return round(num / (dx * dy), 3) if dx and dy else None


def analyse() -> int:
    rows = load()
    us = [r for r in rows if r.get("upstream_max_dbmv") is not None]
    print(f"échantillons : {len(rows)} (dont {len(us)} avec puissance d'émission)")

    if len(us) < MIN_SAMPLES:
        print(f"\n⚠ Série trop courte pour conclure (minimum {MIN_SAMPLES}).")
        print(
            "  Toute corrélation calculée ici serait du bruit — l'hypothèse thermique"
        )
        print("  reste NI confirmée NI écartée. Laisser le timer accumuler.")
        if us:
            lo = min(r["upstream_max_dbmv"] for r in us)
            hi = max(r["upstream_max_dbmv"] for r in us)
            print(f"  Amplitude observée pour l'instant : {lo} → {hi} dBmV")
        return 4

    pw = [r["upstream_max_dbmv"] for r in us]
    lo, hi, amp = min(pw), max(pw), max(pw) - min(pw)
    reboots = sum(1 for r in us if (r.get("uptime_min") or 999) < 30)

    print(f"\nPuissance d'émission : {lo} → {hi} dBmV (amplitude {amp:.1f} dB)")
    print(f"Reboots détectés dans la série : {reboots}")

    up = [r for r in us if r.get("uptime_min") is not None]
    r_uptime = pearson(
        [r["uptime_min"] for r in up], [r["upstream_max_dbmv"] for r in up]
    )
    amb = [r for r in us if r.get("ambient_proxy_max_c") is not None]
    r_amb = pearson(
        [r["ambient_proxy_max_c"] for r in amb], [r["upstream_max_dbmv"] for r in amb]
    )

    print(
        f"\nCorrélation puissance / uptime   : {r_uptime}  (échauffement propre du modem)"
    )
    print(
        f"Corrélation puissance / ambiance : {r_amb}  (proxy M1 — indicatif seulement)"
    )

    print("\nVerdict :")
    if amp < DRIFT_SIGNIFICANT:
        print(f"  Puissance quasi constante (< {DRIFT_SIGNIFICANT} dB d'amplitude).")
        print(
            "  → La thèse thermique n'est PAS soutenue par les mesures. La saturation"
        )
        print("    est structurelle (atténuation de la voie de retour), pas dérivante.")
        rc = 0
    elif r_uptime is not None and r_uptime > 0.6:
        print(f"  La puissance monte avec l'uptime (r={r_uptime}) sur {amp:.1f} dB.")
        print("  → Dérive thermique CONFIRMÉE : le modem s'échauffe et perd sa marge.")
        print(
            "    Améliorer sa ventilation (dégagement, surélévation, hors enceinte close)"
        )
        print("    ET traiter l'atténuation amont — la dérive ne fait décrocher que")
        print("    parce que la marge de départ est déjà nulle.")
        rc = 1
    else:
        print(
            f"  Puissance variable ({amp:.1f} dB) mais sans lien net à l'uptime"
            f" (r={r_uptime})."
        )
        print("  → Instabilité côté réseau plus probable qu'un échauffement propre.")
        rc = 2

    if reboots:
        print(f"\n  ⚠ {reboots} reboot(s) dans la série : la série est fragmentée,")
        print("    un uptime remis à zéro casse la mesure d'échauffement cumulé.")
    print("\nRappel : les températures relevées sont celles de M1, pas de la box —")
    print(
        "elles disent si la pièce chauffe, jamais ce que subit l'électronique du modem."
    )
    return rc


def stability(n: int = 3, gap_s: int = 240) -> int:
    """N relevés espacés : distingue un incident ponctuel d'un défaut permanent.

    Vit ici et non dans un step shell : la boucle avait besoin d'une variable,
    or les steps compilés sont expansés avant `eval` sous `set -u` — `$i` y
    devenait « variable sans liaison ».
    """
    import time

    worst = 0
    for k in range(n):
        rc = sample()
        worst = max(worst, rc)
        if k < n - 1:
            time.sleep(gap_s)
    print(f"\n{n} relevés effectués (pire code={worst})")
    return worst


if __name__ == "__main__":
    if "--stability" in sys.argv:
        i = sys.argv.index("--stability")
        n = int(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 3
        # gap réduit si demandé explicitement, pour les tests
        gap = int(sys.argv[i + 2]) if len(sys.argv) > i + 2 else 240
        sys.exit(stability(n, gap))
    if "--analyse" in sys.argv:
        sys.exit(analyse())
    sys.exit(sample())
