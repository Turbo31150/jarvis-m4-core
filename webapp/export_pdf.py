# -*- coding: utf-8 -*-
"""Module Export PDF — convertit un contenu markdown (cahier-journal, bulletin,
séance…) en PDF imprimable A4, via markdown→HTML→Chrome headless.
Réutilise le pipeline validé pour la production des supports."""

import os
import shutil
import subprocess
import tempfile
import uuid

from flask import request, send_file, jsonify

try:
    import markdown as _md
except Exception:  # pragma: no cover
    _md = None

_CHROME = (
    shutil.which("google-chrome")
    or shutil.which("chromium")
    or shutil.which("chromium-browser")
)

_CSS = """
@page{size:A4;margin:16mm 14mm}*{box-sizing:border-box}
body{font-family:'Segoe UI',Arial,sans-serif;color:#222;font-size:12px;line-height:1.55;margin:0}
h1{color:#2e7d32;font-size:21px;border-bottom:3px solid #66bb6a;padding-bottom:6px;margin:0 0 10px}
h2{color:#1b5e20;font-size:15px;border-left:5px solid #66bb6a;padding-left:8px;margin:16px 0 6px}
h3{color:#ef6c00;font-size:13px;margin:12px 0 4px}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:11px}
th{background:#66bb6a;color:#fff;padding:6px 8px;text-align:left;border:1px solid #4caf50}
td{padding:5px 8px;border:1px solid #cfe8c9;vertical-align:top}
tr:nth-child(even) td{background:#f6fbf4}
ul{margin:4px 0 10px;padding-left:20px}strong{color:#1b5e20}
blockquote{background:#f1f8e9;border-left:4px solid #aed581;padding:6px 12px;color:#555;margin:8px 0}
.foot{margin-top:18px;font-size:9px;color:#999;text-align:center;border-top:1px solid #ddd;padding-top:6px}
"""


def _html(markdown_str, titre):
    body = (
        _md.markdown(
            markdown_str or "",
            extensions=["tables", "fenced_code", "sane_lists", "nl2br"],
        )
        if _md
        else "<pre>" + (markdown_str or "") + "</pre>"
    )
    safe_titre = (titre or "Document").replace("<", "").replace(">", "")
    return (
        f"<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'><title>{safe_titre}</title>"
        f"<style>{_CSS}</style></head><body><h1>{safe_titre}</h1>{body}"
        f"<div class='foot'>Pousseline — préparé avec l'IA · données locales</div></body></html>"
    )


def md_to_pdf_path(markdown_str, titre):
    """Génère un PDF temporaire et renvoie son chemin (ou lève une exception)."""
    if not _CHROME:
        raise RuntimeError("Chrome/Chromium introuvable pour l'export PDF")
    tmp = tempfile.mkdtemp(prefix="pousseline-pdf-")
    base = uuid.uuid4().hex
    html_path = os.path.join(tmp, base + ".html")
    pdf_path = os.path.join(tmp, base + ".pdf")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(_html(markdown_str, titre))
    subprocess.run(
        [
            _CHROME,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            f"--print-to-pdf={pdf_path}",
            "--no-pdf-header-footer",
            f"file://{html_path}",
        ],
        capture_output=True,
        timeout=60,
    )
    if not os.path.exists(pdf_path):
        raise RuntimeError("Échec de génération du PDF")
    return pdf_path


def register(app):
    @app.route("/api/prof/export-pdf", methods=["POST"])
    def _export_pdf():
        d = request.get_json(force=True, silent=True) or {}
        contenu = d.get("markdown") or d.get("contenu") or ""
        titre = d.get("titre") or "Document"
        if not contenu.strip():
            return jsonify({"error": "Contenu vide"}), 400
        try:
            pdf_path = md_to_pdf_path(contenu, titre)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        fname = (
            "".join(c if c.isalnum() or c in " -_" else "_" for c in titre)[:60].strip()
            or "document"
        )
        return send_file(
            pdf_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{fname}.pdf",
        )

    print("[Pousseline] Export PDF chargé (/api/prof/export-pdf)")
