#!/usr/bin/env python3
"""Constructeur de bibliothèque par SCÉNARIOS (0 fine-tuning, 0 token).
Pour chaque scénario de la vie de Claire :
  1. SQL-FIRST : lit la bibliothèque BDQT (corrections + lexicon).
  2. Détecte les termes DOMINANTS du scénario (noms/sigles/jargon, pas les mots vides).
  3. Remplit ce qui manque (ajoute le terme dominant au lexique — curé).
  4. Enregistre la couverture du scénario (cahier), passe au suivant.
Multi-cycle : relançable, n'ajoute que les dominants absents (idempotent).
Usage: bdqt_scenario_builder.py [--apply]
"""

import json
import os
import sys
import bdqt_core as core

# Scénarios = (domaine, phrase type, [termes DOMINANTS à garantir])
SCENARIOS = [
    ("ecole", "Je rédige le PPRE de mon élève suivi par le RASED.", ["PPRE", "RASED"]),
    (
        "ecole",
        "Réunion ESS pour le dossier MDPH et l'AESH de l'élève.",
        ["ESS", "MDPH", "AESH"],
    ),
    ("ecole", "Je saisis les évaluations sur ONDE et AFFELNET.", ["ONDE", "AFFELNET"]),
    ("ecole", "Le PIAL coordonne les AESH de la circonscription.", ["PIAL", "AESH"]),
    ("ecole", "Conseil des maîtres et conseil d'école avant les APC.", ["APC"]),
    (
        "mairie",
        "Je dépose un CERFA d'urbanisme et une déclaration préalable.",
        ["CERFA"],
    ),
    ("mairie", "Demande au CCAS et dossier CAF pour la famille.", ["CCAS", "CAF"]),
    (
        "mairie",
        "Le PLU de Montlaur encadre le permis de construire.",
        ["PLU", "Montlaur"],
    ),
    ("civique", "Courrier à la députée, copie à la préfecture et au DASEN.", ["DASEN"]),
    ("civique", "Pétition transmise à la DSDEN et à l'IEN.", ["DSDEN", "IEN"]),
    ("admin", "Déclaration URSSAF et remboursement CPAM.", ["URSSAF", "CPAM"]),
    (
        "perso",
        "Envoie un mail pro et un mail franck pour le rendez-vous.",
        ["mail pro", "mail franck"],
    ),
    (
        "perso",
        "Je vais à Labège puis à Saint Orens de Gameville.",
        ["Labège", "Saint Orens de Gameville"],
    ),
    (
        "tech",
        "Lance Ollama et Docker sur le cluster JARVIS.",
        ["Ollama", "Docker", "JARVIS"],
    ),
]


def in_library(conn, term):
    t = term.lower()
    if conn.execute(
        "SELECT 1 FROM lexicon WHERE lower(term)=? LIMIT 1", (t,)
    ).fetchone():
        return True
    if conn.execute(
        "SELECT 1 FROM corrections WHERE lower(target_text)=? OR lower(source_text)=? LIMIT 1",
        (t, t),
    ).fetchone():
        return True
    return False


def domain_of(term):
    return "civique"  # sigles admin/école → civique par défaut (sûr, distinctif)


def main():
    apply = "--apply" in sys.argv
    core.ensure_schema()
    conn = core.get_conn()
    cahier = []
    added = 0
    for dom, phrase, dominants in SCENARIOS:
        covered, missing = [], []
        for term in dominants:
            (covered if in_library(conn, term) else missing).append(term)
        # remplissage : ajoute les dominants manquants (curés, distinctifs)
        for term in missing:
            d = (
                dom
                if dom in ("ecole", "mairie", "civique", "tech", "nom_propre")
                else "civique"
            )
            if " " in term:  # proper noun multi-mots
                d = "nom_propre"
            if apply:
                conn.execute(
                    "INSERT OR IGNORE INTO lexicon(term,domain,phonetic_key,weight,in_prompt,source) "
                    "VALUES(?,?,?,?,?,?)",
                    (
                        term,
                        d,
                        core.phonetic_key(term.replace(" ", "")),
                        4,
                        0,
                        "scenario",
                    ),
                )
                added += 1
        cahier.append(
            {
                "domaine": dom,
                "scenario": phrase,
                "couverts": covered,
                "remplis": missing,
            }
        )
        status = "✓ complet" if not missing else f"+{len(missing)} ajoutés: {missing}"
        print(f"[{dom:8}] {phrase[:55]:55} {status}")
    if apply:
        conn.commit()
    # cahier d'échange
    out = os.path.expanduser("~/jarvis/scripts/transcription/cahier_scenarios.json")
    json.dump(cahier, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tot = sum(len(s["couverts"]) + len(s["remplis"]) for s in cahier)
    cov = sum(len(s["couverts"]) for s in cahier)
    print(
        f"\n=== {len(SCENARIOS)} scénarios | couverture initiale {cov}/{tot} "
        f"| {'ajoutés ' + str(added) if apply else '(dry-run)'} | cahier -> {out}"
    )


if __name__ == "__main__":
    main()
