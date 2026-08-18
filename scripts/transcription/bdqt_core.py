#!/usr/bin/env python3
"""BDQT — Base de Données Qualité Transcription : module cœur partagé.

Zéro dépendance externe (pur Python). Fournit :
  - DB_PATH + ensure_schema()/get_conn()
  - strip_accents(), phonetic_key()  : clé phonétique FR pour matching flou
  - levenshtein()                    : distance d'édition bornée
  - correct(text, context)           : post-correction (exacte + phonétique)

Conçu pour être importé par les scripts bdqt_*.py et par le pipeline Whisper
(ptt_daemon / jarvis_dictation_mode). Non-régression : si la base est absente,
correct() renvoie le texte inchangé.
"""

import os
import re
import sqlite3
import json

DB_PATH = os.environ.get(
    "BDQT_DB",
    os.path.expanduser("~/IA/Core/jarvis/db/transcription_quality.db"),
)

# ---------------------------------------------------------------- phonétique FR
_ACCENTS = str.maketrans(
    "àâäáãåçéèêëíìîïñóòôöõúùûüýÿœæ",
    "aaaaaaceeeeiiiinooooouuuuyyoa",  # œ→o, æ→a (approximation)
)


def strip_accents(s: str) -> str:
    return s.lower().translate(_ACCENTS)


# Mots FR fréquents JAMAIS corrigés en flou : ils entrent souvent en collision
# phonétique avec des acronymes/noms propres du lexique (ex. "plus"~"PLU",
# "sont"~"SNT", "cette"~"CETE"). Sans cette garde, la post-correction corrompt
# la dictée normale. (Complète les tests négatifs de bdqt_validate.py.)
COMMON_FR = frozenset(
    """
    plus moins tout tous toute toutes rien bien mal très trop peu assez encore
    aussi alors donc mais comme dans pour avec sans sous sur entre vers chez
    cette cet ces mon ton son mes tes ses nos vos leur leurs notre votre
    sont était étaient sera seront faire fait dit dire avoir être aller venir
    nous vous elle elles ils lui eux même autre autres aucun chaque quelque
    quelques beaucoup certains plusieurs quand parce pendant avant après depuis
    ensuite enfin ici déjà jamais toujours souvent parfois vraiment surtout
    chose choses temps fois jour jours part parts deux trois quatre cinq
    petit grand bon bonne mieux pire premier dernier prochain celui celle ceux
    """.split()
)


def phonetic_key(word: str) -> str:
    """Clé phonétique française simplifiée (pour rapprocher 'biotech'~'bio-tech',
    'sk' ~ 'sc', etc.). Heuristique, pas une norme — suffisant pour fuzzy match."""
    w = strip_accents(word)
    w = re.sub(r"[^a-z]", "", w)
    if not w:
        return ""
    # digrammes / règles FR (ordre important)
    w = w.replace("eau", "o").replace("au", "o")
    w = w.replace("ou", "u")
    w = w.replace("ph", "f")
    w = w.replace("ch", "X")  # son "ch"
    w = w.replace("gn", "N")  # son "gn"
    w = w.replace("qu", "k").replace("q", "k")
    w = w.replace("gu", "g")
    w = re.sub(r"c([eiy])", r"s\1", w)  # c doux
    w = w.replace("c", "k")  # c dur
    w = w.replace("ç", "s")
    w = w.replace("sc", "sk")
    w = w.replace("y", "i")
    w = w.replace("w", "v")
    w = w.replace("h", "")
    w = w.replace("x", "ks") if False else w  # garder X (ch) ; ne pas toucher
    # voyelles nasales grossières
    w = re.sub(r"(on|om)", "5", w)
    w = re.sub(r"(an|am|en|em)", "4", w)
    w = re.sub(r"(in|im|ain|ein)", "1", w)
    # supprime lettres muettes finales courantes
    w = re.sub(r"[stdxpz]$", "", w)
    # collapse doublons
    w = re.sub(r"(.)\1+", r"\1", w)
    return w


def levenshtein(a: str, b: str, max_d: int = 99) -> int:
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if abs(la - lb) > max_d:
        return max_d + 1
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        best = cur[0]
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            best = min(best, cur[j])
        if best > max_d:
            return max_d + 1
        prev = cur
    return prev[lb]


# ----------------------------------------------------------------------- schema
SCHEMA = """
CREATE TABLE IF NOT EXISTS lexicon (
  id INTEGER PRIMARY KEY,
  term TEXT NOT NULL,
  domain TEXT NOT NULL,            -- mairie|tech|ecole|nom_propre
  aliases TEXT DEFAULT '[]',       -- json list
  phonetic_key TEXT,
  weight INTEGER DEFAULT 1,
  in_prompt INTEGER DEFAULT 0,
  source TEXT,
  ts TEXT DEFAULT (datetime('now')),
  UNIQUE(term, domain)
);
CREATE INDEX IF NOT EXISTS idx_lex_phon ON lexicon(phonetic_key);
CREATE INDEX IF NOT EXISTS idx_lex_dom  ON lexicon(domain);

CREATE TABLE IF NOT EXISTS corrections (
  id INTEGER PRIMARY KEY,
  source_text TEXT NOT NULL,
  target_text TEXT NOT NULL,
  domain TEXT DEFAULT 'general',
  category TEXT,
  hit_count INTEGER DEFAULT 0,
  confidence REAL DEFAULT 0.5,
  ts TEXT DEFAULT (datetime('now')),
  UNIQUE(source_text, target_text)
);
CREATE INDEX IF NOT EXISTS idx_corr_src ON corrections(source_text);

CREATE TABLE IF NOT EXISTS prompt_snippets (
  id INTEGER PRIMARY KEY,
  context TEXT NOT NULL,           -- general|mairie|tech|ecole
  text TEXT NOT NULL,
  max_tokens INTEGER DEFAULT 200,
  active INTEGER DEFAULT 1,
  ts TEXT DEFAULT (datetime('now')),
  UNIQUE(context)
);

CREATE TABLE IF NOT EXISTS transcription_log (
  id INTEGER PRIMARY KEY,
  raw_text TEXT,
  corrected_text TEXT,
  applied_rules TEXT DEFAULT '[]',
  context TEXT DEFAULT 'general',
  ts TEXT DEFAULT (datetime('now'))
);
"""


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn=None):
    own = conn is None
    conn = conn or get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    if own:
        conn.close()


