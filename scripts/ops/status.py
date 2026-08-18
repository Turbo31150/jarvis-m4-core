#!/usr/bin/env python3
"""
jarvis status — inspection PASSIVE de l'écosystème.

Contrat strict : zéro réseau, zéro docker, zéro appel LLM, aucun effet de bord.
On lit des fichiers et de la config, rien d'autre. C'est ce qui rend `status`
utilisable quand tout est cassé — y compris sans réseau.

Les clés de configuration sont rapportées PAR LEUR NOM, jamais par leur valeur.
Et le rapport distingue explicitement « configuré » de « disponible » : savoir
qu'une clé existe ne dit pas que le service répond. Pour ça, c'est `doctor`.
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import env as envmod  # noqa: E402

ROOT = Path(os.environ.get("JARVIS_ROOT", Path(__file__).resolve().parents[2]))
BRIQUES = ["mail", "media", "board", "web", "publish", "agent", "mem"]
NOYAU = ["env.py", "events.py", "trust.py", "envelope.py", "webguard.py"]


def main():
    json_out = "--json" in sys.argv
    rapport = {
        "root": str(ROOT),
        "briques": {},
        "noyau": {},
        "config": {},
        "journal": {},
    }

    for b in BRIQUES:
        p = ROOT / "bin" / f"jarvis-{b}"
        rapport["briques"][b] = {
            "present": p.exists(),
            "executable": os.access(p, os.X_OK) if p.exists() else False,
        }

    for m in NOYAU:
        p = ROOT / "scripts" / "lib" / m
        rapport["noyau"][m] = p.exists()

    # NOMS de clés uniquement — jamais les valeurs.
    fichiers_env = []
    for cand in (ROOT / ".env", ROOT / "config" / ".env", Path.home() / ".jarvis.env"):
        if cand.is_file():
            mode = oct(cand.stat().st_mode & 0o777)
            fichiers_env.append(
                {"chemin": str(cand), "mode": mode, "sur": mode == "0o600"}
            )
    cles = sorted(envmod.load_env().keys())
    rapport["config"] = {
        "fichiers_env": fichiers_env,
        "cles_declarees": cles,
        "nb_cles": len(cles),
        "policy_publish": (ROOT / "config" / "publish-policy.json").exists(),
    }

    journal = ROOT / "ops" / "events.jsonl"
    rapport["journal"] = {
        "present": journal.exists(),
        "mode": oct(journal.stat().st_mode & 0o777) if journal.exists() else None,
        "lignes": sum(1 for _ in open(journal, encoding="utf-8", errors="replace"))
        if journal.exists()
        else 0,
    }

    rapport["avertissement"] = (
        "configuré ≠ disponible — status ne teste AUCUN service. Utiliser `jarvis doctor`."
    )

    if json_out:
        print(json.dumps(rapport, indent=2, ensure_ascii=False))
        return 0

    print(f"JARVIS status (passif) — racine {ROOT}")
    print("\n  briques :")
    for b, st in rapport["briques"].items():
        etat = (
            "ok"
            if st["executable"]
            else ("non exécutable" if st["present"] else "ABSENTE")
        )
        print(f"    {b:9} {etat}")
    print("\n  noyau lib/ :")
    for m, present in rapport["noyau"].items():
        print(f"    {m:14} {'ok' if present else 'ABSENT'}")
    print("\n  configuration :")
    for f in fichiers_env:
        flag = "0600 ok" if f["sur"] else f"PERMISSIONS {f['mode']} — attendu 0600"
        print(f"    {f['chemin']}  {flag}")
    print(
        f"    {len(cles)} clés déclarées : {', '.join(cles[:8])}{' …' if len(cles) > 8 else ''}"
    )
    print(
        f"    policy publish : {'présente' if rapport['config']['policy_publish'] else 'ABSENTE'}"
    )
    print("\n  journal d'événements :")
    j = rapport["journal"]
    if j["present"]:
        print(f"    présent — {j['lignes']} événements, mode {j['mode']}")
    else:
        print("    absent (aucune brique n'a encore émis d'événement)")
    print(f"\n  ⚠ {rapport['avertissement']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
