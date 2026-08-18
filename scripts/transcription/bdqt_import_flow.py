#!/usr/bin/env python3
"""Importe le Dictionary de l'appli OFFICIELLE Wispr Flow (flow.sqlite Windows)
dans BDQT. Source par défaut = la base live sur le disque Windows monté.
  phrase+replacement -> corrections   (ex. "mail pro" -> email, "Mont Laure"->Montlaur)
  phrase seule       -> lexicon       (noms propres : Domingues, Alkymia, Labège…)
Rejouable (ON CONFLICT). Usage: bdqt_import_flow.py [chemin_flow.sqlite]
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import bdqt_core as core

DEFAULT = "/mnt/windows/Users/clair/AppData/Roaming/Wispr Flow/flow.sqlite"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    if not os.path.exists(path):
        print(f"[flow] introuvable: {path}", file=sys.stderr)
        sys.exit(1)
    # copie (la base est live avec WAL) pour lecture sûre
    tmp = tempfile.mktemp(suffix=".sqlite")
    shutil.copy(path, tmp)
    for ext in ("-wal", "-shm"):
        if os.path.exists(path + ext):
            shutil.copy(path + ext, tmp + ext)
    src = sqlite3.connect(tmp)
    src.row_factory = sqlite3.Row
    core.ensure_schema()
    dst = core.get_conn()
    nc = nl = 0
    for r in src.execute(
        "SELECT phrase, replacement FROM Dictionary WHERE COALESCE(isDeleted,0)=0"
    ):
        ph = (r["phrase"] or "").strip()
        rep = (r["replacement"] or "").strip()
        if not ph:
            continue
        if rep:
            dst.execute(
                "INSERT INTO corrections(source_text,target_text,domain,category,hit_count,confidence) "
                "VALUES(?,?,?,?,?,?) ON CONFLICT(source_text,target_text) "
                "DO UPDATE SET confidence=0.95, category=excluded.category",
                (ph, rep, "general", "wispr_flow", 1, 0.95),
            )
            nc += 1
            term = rep
        else:
            term = ph
        dst.execute(
            "INSERT OR IGNORE INTO lexicon(term,domain,phonetic_key,weight,in_prompt,source) "
            "VALUES(?,?,?,?,?,?)",
            (
                term,
                "nom_propre",
                core.phonetic_key(term.replace(" ", "")),
                4,
                0,
                "wispr_flow",
            ),
        )
        nl += 1
    dst.commit()
    print(
        f"[flow] importé: {nc} corrections, {nl} termes | "
        f"totaux corrections={dst.execute('SELECT COUNT(*) FROM corrections').fetchone()[0]} "
        f"lexicon={dst.execute('SELECT COUNT(*) FROM lexicon').fetchone()[0]}"
    )
    src.close()
    dst.close()
    for f in (tmp, tmp + "-wal", tmp + "-shm"):
        try:
            os.remove(f)
        except OSError:
            pass


if __name__ == "__main__":
    main()
