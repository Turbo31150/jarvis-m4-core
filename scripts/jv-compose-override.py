#!/usr/bin/env python3
"""jv-compose-override — génère l'override compose qui PÉRENNISE la restructuration.

Pour le projet compose 'docker' : produit docker-compose.jv-entreprise.yml avec,
par service, container_name=jv-<dept>-<unite> + rattachement networks jvnet-<dept>
(externes). NE l'applique PAS (compose up = downtime/recréation → décision humaine).
Sans cet override, un futur 'compose up' perd les connexions jvnet de la Phase C.
"""

import json
import subprocess
import sys
from pathlib import Path

REG = Path.home() / "jarvis" / "orchestrator" / "jv_registry.json"
OUT = Path("/home/pamerys/jarvis-linux/infra/docker/docker-compose.jv-entreprise.yml")
PROJECT = "docker"


def inspect(c, fmt):
    return subprocess.run(
        ["docker", "inspect", c, "--format", fmt],
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout.strip()


def main():
    reg = json.loads(REG.read_text())
    by_name = {u["nom_actuel"]: u for u in reg["units"]}
    running = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True
    ).stdout.split()

    services, depts = {}, set()
    for c in running:
        if (
            inspect(c, '{{index .Config.Labels "com.docker.compose.project"}}')
            != PROJECT
        ):
            continue
        svc = inspect(c, '{{index .Config.Labels "com.docker.compose.service"}}')
        u = by_name.get(c)
        if not svc or not u:
            continue
        services[svc] = (u["nom_cible"], u["dept"])
        depts.add(u["dept"])

    lines = [
        "# Override entreprise — généré par jv-compose-override (NE PAS appliquer sans backup)",
        "# usage: docker compose -f docker-compose.modules.yml -f docker-compose.jv-entreprise.yml up -d",
        "services:",
    ]
    for svc, (cible, dept) in sorted(services.items()):
        lines += [
            f"  {svc}:",
            f"    container_name: {cible}",
            f"    networks: [default, jvnet-{dept}]",
        ]
    lines.append("networks:")
    for d in sorted(depts):
        lines += [f"  jvnet-{d}:", "    external: true"]
    OUT.write_text("\n".join(lines) + "\n")
    print(f"[jv-compose-override] {len(services)} services -> {OUT}")
    for svc, (cible, dept) in sorted(services.items()):
        print(f"  {svc:32} -> {cible:30} (jvnet-{dept})")
    print("\nNON appliqué. Pour activer (recrée les containers, downtime bref) :")
    print(
        f"  cd {OUT.parent} && docker compose -f docker-compose.modules.yml -f {OUT.name} up -d"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
