#!/usr/bin/env python3
"""bdqt-teach — apprendre une correction de transcription, effet IMMÉDIAT.

La post-correction (serveur Whisper + service :8790) lit la table `corrections`
à chaque requête → pas besoin de redémarrer. L'apprentissage s'accumule.

Usage:
  bdqt-teach "mauvais" "correct"        # mot ou phrase
  bdqt-teach --list [N]                 # voir les dernières corrections apprises
  bdqt-teach --del "mauvais"            # supprimer une correction
"""

import sys
import bdqt_core as core


def main():
    a = sys.argv[1:]
    core.ensure_schema()
    conn = core.get_conn()

    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    if a[0] == "--list":
        n = int(a[1]) if len(a) > 1 else 15
        rows = conn.execute(
            "SELECT source_text,target_text,category,ts FROM corrections "
            "ORDER BY id DESC LIMIT ?",
            (n,),
        ).fetchall()
        for r in rows:
            print(f"  {r['source_text']!r} -> {r['target_text']!r}  [{r['category']}]")
        return
    if a[0] == "--del":
        conn.execute(
            "DELETE FROM corrections WHERE lower(source_text)=?",
            (a[1].strip().lower(),),
        )
        conn.commit()
        print(f"supprimé: {a[1]!r}")
        return

    if len(a) < 2:
        print('Usage: bdqt-teach "mauvais" "correct"', file=sys.stderr)
        sys.exit(2)
    src, tgt = a[0].strip(), a[1].strip()
    conn.execute(
        "INSERT INTO corrections(source_text,target_text,domain,category,hit_count,confidence) "
        "VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(source_text,target_text) DO UPDATE SET hit_count=hit_count+1, confidence=0.95",
        (src, tgt, "general", "manual", 1, 0.95),
    )
    conn.commit()
    # vérif immédiate
    out, rules = core.correct(src, context="general", log=False)
    print(f"✅ appris : {src!r} -> {tgt!r}")
    print(f"   test   : {src!r} donne maintenant {out!r}")
    conn.close()


if __name__ == "__main__":
    main()
