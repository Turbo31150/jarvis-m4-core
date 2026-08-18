#!/usr/bin/env python3
"""charger-blocs-postgres.py — Charge la bibliothèque vivante dans Postgres cmdlib.

Alimente deux tables du conteneur jv-infra-biblio-db :
  - holding_index  <- lib/BLOCS-INDEX.tsv  (bu=source, kind=danger, name=nom)
  - library_series <- series/*.sh          (name, type='serie', path, keywords)

Additif et idempotent : ON CONFLICT DO NOTHING, aucun TRUNCATE, aucun DDL.
La table `commands` n'est jamais touchée.

Le schéma de holding_index (bu, kind, name) n'offre pas de colonne d'accueil
pour la 4e colonne `bloc` du TSV : la commande elle-même reste dans le TSV.
"""

from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

TSV = Path("/home/pamerys/labo/bibliotheque/lib/BLOCS-INDEX.tsv")
SERIES_DIR = Path("/home/pamerys/labo/bibliotheque/series")
CONTAINER = os.environ.get("BIBLIO_CONTAINER", "jv-infra-biblio-db")
BATCH = 1000

DB = {
    "dbname": os.environ.get("BIBLIO_DB", "cmdlib"),
    "user": os.environ.get("BIBLIO_USER", "cmduser"),
    "password": os.environ.get("BIBLIO_PASSWORD", "cmdpass"),
    "port": int(os.environ.get("BIBLIO_PORT", "5432")),
    "connect_timeout": 10,
}

RE_SERIE = re.compile(r"^#\s*SERIE\s*:\s*(.+?)\s*$")


def container_host() -> str:
    """IP du conteneur Postgres — le port 5432 n'est pas publié sur l'hôte."""
    if os.environ.get("BIBLIO_HOST"):
        return os.environ["BIBLIO_HOST"]
    out = subprocess.run(
        [
            "docker",
            "inspect",
            "-f",
            "{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}",
            CONTAINER,
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    if not out:
        sys.exit(f"⛔ aucune IP réseau pour le conteneur {CONTAINER}")
    return out[0]


def clean(value: str) -> str:
    """Postgres refuse les octets NUL dans une colonne text."""
    return value.replace("\x00", "").strip()


def lire_blocs() -> tuple[list[tuple[str, str, str]], int, int, int]:
    """-> (lignes prêtes, lues, malformées, doublons internes)."""
    lues = malformees = doublons = 0
    vus: set[tuple[str, str]] = set()
    rows: list[tuple[str, str, str]] = []

    with TSV.open(encoding="utf-8", errors="replace") as fh:
        for num, ligne in enumerate(fh, start=1):
            ligne = ligne.rstrip("\n").rstrip("\r")
            if num == 1 and ligne.split("\t")[:1] == ["nom"]:
                continue  # entête
            if not ligne.strip():
                continue
            lues += 1
            champs = ligne.split("\t")
            if len(champs) != 4:
                malformees += 1
                continue
            nom, source, danger, _bloc = (clean(c) for c in champs)
            if not nom or not source:
                malformees += 1
                continue
            cle = (source, nom)
            if cle in vus:
                doublons += 1
                continue
            vus.add(cle)
            rows.append((source, danger or None, nom))

    return rows, lues, malformees, doublons


def mots_cles(chemin: Path) -> str | None:
    """Description tirée de l'en-tête `# SERIE: nom — description`."""
    try:
        with chemin.open(encoding="utf-8", errors="replace") as fh:
            for _ in range(8):
                ligne = fh.readline()
                if not ligne:
                    break
                m = RE_SERIE.match(ligne.strip())
                if m:
                    return clean(m.group(1))[:500]
    except OSError:
        pass
    return None


def lire_series() -> tuple[list[tuple[str, str, str, str | None]], int, int, int]:
    """-> (lignes prêtes, lues, malformées, doublons internes)."""
    lues = malformees = doublons = 0
    vus: set[str] = set()
    rows: list[tuple[str, str, str, str | None]] = []

    for chemin in sorted(glob.glob(str(SERIES_DIR / "*.sh"))):
        lues += 1
        p = Path(chemin)
        nom = clean(p.stem)
        if not nom:
            malformees += 1
            continue
        if nom in vus:
            doublons += 1
            continue
        vus.add(nom)
        rows.append((nom, "serie", str(p.resolve()), mots_cles(p)))

    return rows, lues, malformees, doublons


def inserer(cur, sql: str, rows: list[tuple]) -> int:
    insere = 0
    for i in range(0, len(rows), BATCH):
        lot = rows[i : i + BATCH]
        execute_values(cur, sql, lot, page_size=BATCH)
        insere += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
    return insere


def compte(cur, table: str) -> int:
    cur.execute(f"SELECT count(*) FROM {table}")
    return cur.fetchone()[0]


def main() -> int:
    if not TSV.is_file():
        sys.exit(f"⛔ TSV introuvable : {TSV}")
    if not SERIES_DIR.is_dir():
        sys.exit(f"⛔ dossier séries introuvable : {SERIES_DIR}")

    blocs, b_lues, b_mal, b_dup = lire_blocs()
    series, s_lues, s_mal, s_dup = lire_series()

    conn = psycopg2.connect(host=container_host(), **DB)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            avant_h = compte(cur, "holding_index")
            avant_s = compte(cur, "library_series")
            avant_c = compte(cur, "commands")

            n_h = inserer(
                cur,
                "INSERT INTO holding_index (bu, kind, name) VALUES %s "
                "ON CONFLICT (bu, name) DO NOTHING",
                blocs,
            )
            n_s = inserer(
                cur,
                "INSERT INTO library_series (name, type, path, keywords) VALUES %s "
                "ON CONFLICT (name) DO NOTHING",
                series,
            )

            apres_h = compte(cur, "holding_index")
            apres_s = compte(cur, "library_series")
            apres_c = compte(cur, "commands")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("═══ BILAN CHARGEMENT BIBLIOTHÈQUE → cmdlib ═══")
    print(f"Source blocs   : {TSV}")
    print(f"Source séries  : {SERIES_DIR}/*.sh")
    print()
    print("── holding_index (blocs) ──")
    print(f"  lues        : {b_lues}")
    print(f"  malformées  : {b_mal}   (colonnes ≠ 4 ou nom/source vide → ignorées)")
    print(f"  doublons    : {b_dup}   (même (source, nom) dans le TSV)")
    print(f"  candidates  : {len(blocs)}")
    print(f"  insérées    : {n_h}   (les autres existaient déjà)")
    print(f"  table       : {avant_h} → {apres_h}")
    print()
    print("── library_series (séries) ──")
    print(f"  lues        : {s_lues}")
    print(f"  malformées  : {s_mal}")
    print(f"  doublons    : {s_dup}")
    print(f"  candidates  : {len(series)}")
    print(f"  insérées    : {n_s}   (les autres existaient déjà)")
    print(f"  table       : {avant_s} → {apres_s}")
    print()
    print(f"── commands (non touchée) : {avant_c} → {apres_c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
