#!/usr/bin/env python3
"""jv-net-wire — câblage réseau départemental (Phase C, additif/non destructif).

Lit orchestrator/jv_registry.json, crée les réseaux jvnet-<dept> (idempotent) et
connecte chaque container docker à son réseau départemental avec un alias DNS
égal à son nom cible jv-<dept>-<unite>. N'enlève AUCUN réseau existant.
Usage: jv-net-wire.py [--apply]   (sans --apply = dry-run)
"""

import json
import subprocess
import sys
from pathlib import Path

REG = Path.home() / "jarvis" / "orchestrator" / "jv_registry.json"
APPLY = "--apply" in sys.argv


def run(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=30)


def main():
    reg = json.loads(REG.read_text())
    docker_units = [u for u in reg["units"] if u["type"] == "docker"]
    depts = sorted({u["dept"] for u in docker_units})

    # containers réellement running
    running = set(run(["docker", "ps", "--format", "{{.Names}}"]).stdout.split())
    existing_nets = set(
        run(["docker", "network", "ls", "--format", "{{.Name}}"]).stdout.split()
    )

    print(
        f"[jv-net-wire] {'APPLY' if APPLY else 'DRY-RUN'} · {len(docker_units)} unités docker · départements: {depts}"
    )

    # 1. créer les réseaux
    for d in depts:
        net = f"jvnet-{d}"
        if net in existing_nets:
            print(f"  net {net:14} déjà présent")
            continue
        if APPLY:
            r = run(["docker", "network", "create", "--driver", "bridge", net])
            print(
                f"  net {net:14} {'créé' if r.returncode == 0 else 'ERREUR ' + r.stderr.strip()}"
            )
        else:
            print(f"  net {net:14} [à créer]")

    # 2. connecter chaque container running à son jvnet avec alias = nom cible
    print("  --- connexions ---")
    done = skipped = 0
    for u in docker_units:
        name, net, alias = u["nom_actuel"], f"jvnet-{u['dept']}", u["nom_cible"]
        if name not in running:
            skipped += 1
            continue
        if not APPLY:
            print(f"  connect {name} -> {net} (alias {alias}) [dry]")
            done += 1
            continue
        r = run(["docker", "network", "connect", "--alias", alias, net, name])
        ok = r.returncode == 0 or "already exists" in r.stderr
        print(
            f"  connect {name:42} -> {net:13} alias {alias:24} {'✓' if ok else '✗ ' + r.stderr.strip()[:60]}"
        )
        done += 1 if ok else 0
    print(f"[jv-net-wire] {done} connectés · {skipped} non-running ignorés")
    return 0


if __name__ == "__main__":
    sys.exit(main())
