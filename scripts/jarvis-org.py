#!/usr/bin/env python3
"""jarvis-org.py — Organigramme « Entreprise JARVIS » : consulter + router par département.

S'appuie sur la table org_chart (jarvis_master.db) + les valises (.valises/).
Route une tâche vers le bon DÉPARTEMENT (mots-clés métier) → lane de sa valise → hub.

Usage :
  jarvis-org.py chart                 # organigramme (départements + effectifs)
  jarvis-org.py dept jv-ia            # entités d'un département
  jarvis-org.py valise <entity_id>    # valise d'une entité
  jarvis-org.py route "<tâche>"       # route métier → département + lane + exécute via hub
"""

import os
import sys
import json
import sqlite3
import urllib.request

ROOT = "/home/pamerys/jarvis"
DB = f"{ROOT}/jarvis_master.db"
VAL = f"{ROOT}/.valises"
HUB = os.environ.get("JARVIS_HUB", "http://127.0.0.1:18800")

# Routage MÉTIER : mots-clés → département (1er match). Chaque dept a sa lane (valise).
DEPT_RULES = [
    (
        "jv-finance",
        ["trading", "crypto", "mexc", "bourse", "signal", "scalp", "btc", "futures"],
    ),
    (
        "jv-front",
        [
            "linkedin",
            "telegram",
            "whatsapp",
            "mail",
            "social",
            "post",
            "publie",
            "n8n",
            "bot",
        ],
    ),
    (
        "jv-studio",
        [
            "carousel",
            "contenu",
            "mirra",
            "bibliothèque",
            "article",
            "blog",
            "short",
            "visuel",
        ],
    ),
    ("jv-sec", ["audit", "sécu", "securit", "secret", "vulnérab", "injection", "rgpd"]),
    (
        "jv-data",
        [
            "sql",
            "base de donnée",
            "memory",
            "mémoire",
            "backup",
            "sauvegarde",
            "pinecone",
            "rag",
            "embedding",
        ],
    ),
    (
        "jv-infra",
        [
            "gpu",
            "service",
            "docker",
            "cluster",
            "systemd",
            "kernel",
            "ram",
            "infra",
            "déploie",
            "monitoring",
        ],
    ),
    (
        "jv-ia",
        [
            "modèle",
            "llm",
            "hub",
            "inférence",
            "ollama",
            "lmstudio",
            "routage llm",
            "gpt-oss",
        ],
    ),
    (
        "jv-studio",
        ["code", "fonction", "refactor", "python", "implémente", "bug"],
    ),  # engineering ⊂ studio
]
DEPT_LANE = {
    "jv-ia": "jarvis-quality",
    "jv-finance": "jarvis-quality",
    "jv-sec": "jarvis-quality",
    "jv-studio": "jarvis-fast",
    "jv-infra": "jarvis-fast",
    "jv-front": "jarvis-fast",
    "jv-log": "jarvis-fast",
    "jv-data": "jarvis-auto",
    "jv-dg": "jarvis-auto",
}


def _c():
    c = sqlite3.connect(DB, timeout=10)
    c.execute("PRAGMA busy_timeout=8000")
    return c


def detect_dept(task):
    t = task.lower()
    for dept, kws in DEPT_RULES:
        if any(k in t for k in kws):
            return dept
    return "jv-dg"


def hub(lane, prompt):
    body = json.dumps(
        {
            "model": lane,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
        }
    ).encode()
    req = urllib.request.Request(
        f"{HUB}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"], d.get("model", lane)


def chart():
    c = _c()
    print("═══ ORGANIGRAMME ENTREPRISE JARVIS ═══")
    for dept, cnt in c.execute(
        "SELECT dept,COUNT(*) FROM org_chart GROUP BY dept ORDER BY 2 DESC"
    ):
        lane = DEPT_LANE.get(dept, "jarvis-auto")
        ex = [
            r[0]
            for r in c.execute(
                "SELECT role FROM org_chart WHERE dept=? LIMIT 3", (dept,)
            )
        ]
        print(f"  {dept:11} {cnt:3} entités  [lane {lane}]  ex: {', '.join(ex)}")
    c.close()


def dept(name):
    c = _c()
    rows = c.execute(
        "SELECT entity_type,role FROM org_chart WHERE dept=? ORDER BY entity_type",
        (name,),
    ).fetchall()
    c.close()
    print(
        f"═══ Département {name} ({len(rows)} entités, lane {DEPT_LANE.get(name)}) ═══"
    )
    for et, role in rows[:40]:
        print(f"  [{et:9}] {role}")


def valise(eid):
    import glob

    hits = glob.glob(f"{VAL}/*{eid.replace('/', '_')}*/valise.json")
    if not hits:
        print(f"  pas de valise pour {eid}")
        return
    print(open(hits[0]).read())


def route(task):
    d = detect_dept(task)
    lane = DEPT_LANE.get(d, "jarvis-auto")
    print(f"[org] tâche → département {d} → lane {lane}")
    try:
        txt, model = hub(lane, task)
        print(f"--- via {model} (dept {d}) ---\n{txt}")
    except Exception as e:  # noqa: BLE001
        print(f"[org] échec hub ({e})")


def main(a):
    if not a or a[0] == "chart":
        return chart()
    if a[0] == "dept" and len(a) > 1:
        return dept(a[1])
    if a[0] == "valise" and len(a) > 1:
        return valise(a[1])
    if a[0] == "route" and len(a) > 1:
        return route(" ".join(a[1:]))
    print('usage: jarvis-org.py chart|dept <d>|valise <id>|route "<tâche>"')


if __name__ == "__main__":
    main(sys.argv[1:])
