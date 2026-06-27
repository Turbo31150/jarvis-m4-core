#!/usr/bin/env python3
"""Gestion notes élèves — JARVIS PAMERYS M4"""

import sqlite3
import argparse
import csv
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

DB = Path.home() / "jarvis" / "notes.db"


def init_db():
    """Initialise la base de données si elle n'existe pas."""
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eleves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            classe TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eleve_id INTEGER NOT NULL,
            matiere TEXT NOT NULL,
            note REAL NOT NULL,
            coefficient REAL DEFAULT 1.0,
            date DATE DEFAULT CURRENT_DATE,
            commentaire TEXT,
            FOREIGN KEY (eleve_id) REFERENCES eleves(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def ajouter_note(nom, prenom, classe, matiere, note, coeff=1.0, commentaire=""):
    """Ajoute une note pour un élève (crée l'élève si absent)."""
    init_db()
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # Valide la note
    if not (0 <= note <= 20):
        print(f"❌ Note invalide: {note} (doit être entre 0 et 20)")
        conn.close()
        return

    # Récupère ou crée l'élève
    cursor.execute(
        "SELECT id FROM eleves WHERE nom=? AND prenom=? AND classe=?",
        (nom, prenom, classe),
    )
    result = cursor.fetchone()

    if result:
        eleve_id = result[0]
    else:
        cursor.execute(
            "INSERT INTO eleves (nom, prenom, classe) VALUES (?, ?, ?)",
            (nom, prenom, classe),
        )
        eleve_id = cursor.lastrowid
        print(f"✅ Élève créé: {prenom} {nom} ({classe})")

    # Ajoute la note
    cursor.execute(
        "INSERT INTO notes (eleve_id, matiere, note, coefficient, commentaire) VALUES (?, ?, ?, ?, ?)",
        (eleve_id, matiere, note, coeff, commentaire),
    )
    conn.commit()
    print(f"✅ Note {note}/20 ({matiere}) ajoutée pour {prenom} {nom}")
    conn.close()


def moyenne_classe(classe, matiere):
    """Calcule la moyenne pondérée d'une classe pour une matière."""
    init_db()
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT AVG(n.note * n.coefficient) / AVG(n.coefficient),
               MIN(n.note), MAX(n.note), COUNT(DISTINCT e.id)
        FROM notes n
        JOIN eleves e ON n.eleve_id = e.id
        WHERE e.classe = ? AND n.matiere = ?
    """,
        (classe, matiere),
    )

    result = cursor.fetchone()
    conn.close()

    if result[0] is None:
        print(f"❌ Aucune note trouvée pour {matiere} en {classe}")
        return

    avg, min_note, max_note, count = result
    print(f"📊 {classe} - {matiere}:")
    print(f"   Moyenne pondérée: {avg:.2f}/20")
    print(f"   Min: {min_note}, Max: {max_note}, Élèves: {count}")


def bulletin(nom, prenom):
    """Affiche le bulletin complet d'un élève."""
    init_db()
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, classe FROM eleves WHERE nom=? AND prenom=?", (nom, prenom)
    )
    result = cursor.fetchone()

    if not result:
        print(f"❌ Élève {prenom} {nom} non trouvé")
        conn.close()
        return

    eleve_id, classe = result

    cursor.execute(
        """
        SELECT matiere, note, coefficient, date, commentaire
        FROM notes
        WHERE eleve_id = ?
        ORDER BY matiere, date DESC
    """,
        (eleve_id,),
    )

    notes = cursor.fetchall()

    if not notes:
        print(f"📋 {prenom} {nom} ({classe}): Aucune note enregistrée")
        conn.close()
        return

    print(f"\n📋 BULLETIN — {prenom} {nom} ({classe})")
    print("=" * 60)

    # Groupe par matière
    matieres = {}
    for matiere, note, coeff, date, commentaire in notes:
        if matiere not in matieres:
            matieres[matiere] = []
        matieres[matiere].append((note, coeff, date, commentaire))

    # Affiche par matière
    for matiere in sorted(matieres.keys()):
        notes_mat = matieres[matiere]
        moyenne = sum(n[0] * n[1] for n in notes_mat) / sum(n[1] for n in notes_mat)
        print(f"\n{matiere}: {moyenne:.2f}/20")
        for note, coeff, date, commentaire in sorted(
            notes_mat, key=lambda x: x[2], reverse=True
        ):
            comm = f" ({commentaire})" if commentaire else ""
            print(f"  • {note}/20 (coeff {coeff}) — {date}{comm}")

    conn.close()


