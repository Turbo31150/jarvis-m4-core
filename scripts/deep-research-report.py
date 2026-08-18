#!/usr/bin/env python3
"""deep-research-report.py — markdown findings.md -> report.html (+ index) self-contained.

Découvre tout sous-dossier de BASE contenant un findings.md, génère un report.html
stylé par dossier + un index-deep-research.html consolidé dans BASE.
Mini-converter markdown->HTML (stdlib seule) : titres, **gras**, _italique_, `code`,
[liens](url), listes, tables, et findings numérotés -> cartes.

Usage :
  deep-research-report.py [BASE_DIR]        # défaut : ~/Downloads
  BASE=/chemin deep-research-report.py
Export PDF (séparé, hors script) : wkhtmltopdf -q --enable-local-file-access in.html out.pdf
"""

import re
import html
import os
import sys
import glob

BASE = (
    sys.argv[1]
    if len(sys.argv) > 1
    else os.environ.get("BASE") or os.path.expanduser("~/Downloads")
)


def inline(s):
    s = html.escape(s)
    s = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" target="_blank">\1</a>', s
    )
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def md_to_html(md):
    out, i, lines = [], 0, md.split("\n")
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("# "):
            out.append(f"<h1>{inline(ln[2:])}</h1>")
        elif ln.startswith("## "):
            out.append(f"<h2>{inline(ln[3:])}</h2>")
        elif ln.startswith("---"):
            out.append("<hr>")
        elif ln.lstrip().startswith("|"):
            tbl = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                tbl.append(lines[i])
                i += 1
            rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in tbl]
            rows = [r for r in rows if not all(set(c) <= set("-: ") for c in r)]
            if rows:
                out.append(
                    "<table><thead><tr>"
                    + "".join(f"<th>{inline(c)}</th>" for c in rows[0])
                    + "</tr></thead><tbody>"
                )
                for r in rows[1:]:
                    out.append(
                        "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                    )
                out.append("</tbody></table>")
            continue
        elif re.match(r"^\d+\.\s", ln):
            m = re.match(r"^(\d+)\.\s+(.*)", ln)
            num, head = m.group(1), m.group(2)
            body = []
            i += 1
            while (
                i < len(lines)
                and lines[i].strip()
                and not re.match(r"^\d+\.\s", lines[i])
                and not lines[i].startswith("#")
                and not lines[i].lstrip().startswith("|")
            ):
                body.append(lines[i].strip())
                i += 1
            out.append(
                f'<div class="card"><div class="num">{num}</div><div class="card-body">'
                f'<p class="ctitle">{inline(head)}</p>'
                + "".join(f"<p>{inline(b)}</p>" for b in body)
                + "</div></div>"
            )
            continue
        elif ln.lstrip().startswith("- "):
            out.append("<ul>")
            while i < len(lines) and lines[i].lstrip().startswith("- "):
                out.append(f"<li>{inline(lines[i].lstrip()[2:])}</li>")
                i += 1
            out.append("</ul>")
            continue
        else:
            out.append(f"<p>{inline(ln)}</p>")
        i += 1
    return "\n".join(out)


CSS = """*{box-sizing:border-box}body{margin:0;background:#fff;color:#1a1a2e;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;line-height:1.6}
.wrap{max-width:880px;margin:0 auto;padding:0 22px 60px}
.banner{background:linear-gradient(135deg,#0b3d91,#1565c0);color:#fff;padding:38px 22px;margin-bottom:8px}
.banner .wrap{padding-bottom:0}.banner h1{margin:.1em 0;font-size:1.7em}.banner .sub{opacity:.85;font-size:.95em}
h1{font-size:1.5em;border-bottom:2px solid #eee;padding-bottom:.2em}h2{font-size:1.2em;color:#0b3d91;margin-top:1.8em}
a{color:#1565c0;text-decoration:none}a:hover{text-decoration:underline}
code{background:#f1f3f8;padding:1px 5px;border-radius:4px;font-size:.9em}
hr{border:none;border-top:1px solid #eee;margin:1.5em 0}
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:.9em}th,td{border:1px solid #e3e6ef;padding:8px 10px;text-align:left;vertical-align:top}
th{background:#f5f7fb}tr:nth-child(even) td{background:#fafbfe}
.card{display:flex;gap:14px;background:#f8faff;border:1px solid #e3e8f5;border-left:4px solid #1565c0;border-radius:8px;padding:14px 16px;margin:12px 0}
.card .num{font-weight:700;font-size:1.3em;color:#1565c0;min-width:28px}.card .ctitle{font-weight:600;margin:.1em 0 .3em}
.card p{margin:.25em 0}.card em{color:#5a6b8c;font-size:.88em}
footer{margin-top:40px;padding-top:16px;border-top:1px solid #eee;color:#8892a8;font-size:.85em;text-align:center}
.toc a{display:block;padding:10px 14px;margin:8px 0;background:#f8faff;border:1px solid #e3e8f5;border-radius:8px}"""


def page(title, sub, body):
    return (
        f'<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
        f'<div class="banner"><div class="wrap"><h1>{html.escape(title)}</h1>'
        f'<div class="sub">{html.escape(sub)}</div></div></div>'
        f'<div class="wrap">{body}<footer>Generated by JARVIS Deep Research</footer></div></body></html>'
    )


def title_of(md, fallback):
    for ln in md.split("\n"):
        if ln.startswith("# "):
            return re.sub(r"^Research Findings:\s*", "", ln[2:]).strip()
    return fallback


def main():
    found = sorted(glob.glob(os.path.join(BASE, "*", "findings.md")))
    if not found:
        print(f"[report] aucun findings.md sous {BASE}")
        return 1
    cards = []
    for fm in found:
        d = os.path.dirname(fm)
        slug = os.path.basename(d)
        md = open(fm, encoding="utf-8").read()
        title = title_of(md, slug)
        nsrc = len(glob.glob(os.path.join(d, "sources", "*.md")))
        open(os.path.join(d, "report.html"), "w", encoding="utf-8").write(
            page(title, f"Deep Research · {nsrc} sources", md_to_html(md))
        )
        cards.append((slug, title, nsrc))
        print(f"[report] {slug}/report.html ({nsrc} sources)")
    toc = (
        '<div class="toc">'
        + "".join(
            f'<a href="{s}/report.html"><strong>{html.escape(t)}</strong> — {n} sources</a>'
            for s, t, n in cards
        )
        + "</div>"
    )
    total = sum(n for _, _, n in cards)
    open(os.path.join(BASE, "index-deep-research.html"), "w", encoding="utf-8").write(
        page(
            "Deep Research — Index",
            f"{len(cards)} rapports · {total} sources",
            f"<p>{len(cards)} recherches, {total} sources citées.</p><h2>Rapports</h2>"
            + toc,
        )
    )
    print(f"[index] index-deep-research.html ({len(cards)} rapports, {total} sources)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
