#!/usr/bin/env python3
"""build_index.py — indexe JARVIS en organigramme par département (0-token, déterministe).

Scanne agents/skills/services/ports/outils/scripts, classe chacun par DÉPARTEMENT
(règles mot-clé/chemin), remplit org_chart/org_routing/org_ports (SQLite + Postgres
best-effort) et génère docs/ORGANIGRAMME.md + docs/PORTS_CABLAGE.md.
Idempotent (tables recréées). Aucun déménagement de code — étiquetage logique.
"""

from __future__ import annotations
import glob
import sqlite3
import subprocess
import pathlib
import datetime

HOME = pathlib.Path.home()
J = HOME / "jarvis"
DB = J / "jarvis.db"

# Départements : (nom, label, mots-clés de classification)
DEPTS = [
    (
        "dept.social",
        "🟦 SOCIAL & CONTENU",
        [
            "mirr",
            "mirra",
            "carousel",
            "linkedin",
            "instagram",
            "threads",
            "tiktok",
            "social",
            "content",
            "publish",
            "predis",
            "cdp",
            "post",
            "compose",
        ],
    ),
    (
        "dept.cluster",
        "🟩 CLUSTER & LLM",
        [
            "lm-ask",
            "lmstudio",
            "lms",
            "gemini",
            "ollama",
            "llm",
            "cluster",
            "dispatch",
            "model",
            "inference",
            "qwen",
            "deepseek",
            "gpt-oss",
            "gemma",
            "router",
            "ask-ai",
            "consensus",
            "multi-llm",
            "gpu",
        ],
    ),
    (
        "dept.infra",
        "🟨 INFRA & BROWSER",
        [
            "browseros",
            "antigravity",
            "chrome",
            "browser",
            "docker",
            "boot",
            "deploy",
            "systemd",
            "infra",
            "demarrage",
            "launcher",
            "autoheal",
            "watchdog",
            "service",
        ],
    ),
    (
        "dept.data",
        "🟧 DATA & BACKUP",
        [
            "sql",
            "backup",
            "postgres",
            "n8n",
            "pinecone",
            "sqlite",
            "data",
            "memory",
            "etl",
            "ingest",
            "share",
            "mount",
        ],
    ),
    (
        "dept.security",
        "🟥 SÉCURITÉ",
        [
            "security",
            "secret",
            "rgpd",
            "gitleaks",
            "threat",
            "audit",
            "vuln",
            "rotation",
        ],
    ),
    (
        "dept.voice",
        "🟪 VOICE",
        ["voice", "whisper", "tts", "stt", "piper", "easyspeak", "vocal", "lumen"],
    ),
    (
        "dept.trading",
        "⬛ TRADING",
        ["trading", "mexc", "crypto", "signal", "scalp", "market", "trade"],
    ),
]
DEFAULT = "dept.infra"

# Overrides ciblés : agents/skills génériques mal captés par les mots-clés (réduisent
# le fourre-tout dept.infra). substring → département (prioritaire sur le scoring).
OVERRIDES = [
    ("cowork-ai", "dept.cluster"),
    ("services-ai", "dept.cluster"),
    ("cowork-voice", "dept.voice"),
    ("cowork-comms", "dept.social"),
    ("services-business", "dept.trading"),
    ("services-data", "dept.data"),
    ("cowork-monitoring", "dept.infra"),
    ("github", "dept.data"),
    ("freelance", "dept.trading"),
    ("prospect", "dept.trading"),
    ("codeur", "dept.trading"),
    ("compare-price", "dept.trading"),
    ("embedding", "dept.cluster"),
    ("smart-routing", "dept.cluster"),
    ("multi-ia", "dept.cluster"),
    ("multi-llm", "dept.cluster"),
    ("consensus", "dept.cluster"),
    ("telegram", "dept.social"),
    ("linkedin", "dept.social"),
    ("content", "dept.social"),
    ("carousel", "dept.social"),
    ("mirr", "dept.social"),
    ("sql", "dept.data"),
    ("memory", "dept.data"),
    ("pinecone", "dept.data"),
    ("rgpd", "dept.security"),
    ("security", "dept.security"),
    ("threat", "dept.security"),
]


