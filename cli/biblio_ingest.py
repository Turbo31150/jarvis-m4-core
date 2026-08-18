#!/usr/bin/env python3
"""biblio_ingest.py — Ingestion du patrimoine JARVIS dans la bibliothèque vivante.

Lit les sources INTERNES (repos GitHub, containers Docker, documents markdown,
bases SQL dont etoile.db) et TRANSFORME chaque source en fiche de connaissance
(synthèse LM Studio :1234, 0-token) → table biblio_knowledge + data/biblio_knowledge/.

Idempotent (skip si fiche existe), cache SQL, garde thermique, parallèle (2 workers
pour laisser le daemon biblio-filler respirer).
"""

from __future__ import annotations
import os
import re
import sys
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "/home/turbo/jarvis/cli")
import biblio_filler as b

ROOT = "/home/turbo/jarvis"
KNOW_DIR = os.path.join(ROOT, "data", "biblio_knowledge")


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def sh(cmd, timeout=30):
    try:
        return subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        ).stdout.strip()
    except Exception:
        return ""


# ---------------------------------------------------------------- collecte
def collect():
    items = []  # (domain, key, source_text)

    # 1. Repos GitHub (nom + description)
    for line in sh("gh repo list Turbo31150 --limit 100 2>/dev/null").splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1].strip():
            items.append(
                (
                    "GitHub",
                    parts[0].split("/")[-1],
                    f"Repo GitHub: {parts[0]} — {parts[1]}",
                )
            )

    # 2. Containers Docker (nom + image)
    for line in sh(
        "docker ps --format '{{.Names}}|{{.Image}}|{{.Status}}'"
    ).splitlines():
        p = line.split("|")
        if len(p) >= 2:
            items.append(
                (
                    "Containers",
                    p[0],
                    f"Container Docker: {p[0]} (image {p[1]}, {p[2] if len(p) > 2 else ''})",
                )
            )

    # 3. Documents markdown (titre + extrait)
    for path in sh("find docs -name '*.md' 2>/dev/null | head -40").splitlines():
        fp = os.path.join(ROOT, path)
        try:
            head = open(fp, encoding="utf-8", errors="ignore").read(1200)
        except Exception:
            continue
        title = next(
            (l.strip("# ").strip() for l in head.splitlines() if l.startswith("#")),
            os.path.basename(path),
        )
        items.append(
            (
                "Documents",
                os.path.basename(path),
                f"Document {path} — « {title} »\nExtrait:\n{head[:800]}",
            )
        )

    # 4. Bases SQL (schéma + comptes) — etoile.db + master
    for db, label in [
        ("/home/turbo/jarvis-cowork/etoile.db", "etoile"),
        (os.path.join(ROOT, "jarvis_master.db"), "jarvis_master"),
    ]:
        if not os.path.exists(db):
            continue
        tables = sh(
            f"sqlite3 '{db}' \"SELECT name FROM sqlite_master WHERE type='table' LIMIT 40;\""
        ).split()
        for t in tables:
            n = sh(f"sqlite3 '{db}' 'SELECT count(*) FROM {t};'") or "?"
            cols = sh(
                f"sqlite3 '{db}' 'PRAGMA table_info({t});' | cut -d'|' -f2 | tr '\\n' ',' "
            )
            items.append(
                (
                    "Bases SQL",
                    f"{label}.{t}",
                    f"Table SQL {label}.{t} ({n} lignes). Colonnes: {cols}",
                )
            )
    return items


# ---------------------------------------------------------------- transformation
def _fiche(item):
    domain, key, src = item
    slug = re.sub(r"[^a-z0-9]+", "-", f"{domain}-{key}".lower()).strip("-")[:60]
    fp = os.path.join(KNOW_DIR, f"ingest-{slug}.md")
    if os.path.exists(fp):
        return ("skip", key)
    while b.gpu_temp_max() >= 84:
        log("⏸️ pause thermique")
        time.sleep(60)
    prompt = (
        f"Transforme cette source du patrimoine JARVIS en fiche de connaissance Markdown française "
        f"(150-250 mots). Explique son RÔLE dans l'écosystème, ce qu'elle contient/fait, quand s'en servir, "
        f"et les liens avec le reste du cluster. Factuel, sans inventer de détails absents de la source.\n\n"
        f"SOURCE ({domain}) :\n{src}"
    )
    txt = b.gen(
        prompt,
        system="Tu cartographies l'infra JARVIS. Markdown concis, factuel.",
        timeout=120,
    )
    if not txt or len(txt) < 100:
        return ("fail", key)
    os.makedirs(KNOW_DIR, exist_ok=True)
    open(fp, "w", encoding="utf-8").write(
        f"# {domain} — {key}\n\n*Ingéré du patrimoine JARVIS*\n\n{txt}\n"
    )
    conn = b.db()
    conn.execute(
        "INSERT OR REPLACE INTO biblio_knowledge(domain,topic,title,content_md,backend,path) "
        "VALUES(?,?,?,?,?,?)",
        (
            f"patrimoine/{domain}",
            f"{domain}:{key}",
            key,
            txt,
            "ingest+" + b.LMS_MODEL,
            fp,
        ),
    )
    conn.commit()
    conn.close()
    return ("made", key)


def main():
    b.migrate()
    items = collect()
    log(
        f"collecté: {len(items)} sources internes "
        f"({sum(1 for i in items if i[0] == 'GitHub')} repos, "
        f"{sum(1 for i in items if i[0] == 'Containers')} containers, "
        f"{sum(1 for i in items if i[0] == 'Documents')} docs, "
        f"{sum(1 for i in items if i[0] == 'Bases SQL')} tables)"
    )
    made = skip = fail = 0
    with ThreadPoolExecutor(
        max_workers=2
    ) as ex:  # 2 workers, laisse le daemon respirer
        for status, key in ex.map(_fiche, items):
            if status == "made":
                made += 1
                log(f"  ✓ {key}")
            elif status == "skip":
                skip += 1
            else:
                fail += 1
    log(
        f"✅ ingestion: +{made} fiches patrimoine, {skip} déjà présentes, {fail} échecs"
    )


if __name__ == "__main__":
    main()
