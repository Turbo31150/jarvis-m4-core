#!/usr/bin/env python3
"""Assemble un PLAN DE TRAVAIL sur 3 mois (une période) à partir de l'existant :
programme 2026 (5 domaines) + fiches déjà en banque. 0 génération IA, 0 throttle.
Sortie : HTML imprimable/adaptable, 7 semaines × 5 domaines, par niveau."""

import os
import sqlite3
import html

WEBAPP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(WEBAPP, "ecole.db")
OUT = os.path.join(WEBAPP, "static", "plans")

DOMAINES = [
    "Développement et structuration du langage oral et écrit",
    "Acquisition des premiers outils mathématiques",
    "Agir, s'exprimer, comprendre à travers l'activité physique",
    "Agir, s'exprimer, comprendre à travers les activités artistiques",
    "Explorer le monde",
]
COURT = {
    DOMAINES[0]: "Langage",
    DOMAINES[1]: "Maths",
    DOMAINES[2]: "EPS",
    DOMAINES[3]: "Arts",
    DOMAINES[4]: "Explorer le monde",
}
PERIODES = {
    1: "Période 1 — septembre/octobre",
    2: "Période 2 — nov./déc.",
    3: "Période 3 — janv./févr.",
    4: "Période 4 — mars/avril",
    5: "Période 5 — mai/juin",
}
NB_SEMAINES = 7


def plan_niveau(niveau, periode=1):
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    # notions par domaine (5 domaines officiels), pour cette période
    par_dom = {d: [] for d in DOMAINES}
    for r in c.execute(
        "SELECT matiere, notion, id FROM banque WHERE niveau=? AND periode=? AND matiere IN (?,?,?,?,?) ORDER BY id",
        (niveau, periode, *DOMAINES),
    ):
        par_dom[r["matiere"]].append((r["notion"], r["id"]))
    c.close()

    rows = []
    for sem in range(1, NB_SEMAINES + 1):
        idx = sem - 1
        cells = []
        for d in DOMAINES:
            items = par_dom[d]
            if sem <= 5 and idx < len(items):
                notion, fid = items[idx]
                cells.append(
                    f'<td><b>{html.escape(notion)}</b><br><a href="../recueils/recueil-{niveau}.html">fiche</a></td>'
                )
            elif sem == 6:
                cells.append('<td class="c">Consolidation / reprise des acquis</td>')
            elif sem == 7:
                cells.append(
                    '<td class="c">Évaluation positive · observation · carnet de suivi</td>'
                )
            else:
                cells.append(
                    '<td class="c">Réinvestissement libre (ateliers autonomes)</td>'
                )
        libelle = (
            "Semaine 1 — accueil, rituels, découverte des coins"
            if sem == 1
            else f"Semaine {sem}"
        )
        rows.append(f"<tr><th>{libelle}</th>{''.join(cells)}</tr>")
    return rows


def build(periode=1):
    os.makedirs(OUT, exist_ok=True)
    css = (
        "body{font-family:system-ui,sans-serif;max-width:1100px;margin:auto;padding:24px;background:#f7f5ef;color:#222}"
        "h1{color:#1a6a4a}table{width:100%;border-collapse:collapse;margin:16px 0;font-size:13px}"
        "th,td{border:1px solid #d9d4c7;padding:8px;vertical-align:top;text-align:left}"
        "thead th{background:#1a6a4a;color:#fff}tbody th{background:#eef3ee;width:130px}"
        "td.c{color:#888;font-style:italic}a{color:#1a6a4a}.tip{background:#fff6e9;border-left:4px solid #d89a3a;padding:12px;border-radius:6px;margin:14px 0}"
        "@media print{body{background:#fff}table{page-break-inside:avoid}}"
    )
    links = []
    for niv in ("MS", "GS"):
        rows = plan_niveau(niv, periode)
        head = (
            "<tr><th></th>"
            + "".join(f"<th>{COURT[d]}</th>" for d in DOMAINES)
            + "</tr>"
        )
        doc = (
            f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Plan {niv} — {PERIODES[periode]}</title>'
            f"<style>{css}</style></head><body>"
            f"<h1>🗓️ Plan de travail — {niv} — {PERIODES[periode]}</h1>"
            f"<p>3 mois assemblés depuis le programme officiel 2026 (BO n°19) et la banque de fiches. "
            f"Structure indicative et <b>adaptable</b> : déplace, remplace, pioche selon ta semaine réelle.</p>"
            f'<div class="tip">💡 Journée changeante ? Va dans <b>Plan B</b> pour piocher une fiche prête (600+), '
            f"ou raccourcis avec « Version courte ». Chaque fiche = 3 niveaux différenciés.</div>"
            f"<table><thead>{head}</thead><tbody>{''.join(rows)}</tbody></table>"
            f'<p class="tip">📌 Semaines 6-7 = consolidation + évaluation positive (carnet de suivi). '
            f"Périodes suivantes : relance ce plan avec periode=2..5.</p></body></html>"
        )
        f = os.path.join(OUT, f"plan-{niv}-P{periode}.html")
        open(f, "w", encoding="utf-8").write(doc)
        links.append((niv, f))
    return links


if __name__ == "__main__":
    for niv, f in build(1):
        print(f"✅ {niv} : {f}")
