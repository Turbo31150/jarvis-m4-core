# -*- coding: utf-8 -*-
"""Seed de données de DÉMONSTRATION (classe « Démonstration »).
Idempotent : relançable sans doublon. Préserve les vraies données de l'enseignante.
Ajoute aussi la colonne `classe` (fondation multi-classe)."""

import json
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / "ecole.db"
CLASSE_DEMO = "Démonstration"

# 10 élèves variés (PS→CM2) pour démontrer la différenciation 3 niveaux
ELEVES = [
    (
        "Martin",
        "Jade",
        "GS",
        "B",
        "très bonne mémoire, leadership",
        "graphisme à consolider",
    ),
    (
        "Bernard",
        "Gabin",
        "GS",
        "A",
        "logique, numération solide",
        "langage oral, timidité",
    ),
    ("Petit", "Louna", "CP", "B", "déchiffrage rapide, curieuse", "geste d'écriture"),
    ("Robert", "Nael", "CP", "C", "oral riche, imaginatif", "PPRE lecture, confiance"),
    (
        "Richard",
        "Ambre",
        "CE1",
        "A",
        "lectrice fluide, autonome",
        "approfondissement à prévoir",
    ),
    (
        "Durand",
        "Tiago",
        "CE1",
        "C",
        "motivé, manuel",
        "dyslexie, segmentation des mots",
    ),
    ("Moreau", "Lina", "CE2", "B", "raisonnement maths", "français écrit, orthographe"),
    ("Laurent", "Sacha", "CE2", "C", "sociable, sportif", "TDA, attention soutenue"),
    (
        "Simon",
        "Maya",
        "CM1",
        "A",
        "rédaction soignée, méthodique",
        "prise de parole en groupe",
    ),
    (
        "Michel",
        "Ethan",
        "CM2",
        "C",
        "bon esprit d'équipe",
        "allophone (arrivée récente), lexique",
    ),
]


def main():
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    # 1) colonne classe (idempotent)
    cols = [r[1] for r in cur.execute("PRAGMA table_info(eleves)")]
    if "classe" not in cols:
        cur.execute("ALTER TABLE eleves ADD COLUMN classe TEXT DEFAULT 'Ma classe'")
        cur.execute(
            "UPDATE eleves SET classe='Ma classe' WHERE classe IS NULL OR classe=''"
        )
        print("colonne 'classe' ajoutée")
    # 2) nettoyer l'élève vide (id sans prénom ni nom)
    n = cur.execute(
        "DELETE FROM eleves WHERE COALESCE(prenom,'')='' AND COALESCE(nom,'')=''"
    ).rowcount
    if n:
        print(f"{n} élève(s) vide(s) supprimé(s)")
    # 3) seed démo (idempotent par prénom+nom dans la classe démo)
    added = 0
    for nom, prenom, niveau, groupe, forts, besoins in ELEVES:
        exists = cur.execute(
            "SELECT 1 FROM eleves WHERE prenom=? AND nom=? AND classe=?",
            (prenom, nom, CLASSE_DEMO),
        ).fetchone()
        if exists:
            continue
        cur.execute(
            "INSERT INTO eleves (nom, prenom, niveau, groupe, points_forts, besoins, notes_json, classe) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (nom, prenom, niveau, groupe, forts, besoins, json.dumps({}), CLASSE_DEMO),
        )
        added += 1
    conn.commit()
    total = cur.execute("SELECT COUNT(*) FROM eleves").fetchone()[0]
    demo = cur.execute(
        "SELECT COUNT(*) FROM eleves WHERE classe=?", (CLASSE_DEMO,)
    ).fetchone()[0]
    conn.close()
    print(
        f"{added} élèves démo ajoutés · {demo} en classe « {CLASSE_DEMO} » · {total} élèves au total"
    )


if __name__ == "__main__":
    main()
