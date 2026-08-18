"""Score qualité d'une fiche + journalisation des runs (règle autoreport JARVIS).
Score 0-100 : sources tracées (40) + densité de chiffres (40) + volume utile (20).
`feedback` reste NULL — rempli plus tard par Turbo ou la boucle task-feedback."""

import re
import sqlite3
from pathlib import Path

DEFAULT_DB = Path.home() / "jarvis/logs/jarvis_logs.db"


def score_fiche(fiche_path, sources_count):
    body = Path(fiche_path).read_text(errors="replace")
    s_sources = min(40, sources_count * 7)
    chiffres = len(re.findall(r"\d[\d\s%€$xk+,.]*", body))
    s_chiffres = min(40, chiffres * 2)
    s_volume = min(20, len(body) // 200)
    return min(100, s_sources + s_chiffres + s_volume)


def log_run(platform, sources, score, fiche, db_path=DEFAULT_DB):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("""CREATE TABLE IF NOT EXISTS content_perf_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP,
        platform TEXT, sources INTEGER, score INTEGER,
        fiche TEXT, feedback TEXT)""")
    con.execute(
        "INSERT INTO content_perf_runs (platform, sources, score, fiche) VALUES (?,?,?,?)",
        (platform, sources, score, str(fiche)),
    )
    con.commit()
    con.close()
