#!/usr/bin/env python3
"""Bibliothèque de transcription personnalisée — source unique de vérité.

Base SQLite ~/IA/Core/jarvis/db/jarvis_lexicon.db qui alimente DEUX niveaux :
  - amont  : hotwords + initial_prompt envoyés à Whisper (le modèle « entend » les bons mots)
  - aval   : corrections (apply_dictionary) + glossaire (relecture/traduction LLM)

0 token, lecture SQL avant tout calcul (cf protocole-sql-avant-compute), rechargeable
à chaud (cache sur mtime de la base), repli sur voice_dict.json si la base est absente.

Usage CLI :
  lexicon init                          crée la base + seed métier + import voice_dict.json
  lexicon add "AESH" --cat acteur --variants "a e s h,aiche"
  lexicon list [--cat civique]
  lexicon stats
  lexicon import-json [chemin]          importe voice_dict.json dans la base
  lexicon export-json [chemin]          régénère voice_dict.json depuis la base (fallback)
  lexicon hotwords | prompt | glossary  affiche ce qui est envoyé à Whisper/LLM
  lexicon mine                          propose des termes candidats depuis voice_logs/
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LEXICON_DB = Path.home() / "IA" / "Core" / "jarvis" / "db" / "jarvis_lexicon.db"
DICT_JSON = Path.home() / "jarvis" / "voice_dict.json"
VOICE_LOGS = Path.home() / "jarvis" / "voice_logs"

CATEGORIES = ("niveau", "acteur", "admin", "civique", "nom_propre", "general")

SCHEMA = """
CREATE TABLE IF NOT EXISTS lexicon (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  term TEXT NOT NULL,
  variants TEXT DEFAULT '[]',
  category TEXT,
  use_hotword INTEGER DEFAULT 1,
  use_prompt INTEGER DEFAULT 1,
  frequency INTEGER DEFAULT 0,
  source TEXT DEFAULT 'pamerys',
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  UNIQUE(term, category)
);
CREATE INDEX IF NOT EXISTS idx_lexicon_cat ON lexicon(category);
"""

# ── Seed métier curé (professeure des écoles + courriers député/pétitions) ──────
# (term, category, use_hotword, use_prompt, [variantes fautives fréquentes])
SEED = [
    # niveaux
    ("CP", "niveau", 1, 1, ["c p", "cé pé"]),
    ("CE1", "niveau", 1, 1, ["ce 1", "ce un", "cé un"]),
    ("CE2", "niveau", 1, 1, ["ce 2", "ce deux", "cé deux"]),
    ("CM1", "niveau", 1, 1, ["cm 1", "cé aime un"]),
    ("CM2", "niveau", 1, 1, ["cm 2", "cé aime deux"]),
    ("maternelle", "niveau", 0, 1, []),
    ("cycle 2", "niveau", 0, 1, ["cycle deux", "c2"]),
    ("cycle 3", "niveau", 0, 1, ["cycle trois", "c3"]),
    # acteurs
    ("AESH", "acteur", 1, 1, ["a e s h", "aiche", "a-e-s-h"]),
    ("ATSEM", "acteur", 1, 1, ["atsème", "at sem"]),
    ("RASED", "acteur", 1, 1, ["rasé", "razed"]),
    ("IEN", "acteur", 1, 1, ["i e n"]),
    ("DASEN", "acteur", 1, 1, ["da zen", "dassin"]),
    ("psychologue scolaire", "acteur", 0, 1, []),
    ("médecin scolaire", "acteur", 0, 1, []),
    # admin
    (
        "Éducation nationale",
        "admin",
        1,
        1,
        ["education nationale", "éducation nationale"],
    ),
    ("inspection académique", "admin", 0, 1, []),
    ("conseil d'école", "admin", 0, 1, ["conseil d ecole"]),
    ("socle commun", "admin", 0, 1, []),
    ("PRONOTE", "admin", 1, 1, ["pronote", "pro note"]),
    ("livret scolaire", "admin", 0, 1, []),
    ("PAI", "admin", 1, 1, ["p a i", "paille"]),
    ("PPS", "admin", 1, 1, ["p p s"]),
    ("PAP", "admin", 1, 1, ["p a p", "pape"]),
    ("REP+", "admin", 1, 1, ["rep plus", "rep +"]),
    ("différenciation", "admin", 0, 1, []),
    ("évaluation formative", "admin", 0, 1, []),
    ("parents-professeurs", "admin", 0, 1, ["par un professeur", "parent professeur"]),
    # civique (courriers au député / pétitions)
    ("député", "civique", 1, 1, ["le député"]),
    ("députée", "civique", 1, 1, ["la députée"]),
    ("circonscription", "civique", 1, 1, []),
    ("Assemblée nationale", "civique", 1, 1, ["assemblée nationale"]),
    ("pétition", "civique", 1, 1, []),
    ("motion", "civique", 0, 1, []),
    ("MDPH", "civique", 1, 1, ["m d p h", "em dé pé ache"]),
    ("CAF", "civique", 1, 1, ["c a f"]),
    ("services publics", "civique", 0, 1, []),
    # noms propres
    ("Pamerys", "nom_propre", 1, 1, ["paméris", "pamériss", "pamerisse"]),
    ("Whisper", "nom_propre", 1, 1, ["wisp", "wispeur", "whispeur"]),
    ("JARVIS", "nom_propre", 1, 1, ["jarviss", "jar vis"]),
]


# ── Accès base ─────────────────────────────────────────────────────────────────
def _connect():
    LEXICON_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(LEXICON_DB))
    conn.executescript(SCHEMA)
    return conn


def add_term(
    term,
    category="general",
    variants=None,
    use_hotword=1,
    use_prompt=1,
    source="pamerys",
    frequency=0,
):
    variants = variants or []
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO lexicon(term,variants,category,use_hotword,use_prompt,source,frequency) "
            "VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(term,category) DO UPDATE SET "
            "variants=excluded.variants, use_hotword=excluded.use_hotword, "
            "use_prompt=excluded.use_prompt, updated_at=datetime('now')",
            (
                term,
                json.dumps(variants, ensure_ascii=False),
                category,
                use_hotword,
                use_prompt,
                source,
                frequency,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _rows():
    if not LEXICON_DB.exists():
        return []
    conn = sqlite3.connect(str(LEXICON_DB))
    try:
        cur = conn.execute(
            "SELECT term,variants,category,use_hotword,use_prompt,frequency "
            "FROM lexicon ORDER BY frequency DESC, category, term"
        )
        return cur.fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()


# ── Cache hot-reload (clé = mtime de la base) ──────────────────────────────────
_cache = {"mtime": None, "rows": None}


def _cached_rows():
    try:
        mtime = LEXICON_DB.stat().st_mtime
    except FileNotFoundError:
        return None
    if _cache["mtime"] != mtime:
        _cache["rows"] = _rows()
        _cache["mtime"] = mtime
    return _cache["rows"]


# ── Générateurs (consommés par le widget) ──────────────────────────────────────
def build_hotwords(limit=80):
    """Liste des sigles/noms propres prioritaires envoyés à Whisper (amont)."""
    rows = _cached_rows()
    if not rows:
        return ""
    words = [r[0] for r in rows if r[3]]  # use_hotword
    return ", ".join(words[:limit])


def build_initial_prompt():
    """Phrase d'amorçage française qui contextualise le domaine pour Whisper (amont)."""
    rows = _cached_rows()
    if not rows:
        return ""
    terms = [r[0] for r in rows if r[4]]  # use_prompt
    if not terms:
        return ""
    return (
        "Contexte : enseignement primaire et courrier administratif. "
        "Vocabulaire : " + ", ".join(terms[:60]) + "."
    )


