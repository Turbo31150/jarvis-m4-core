#!/usr/bin/env python3
"""Mine les corrections RÉELLES (voix de l'utilisatrice) depuis flow.sqlite History :
aligne asrText (entendu) vs editedText/formattedText (corrigé), extrait les
substitutions de MOTS, agrège par fréquence, importe les fiables dans BDQT.

Filtre anti-bruit : ignore ponctuation/reformulation, ne garde que des
substitutions 1→1 ou 1→2 mots, alphabétiques, où la source n'est pas un mot
français ultra-courant (liste stop) — sauf si récurrent (≥2).
Usage: bdqt_mine_history.py [flow.sqlite] [--apply]
"""

import difflib
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from collections import Counter
import bdqt_core as core

DEFAULT = "/mnt/windows/Users/clair/AppData/Roaming/Wispr Flow/flow.sqlite"
STOP = set(
    "le la les un une des de du au aux et ou à a il elle je tu nous vous ils "
    "elles ce ça se sa son ses mon ma mes ton ta tes que qui quoi est sont "
    "pour par sur dans avec sans plus moins très tout tous toute toutes en y "
    "ne pas plus puis donc car mais or ni comme si oui non bien fait".split()
)
_W = re.compile(r"[a-zA-Zàâäéèêëïîôöùûüçœ'’-]+")


def words(s):
    return _W.findall((s or "").lower().replace("’", "'"))


def main():
    path = (
        sys.argv[1]
        if len(sys.argv) > 1 and not sys.argv[1].startswith("--")
        else DEFAULT
    )
    apply = "--apply" in sys.argv
    tmp = tempfile.mktemp(suffix=".sqlite")
    shutil.copy(path, tmp)
    for e in ("-wal", "-shm"):
        if os.path.exists(path + e):
            shutil.copy(path + e, tmp + e)
    c = sqlite3.connect(tmp)
    c.row_factory = sqlite3.Row

    subs = Counter()
    for r in c.execute(
        "SELECT asrText, editedText, formattedText FROM History "
        "WHERE COALESCE(asrText,'')<>''"
    ):
        asr = r["asrText"]
        tgt = r["editedText"] or r["formattedText"]
        if not tgt or tgt == asr:
            continue
        a, b = words(asr), words(tgt)
        sm = difflib.SequenceMatcher(None, a, b)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op != "replace":
                continue
            src = a[i1:i2]
            dst = b[j1:j2]
            # 1→1 ou 1→2 mots seulement
            if len(src) == 1 and 1 <= len(dst) <= 2:
                s = src[0]
                d = " ".join(dst)
                if s == d or len(s) < 3:
                    continue
                subs[(s, d)] += 1

    # candidats : récurrents (≥2) OU source non-stop et "inhabituelle"
    cands = []
    for (s, d), n in subs.most_common():
        if n >= 2 or (
            s not in STOP and d.replace(" ", "").isalpha() is not False and s.isalpha()
        ):
            cands.append((s, d, n))
    # garder fiables : récurrent OU source absente du français courant (heuristique stop)
    keep = [(s, d, n) for s, d, n in cands if n >= 2 or s not in STOP]

    print(
        f"=== {len(subs)} substitutions distinctes, {len(keep)} candidates retenues ==="
    )
    for s, d, n in keep[:40]:
        print(f"  ({n}x) {s!r} -> {d!r}")

    if apply and keep:
        core.ensure_schema()
        dst = core.get_conn()
        nc = 0
        for s, d, n in keep:
            if n < 2 and len(s) < 5:  # prudence : 1 occurrence + mot court = on saute
                continue
            dst.execute(
                "INSERT INTO corrections(source_text,target_text,domain,category,hit_count,confidence) "
                "VALUES(?,?,?,?,?,?) ON CONFLICT(source_text,target_text) "
                "DO UPDATE SET hit_count=corrections.hit_count+excluded.hit_count",
                (s, d, "general", "history_mined", n, min(0.95, 0.6 + n * 0.1)),
            )
            nc += 1
        dst.commit()
        print(
            f"\n[apply] {nc} corrections importées | total="
            f"{dst.execute('SELECT COUNT(*) FROM corrections').fetchone()[0]}"
        )
        dst.close()
    elif not apply:
        print("\n(dry-run — relancer avec --apply pour importer)")
    c.close()
    for f in (tmp, tmp + "-wal", tmp + "-shm"):
        try:
            os.remove(f)
        except OSError:
            pass


if __name__ == "__main__":
    main()
