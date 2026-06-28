#!/usr/bin/env python3
"""Retranscription : applique la post-correction BDQT à un transcript existant.
Usage:
  bdqt_retranscribe.py fichier.txt [--context tech] [--diff] [--inplace]
  echo "texte" | bdqt_retranscribe.py --context general
"""

import sys
import bdqt_core as core


def main():
    args = sys.argv[1:]
    context = "general"
    diff = "--diff" in args
    inplace = "--inplace" in args
    if "--context" in args:
        i = args.index("--context")
        context = args[i + 1]
        del args[i : i + 2]
    files = [a for a in args if not a.startswith("--")]

    if files:
        path = files[0]
        text = open(path, encoding="utf-8", errors="ignore").read()
    else:
        text = sys.stdin.read()
        path = None

    out, rules = core.correct(text, context=context, log=False)

    if diff or not files:
        sys.stderr.write(
            f"[retranscribe] {len(rules)} correction(s), contexte={context}\n"
        )
        for r in rules:
            sys.stderr.write(
                f"  · {r.get('type')}: {r.get('from')!r} → {r.get('to')!r}\n"
            )

    if inplace and path:
        open(path, "w", encoding="utf-8").write(out)
        print(f"[retranscribe] {path} mis à jour ({len(rules)} corrections)")
    else:
        print(out)


if __name__ == "__main__":
    main()
