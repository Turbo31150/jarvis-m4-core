#!/usr/bin/env python3
"""build-unit-index.py — Cascade P0+P1 : index/registre/ports des unités JARVIS.

Scanne repos Git + services systemd + ports → table `unit_registry` (jarvis_master.db)
+ docs/INDEX_UNITES.md + docs/PORTS_REGISTRY.md. Nommage HYBRIDE code D<n>-slug + marque.
Non-destructif (lecture seule + écriture index/docs). stdlib uniquement, 0 token.
"""

import os
import re
import sqlite3
import subprocess
from datetime import datetime, timezone

ROOT = "/home/pamerys/jarvis"
DB = f"{ROOT}/jarvis_master.db"
DOCS = f"{ROOT}/docs"
HOME = "/home/pamerys"

# Organigramme : division -> (marque, [repos]). Codes D<n>-slug assignés auto.
DIVISIONS = [
    (
        "D0",
        "HOLDING/OS",
        [
            "jarvis",
            "jarvis-alkymia-os",
            "jarvis-zero-token",
            "configuration-llm-openclaw",
        ],
    ),
    ("D1", "IA/LLM", ["agentkit", "awesome-local-ai", "llama.cpp"]),
    ("D2", "VOICE", ["jarvis-voice-platform", "jarvis/lumen"]),
    ("D3", "CONTENU/SOCIAL", ["github-social-automation", "jarvis-cowork"]),
    (
        "D4",
        "WEB/SITES",
        [
            "jarvis-delmas-site",
            "jarvis-delmas-tunnel",
            "alkymia-site",
            "app.atsd.info",
            "jarvis-website-from-m5",
            "claire-poste-futur",
        ],
    ),
    ("D5", "FINTECH/TRADING", ["tradingviewMaison"]),
    (
        "D6",
        "DATA/MEMOIRE",
        ["jarvis-chat-vault", "jarvis-sql-backups", "jarvis-n8n-workflows"],
    ),
    ("D7", "INFRA/CLUSTER", ["jarvis-machines-private", "novnc"]),
    ("D8", "METIER/SaaS", ["passcerfa-app", "alkymia", "jarvis-superpowers-plans"]),
]

# Marques par repo (affichage hybride). Défaut = slug capitalisé.
BRANDS = {
    "jarvis": "JARVIS Core",
    "jarvis-alkymia-os": "AlkymIA-OS",
    "agentkit": "AgentKit",
    "jarvis-voice-platform": "VoiceForge",
    "lumen": "Lumen",
    "jarvis/lumen": "Lumen",
    "github-social-automation": "GitFlow·AI",
    "jarvis-cowork": "Cowork",
    "jarvis-delmas-tunnel": "Delmas Tunnel",
    "alkymia-site": "AlkymIA Web",
    "passcerfa-app": "PassCerfa",
    "tradingviewMaison": "Orion Fintech",
    "jarvis-chat-vault": "ChatVault",
    "jarvis-sql-backups": "DataVault",
}


def sh(cmd):
    try:
        return subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=15
        ).stdout.strip()
    except Exception:
        return ""


def find_repo(slug):
    for base in (HOME, ROOT):
        p = os.path.join(base, slug)
        if os.path.isdir(os.path.join(p, ".git")) or os.path.isdir(p):
            return p
    return ""


def services():
    out = sh(
        "systemctl --user list-units --type=service --state=running --no-legend 2>/dev/null"
    )
    svc = [l.split()[0] for l in out.splitlines() if l.strip()]
    return [
        s
        for s in svc
        if re.search(
            r"jarvis|mirra|telegram|chat|router|whisper|browseros|lms|cowork|trade|orion|aria|antigravity|lumen|ccr|requestly|sql|wakeword|zombie",
            s,
            re.I,
        )
    ]


