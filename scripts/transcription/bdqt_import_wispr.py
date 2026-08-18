#!/usr/bin/env python3
"""Importe l'apprentissage Wispr Flow (export Windows) dans BDQT.

  snippets            -> corrections (phrase -> replacement)   ex. "mail pro" -> email
  vocabulaire[+repl]  -> corrections (mauvaise graphie -> bonne) ex. "mont laure"->"Montlaur"
  vocabulaire[sans]   -> lexicon (mots/noms propres perso)      ex. Domingues, Alkymia
  raccourcis          -> ignorés (config clavier de l'appli, pas de la transcription)

Usage: bdqt_import_wispr.py [chemin_export.json]
Défaut: /mnt/windows/Users/clair/SymbioseVoice/wispr-export.json
"""

import json
import sys
import bdqt_core as core

DEFAULT = "/mnt/windows/Users/clair/SymbioseVoice/wispr-export.json"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    d = json.load(open(path, encoding="utf-8", errors="ignore"))
    core.ensure_schema()
    conn = core.get_conn()
    nc = nl = 0

    def add_corr(src, tgt, cat):
        nonlocal nc
        if not src or not tgt:
            return
        conn.execute(
            "INSERT INTO corrections(source_text,target_text,domain,category,hit_count,confidence) "
            "VALUES(?,?,?,?,?,?) ON CONFLICT(source_text,target_text) "
            "DO UPDATE SET confidence=0.95, category=excluded.category",
            (src.strip(), tgt.strip(), "general", cat, 1, 0.95),
        )
        nc += 1

    def add_lex(term, cat):
        nonlocal nl
        term = (term or "").strip()
        if not term:
            return
        pk = core.phonetic_key(term.replace(" ", ""))
        conn.execute(
            "INSERT OR IGNORE INTO lexicon(term,domain,phonetic_key,weight,in_prompt,source) "
            "VALUES(?,?,?,?,?,?)",
            (term, "nom_propre", pk, 4, 0, "wispr"),
        )
        nl += 1

    for s in d.get("snippets", []):
        add_corr(s.get("phrase"), s.get("replacement"), "wispr_snippet")
    for v in d.get("vocabulaire", []):
        ph, rep = v.get("phrase"), v.get("replacement")
        if rep:
            add_corr(ph, rep, "wispr_vocab")
            add_lex(rep, "wispr")
        else:
            add_lex(ph, "wispr")

    conn.commit()
    print(f"[wispr] importé : {nc} corrections, {nl} termes lexique")
    print(
        f"  total corrections={conn.execute('SELECT COUNT(*) FROM corrections').fetchone()[0]}"
        f" lexicon={conn.execute('SELECT COUNT(*) FROM lexicon').fetchone()[0]}"
    )
    conn.close()


if __name__ == "__main__":
    main()
