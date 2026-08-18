#!/usr/bin/env python3
"""board-multi — plusieurs boards, groupes, tâches et super-assistants.

Le board d'origine tient dans quatre tables : domains -> experts, queries -> answers.
Un seul espace, pas de regroupement, pas de file de travail, pas d'échelon au-dessus
de l'expert. Ce module ajoute cette couche SANS toucher aux tables existantes :
la migration est strictement additive et idempotente.

    boards          un espace de travail (plusieurs boards coexistent)
      board_domaines  N-N : un domaine peut servir plusieurs boards
    groupes         un sous-ensemble d'un board (une équipe, un chantier)
      groupe_membres  experts et assistants d'un groupe
    assistants      super-assistant : l'échelon au-dessus de l'expert, il pilote
                    un groupe et rend l'arbitrage
    taches          file de travail rattachée à un board (et souvent un groupe)
    seances         une table ronde : question posée à un board, tracée

Sous-commandes :
    migrer                          crée les tables (idempotent)
    board list|creer|montrer        gestion des boards
    groupe list|creer|ajouter       gestion des groupes et de leurs membres
    assistant list|creer            gestion des super-assistants
    tache list|creer|statut         file de travail
    seance creer|list               tables rondes tracées
    etat                            vue d'ensemble
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import uuid

DB = os.path.expanduser("~/jarvis/databases/board.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS boards (
    id           TEXT PRIMARY KEY,
    nom          TEXT NOT NULL UNIQUE,
    description  TEXT,
    visibilite   TEXT NOT NULL DEFAULT 'prive',   -- prive | lan | public
    cree_le      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS board_domaines (
    board_id   TEXT NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    domain_id  TEXT NOT NULL,
    PRIMARY KEY (board_id, domain_id)
);

CREATE TABLE IF NOT EXISTS groupes (
    id        TEXT PRIMARY KEY,
    board_id  TEXT NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    nom       TEXT NOT NULL,
    objectif  TEXT,
    cree_le   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (board_id, nom)
);

CREATE TABLE IF NOT EXISTS assistants (
    id        TEXT PRIMARY KEY,
    board_id  TEXT REFERENCES boards(id) ON DELETE SET NULL,
    nom       TEXT NOT NULL UNIQUE,
    role      TEXT NOT NULL,
    consigne  TEXT,                                -- prompt systeme
    model     TEXT,
    backend   TEXT,                                -- hub:18800 | m6 | ollama
    rang      INTEGER NOT NULL DEFAULT 1,          -- 1 = pilote, 2 = second
    cree_le   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS groupe_membres (
    groupe_id    TEXT NOT NULL REFERENCES groupes(id) ON DELETE CASCADE,
    membre_type  TEXT NOT NULL,                    -- expert | assistant
    membre_id    TEXT NOT NULL,
    PRIMARY KEY (groupe_id, membre_type, membre_id)
);

CREATE TABLE IF NOT EXISTS taches (
    id         TEXT PRIMARY KEY,
    board_id   TEXT NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    groupe_id  TEXT REFERENCES groupes(id) ON DELETE SET NULL,
    titre      TEXT NOT NULL,
    detail     TEXT,
    statut     TEXT NOT NULL DEFAULT 'a_faire',    -- a_faire | en_cours | fait | bloque
    priorite   INTEGER NOT NULL DEFAULT 2,         -- 1 haute .. 3 basse
    assignee_type TEXT,                            -- expert | assistant
    assignee_id   TEXT,
    cree_le    TEXT NOT NULL DEFAULT (datetime('now')),
    maj_le     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS seances (
    id        TEXT PRIMARY KEY,
    board_id  TEXT NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    groupe_id TEXT REFERENCES groupes(id) ON DELETE SET NULL,
    question  TEXT NOT NULL,
    mode      TEXT NOT NULL DEFAULT 'consensus',   -- consensus | debat | arbitrage
    statut    TEXT NOT NULL DEFAULT 'ouverte',     -- ouverte | close
    query_id  TEXT,                                -- lien vers queries(id) du board d'origine
    cree_le   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_taches_board  ON taches(board_id, statut);
CREATE INDEX IF NOT EXISTS idx_groupes_board ON groupes(board_id);
CREATE INDEX IF NOT EXISTS idx_seances_board ON seances(board_id);
"""