def classify(name: str, path: str = "") -> str:
    s = (name + " " + path).lower()
    for sub, dep in OVERRIDES:
        if sub in s:
            return dep
    best, score = DEFAULT, 0
    for dep, _lbl, kws in DEPTS:
        c = sum(1 for k in kws if k in s)
        if c > score:
            best, score = dep, c
    return best


def scan():
    rows = []  # (dept, kind, name, path, status)
    # agents (plugins + locaux)
    for f in glob.glob(
        str(HOME / ".claude/plugins/**/agents/*.md"), recursive=True
    ) + glob.glob(str(J / ".claude/agents/*.md")):
        n = pathlib.Path(f).stem
        rows.append(
            (classify(n, f), "agent", n, f.replace(str(HOME), "~"), "registered")
        )
    # skills
    for f in glob.glob(str(HOME / ".claude/**/SKILL.md"), recursive=True):
        n = pathlib.Path(f).parent.name
        rows.append(
            (classify(n, f), "skill", n, f.replace(str(HOME), "~"), "registered")
        )
    # services systemd --user running
    try:
        out = subprocess.run(
            [
                "systemctl",
                "--user",
                "list-units",
                "--type=service",
                "--state=running",
                "--no-legend",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout
        for line in out.splitlines():
            svc = line.split()[0] if line.split() else ""
            if svc.endswith(".service"):
                n = svc[:-8]
                rows.append(
                    (classify(n, svc), "service", n, "systemd --user", "running")
                )
    except Exception:
        pass
    # outils (library_tools)
    try:
        for name, typ, path in sqlite3.connect(DB).execute(
            "SELECT name,type,path FROM library_tools"
        ):
            rows.append(
                (classify(name, path or ""), "tool", name, path or "", "library")
            )
    except Exception:
        pass
    # scripts clés
    for f in (
        glob.glob(str(J / "scripts/*.sh"))
        + glob.glob(str(J / "scripts/*.py"))
        + glob.glob(str(J / "integrations/mirr/*publish*.py"))
    ):
        n = pathlib.Path(f).name
        rows.append((classify(n, f), "script", n, f.replace(str(HOME), "~"), "file"))
    # dédup
    seen, uniq = set(), []
    for r in rows:
        k = (r[1], r[2])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    return uniq


# Ports → service + dept + rôle
PORTS = [
    (1234, "dept.cluster", "M1 LM Studio (modèles locaux)"),
    (11434, "dept.cluster", "OL1 Ollama (local + cloud gpt-oss)"),
    (18800, "dept.cluster", "chat_proxy (hub LLM OpenAI-compat)"),
    (18802, "dept.cluster", "ccr claude-code-router"),
    (9201, "dept.infra", "BrowserOS MCP natif"),
    (9108, "dept.infra", "BrowserOS container (browserless CDP)"),
    (9105, "dept.infra", "BrowserOS navigateur CDP"),
    (9222, "dept.social", "Chrome CDP (publishers réseaux)"),
    (5678, "dept.data", "n8n (workflows)"),
    (9743, "dept.voice", "WhisperFlow STT"),
]

# Routage : (intent regex, dept, commande/backend)
ROUTES = [
    (
        r"publi|carousel|linkedin|post|r.seau|social",
        "dept.social",
        "mirra publish-li / publish-ig",
    ),
    (r"g.n.r|contenu|brief|short|r.dige", "dept.social", "mirra pipeline / generate"),
    (
        r"llm|mod.le|inf.rence|cluster|raisonnement|consensus",
        "dept.cluster",
        "lm-ask.sh / ollama gpt-oss:120b-cloud",
    ),
    (
        r"backup|sauvegarde|sql|postgres|dump|n8n",
        "dept.data",
        "jarvis-sql-backup / jarvis-n8n-backup",
    ),
    (
        r"browser|browseros|chrome|cdp|navig|capture",
        "dept.infra",
        "browseros MCP 9201 / CDP 9222",
    ),
    (r"s.curit|secret|audit|rgpd|vuln", "dept.security", "security agents / gitleaks"),
    (r"voix|voice|whisper|tts|stt|parle", "dept.voice", "WhisperFlow 9743 / Piper"),
    (r"trading|crypto|mexc|signal", "dept.trading", "trading-engine"),
    (
        r"recherche|deep.?research|veille",
        "dept.social",
        "deep-research-local (gpt-oss)",
    ),
]


def write_sql(rows):
    con = sqlite3.connect(DB)
    c = con.cursor()
    c.execute("DROP TABLE IF EXISTS org_chart")
    c.execute(
        "CREATE TABLE org_chart(id INTEGER PRIMARY KEY, dept TEXT, kind TEXT, name TEXT, path TEXT, status TEXT)"
    )
    c.executemany(
        "INSERT INTO org_chart(dept,kind,name,path,status) VALUES(?,?,?,?,?)", rows
    )
    c.execute("DROP TABLE IF EXISTS org_ports")
    c.execute("CREATE TABLE org_ports(port INT, dept TEXT, role TEXT)")
    c.executemany("INSERT INTO org_ports VALUES(?,?,?)", PORTS)
    c.execute("DROP TABLE IF EXISTS org_routing")
    c.execute("CREATE TABLE org_routing(intent TEXT, dept TEXT, target TEXT)")
    c.executemany("INSERT INTO org_routing VALUES(?,?,?)", ROUTES)
    con.commit()
    con.close()


def gen_docs(rows):
    ts = datetime.date.today()
    docs = J / "docs"
    docs.mkdir(exist_ok=True)
    by = {d: [] for d, _l, _k in DEPTS}
    for dept, kind, name, path, status in rows:
        by.setdefault(dept, []).append((kind, name))
    lines = [
        f"# Organigramme JARVIS-OS\n\n_Généré {ts} par tools/org-index/build_index.py (0-token). {len(rows)} ressources indexées._\n"
    ]
    lines.append("\n```\nDG JARVIS-OS  (mirra · jarvis_master · library_tools)\n```\n")
    label = {d: l for d, l, _ in DEPTS}
    for dep, lbl, _ in DEPTS:
        items = by.get(dep, [])
        cnt = {}
        for k, _n in items:
            cnt[k] = cnt.get(k, 0) + 1
        lines.append(f"\n## {lbl}  (`{dep}`) — {len(items)} ressources")
        lines.append(
            "Valise : " + ", ".join(f"{v} {k}s" for k, v in sorted(cnt.items())) or "—"
        )
        ports = [f"{p} ({r})" for p, d, r in PORTS if d == dep]
        if ports:
            lines.append("Ports : " + " · ".join(ports))
        ex = [n for _k, n in items][:12]
        if ex:
            lines.append("Exemples : " + ", ".join(ex))
    (docs / "ORGANIGRAMME.md").write_text("\n".join(lines), encoding="utf-8")
    # ports
    pl = [
        f"# Ports & câblage JARVIS-OS\n\n_Généré {ts}._\n",
        "| Port | Département | Rôle |",
        "|---|---|---|",
    ]
    for p, d, r in PORTS:
        pl.append(f"| {p} | {label.get(d, d)} | {r} |")
    (docs / "PORTS_CABLAGE.md").write_text("\n".join(pl), encoding="utf-8")


if __name__ == "__main__":
    rows = scan()
    write_sql(rows)
    gen_docs(rows)
    con = sqlite3.connect(DB)
    print("=== org_chart par département ===")
    for dep, n in con.execute(
        "SELECT dept, COUNT(*) FROM org_chart GROUP BY dept ORDER BY 2 DESC"
    ):
        print(f"  {dep:16} {n}")
    print(
        f"total: {con.execute('SELECT COUNT(*) FROM org_chart').fetchone()[0]} ressources · "
        f"{con.execute('SELECT COUNT(*) FROM org_ports').fetchone()[0]} ports · "
        f"{con.execute('SELECT COUNT(*) FROM org_routing').fetchone()[0]} routes"
    )
