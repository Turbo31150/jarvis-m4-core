#!/usr/bin/env python3
"""
moisson_reelle.py — Moissonneur de contacts REELS. 0 token, aucune inference.

Difference avec l'ancien jarvis-moisson : celui-ci n'ecrit QUE ce qu'il a
effectivement lu dans le HTML d'une page. Il ne fabrique jamais d'adresse par
convention (contact@domaine, info@domaine) — c'est ce qui avait produit 50
fausses entrees marquees a tort "FORMAT_STANDARD_VERIFIE".

Regles appliquees :
  - une adresse n'entre en base que si elle apparait littéralement dans le HTML
  - on stocke l'URL exacte ou elle a ete lue + l'extrait de contexte (preuve)
  - les boites a risque sont qualifiees, jamais livrees comme prospectables
  - aucun envoi n'est declenche ici

Usage :
    moisson_reelle.py --cibles cibles.tsv     # TSV : entreprise <TAB> url
    moisson_reelle.py --url https://... --entreprise "Nom"
    moisson_reelle.py --rapport               # etat de la base
"""

import argparse
import os
import re
import sqlite3
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

import requests

DB = os.path.expanduser("~/jarvis/data/prospection_reelle.db")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151.0 Safari/537.36"
DELAI = 2.0  # politesse entre deux requetes

# Adresse valide, non suivie d'une extension d'image (évite les faux positifs CSS/JS)
RE_MAIL = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}(?![a-zA-Z0-9.\-]*\.(?:png|jpg|jpeg|gif|svg|webp))"
)

# Boites qui ne doivent JAMAIS recevoir de prospection commerciale.
INTERDITS = {
    "securite": (
        r"^(vuln|security|abuse|cert|psirt|soc)@",
        "canal de signalement securite",
    ),
    "rgpd": (
        r"^(dpo|privacy|rgpd|gdpr|donnees-personnelles)@",
        "delegue protection des donnees",
    ),
    "technique": (
        r"^(webmaster|postmaster|noreply|no-reply|hostmaster|admin)@",
        "boite technique",
    ),
    "recrutement": (
        r"^(phd|these|stage|recrutement|jobs?|career|rh)@",
        "canal RH / academique",
    ),
}


def qualifier(mail):
    """Renvoie (qualification, motif). EXPLOITABLE = prospectable."""
    local = mail.split("@")[0].lower()
    for nom, (motif, raison) in INTERDITS.items():
        if re.match(motif, local + "@"):
            return f"INTERDIT_{nom.upper()}", raison
    # Prefixes generiques : restent exploitables meme suivis d'un lieu/service
    # (contact.toulouse@, info.presse@ ne designent pas une personne).
    GENERIQUES = (
        "contact",
        "info",
        "infos",
        "commercial",
        "sales",
        "presse",
        "press",
        "communication",
        "accueil",
        "hello",
        "bonjour",
        "service",
        "support",
        "direction",
        "secretariat",
        "agence",
    )
    if "." in local or "-" in local:
        prefixe = re.split(r"[.\-]", local)[0]
        if prefixe in GENERIQUES:
            return "EXPLOITABLE", "boite generique (prefixe + service/lieu)"
        # Prenom.nom@ => personne physique nommee : RGPD, prudence renforcee
        if re.match(r"^[a-z]+[.\-][a-z]+$", local):
            return "PERSONNE_NOMMEE", "personne physique identifiee"
    return "EXPLOITABLE", "boite generique d'entreprise"


SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts_preuve (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    moissonne_le   TEXT,
    entreprise     TEXT,
    email          TEXT,
    url_source     TEXT,
    preuve         TEXT,      -- extrait HTML entourant l'adresse
    qualification  TEXT,
    motif          TEXT,
    UNIQUE(entreprise, email)
);
"""


def db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def moissonner(entreprise, url, conn, timeout=20):
    """Lit une page, extrait les adresses REELLEMENT presentes. Renvoie le nb ecrit."""
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        print(f"  ECHEC  {entreprise:<32} {str(e)[:60]}")
        return 0

    html = r.text
    domaine = urlparse(url).netloc.lower().replace("www.", "")
    vus, ecrits = set(), 0
    now = datetime.now().isoformat(timespec="seconds")

    for m in RE_MAIL.finditer(html):
        mail = m.group(0).lower().strip(".")
        if mail in vus:
            continue
        vus.add(mail)
        # Ecarter les adresses d'un autre domaine (regies pub, CDN, exemples)
        dom_mail = mail.split("@")[1]
        if domaine.split(".")[0] not in dom_mail and dom_mail not in domaine:
            continue
        preuve = re.sub(r"\s+", " ", html[max(0, m.start() - 90) : m.end() + 90])
        qual, motif = qualifier(mail)
        try:
            conn.execute(
                "INSERT OR IGNORE INTO contacts_preuve "
                "(moissonne_le, entreprise, email, url_source, preuve, qualification, motif) "
                "VALUES (?,?,?,?,?,?,?)",
                (now, entreprise, mail, r.url, preuve, qual, motif),
            )
            ecrits += 1
        except sqlite3.Error as e:
            print(f"  SQL   {e}")
    conn.commit()

    if ecrits:
        print(f"  OK     {entreprise:<32} {ecrits} adresse(s) lue(s) sur la page")
    else:
        print(f"  VIDE   {entreprise:<32} aucune adresse dans le HTML (formulaire ?)")
    return ecrits


def rapport(conn):
    print(f"{'qualification':<24}{'nb':<6}exemple")
    print("-" * 78)
    for q, n, ex in conn.execute(
        "SELECT qualification, count(*), min(email) FROM contacts_preuve GROUP BY 1 ORDER BY 2 DESC"
    ):
        print(f"{q:<24}{n:<6}{ex}")
    tot = conn.execute("SELECT count(*) FROM contacts_preuve").fetchone()[0]
    expl = conn.execute(
        "SELECT count(*) FROM contacts_preuve WHERE qualification='EXPLOITABLE'"
    ).fetchone()[0]
    print(f"\nTotal {tot} — prospectables {expl}. Base : {DB}")
    print("Aucune adresse n'a ete deduite : chacune est accompagnee de sa preuve HTML.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cibles", help="fichier TSV : entreprise <TAB> url")
    ap.add_argument("--url")
    ap.add_argument("--entreprise")
    ap.add_argument("--rapport", action="store_true")
    args = ap.parse_args()

    conn = db()

    if args.rapport:
        rapport(conn)
        return 0

    if args.url:
        moissonner(args.entreprise or urlparse(args.url).netloc, args.url, conn)
        rapport(conn)
        return 0

    if not args.cibles:
        ap.print_help()
        return 2

    lignes = [
        l.rstrip("\n").split("\t")
        for l in open(args.cibles, encoding="utf-8")
        if l.strip() and not l.startswith("#")
    ]
    print(f"{len(lignes)} cible(s) — extraction stricte, aucune adresse deduite\n")
    for i, parts in enumerate(lignes, 1):
        if len(parts) < 2:
            continue
        ent, url = parts[0].strip(), parts[1].strip()
        print(f"[{i}/{len(lignes)}]", end=" ")
        moissonner(ent, url, conn)
        time.sleep(DELAI)
    print()
    rapport(conn)
    return 0


if __name__ == "__main__":
    sys.exit(main())
