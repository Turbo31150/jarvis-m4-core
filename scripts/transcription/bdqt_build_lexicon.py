#!/usr/bin/env python3
"""Construit le lexique BDQT (4 domaines) : seed curé + extraction des données
existantes. Déterministe et hors-ligne. Enrichissement LLM optionnel (--enrich)
via sql-first (0 token, OL1/CPU) — désactivé par défaut pour fiabilité.

Usage: bdqt_build_lexicon.py [--enrich]
"""

import os
import re
import sys
import glob
import subprocess
import bdqt_core as core

TEMPLATES = os.path.expanduser("~/Bureau/workflow-gestion/data/templates_mairie")

# --- seeds curés (forme canonique correcte) ---------------------------------
SEED = {
    "mairie": [
        "CERFA",
        "permis de construire",
        "déclaration préalable",
        "urbanisme",
        "certificat d'urbanisme",
        "plan local d'urbanisme",
        "PLU",
        "zone UA",
        "état civil",
        "acte de naissance",
        "acte de mariage",
        "acte de décès",
        "voirie",
        "nid-de-poule",
        "signalement",
        "arrêté municipal",
        "conseil municipal",
        "délibération",
        "RGPD",
        "charte Marianne",
        "Trésor public",
        "DGFIP",
        "mandatement",
        "salle des fêtes",
        "agglomération",
        "communauté de communes",
        "cadastre",
        "plan de masse",
    ],
    "tech": [
        "MEXC",
        "VS Code",
        "Ollama",
        "Docker",
        "Portainer",
        "BrowserOS",
        "LM Studio",
        "Whisper",
        "faster-whisper",
        "n8n",
        "JARVIS",
        "OpenClaw",
        "Qwen",
        "Gemma",
        "DeepSeek",
        "Kimi",
        "PostgreSQL",
        "SQLite",
        "FastAPI",
        "Python",
        "GPU",
        "VRAM",
        "CUDA",
        "MCP",
        "cluster",
        "systemd",
        "Netlify",
        "GitHub",
        "Telegram",
        "plein écran",
        "terminal",
        "localhost",
    ],
    "ecole": [
        "CE2",
        "CP",
        "CE1",
        "CM1",
        "CM2",
        "maternelle",
        "élémentaire",
        "calcul mental",
        "table de multiplication",
        "numération",
        "dictée",
        "lecture",
        "compréhension",
        "production d'écrit",
        "grammaire",
        "conjugaison",
        "orthographe",
        "vocabulaire",
        "questionner le monde",
        "éducation musicale",
        "arts plastiques",
        "EPS",
        "programme scolaire",
        "compétences",
        "évaluation",
        "cahier journal",
        "séquence",
        "séance",
        "différenciation",
        "ATSEM",
        "récréation",
        "conseil d'école",
    ],
    "civique": [
        "député",
        "députée",
        "sénateur",
        "sénatrice",
        "circonscription",
        "Assemblée nationale",
        "Sénat",
        "pétition",
        "motion",
        "amendement",
        "proposition de loi",
        "ministre",
        "ministère",
        "préfet",
        "préfecture",
        "rectorat",
        "inspection académique",
        "Éducation nationale",
        "AESH",
        "RASED",
        "IEN",
        "DASEN",
        "REP+",
        "PAI",
        "PPS",
        "PAP",
        "MDPH",
        "CAF",
        "CCAS",
        "services publics",
        "doléances",
        "courrier",
        "parents-professeurs",
    ],
    "nom_propre": [
        "Pamerys",
        "Franck Delmas",
        "Alkymia",
        "OmertaFlow",
        "WhisperFlow",
        "Phanesis",
        "Toulouse",
        "Merville",
        "Eduscol",
        "France Connect",
        "Claude",
        "Anthropic",
        "Google",
        "Mistral",
    ],
}


def extract_mairie_templates():
    terms = set()
    for fp in glob.glob(os.path.join(TEMPLATES, "*.txt")):
        try:
            txt = open(fp, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        # mots/expressions avec majuscule interne ou acronymes
        for m in re.findall(r"\b[A-ZÀ-Ÿ][\wÀ-ÿ'-]{2,}\b", txt):
            terms.add(m.strip("'-"))
    return terms


def extract_tech_from_corrections():
    terms = set()
    try:
        src = __import__("sqlite3").connect(os.path.expanduser("~/jarvis.db"))
        for (t,) in src.execute(
            "SELECT DISTINCT target_text FROM voice_corrections "
            "WHERE category IN ('alias','auto_training') AND instr(target_text,'{')=0"
        ).fetchall():
            if t and 2 <= len(t) <= 30:
                terms.add(t.strip())
        src.close()
    except Exception:
        pass
    return terms


def enrich_ecole():
    """Optionnel : étend le vocabulaire école via sql-first (0 token)."""
    try:
        out = subprocess.run(
            [
                "sql-first",
                "--no-store",
                "Liste 30 termes de vocabulaire scolaire primaire français "
                "(un par ligne, sans numéro, sans explication)",
            ],
            capture_output=True,
            text=True,
            timeout=200,
        ).stdout
        terms = [
            line.strip("-*• \t")
            for line in out.splitlines()
            if line.strip() and not line.startswith("[")
        ]
        return [t for t in terms if 2 <= len(t) <= 40]
    except Exception as e:
        print(f"[enrich] ignoré ({e})", file=sys.stderr)
        return []


def main():
    enrich = "--enrich" in sys.argv
    core.ensure_schema()
    conn = core.get_conn()

    buckets = {k: set(v) for k, v in SEED.items()}
    buckets["mairie"] |= extract_mairie_templates()
    buckets["tech"] |= extract_tech_from_corrections()
    if enrich:
        buckets["ecole"] |= set(enrich_ecole())

    n = 0
    for domain, terms in buckets.items():
        for term in terms:
            term = term.strip()
            if not term:
                continue
            pk = (
                core.phonetic_key(term.split()[0])
                if " " not in term
                else core.phonetic_key(term.replace(" ", ""))
            )
            # weight : termes courts/fréquents + seeds = poids fort
            weight = 5 if term in SEED.get(domain, []) else 2
            in_prompt = 1 if weight >= 5 else 0
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO lexicon"
                    "(term,domain,phonetic_key,weight,in_prompt,source) "
                    "VALUES(?,?,?,?,?,?)",
                    (term, domain, pk, weight, in_prompt, "seed/extract"),
                )
                n += 1
            except Exception:
                pass
    conn.commit()
    stats = conn.execute(
        "SELECT domain, COUNT(*) FROM lexicon GROUP BY domain"
    ).fetchall()
    print(f"[lexicon] insérés/vus={n}")
    for d, c in stats:
        print(f"  {d:12} {c}")
    conn.close()


if __name__ == "__main__":
    main()
