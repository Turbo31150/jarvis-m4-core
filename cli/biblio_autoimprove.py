#!/usr/bin/env python3
"""biblio_autoimprove.py — Auto-amélioration de la Bibliothèque Vivante selon l'USAGE réel.

Le système apprend de ce que Turbo utilise et de ses échecs, puis oriente le daemon :
  1. RETRY  — remet les topics 'failed' en 'pending' (2ᵉ chance).
  2. BOOST  — les domaines des action_series les plus assemblées (usage_count) voient
              leurs topics montés en priorité → le daemon les traite d'abord.
  3. EXPAND — pour chaque domaine à fort usage, le LLM local (0-token) génère de
              nouveaux sujets ciblés → la bibliothèque grossit là où Turbo travaille.
  4. GAP    — détecte les catégories de commandes sous-représentées et les renforce.

Lançable seul (`--once`) ou via timer. 0 token (LM Studio local), idempotent.
"""

from __future__ import annotations
import sys
import sqlite3
import subprocess

sys.path.insert(0, "/home/turbo/jarvis/cli")
import biblio_filler as b

MASTER = "/home/pamerys/jarvis/jarvis_master.db"
PG = [
    "docker",
    "exec",
    "-i",
    "jv-infra-biblio-db",
    "psql",
    "-U",
    "cmduser",
    "-d",
    "cmdlib",
    "-tA",
]


def log(m):
    print(f"[auto-improve] {m}", flush=True)


def db():
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    c = sqlite3.connect(MASTER, timeout=120)
    c.execute("PRAGMA busy_timeout=120000")
    c.execute("PRAGMA journal_mode=WAL")
    return c


def retry_failed(c):
    n = c.execute(
        "UPDATE biblio_topics SET status='pending' WHERE status='failed'"
    ).rowcount
    c.commit()
    log(f"RETRY : {n} topics 'failed' remis en file")
    return n


def used_domains(c):
    """Domaines les plus sollicités = ceux des action_series assemblées (usage_count)."""
    rows = c.execute("""SELECT name, keywords, usage_count FROM action_series
                        WHERE usage_count > 0 ORDER BY usage_count DESC""").fetchall()
    # map nom de série -> domaine plausible via ses mots-clés (1er mot significatif)
    doms = []
    for name, _kw, uc in rows:
        # domaine = dernier mot du nom (ex "déployer stack docker" -> "docker")
        doms.append((name.split()[-1], uc))
    return doms


def boost(c, domains):
    boosted = 0
    for dom, uc in domains:
        r = c.execute(
            "UPDATE biblio_topics SET priority = min(priority + 2, 10) "
            "WHERE status='pending' AND lower(domain) LIKE ?",
            (f"%{dom.lower()}%",),
        )
        boosted += r.rowcount
    c.commit()
    log(f"BOOST : {boosted} topics montés en priorité (domaines les + utilisés)")
    return boosted


def expand_used(c, domains):
    """Génère (0-token) de nouveaux sujets ciblés sur les domaines à fort usage."""
    made = 0
    for dom, uc in domains[:3]:  # top-3 domaines sollicités
        existing = [
            r[0]
            for r in c.execute(
                "SELECT topic FROM biblio_topics WHERE lower(domain) LIKE ?",
                (f"%{dom.lower()}%",),
            ).fetchall()
        ]
        prompt = (
            f"Domaine technique très utilisé sur ce système : « {dom} ». "
            f"Sujets déjà couverts : {', '.join(existing[:20]) or 'aucun'}.\n"
            f"Propose 4 NOUVEAUX sujets concrets et avancés NON couverts. "
            f'Réponds UNIQUEMENT en JSON: [{{"kind":"command|knowledge","topic":"..."}}]'
        )
        txt = b.gen(prompt, system="Tu réponds uniquement en JSON valide.", timeout=90)
        data = b.extract_json(txt or "")
        if not isinstance(data, list):
            continue
        for it in data:
            try:
                kind = (
                    "command"
                    if str(it.get("kind", "")).startswith("command")
                    else "knowledge"
                )
                cur = c.execute(
                    "INSERT OR IGNORE INTO biblio_topics(kind,domain,topic,source,priority) "
                    "VALUES(?,?,?, 'auto-improve', 8)",
                    (kind, dom, str(it["topic"])[:200]),
                )
                made += cur.rowcount
            except Exception:
                continue
    c.commit()
    log(f"EXPAND : +{made} sujets générés sur les domaines sollicités")
    return made


def fill_gaps(c):
    """Catégories de commandes sous-représentées → topics de renforcement."""
    try:
        out = subprocess.run(
            PG + ["-c", "SELECT category, count(*) FROM commands GROUP BY category;"],
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout
    except Exception:
        return 0
    cats = {}
    for line in out.splitlines():
        p = line.split("|")
        if len(p) == 2 and p[1].strip().isdigit():
            cats[p[0]] = int(p[1])
    if not cats:
        return 0
    avg = sum(cats.values()) / len(cats)
    weak = [cat for cat, n in cats.items() if n < avg * 0.5][:4]
    made = 0
    for cat in weak:
        cur = c.execute(
            "INSERT OR IGNORE INTO biblio_topics(kind,domain,topic,source,priority) "
            "VALUES('command',?,?, 'auto-improve-gap', 7)",
            (cat, f"Commandes avancées supplémentaires — {cat}"),
        )
        made += cur.rowcount
    c.commit()
    log(
        f"GAP : +{made} topics de renforcement sur catégories faibles ({', '.join(weak) or 'aucune'})"
    )
    return made


def main():
    b.migrate()
    c = db()
    log("=== cycle d'auto-amélioration (0-token, selon usage) ===")
    retry_failed(c)
    doms = used_domains(c)
    if doms:
        log(
            f"domaines les + sollicités : {', '.join(f'{d}({u})' for d, u in doms[:5])}"
        )
        boost(c, doms)
        expand_used(c, doms)
    else:
        log(
            "aucun usage encore enregistré (assemble des séries via action_series pour guider l'apprentissage)"
        )
    fill_gaps(c)
    p = c.execute(
        "SELECT count(*) FROM biblio_topics WHERE status='pending'"
    ).fetchone()[0]
    c.close()
    log(f"✅ terminé — {p} topics en file, le daemon les traitera par priorité")


if __name__ == "__main__":
    main()