def cx() -> sqlite3.Connection:
    c = sqlite3.connect(DB, timeout=60)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def ident(prefixe: str) -> str:
    return f"{prefixe}_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------- migration
def cmd_migrer(_a) -> int:
    c = cx()
    c.executescript(SCHEMA)
    c.commit()
    tables = [r[0] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
        "('boards','board_domaines','groupes','assistants','groupe_membres','taches','seances')"
    )]
    print(f"migration OK — {len(tables)}/7 tables : {', '.join(sorted(tables))}")

    # amorçage : un board par defaut reprenant tous les domaines existants
    if not c.execute("SELECT 1 FROM boards LIMIT 1").fetchone():
        bid = ident("brd")
        c.execute(
            "INSERT INTO boards (id,nom,description,visibilite) VALUES (?,?,?,?)",
            (bid, "principal", "Board historique — reprend les 18 domaines d'origine", "lan"),
        )
        doms = [r[0] for r in c.execute("SELECT id FROM domains")]
        c.executemany(
            "INSERT OR IGNORE INTO board_domaines (board_id,domain_id) VALUES (?,?)",
            [(bid, d) for d in doms],
        )
        c.commit()
        print(f"board 'principal' cree ({bid}) avec {len(doms)} domaines rattaches")
    return 0


# ---------------------------------------------------------------- boards
def cmd_board(a) -> int:
    c = cx()
    if a.action == "list":
        for r in c.execute(
            "SELECT b.id,b.nom,b.visibilite,"
            " (SELECT count(*) FROM board_domaines d WHERE d.board_id=b.id) nd,"
            " (SELECT count(*) FROM groupes g WHERE g.board_id=b.id) ng,"
            " (SELECT count(*) FROM taches t WHERE t.board_id=b.id AND t.statut!='fait') nt"
            " FROM boards b ORDER BY b.nom"
        ):
            print(f"{r['nom']:22s} {r['visibilite']:7s} {r['nd']:3d} domaines "
                  f"{r['ng']:2d} groupes {r['nt']:3d} taches ouvertes   {r['id']}")
        return 0
    if a.action == "creer":
        bid = ident("brd")
        c.execute("INSERT INTO boards (id,nom,description,visibilite) VALUES (?,?,?,?)",
                  (bid, a.nom, a.description or "", a.visibilite))
        for d in (a.domaines or "").split(",") if a.domaines else []:
            if d.strip():
                c.execute("INSERT OR IGNORE INTO board_domaines VALUES (?,?)", (bid, d.strip()))
        c.commit()
        print(f"board cree : {a.nom} ({bid})")
        return 0
    if a.action == "montrer":
        b = c.execute("SELECT * FROM boards WHERE nom=? OR id=?", (a.nom, a.nom)).fetchone()
        if not b:
            print("board introuvable", file=sys.stderr)
            return 2
        print(f"# {b['nom']}  ({b['id']}, {b['visibilite']})")
        print(f"  {b['description'] or ''}")
        doms = [r[0] for r in c.execute(
            "SELECT domain_id FROM board_domaines WHERE board_id=?", (b["id"],))]
        print(f"  domaines ({len(doms)}) : {', '.join(doms[:12])}{' …' if len(doms) > 12 else ''}")
        for g in c.execute("SELECT * FROM groupes WHERE board_id=?", (b["id"],)):
            n = c.execute("SELECT count(*) FROM groupe_membres WHERE groupe_id=?",
                          (g["id"],)).fetchone()[0]
            print(f"  groupe {g['nom']:20s} {n} membre(s) — {g['objectif'] or ''}")
        return 0
    return 1


