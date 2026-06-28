#!/usr/bin/env python3
"""Génère les prompt_snippets Whisper (initial_prompt) depuis le lexique.
Un snippet 'general' (top termes tous domaines) + un par domaine.
Borné en longueur (~ MAX_CHARS) car faster-whisper limite l'initial_prompt.
"""

import bdqt_core as core

MAX_CHARS = 800  # ~200 tokens
CONTEXTS = ["general", "mairie", "tech", "ecole", "civique"]


def build_text(conn, context):
    if context == "general":
        rows = conn.execute(
            "SELECT term FROM lexicon ORDER BY weight DESC, length(term) ASC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT term FROM lexicon WHERE domain=? ORDER BY weight DESC", (context,)
        ).fetchall()
    terms, acc = [], 0
    for r in rows:
        t = r["term"]
        if acc + len(t) + 2 > MAX_CHARS:
            break
        terms.append(t)
        acc += len(t) + 2
    if not terms:
        return None
    # phrase de contexte naturelle (aide le biais Whisper en FR)
    return "Vocabulaire courant : " + ", ".join(terms) + "."


def main():
    core.ensure_schema()
    conn = core.get_conn()
    for ctx in CONTEXTS:
        txt = build_text(conn, ctx)
        if not txt:
            continue
        conn.execute(
            "INSERT INTO prompt_snippets(context,text,active) VALUES(?,?,1) "
            "ON CONFLICT(context) DO UPDATE SET text=excluded.text, active=1, ts=datetime('now')",
            (ctx, txt),
        )
        print(f"[prompt] {ctx}: {len(txt)} car. — {txt[:70]}…")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
