#!/usr/bin/env python3
"""JARVIS Budget Enseignante — PAMERYS M4
Gestionnaire budget mensuel standalone pour enseignante.
"""

import argparse
import sqlite3
import csv
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple
import json

DB_PATH = Path.home() / "jarvis" / "budget" / "budget.db"
EXPORT_DIR = Path.home() / "Documents" / "Budget" / "Mensuel"

CATEGORIES_DEPENSES = [
    "Logement",
    "Alimentation",
    "Transport",
    "Santé",
    "Classe",
    "Livres",
    "Loisirs",
    "Épargne",
    "Divers",
]

CATEGORIES_REVENUS = ["Salaire", "Primes", "Autres"]


class BudgetDB:
    """Gestion base de données SQLite pour transactions."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Crée la table si elle n'existe pas."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    categorie TEXT NOT NULL,
                    montant REAL NOT NULL,
                    description TEXT,
                    date TEXT NOT NULL
                )
            """)
            conn.commit()

    def ajouter(self, type_trans: str, categorie: str, montant: float, desc: str = ""):
        """Ajoute une transaction."""
        today = date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO transactions (type, categorie, montant, description, date)
                VALUES (?, ?, ?, ?, ?)
            """,
                (type_trans, categorie, montant, desc, today),
            )
            conn.commit()
        print(f"✓ {type_trans.capitalize()} ajouté : {categorie} {montant}€")

    def get_all_transactions(self) -> List[Tuple]:
        """Retourne toutes les transactions."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, type, categorie, montant, description, date
                FROM transactions ORDER BY date DESC
            """)
            return cursor.fetchall()

    def get_monthly(self, year: int, month: int) -> List[Tuple]:
        """Retourne les transactions du mois."""
        date_start = f"{year:04d}-{month:02d}-01"
        if month == 12:
            date_end = f"{year + 1:04d}-01-01"
        else:
            date_end = f"{year:04d}-{month + 1:02d}-01"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, type, categorie, montant, description, date
                FROM transactions
                WHERE date >= ? AND date < ?
                ORDER BY date DESC
            """,
                (date_start, date_end),
            )
            return cursor.fetchall()


class Budget:
    """Gestionnaire budget avec rapports et export."""

    def __init__(self):
        self.db = BudgetDB(DB_PATH)

    def rapport(self, year: int = None, month: int = None) -> Dict:
        """Génère rapport mensuel avec totaux et pourcentages."""
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month

        transactions = self.db.get_monthly(year, month)

        revenus = {}
        depenses = {}
        total_revenus = 0
        total_depenses = 0

        for _, type_trans, categorie, montant, _, _ in transactions:
            if type_trans == "revenu":
                revenus[categorie] = revenus.get(categorie, 0) + montant
                total_revenus += montant
            else:
                depenses[categorie] = depenses.get(categorie, 0) + montant
                total_depenses += montant

        solde = total_revenus - total_depenses
        pct_depenses = (
            (total_depenses / total_revenus * 100) if total_revenus > 0 else 0
        )

        rapport = {
            "date": f"{year:04d}-{month:02d}",
            "revenus": revenus,
            "total_revenus": total_revenus,
            "depenses": depenses,
            "total_depenses": total_depenses,
            "solde": solde,
            "pct_depenses": pct_depenses,
            "alerte": pct_depenses > 80,
        }

        return rapport

    def afficher_rapport(self, year: int = None, month: int = None):
        """Affiche rapport formaté en tableau."""
        rapport = self.rapport(year, month)

        print(f"\n{'=' * 60}")
        print(f"RAPPORT BUDGET — {rapport['date']}")
        print(f"{'=' * 60}\n")

        print("REVENUS :")
        for cat, montant in rapport["revenus"].items():
            print(f"  {cat:20} {montant:8.2f}€")
        print(f"  {'Total revenus':20} {rapport['total_revenus']:8.2f}€\n")

        print("DÉPENSES :")
        for cat, montant in sorted(rapport["depenses"].items(), key=lambda x: -x[1]):
            pct = (
                (montant / rapport["total_revenus"] * 100)
                if rapport["total_revenus"] > 0
                else 0
            )
            print(f"  {cat:20} {montant:8.2f}€ ({pct:5.1f}%)")
        print(
            f"  {'Total dépenses':20} {rapport['total_depenses']:8.2f}€ ({rapport['pct_depenses']:5.1f}%)\n"
        )

        print(f"{'SOLDE':20} {rapport['solde']:8.2f}€")

        if rapport["alerte"]:
            print(
                f"\n⚠️  ALERTE : Dépenses > 80% des revenus ({rapport['pct_depenses']:.1f}%)"
            )

        print(f"{'=' * 60}\n")

    def export_csv(self, year: int = None, month: int = None) -> Path:
        """Exporte rapport en CSV."""
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month

        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"budget_{year:04d}-{month:02d}.csv"
        filepath = EXPORT_DIR / filename

        rapport = self.rapport(year, month)
        transactions = self.db.get_monthly(year, month)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")

            writer.writerow(["Type", "Catégorie", "Montant", "Description", "Date"])
            for _, type_trans, categorie, montant, desc, trans_date in transactions:
                writer.writerow(
                    [type_trans, categorie, f"{montant:.2f}", desc, trans_date]
                )

            writer.writerow([])
            writer.writerow(["RÉSUMÉ", "", "", "", ""])
            writer.writerow(
                ["Total revenus", "", f"{rapport['total_revenus']:.2f}", "", ""]
            )
            writer.writerow(
                ["Total dépenses", "", f"{rapport['total_depenses']:.2f}", "", ""]
            )
            writer.writerow(["Solde", "", f"{rapport['solde']:.2f}", "", ""])
            writer.writerow(
                ["% dépenses", "", f"{rapport['pct_depenses']:.1f}%", "", ""]
            )

        print(f"✓ Export : {filepath}")
        return filepath


