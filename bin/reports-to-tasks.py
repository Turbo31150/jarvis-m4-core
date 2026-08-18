#!/usr/bin/env python3
"""reports-to-tasks.py — E2 : transforme les décisions des reports d'audit en tâches.

Les 43 AUDIT_DEEP_REPORT.md contiennent une section « Roadmap / Actions Immédiates »
avec des puces actionnables (Quick Wins, refactoring, priorités). Ce script les extrait,
les nettoie, dédup (vs jarvis_master done+pending), et les insère en pending taguées
`[report-decision]` → l'exécuteur/prod-exec les traite. Ferme le trou : reports lus mais
décisions jamais exécutées.

Idempotent, --dry par défaut, --go pour insérer. Cap anti-flood. 0-token.
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys

RUNS = os.path.expanduser("~/jarvis/audit/runs")
DB = os.path.expanduser("~/jarvis/jarvis_master.db")
CAP = 100

# une puce d'action dans la roadmap
_BULLET = re.compile(r"^\s*[*\-]\s+(.+)")
# entête de section actionnable
_SECTION = re.compile(
    r"roadmap|action|quick win|priorit|recommand|à faire|semaine", re.I
)


def _clean(txt: str) -> str:
    txt = re.sub(r"\*\*(Quick Win \d+|Action \d+)\s*:?\*\*\s*", "", txt)  # préfixe QW
    txt = re.sub(r"\*\*|\*|`", "", txt)  # markdown
    txt = re.sub(r"\.?\s*Priorit[ée]\s*:.*$", "", txt, flags=re.I)  # suffixe priorité
    return txt.strip(" .:-")


def extract(md_path) -> list[str]:
    try:
        lines = open(md_path, encoding="utf-8", errors="ignore").read().splitlines()
    except Exception:
        return []
    out, in_action = [], False
    for ln in lines:
        h = re.match(r"^\s*#{1,4}\s*(.+)", ln)
        if h:
            in_action = bool(_SECTION.search(h.group(1)))
            continue
        if not in_action:
            continue
        m = _BULLET.match(ln)
        if m:
            txt = _clean(m.group(1))
            if len(txt) >= 15 and txt[0:1].isupper():
                out.append(txt)
    return out


def main() -> int:
    go = "--go" in sys.argv
    reports = (
        sorted(
            [
                os.path.join(dp, "AUDIT_DEEP_REPORT.md")
                for dp in (os.path.join(RUNS, d) for d in os.listdir(RUNS))
                if os.path.isfile(os.path.join(dp, "AUDIT_DEEP_REPORT.md"))
            ],
            reverse=True,
        )
        if os.path.isdir(RUNS)
        else []
    )

    c = sqlite3.connect(DB, timeout=15)
    c.execute("PRAGMA busy_timeout=15000")
    seen = {
        r[0]
        for r in c.execute(
            "SELECT title FROM tasks WHERE status IN ('pending','done','to_validate') "
            "OR (status='analyzed')"
        )
    }

    inserted, scanned = 0, 0
    for rp in reports:
        run = os.path.basename(os.path.dirname(rp))[:24]
        for action in extract(rp):
            scanned += 1
            title = f"[{run}] {action[:130]}"
            if inserted >= CAP or title in seen:
                continue
            seen.add(title)
            if go:
                c.execute(
                    "INSERT INTO tasks(title, context, status, machine) "
                    "VALUES(?,?,'pending','M1')",
                    (title, "🟣 [report-decision] issu d'un AUDIT_DEEP_REPORT"),
                )
            inserted += 1

    if go:
        c.commit()
    c.close()
    tag = "GO" if go else "DRY"
    print(
        f"[reports-to-tasks] {tag} · {len(reports)} reports · {scanned} actions vues · "
        f"+{inserted} tâches [report-decision] (cap {CAP})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
