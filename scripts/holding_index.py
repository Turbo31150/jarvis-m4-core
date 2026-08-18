#!/usr/bin/env python3
"""holding_index.py — Index maître « holding d'entreprises » JARVIS.
Classe agents/skills (registry.json) + services (ss) + containers (docker) dans
les 9 BU (Legions L1-L9), produit docs/holding/INDEX.md, et alimente la table
cmdlib.holding_index. Déterministe, 0 token LLM."""

from __future__ import annotations
import json
import re
import subprocess
import datetime
from pathlib import Path

ROOT = Path("/home/pamerys/jarvis")
REG = ROOT / "orchestrator" / "registry.json"
OUT = ROOT / "docs" / "holding"
OUT.mkdir(parents=True, exist_ok=True)

# BU : (label, regex de classement sur le nom, en ordre de priorité)
BU = [
    ("L6", "Trading", r"trad|mexc|signal|crypto|bourse"),
    (
        "L7",
        "Comms/Voix/Business",
        r"telegram|comms|voice|tts|whisper|vocal|linkedin|social|mirra|content|carousel|predis|business|freelance|prospect|client|mail|notion",
    ),
    (
        "L9",
        "Data & Mémoire",
        r"data|sql|backup|pinecone|memory|mémoire|\bdb\b|n8n|cmdlib|library|timeshift",
    ),
    (
        "L8",
        "Cluster & Monitoring",
        r"cluster|monitor|gpu|watchdog|backpressure|scaler|health|llm-stat|lms|node|thermal",
    ),
    (
        "L5",
        "Automatisation/Dispatch",
        r"automation|cascade|domino|orchestrat|flow|dispatch|task|queue|scheduler|pipeline|router",
    ),
    (
        "L3",
        "Ops & Système",
        r"linux|ops|deploy|maintenance|\bboot\b|sys|heal|service|autoheal|security|audit|docker|incident|zombie|disk|devops|share|launcher",
    ),
    ("L2", "CLI & Outils", r"cli|jarvis-cli|master|tool|compile"),
    (
        "L1",
        "IA & Inférence",
        r"\bai\b|llm|model|ollama|inference|engine|consensus|cowork-ai|core-agent|antigravity|gemini|ask-ai|smart-rout|dispatcher",
    ),
]
DEFAULT = ("L0", "Transverse / non classé", "")


def classify(name: str) -> str:
    n = name.lower()
    for code, _, rx in BU:
        if rx and re.search(rx, n):
            return code
    return DEFAULT[0]


def sh(cmd: str) -> str:
    try:
        return subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=20
        ).stdout
    except Exception:
        return ""


def main() -> int:
    reg = json.loads(REG.read_text())
    entries = reg.get("entries", reg if isinstance(reg, list) else [])
    buckets: dict[str, list] = {c: [] for c, _, _ in BU}
    buckets[DEFAULT[0]] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        nm = e.get("name", "?")
        buckets[classify(nm)].append((e.get("kind", "?"), nm))

    # services en écoute (ports → câblage)
    ports = sorted(
        set(re.findall(r":(\d{3,5})\b", sh("ss -tlnp 2>/dev/null | awk '{print $4}'")))
    )
    containers = [
        c for c in sh("docker ps --format '{{.Names}}' 2>/dev/null").splitlines() if c
    ]

    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# INDEX MAÎTRE — Holding JARVIS OS\n",
        f"_Généré {ts} par holding_index.py (déterministe)_\n",
        f"\n**Total classé** : {sum(len(v) for v in buckets.values())} entrées · "
        f"{len(ports)} ports · {len(containers)} containers\n",
    ]
    labels = {c: l for c, l, _ in BU}
    labels[DEFAULT[0]] = DEFAULT[1]
    rows = []  # pour SQL
    for code in [c for c, _, _ in BU] + [DEFAULT[0]]:
        items = sorted(buckets[code])
        lines.append(f"\n## BU-{code} — {labels[code]} ({len(items)})\n")
        for kind, nm in items:
            lines.append(f"- `{kind}` **{nm}**")
            rows.append((code, kind, nm))
    lines.append("\n## Ports en écoute (câblage)\n")
    lines.append("`" + " ".join(ports) + "`\n")
    lines.append("\n## Containers actifs\n")
    lines += [f"- {c}" for c in sorted(containers)]

    (OUT / "INDEX.md").write_text("\n".join(lines))
    print(
        f"✅ {OUT / 'INDEX.md'} — {len(rows)} entrées, {len(ports)} ports, {len(containers)} containers"
    )

    # répartition
    for code in [c for c, _, _ in BU] + [DEFAULT[0]]:
        print(f"   BU-{code} {labels[code]:28} {len(buckets[code])}")

    # SQL (best-effort, idempotent)
    sql = "CREATE TABLE IF NOT EXISTS holding_index(bu text,kind text,name text,added timestamptz default now(),PRIMARY KEY(bu,name));"
    sql += "TRUNCATE holding_index;"
    for bu_, k, nm in rows:
        nm2 = nm.replace("'", "''")
        k2 = k.replace("'", "''")
        sql += f"INSERT INTO holding_index(bu,kind,name) VALUES('{bu_}','{k2}','{nm2}') ON CONFLICT DO NOTHING;"
    (OUT / "_holding_index.sql").write_text(sql)
    print(f"   SQL → {OUT / '_holding_index.sql'} (applique via docker exec psql)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