# ---------------------------------------------------------------- groupes
def cmd_groupe(a) -> int:
    c = cx()
    if a.action == "list":
        for r in c.execute(
            "SELECT g.id,g.nom,g.objectif,b.nom bnom,"
            " (SELECT count(*) FROM groupe_membres m WHERE m.groupe_id=g.id) n"
            " FROM groupes g JOIN boards b ON b.id=g.board_id ORDER BY b.nom,g.nom"
        ):
            print(f"[{r['bnom']:14s}] {r['nom']:20s} {r['n']:2d} membre(s)  {r['objectif'] or ''}")
        return 0
    if a.action == "creer":
        b = c.execute("SELECT id FROM boards WHERE nom=? OR id=?", (a.board, a.board)).fetchone()
        if not b:
            print("board introuvable", file=sys.stderr)
            return 2
        gid = ident("grp")
        c.execute("INSERT INTO groupes (id,board_id,nom,objectif) VALUES (?,?,?,?)",
                  (gid, b["id"], a.nom, a.objectif or ""))
        c.commit()
        print(f"groupe cree : {a.nom} ({gid})")
        return 0
    if a.action == "ajouter":
        g = c.execute("SELECT id FROM groupes WHERE nom=? OR id=?", (a.groupe, a.groupe)).fetchone()
        if not g:
            print("groupe introuvable", file=sys.stderr)
            return 2
        for m in a.membres.split(","):
            m = m.strip()
            if not m:
                continue
            typ = "assistant" if c.execute(
                "SELECT 1 FROM assistants WHERE id=? OR nom=?", (m, m)).fetchone() else "expert"
            reel = c.execute(
                f"SELECT id FROM {'assistants' if typ=='assistant' else 'experts'} "
                f"WHERE id=? OR {'nom' if typ=='assistant' else 'display_name'}=?",
                (m, m)).fetchone()
            if not reel:
                print(f"  ignore (inconnu) : {m}")
                continue
            c.execute("INSERT OR IGNORE INTO groupe_membres VALUES (?,?,?)",
                      (g["id"], typ, reel["id"]))
            print(f"  + {typ} {m}")
        c.commit()
        return 0
    return 1


# ---------------------------------------------------------------- assistants
def cmd_assistant(a) -> int:
    c = cx()
    if a.action == "list":
        for r in c.execute(
            "SELECT a.*, b.nom bnom FROM assistants a "
            "LEFT JOIN boards b ON b.id=a.board_id ORDER BY a.rang, a.nom"
        ):
            print(f"rang {r['rang']}  {r['nom']:22s} [{r['bnom'] or '-':14s}] "
                  f"{r['role']:28s} {r['backend'] or ''} {r['model'] or ''}")
        return 0
    if a.action == "creer":
        bid = None
        if a.board:
            b = c.execute("SELECT id FROM boards WHERE nom=? OR id=?", (a.board, a.board)).fetchone()
            bid = b["id"] if b else None
        aid = ident("ast")
        c.execute(
            "INSERT INTO assistants (id,board_id,nom,role,consigne,model,backend,rang)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (aid, bid, a.nom, a.role, a.consigne or "", a.model or "", a.backend or "", a.rang),
        )
        c.commit()
        print(f"assistant cree : {a.nom} ({aid}) rang {a.rang}")
        return 0
    return 1


# ---------------------------------------------------------------- taches
def cmd_tache(a) -> int:
    c = cx()
    if a.action == "list":
        q = ("SELECT t.*, b.nom bnom, g.nom gnom FROM taches t "
             "JOIN boards b ON b.id=t.board_id "
             "LEFT JOIN groupes g ON g.id=t.groupe_id WHERE 1=1")
        p = []
        if a.board:
            q += " AND (b.nom=? OR b.id=?)"; p += [a.board, a.board]
        if a.statut:
            q += " AND t.statut=?"; p.append(a.statut)
        q += " ORDER BY t.priorite, t.cree_le"
        for r in c.execute(q, p):
            print(f"P{r['priorite']} {r['statut']:9s} [{r['bnom']:14s}/{r['gnom'] or '-':14s}] "
                  f"{r['titre'][:60]:60s} {r['id']}")
        return 0
    if a.action == "creer":
        b = c.execute("SELECT id FROM boards WHERE nom=? OR id=?", (a.board, a.board)).fetchone()
        if not b:
            print("board introuvable", file=sys.stderr)
            return 2
        gid = None
        if a.groupe:
            g = c.execute("SELECT id FROM groupes WHERE nom=? OR id=?",
                          (a.groupe, a.groupe)).fetchone()
            gid = g["id"] if g else None
        tid = ident("tch")
        c.execute(
            "INSERT INTO taches (id,board_id,groupe_id,titre,detail,priorite) VALUES (?,?,?,?,?,?)",
            (tid, b["id"], gid, a.titre, a.detail or "", a.priorite),
        )
        c.commit()
        print(f"tache creee : {a.titre} ({tid})")
        return 0
    if a.action == "statut":
        c.execute("UPDATE taches SET statut=?, maj_le=datetime('now') WHERE id=?",
                  (a.valeur, a.id))
        c.commit()
        print(f"tache {a.id} -> {a.valeur}")
        return 0
    return 1