def export_classe(classe):
    """Exporte les notes d'une classe en CSV."""
    init_db()
    export_dir = Path.home() / "Documents" / "Eleves" / "Notes"
    export_dir.mkdir(parents=True, exist_ok=True)

    filename = export_dir / f"classe_{classe}_{datetime.now().strftime('%Y-%m')}.csv"

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT e.nom, e.prenom, n.matiere, n.note, n.coefficient, n.date, n.commentaire
        FROM notes n
        JOIN eleves e ON n.eleve_id = e.id
        WHERE e.classe = ?
        ORDER BY e.nom, e.prenom, n.matiere, n.date
    """,
        (classe,),
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(f"❌ Aucune note trouvée pour la classe {classe}")
        return

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Nom", "Prénom", "Matière", "Note", "Coefficient", "Date", "Commentaire"]
        )
        writer.writerows(rows)

    print(f"✅ Export: {filename}")


def liste_classe(classe):
    """Liste tous les élèves d'une classe."""
    init_db()
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT e.id, e.nom, e.prenom, COUNT(n.id) as nb_notes
        FROM eleves e
        LEFT JOIN notes n ON e.id = n.eleve_id
        WHERE e.classe = ?
        GROUP BY e.id
        ORDER BY e.nom, e.prenom
    """,
        (classe,),
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(f"❌ Aucun élève dans la classe {classe}")
        return

    print(f"\n👥 Classe {classe} — {len(rows)} élève(s)")
    table = [[row[1], row[2], row[3]] for row in rows]
    print(tabulate(table, headers=["Nom", "Prénom", "Notes"], tablefmt="grid"))


def main():
    parser = argparse.ArgumentParser(description="Gestion notes élèves")
    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

    # ajouter
    add_parser = subparsers.add_parser("ajouter", help="Ajouter une note")
    add_parser.add_argument("--nom", required=True)
    add_parser.add_argument("--prenom", required=True)
    add_parser.add_argument("--classe", required=True)
    add_parser.add_argument("--matiere", required=True)
    add_parser.add_argument("--note", type=float, required=True)
    add_parser.add_argument("--coeff", type=float, default=1.0)
    add_parser.add_argument("--commentaire", default="")

    # moyenne
    moy_parser = subparsers.add_parser("moyenne", help="Moyenne classe/matière")
    moy_parser.add_argument("--classe", required=True)
    moy_parser.add_argument("--matiere", required=True)

    # bulletin
    bul_parser = subparsers.add_parser("bulletin", help="Bulletin élève")
    bul_parser.add_argument("--nom", required=True)
    bul_parser.add_argument("--prenom", required=True)

    # export
    exp_parser = subparsers.add_parser("export", help="Export CSV classe")
    exp_parser.add_argument("--classe", required=True)

    # liste
    lst_parser = subparsers.add_parser("liste", help="Lister élèves")
    lst_parser.add_argument("--classe", required=True)

    args = parser.parse_args()

    if args.command == "ajouter":
        ajouter_note(
            args.nom,
            args.prenom,
            args.classe,
            args.matiere,
            args.note,
            args.coeff,
            args.commentaire,
        )
    elif args.command == "moyenne":
        moyenne_classe(args.classe, args.matiere)
    elif args.command == "bulletin":
        bulletin(args.nom, args.prenom)
    elif args.command == "export":
        export_classe(args.classe)
    elif args.command == "liste":
        liste_classe(args.classe)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
