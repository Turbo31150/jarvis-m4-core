#!/usr/bin/env python3
"""Sorties de la brique box-docsis conformes aux frontières JARVIS.

Deux effets, chacun par son unique point de passage :

  A4 — alerte : `jarvis-publish stage` (draft-first). On s'arrête au brouillon.
       approve/commit restent humains : aucun composant ne s'auto-approuve (A5).
  A2 — mémoire : `jarvis-mem write`, marqué --untrusted --source parce que le
       journal DOCSIS vient de la box, donc entrée externe (A0) : c'est une
       donnée constatée, jamais une instruction.

  box_docsis_notify.py          → brouillon d'alerte (A4)
  box_docsis_notify.py --mem    → atome de mémoire durable (A2)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROBE = Path(__file__).with_name("box_docsis_probe.py")
BIN = Path.home() / "jarvis" / "bin"
SOURCE = "http://192.168.0.1/Numreseau_pa3_frequencecable.asp"


def probe() -> dict:
    p = subprocess.run(
        [sys.executable, str(PROBE)], capture_output=True, text=True, timeout=200
    )
    if not p.stdout.strip():
        raise SystemExit("sonde muette — rien à publier ni à mémoriser")
    return json.loads(p.stdout)


def resume(r: dict) -> str:
    if not r.get("ok"):
        return f"BOX sonde indisponible : {r.get('reason', '?')}"
    return (
        f"BOX {r.get('severity')} — émission {r.get('upstream_max_dbmv')} dBmV, "
        f"SNR {r.get('downstream_snr_min_db')} dB, "
        f"{r.get('log', {}).get('t3_timeout')} T3, uptime {r.get('uptime_min')} min. "
        + ("; ".join(r.get("reasons", [])) or "nominal")
        + f" → {r.get('verdict')}"
    )


# Fragments qui trahiraient du texte recopié depuis la box. Le résumé ne doit
# contenir que des nombres extraits et des libellés écrits ici — c'est ce qui
# permet de le publier sans le drapeau external_untrusted (A0/A4).
TRACES_EXTERNES = ("CM-MAC", "CMTS-MAC", "CM-QOS", "CM-VER", "Ranging", "DSID", "MDD")


def assert_derive(txt: str) -> None:
    """Garantit que rien de la box n'est recopié tel quel avant un publish."""
    fuites = [m for m in TRACES_EXTERNES if m.lower() in txt.lower()]
    if fuites:
        raise SystemExit(
            f"refus de publier : fragments externes détectés {fuites} — "
            "le résumé doit être dérivé, pas recopié (A0)"
        )


def run(cmd: list[str]) -> int:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    out = (p.stdout or p.stderr).strip()
    print(out[:600] if out else f"(rc={p.returncode})")
    return p.returncode


def main() -> int:
    r = probe()
    txt = resume(r)

    if "--mem" in sys.argv:
        return run(
            [
                str(BIN / "jarvis-mem"),
                "write",
                "--scope",
                "reseau-acces",
                "--content",
                txt,
                "--tags",
                "box",
                "docsis",
                "upstream",
                r.get("severity", "unknown"),
                "--untrusted",
                "--source",
                SOURCE,
                "--voie",
                "box-admin",
                "--json",
            ]
        )

    # Rien à annoncer quand tout est nominal : une alerte qui crie en permanence
    # n'est plus lue.
    if r.get("ok") and r.get("severity") == "ok":
        print("état nominal — aucun brouillon d'alerte créé")
        return 0

    # Pas de --untrusted ici, contrairement à mem : ce qui sort est un constat
    # DÉRIVÉ (nombres extraits + libellés écrits dans ce dépôt), aucun octet
    # recopié de la box. `assert_derive` le prouve avant chaque publication —
    # si un jour on y injecte du texte de journal, la publication s'arrête.
    assert_derive(txt)
    return run(
        [
            str(BIN / "jarvis-publish"),
            "stage",
            txt,
            "--channel",
            "telegram",
            # Cible imposée par l'allowlist de la policy A5. Ne jamais élargir
            # l'allowlist pour faire passer une cible : c'est le garde-fou, pas l'obstacle.
            "--target",
            "@JarvisTurbosseBot",
            "--source-ids",
            SOURCE,
            "--json",
        ]
    )


if __name__ == "__main__":
    sys.exit(main())