# ---------------------------------------------------------------- seances
def cmd_seance(a) -> int:
    c = cx()
    if a.action == "list":
        for r in c.execute(
            "SELECT s.*, b.nom bnom FROM seances s JOIN boards b ON b.id=s.board_id "
            "ORDER BY s.cree_le DESC LIMIT 40"
        ):
            print(f"{r['cree_le']} [{r['bnom']:14s}] {r['mode']:10s} {r['statut']:7s} "
                  f"{r['question'][:70]}")
        return 0
    if a.action == "creer":
        b = c.execute("SELECT id FROM boards WHERE nom=? OR id=?", (a.board, a.board)).fetchone()
        if not b:
            print("board introuvable", file=sys.stderr)
            return 2
        sid = ident("sea")
        c.execute("INSERT INTO seances (id,board_id,question,mode) VALUES (?,?,?,?)",
                  (sid, b["id"], a.question, a.mode))
        c.commit()
        print(f"seance ouverte : {sid}")
        return 0
    return 1


# ---------------------------------------------------------------- etat
def cmd_etat(_a) -> int:
    c = cx()
    def n(t):
        try:
            return c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        except sqlite3.OperationalError:
            return "-"
    print("=== BOARD MULTI — etat ===")
    print(f"  boards      {n('boards'):>7}")
    print(f"  groupes     {n('groupes'):>7}")
    print(f"  assistants  {n('assistants'):>7}")
    print(f"  taches      {n('taches'):>7}")
    print(f"  seances     {n('seances'):>7}")
    print("--- socle d'origine ---")
    for t in ("domains", "experts", "sources", "chunks", "queries", "answers"):
        print(f"  {t:11s} {n(t):>7}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="board-multi")
    sp = p.add_subparsers(dest="cmd", required=True)

    sp.add_parser("migrer").set_defaults(fn=cmd_migrer)
    sp.add_parser("etat").set_defaults(fn=cmd_etat)

    b = sp.add_parser("board"); b.add_argument("action", choices=["list", "creer", "montrer"])
    b.add_argument("nom", nargs="?", default="")
    b.add_argument("--description"); b.add_argument("--domaines")
    b.add_argument("--visibilite", default="prive", choices=["prive", "lan", "public"])
    b.set_defaults(fn=cmd_board)

    g = sp.add_parser("groupe"); g.add_argument("action", choices=["list", "creer", "ajouter"])
    g.add_argument("nom", nargs="?", default=""); g.add_argument("--board", default="")
    g.add_argument("--objectif"); g.add_argument("--groupe", default=""); g.add_argument("--membres", default="")
    g.set_defaults(fn=cmd_groupe)

    a_ = sp.add_parser("assistant"); a_.add_argument("action", choices=["list", "creer"])
    a_.add_argument("nom", nargs="?", default=""); a_.add_argument("--board", default="")
    a_.add_argument("--role", default="pilote"); a_.add_argument("--consigne")
    a_.add_argument("--model"); a_.add_argument("--backend"); a_.add_argument("--rang", type=int, default=1)
    a_.set_defaults(fn=cmd_assistant)

    t = sp.add_parser("tache"); t.add_argument("action", choices=["list", "creer", "statut"])
    t.add_argument("titre", nargs="?", default=""); t.add_argument("--board", default="")
    t.add_argument("--groupe"); t.add_argument("--detail"); t.add_argument("--priorite", type=int, default=2)
    t.add_argument("--statut"); t.add_argument("--id"); t.add_argument("--valeur")
    t.set_defaults(fn=cmd_tache)

    s = sp.add_parser("seance"); s.add_argument("action", choices=["list", "creer"])
    s.add_argument("question", nargs="?", default=""); s.add_argument("--board", default="")
    s.add_argument("--mode", default="consensus", choices=["consensus", "debat", "arbitrage"])
    s.set_defaults(fn=cmd_seance)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