def build_corrections():
    """dict {variante|terme: terme} pour apply_dictionary (aval). Repli voice_dict.json."""
    rows = _cached_rows()
    out = {}
    if rows:
        for term, variants_json, *_ in rows:
            try:
                for v in json.loads(variants_json or "[]"):
                    if v:
                        out[v] = term
            except (json.JSONDecodeError, TypeError):
                pass
        if out:
            return out
    # Fallback : voice_dict.json
    try:
        data = json.loads(DICT_JSON.read_text(encoding="utf-8"))
        return dict(data.get("replacements", {}))
    except Exception:
        return out


def build_glossary(limit=40):
    """Glossaire court injecté dans le prompt LLM (relecture/traduction, aval)."""
    rows = _cached_rows()
    if not rows:
        return ""
    return ", ".join(r[0] for r in rows[:limit])


# ── Init / seed / import-export ────────────────────────────────────────────────
def cmd_init():
    conn = _connect()
    conn.close()
    for term, cat, hw, pr, variants in SEED:
        add_term(term, cat, variants, hw, pr, source="seed")
    n_json = cmd_import_json(verbose=False)
    print(f"✅ base créée : {LEXICON_DB}")
    print(
        f"   seed métier : {len(SEED)} termes · import voice_dict.json : {n_json} variantes"
    )
    cmd_stats()


def cmd_import_json(path=None, verbose=True):
    path = Path(path) if path else DICT_JSON
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        if verbose:
            print(f"⚠ import impossible ({e})")
        return 0
    reps = data.get("replacements", {})
    # Regrouper variantes par terme correct
    by_term = {}
    for variant, term in reps.items():
        if variant == term:
            continue
        by_term.setdefault(term, []).append(variant)
    n = 0
    for term, variants in by_term.items():
        # ne pas écraser une catégorie seed : insérer en 'general' seulement si absent
        existing = [r for r in _rows() if r[0] == term]
        if existing:
            continue
        add_term(term, "general", variants, 1, 1, source="voice_dict")
        n += len(variants)
    if verbose:
        print(f"✅ {n} variantes importées depuis {path}")
    return n


