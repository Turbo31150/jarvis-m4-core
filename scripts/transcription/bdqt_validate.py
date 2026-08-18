#!/usr/bin/env python3
"""Suite de validation multi-scénarios de la bibliothèque BDQT (sans TTS, sans GPU).
- POSITIFS : une erreur connue DOIT donner la forme correcte.
- NÉGATIFS : une phrase normale NE DOIT PAS changer (anti-faux-positifs).
Produit un « cahier d'échange » (rapport) + propose des ajouts curés à valider.
Usage: bdqt_validate.py
"""

import bdqt_core as core

# (entrée, sortie_attendue) — l'attendu == entrée signifie « ne doit pas changer »
POSITIFS = [
    # perso / appris (snippets + lieux + noms)
    ("mail pro", "claire.domingues@ac-toulouse.fr"),
    ("mail franck", "franckdelmas00@gmail.com"),
    ("mail hotmail", "claire.dms@hotmail.fr"),
    ("je vais à mont laure", "je vais à Montlaur"),
    ("réunion à saint-oise de gammeville", "réunion à Saint Orens de Gameville"),
    ("ouvre olama", "ouvre Ollama"),
    ("lance le doquer", "lance le Docker"),
    ("demande de serfa", "demande de CERFA"),
    ("mon ondrive est plein", "mon OneDrive est plein"),
    ("projet alchimia", "projet Alkymia"),
    ("un fichier grafique", "un fichier graphique"),
]
NEGATIFS = [
    "je vais dans la chambre préparer mes affaires",
    "il faut continuer le travail demain matin",
    "ouvre le tiroir du bureau s'il te plaît",
    "les élèves sont dans la cour de récréation",
    "mon fils a mangé une pomme au déjeuner",
    "nous allons au marché acheter des légumes",
    "le chat dort tranquillement sur le canapé",
    "j'ai rendez-vous chez le médecin jeudi prochain",
    "la réunion de parents est prévue la semaine prochaine",
    "il fait beau aujourd'hui pour se promener dehors",
]


def run():
    okp = okn = 0
    fails = []
    print("=== POSITIFS (doivent être corrigés) ===")
    for src, exp in POSITIFS:
        out, _ = core.correct(src, log=False)
        ok = out == exp
        okp += ok
        print(
            f"  {'✓' if ok else '✗'} {src!r} -> {out!r}"
            + ("" if ok else f"  [attendu {exp!r}]")
        )
        if not ok:
            fails.append(("POS", src, out, exp))
    print(f"  => {okp}/{len(POSITIFS)} positifs OK")
    print("\n=== NÉGATIFS (ne doivent PAS changer) ===")
    for s in NEGATIFS:
        out, rules = core.correct(s, log=False)
        ok = out == s
        okn += ok
        if not ok:
            print(f"  ✗ FAUX POSITIF: {s!r} -> {out!r} {rules}")
            fails.append(("NEG", s, out, s))
    print(
        f"  => {okn}/{len(NEGATIFS)} négatifs OK (aucun faux positif = {okn == len(NEGATIFS)})"
    )
    tot = len(POSITIFS) + len(NEGATIFS)
    print(f"\n=== SCORE GLOBAL: {okp + okn}/{tot} ===")
    return fails


if __name__ == "__main__":
    run()