def main():
    parser = argparse.ArgumentParser(
        description="JARVIS Budget Enseignante — Gestionnaire budget mensuel"
    )
    subparsers = parser.add_subparsers(dest="commande", help="Commandes disponibles")

    # Commande : ajouter
    add_parser = subparsers.add_parser("ajouter", help="Ajouter une transaction")
    add_parser.add_argument(
        "--type",
        required=True,
        choices=["revenu", "depense"],
        help="Type de transaction",
    )
    add_parser.add_argument("--cat", required=True, help="Catégorie")
    add_parser.add_argument("--montant", type=float, required=True, help="Montant en €")
    add_parser.add_argument("--desc", default="", help="Description")

    # Commande : rapport
    rap_parser = subparsers.add_parser("rapport", help="Afficher rapport mensuel")
    rap_parser.add_argument("--year", type=int, help="Année (défaut: courant)")
    rap_parser.add_argument("--month", type=int, help="Mois (défaut: courant)")

    # Commande : export
    exp_parser = subparsers.add_parser("export", help="Exporter en CSV")
    exp_parser.add_argument("--year", type=int, help="Année")
    exp_parser.add_argument("--month", type=int, help="Mois")

    # Commande : list
    list_parser = subparsers.add_parser("list", help="Lister toutes les transactions")

    # Commande : json
    json_parser = subparsers.add_parser("json", help="Rapport en JSON")
    json_parser.add_argument("--year", type=int, help="Année")
    json_parser.add_argument("--month", type=int, help="Mois")

    args = parser.parse_args()
    budget = Budget()

    if args.commande == "ajouter":
        budget.db.ajouter(args.type, args.cat, args.montant, args.desc)

    elif args.commande == "rapport":
        budget.afficher_rapport(args.year, args.month)

    elif args.commande == "export":
        budget.export_csv(args.year, args.month)

    elif args.commande == "list":
        transactions = budget.db.get_all_transactions()
        print(
            f"\n{'Type':8} {'Catégorie':15} {'Montant':>10} {'Description':20} {'Date':10}"
        )
        print("-" * 70)
        for _, type_trans, cat, montant, desc, trans_date in transactions:
            print(
                f"{type_trans:8} {cat:15} {montant:>10.2f}€ {desc[:20]:20} {trans_date:10}"
            )

    elif args.commande == "json":
        rapport = budget.rapport(args.year, args.month)
        print(json.dumps(rapport, ensure_ascii=False, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