def cmd_export_json(path=None):
    path = Path(path) if path else DICT_JSON
    reps = {}
    for term, variants_json, *_ in _rows():
        try:
            for v in json.loads(variants_json or "[]"):
                reps[v] = term
        except (json.JSONDecodeError, TypeError):
            pass
    payload = {
        "_aide": "Fichier de FALLBACK régénéré depuis jarvis_lexicon.db (lexicon export-json). "
        "Éditer de préférence la base via 'lexicon add'.",
        "replacements": reps,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ {len(reps)} corrections exportées vers {path}")


def cmd_list(category=None):
    for term, variants_json, cat, hw, pr, freq in _rows():
        if category and cat != category:
            continue
        flags = ("H" if hw else "-") + ("P" if pr else "-")
        print(f"[{cat:10}] {flags} {term:28} ← {variants_json}")


def cmd_stats():
    rows = _rows()
    by_cat = {}
    hot = 0
    for term, _v, cat, hw, _pr, _f in rows:
        by_cat[cat] = by_cat.get(cat, 0) + 1
        hot += 1 if hw else 0
    print(f"📚 {len(rows)} termes · {hot} hotwords")
    for cat in CATEGORIES:
        if cat in by_cat:
            print(f"   {cat:12} {by_cat[cat]}")
    other = sum(v for k, v in by_cat.items() if k not in CATEGORIES)
    if other:
        print(f"   {'(autre)':12} {other}")


def cmd_mine():
    """Propose des termes candidats récurrents depuis les sessions, à valider à la main."""
    import re
    from collections import Counter

    known = {r[0].lower() for r in _rows()}
    for r in _rows():
        try:
            known |= {v.lower() for v in json.loads(r[1] or "[]")}
        except (json.JSONDecodeError, TypeError):
            pass
    counter = Counter()
    for f in sorted(VOICE_LOGS.glob("session_*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        entries = data if isinstance(data, list) else data.get("entries", [])
        for e in entries:
            txt = e.get("text", "") if isinstance(e, dict) else str(e)
            # Sigles majuscules + mots Capitalisés (noms propres potentiels)
            for w in re.findall(r"\b[A-ZÀ-Ÿ]{2,}\b|\b[A-ZÀ-Ÿ][a-zà-ÿ]{3,}\b", txt):
                if w.lower() not in known and w.lower() not in ("bonjour", "merci"):
                    counter[w] += 1
    cands = [(w, c) for w, c in counter.most_common(30) if c >= 2]
    if not cands:
        print("Aucun candidat récurrent (≥2) trouvé dans voice_logs/.")
        return
    print("Candidats (à ajouter via 'lexicon add' si pertinents) :")
    for w, c in cands:
        print(f"   {c}×  {w}")


def main():
    p = argparse.ArgumentParser(prog="lexicon")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("init")
    pa = sub.add_parser("add")
    pa.add_argument("term")
    pa.add_argument("--cat", default="general", choices=CATEGORIES)
    pa.add_argument("--variants", default="")
    pa.add_argument("--no-hotword", action="store_true")
    pl = sub.add_parser("list")
    pl.add_argument("--cat", default=None)
    sub.add_parser("stats")
    pi = sub.add_parser("import-json")
    pi.add_argument("path", nargs="?")
    pe = sub.add_parser("export-json")
    pe.add_argument("path", nargs="?")
    sub.add_parser("hotwords")
    sub.add_parser("prompt")
    sub.add_parser("glossary")
    sub.add_parser("mine")
    args = p.parse_args()

    if args.cmd == "init":
        cmd_init()
    elif args.cmd == "add":
        variants = [v.strip() for v in args.variants.split(",") if v.strip()]
        add_term(args.term, args.cat, variants, use_hotword=0 if args.no_hotword else 1)
        print(f"✅ ajouté : {args.term} ({args.cat}) ← {variants}")
    elif args.cmd == "list":
        cmd_list(args.cat)
    elif args.cmd == "stats":
        cmd_stats()
    elif args.cmd == "import-json":
        cmd_import_json(args.path)
    elif args.cmd == "export-json":
        cmd_export_json(args.path)
    elif args.cmd == "hotwords":
        print(build_hotwords())
    elif args.cmd == "prompt":
        print(build_initial_prompt())
    elif args.cmd == "glossary":
        print(build_glossary())
    elif args.cmd == "mine":
        cmd_mine()
    else:
        p.print_help()


if __name__ == "__main__":
    sys.exit(main())
