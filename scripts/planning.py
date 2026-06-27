#!/usr/bin/env python3
"""
Planning Enseignante - Gestion calendrier hebdomadaire
Stockage SQLite, notifications GNOME, CLI intégré
"""

import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
import subprocess

DB_PATH = Path.home() / "jarvis" / "planning.db"
JOURS_SEMAINE = [
    "Lundi",
    "Mardi",
    "Mercredi",
    "Jeudi",
    "Vendredi",
    "Samedi",
    "Dimanche",
]


def init_db():
    """Crée la table planning si n'existe pas"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS cours (
        id INTEGER PRIMARY KEY,
        jour TEXT NOT NULL,
        heure TEXT NOT NULL,
        duree TEXT NOT NULL,
        titre TEXT NOT NULL,
        salle TEXT,
        date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


def ajouter_cours(jour, heure, duree, titre, salle=None):
    """Ajoute un cours au planning"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
    INSERT INTO cours (jour, heure, duree, titre, salle)
    VALUES (?, ?, ?, ?, ?)
    """,
        (jour, heure, duree, titre, salle or "N/A"),
    )
    conn.commit()
    conn.close()
    print(f"✅ Cours ajouté: {jour} à {heure} - {titre} ({salle or 'N/A'})")


def afficher_aujourd_hui():
    """Affiche le programme du jour"""
    init_db()
    jour_fr = JOURS_SEMAINE[datetime.now().weekday()]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT heure, duree, titre, salle FROM cours WHERE jour = ? ORDER BY heure",
        (jour_fr,),
    )
    resultats = c.fetchall()
    conn.close()

    if not resultats:
        print(f"📅 {jour_fr} - Aucun cours")
        return

    print(f"\n📅 PROGRAMME DU JOUR ({jour_fr})\n{'=' * 60}")
    for heure, duree, titre, salle in resultats:
        print(f"  {heure:5s} → {duree:4s} | {titre:30s} | {salle}")
    print()


def afficher_semaine():
    """Tableau complet de la semaine"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT jour, heure, titre, salle FROM cours ORDER BY CASE jour WHEN 'Lundi' THEN 1 WHEN 'Mardi' THEN 2 WHEN 'Mercredi' THEN 3 WHEN 'Jeudi' THEN 4 WHEN 'Vendredi' THEN 5 WHEN 'Samedi' THEN 6 WHEN 'Dimanche' THEN 7 END, heure"
    )
    resultats = c.fetchall()
    conn.close()

    print("\n📋 PLANNING SEMAINE")
    print(f"{'Jour':<12} {'Heure':<8} {'Cours':<30} {'Salle':<8}")
    print("=" * 60)
    for jour, heure, titre, salle in resultats:
        print(f"{jour:<12} {heure:<8} {titre:<30} {salle:<8}")
    print()


def rappel_cours():
    """Envoie une notification si cours dans 15 min"""
    init_db()
    now = datetime.now()
    jour_fr = JOURS_SEMAINE[now.weekday()]
    heure_actuelle = now.strftime("%H:%M")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT heure, titre, salle FROM cours WHERE jour = ? ORDER BY heure",
        (jour_fr,),
    )
    resultats = c.fetchall()
    conn.close()

    for heure, titre, salle in resultats:
        h, m = map(int, heure.split(":"))
        t = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
        delta = (t - now).total_seconds() / 60

        if 0 < delta <= 15:
            msg = f"📚 RAPPEL: {titre} à {heure} ({salle})"
            try:
                subprocess.run(["notify-send", "Planning", msg], check=True)
                print(f"🔔 {msg}")
            except FileNotFoundError:
                print(f"⚠️  notify-send indisponible - Message: {msg}")
            return

    print("✅ Aucun cours imminent")


def main():
    parser = argparse.ArgumentParser(description="Gestion planning enseignante")
    subparsers = parser.add_subparsers(dest="cmd", help="Commandes disponibles")

    # Subcommande: ajouter
    add_parser = subparsers.add_parser("ajouter", help="Ajouter un cours")
    add_parser.add_argument("--jour", required=True, choices=JOURS_SEMAINE)
    add_parser.add_argument("--heure", required=True, help="HH:MM")
    add_parser.add_argument("--duree", required=True, help="1h, 1h30, etc.")
    add_parser.add_argument("--titre", required=True)
    add_parser.add_argument("--salle", default=None)

    # Subcommande: aujourd'hui
    subparsers.add_parser("aujourd'hui", help="Programme du jour")

    # Subcommande: semaine
    subparsers.add_parser("semaine", help="Planning semaine")

    # Subcommande: rappel
    subparsers.add_parser("rappel", help="Notification rappel (15 min)")

    args = parser.parse_args()

    if args.cmd == "ajouter":
        ajouter_cours(args.jour, args.heure, args.duree, args.titre, args.salle)
    elif args.cmd == "aujourd'hui":
        afficher_aujourd_hui()
    elif args.cmd == "semaine":
        afficher_semaine()
    elif args.cmd == "rappel":
        rappel_cours()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