# -------------------------------------------------------------- post-correction
_WORD_RE = re.compile(r"\w+|[^\w\s]|\s+", re.UNICODE)


def _load_lexicon(conn, context):
    """Retourne {phonetic_key: [(term, weight), ...]} filtré par contexte."""
    if context and context != "general":
        rows = conn.execute(
            "SELECT term, phonetic_key, weight FROM lexicon WHERE domain=?",
            (context,),
        ).fetchall()
        if not rows:  # contexte vide → tout le lexique
            rows = conn.execute(
                "SELECT term, phonetic_key, weight FROM lexicon"
            ).fetchall()
    else:
        rows = conn.execute("SELECT term, phonetic_key, weight FROM lexicon").fetchall()
    idx = {}
    for r in rows:
        idx.setdefault(r["phonetic_key"], []).append((r["term"], r["weight"]))
    return idx


def correct(text, context="general", log=True, fuzzy=True, max_edit=1):
    """Corrige `text`. Renvoie (corrected_text, applied_rules:list).
    Non-régression : si la base n'existe pas, renvoie (text, [])."""
    if not text or not os.path.exists(DB_PATH):
        return text, []
    try:
        conn = get_conn()
    except Exception:
        return text, []
    rules = []
    try:
        # 1) corrections exactes (phrase entière puis insensible casse)
        low = text.strip().lower()
        row = conn.execute(
            "SELECT target_text FROM corrections WHERE lower(source_text)=?",
            (low,),
        ).fetchone()
        if row and "{" not in row["target_text"]:  # ignore templates type {site}
            rules.append({"type": "exact_full", "from": text, "to": row["target_text"]})
            out = row["target_text"]
            _log(conn, text, out, rules, context, log)
            return out, rules

        # 1bis) corrections MULTI-MOTS (phrases) en sous-chaîne : ex. "mont laure"
        #       -> "Montlaur" même au milieu d'une phrase. Bornes de mots, insensible
        #       à la casse. Appliqué avant le mot-à-mot.
        for r in conn.execute(
            "SELECT source_text, target_text FROM corrections "
            "WHERE instr(source_text,' ')>0 AND instr(target_text,'{')=0 "
            "ORDER BY length(source_text) DESC"
        ).fetchall():
            src, tgt = r["source_text"], r["target_text"]
            rx = re.compile(r"(?<!\w)" + re.escape(src) + r"(?!\w)", re.IGNORECASE)
            new = rx.sub(lambda m: tgt, text)
            if new != text:
                rules.append({"type": "phrase", "from": src, "to": tgt})
                text = new

        # 2) correction mot-à-mot : exact puis phonétique flou
        lex = _load_lexicon(conn, context) if fuzzy else {}
        # mots déjà valides (présents tels quels dans le lexique) → NE PAS toucher
        # (évite p.ex. "député" -> "députée" qui partagent la clé phonétique)
        known_terms = {t.lower() for lst in lex.values() for t, _ in lst}
        # map des corrections exactes au niveau mot
        corr_words = {
            r["source_text"].lower(): r["target_text"]
            for r in conn.execute(
                "SELECT source_text, target_text FROM corrections "
                "WHERE instr(source_text,' ')=0 AND instr(target_text,'{')=0"
            ).fetchall()
        }
        out_parts = []
        for tok in _WORD_RE.findall(text):
            if not tok.strip() or not re.match(r"\w", tok):
                out_parts.append(tok)
                continue
            wl = tok.lower()
            if wl in corr_words:
                rep = _match_case(tok, corr_words[wl])
                rules.append({"type": "exact_word", "from": tok, "to": rep})
                out_parts.append(rep)
                continue
            if fuzzy and len(wl) >= 4 and wl not in known_terms and wl not in COMMON_FR:
                pk = phonetic_key(wl)
                cands = lex.get(pk)
                if cands:
                    best = max(cands, key=lambda c: c[1])  # plus fort weight
                    if best[0].lower() != wl:
                        rep = _match_case(tok, best[0])
                        rules.append(
                            {"type": "phonetic", "from": tok, "to": rep, "key": pk}
                        )
                        out_parts.append(rep)
                        continue
            out_parts.append(tok)
        out = "".join(out_parts)
        _log(conn, text, out, rules, context, log)
        return out, rules
    finally:
        conn.close()


def _match_case(src, rep):
    if src.isupper():
        return rep.upper()
    if src[:1].isupper():
        return rep[:1].upper() + rep[1:]
    return rep


def _log(conn, raw, corrected, rules, context, do_log):
    if not do_log or raw == corrected:
        return
    try:
        conn.execute(
            "INSERT INTO transcription_log(raw_text,corrected_text,applied_rules,context) "
            "VALUES(?,?,?,?)",
            (raw, corrected, json.dumps(rules, ensure_ascii=False), context),
        )
        conn.commit()
    except Exception:
        pass


if __name__ == "__main__":
    import sys

    ensure_schema()
    if len(sys.argv) > 1:
        out, rules = correct(" ".join(sys.argv[1:]))
        print(out)
        for r in rules:
            print("  ·", r, file=sys.stderr)