def ports():
    out = sh("ss -tlnp 2>/dev/null")
    rows = []
    for l in out.splitlines()[1:]:
        m = re.search(r"\s(\S+):(\d+)\s.*users:\(\(\"([^\"]+)\"", l)
        if m:
            rows.append((int(m.group(2)), m.group(1), m.group(3)))
    seen, uniq = {}, []
    for port, addr, proc in sorted(rows):
        if port in seen:
            seen[port].append(proc)
        else:
            seen[port] = [proc]
            uniq.append((port, addr, proc))
    collisions = {p: v for p, v in seen.items() if len(set(v)) > 1}
    return uniq, collisions


def build():
    os.makedirs(DOCS, exist_ok=True)
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    con = sqlite3.connect(DB, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    con.execute("""CREATE TABLE IF NOT EXISTS unit_registry(
        code TEXT PRIMARY KEY, brand TEXT, slug TEXT, division TEXT,
        repo_path TEXT, has_valise INTEGER DEFAULT 0, last_commit TEXT, indexed_at TEXT)""")
    units = []
    for dcode, dname, repos in DIVISIONS:
        for i, slug in enumerate(repos, 1):
            code = f"{dcode}-{slug.split('/')[-1]}"
            brand = BRANDS.get(
                slug,
                BRANDS.get(
                    slug.split("/")[-1], slug.split("/")[-1].replace("-", " ").title()
                ),
            )
            path = find_repo(slug)
            valise = (
                1 if path and os.path.isdir(os.path.join(path, ".claude/skills")) else 0
            )
            commit = (
                sh(f"git -C '{path}' log --oneline -1 2>/dev/null")[:60] if path else ""
            )
            units.append((code, brand, slug, f"{dcode} {dname}", path, valise, commit))
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    con.executemany(
        "INSERT OR REPLACE INTO unit_registry"
        "(code,brand,slug,division,repo_path,has_valise,last_commit,indexed_at)"
        " VALUES(?,?,?,?,?,?,?,?)",
        [(u[0], u[1], u[2], u[3], u[4], u[5], u[6], ts) for u in units],
    )
    con.commit()

    # INDEX_UNITES.md
    with open(f"{DOCS}/INDEX_UNITES.md", "w", encoding="utf-8") as f:
        f.write(
            f"# INDEX DES UNITÉS JARVIS — Holding\n\n> Généré {ts} · {len(units)} unités · non-destructif\n\n"
        )
        f.write(
            "| Code | Marque | Division | Repo | Valise | Dernier commit |\n|---|---|---|---|:---:|---|\n"
        )
        cur = None
        for u in units:
            f.write(
                f"| `{u[0]}` | {u[1]} | {u[3]} | `{u[2]}` | {'✅' if u[5] else '—'} | {u[6] or 'n/a'} |\n"
            )
        nv = sum(1 for u in units if u[5])
        f.write(
            f"\n**Couverture valise : {nv}/{len(units)}** — unités sans valise = cibles P2.\n"
        )

    # PORTS_REGISTRY.md
    uniq, collisions = ports()
    svc = services()
    with open(f"{DOCS}/PORTS_REGISTRY.md", "w", encoding="utf-8") as f:
        f.write(
            f"# REGISTRE DES PORTS — Câblage JARVIS\n\n> Généré {ts} · {len(uniq)} ports · {len(svc)} services actifs\n\n"
        )
        f.write(
            "## Ports (port → bind → process)\n\n| Port | Bind | Process |\n|---|---|---|\n"
        )
        for port, addr, proc in uniq:
            f.write(f"| {port} | {addr} | {proc} |\n")
        f.write("\n## Collisions détectées\n\n")
        if collisions:
            for p, procs in collisions.items():
                f.write(f"- ⚠️ port {p} : {', '.join(set(procs))}\n")
        else:
            f.write("Aucune collision (1 process par port).\n")
        f.write(f"\n## Services systemd actifs ({len(svc)})\n\n")
        for s in svc:
            f.write(f"- {s}\n")
    con.close()
    return len(units), nv, len(uniq), len(collisions), len(svc)


if __name__ == "__main__":
    n, nv, np_, nc, ns = build()
    print(f"✅ unit_registry: {n} unités ({nv} avec valise)")
    print(
        f"✅ INDEX_UNITES.md + PORTS_REGISTRY.md: {np_} ports, {nc} collisions, {ns} services"
    )
