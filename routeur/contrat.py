#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
contrat.py — Contrat d'entree/sortie du routeur deterministe.

Principe : RIEN n'est pris en charge sans format declare et valide.
Une ligne qui n'entre pas dans le schema canonique n'est pas devinee :
elle est REJETEE avec un motif explicite, et le rejet est conserve.

Formats d'entree acceptes : tsv, csv, json, jsonl, sqlite
Formats de sortie produits : tsv, csv, json, jsonl, sqlite

Aucune dependance externe (stdlib seule).
"""

import csv
import json
import os
import re
import sqlite3
import sys
import unicodedata

# ---------------------------------------------------------------------------
# SCHEMA CANONIQUE — les 11 colonnes d'entree
# ---------------------------------------------------------------------------

CHAMPS_ENTREE = [
    "bloc",           # famille de source (PLATEFORME_FREELANCE, AGENCE_SOUSTRAITANCE, ...)
    "type",           # sous-type (MISSION, OFFRE, AGENCE_NOCODE, ...)
    "nom",            # nom lisible de la cible          [OBLIGATOIRE]
    "url",            # URL verifiable                   [OBLIGATOIRE]
    "pays",           # FR / BE / CH / LU / CA / INT
    "canal_contact",  # EMAIL_VERIFIE / FORMULAIRE / LINKEDIN / NON_PUBLIC / ...
    "contact",        # email reel OU marqueur (jamais devine)
    "signal",         # le fait qui rend la cible interessante
    "date_signal",    # AAAA-MM-JJ ou INCONNU
    "pertinence",     # entier 1..5
    "preuve",         # citation courte justifiant la ligne
]

# Colonnes ajoutees par le moteur de routage
CHAMPS_SORTIE = CHAMPS_ENTREE + [
    "cle",            # cle de deduplication stable
    "decision",       # verdict de routage
    "action",         # action concrete a executer
    "file",           # file d'attente de destination
    "score",          # score numerique deterministe
    "priorite",       # P0 / P1 / P2 / P3
    "regle",          # identifiant de la regle qui a tranche
    "motif",          # explication lisible de la decision
]

OBLIGATOIRES = ("nom", "url")

# ---------------------------------------------------------------------------
# ALIAS — pour avaler des sources heterogenes sans les reecrire a la main
# ---------------------------------------------------------------------------

ALIAS = {
    "nom":           ["nom", "entreprise", "societe", "company", "name", "titre",
                      "title", "raison_sociale", "agence", "organisation"],
    "url":           ["url", "site_url", "site", "lien", "link", "website",
                      "url_source", "page"],
    "contact":       ["contact", "email", "contact_email", "mail", "email_reel",
                      "adresse_email", "e_mail"],
    "pays":          ["pays", "country", "pays_code"],
    "canal_contact": ["canal_contact", "canal", "channel", "statut", "voie"],
    "signal":        ["signal", "notes", "note", "commentaire", "description",
                      "activite", "besoin"],
    "date_signal":   ["date_signal", "date", "date_ajout", "date_publication",
                      "published", "date_maj"],
    "pertinence":    ["pertinence", "score_pertinence", "priorite_source", "rating"],
    "preuve":        ["preuve", "extrait", "citation", "evidence", "source_texte"],
    "bloc":          ["bloc", "famille", "categorie", "source_bloc", "source"],
    "type":          ["type", "sous_type", "kind", "secteur"],
}

_INDEX_ALIAS = {}
for _canon, _variantes in ALIAS.items():
    for _v in _variantes:
        _INDEX_ALIAS[_v] = _canon


class ErreurContrat(Exception):
    """Le format demande n'est pas pris en charge, ou la source est illisible."""


# ---------------------------------------------------------------------------
# NORMALISATION
# ---------------------------------------------------------------------------

def _sans_accent(texte):
    decompose = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in decompose if not unicodedata.combining(c))


def normaliser_entete(nom_colonne):
    """'Contact Email ' -> 'contact_email' -> canonique 'contact'."""
    brut = _sans_accent(str(nom_colonne or "")).strip().lower()
    brut = re.sub(r"[^a-z0-9]+", "_", brut).strip("_")
    return _INDEX_ALIAS.get(brut, brut)


def _nettoyer(valeur):
    if valeur is None:
        return ""
    texte = str(valeur).replace("\t", " ").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", texte).strip()


def normaliser_ligne(brute):
    """Projette un dict quelconque sur le schema canonique."""
    projete = {}
    for cle_brute, valeur in brute.items():
        canon = normaliser_entete(cle_brute)
        if canon in CHAMPS_ENTREE and not projete.get(canon):
            projete[canon] = _nettoyer(valeur)
    ligne = {champ: projete.get(champ, "") for champ in CHAMPS_ENTREE}

    # pertinence : entier borne 1..5, sinon 0 (= non renseigne, jamais invente)
    brut_pert = ligne["pertinence"]
    try:
        ligne["pertinence"] = str(max(1, min(5, int(float(brut_pert)))))
    except (TypeError, ValueError):
        ligne["pertinence"] = "0"

    if not ligne["date_signal"]:
        ligne["date_signal"] = "INCONNU"
    ligne["pays"] = ligne["pays"].upper()[:3]
    return ligne


def valider(ligne, numero):
    """Retourne (True, '') si la ligne est recevable, sinon (False, motif)."""
    for champ in OBLIGATOIRES:
        if not ligne.get(champ):
            return False, "champ obligatoire vide: %s" % champ
    url = ligne["url"]
    if not re.match(r"^https?://[^\s]+\.[^\s]+", url):
        return False, "url non verifiable: %r" % url[:80]
    return True, ""


# ---------------------------------------------------------------------------
# LECTURE — entree
# ---------------------------------------------------------------------------

def _lire_delimite(chemin, delimiteur):
    with open(chemin, "r", encoding="utf-8-sig", newline="") as flux:
        for brute in csv.DictReader(flux, delimiter=delimiteur):
            yield brute


def _lire_json(chemin):
    with open(chemin, "r", encoding="utf-8") as flux:
        charge = json.load(flux)
    if isinstance(charge, dict):
        for valeur in charge.values():
            if isinstance(valeur, list):
                charge = valeur
                break
        else:
            charge = [charge]
    if not isinstance(charge, list):
        raise ErreurContrat("JSON: liste d'objets attendue, recu %s" % type(charge).__name__)
    for element in charge:
        if isinstance(element, dict):
            yield element


def _lire_jsonl(chemin):
    with open(chemin, "r", encoding="utf-8") as flux:
        for ligne in flux:
            ligne = ligne.strip()
            if not ligne:
                continue
            try:
                element = json.loads(ligne)
            except json.JSONDecodeError:
                continue
            if isinstance(element, dict):
                yield element


def _lire_sqlite(chemin, table=None):
    connexion = sqlite3.connect("file:%s?mode=ro" % chemin, uri=True)
    connexion.row_factory = sqlite3.Row
    try:
        if not table:
            tables = [r[0] for r in connexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'")]
            if not tables:
                raise ErreurContrat("SQLite: aucune table dans %s" % chemin)
            if len(tables) > 1:
                raise ErreurContrat(
                    "SQLite: %d tables, precisez laquelle via source#table (%s)"
                    % (len(tables), ", ".join(tables[:8])))
            table = tables[0]
        for enregistrement in connexion.execute('SELECT * FROM "%s"' % table):
            yield dict(enregistrement)
    finally:
        connexion.close()


EXTENSIONS = {
    ".tsv": "tsv", ".tab": "tsv",
    ".csv": "csv",
    ".json": "json",
    ".jsonl": "jsonl", ".ndjson": "jsonl",
    ".db": "sqlite", ".sqlite": "sqlite", ".sqlite3": "sqlite",
}


def detecter_format(chemin):
    extension = os.path.splitext(chemin)[1].lower()
    if extension in EXTENSIONS:
        return EXTENSIONS[extension]
    raise ErreurContrat(
        "format d'entree non pris en charge: %r "
        "(attendus: %s)" % (extension or chemin, ", ".join(sorted(set(EXTENSIONS.values())))))


def lire(source, format_force=None):
    """
    Lit une source et renvoie (lignes_valides, rejets).
    'source' accepte la syntaxe chemin.db#table pour SQLite.
    Aucune ligne n'est devinee : ce qui ne valide pas part en rejet trace.
    """
    table = None
    chemin = source
    if "#" in source:
        chemin, table = source.split("#", 1)

    if not os.path.exists(chemin):
        raise ErreurContrat("source introuvable: %s" % chemin)

    fmt = format_force or detecter_format(chemin)
    if fmt == "tsv":
        flux = _lire_delimite(chemin, "\t")
    elif fmt == "csv":
        flux = _lire_delimite(chemin, ",")
    elif fmt == "json":
        flux = _lire_json(chemin)
    elif fmt == "jsonl":
        flux = _lire_jsonl(chemin)
    elif fmt == "sqlite":
        flux = _lire_sqlite(chemin, table)
    else:
        raise ErreurContrat("format d'entree non pris en charge: %r" % fmt)

    valides, rejets = [], []
    for numero, brute in enumerate(flux, start=1):
        ligne = normaliser_ligne(brute)
        ok, motif = valider(ligne, numero)
        ligne["_source"] = os.path.basename(chemin)
        ligne["_ligne"] = numero
        if ok:
            valides.append(ligne)
        else:
            ligne["motif"] = motif
            rejets.append(ligne)
    return valides, rejets


# ---------------------------------------------------------------------------
# ECRITURE — sortie
# ---------------------------------------------------------------------------

def _ecrire_delimite(chemin, lignes, colonnes, delimiteur):
    with open(chemin, "w", encoding="utf-8", newline="") as flux:
        redacteur = csv.DictWriter(
            flux, fieldnames=colonnes, delimiter=delimiteur,
            extrasaction="ignore", lineterminator="\n")
        redacteur.writeheader()
        for ligne in lignes:
            redacteur.writerow({c: ligne.get(c, "") for c in colonnes})


def _ecrire_sqlite(chemin, lignes, colonnes, table="routage"):
    connexion = sqlite3.connect(chemin)
    try:
        colonnes_sql = ", ".join('"%s" TEXT' % c for c in colonnes)
        connexion.execute(
            'CREATE TABLE IF NOT EXISTS "%s" (%s, PRIMARY KEY ("cle"))'
            % (table, colonnes_sql) if "cle" in colonnes else
            'CREATE TABLE IF NOT EXISTS "%s" (%s)' % (table, colonnes_sql))
        marqueurs = ",".join("?" for _ in colonnes)
        connexion.executemany(
            'INSERT OR REPLACE INTO "%s" VALUES (%s)' % (table, marqueurs),
            [[ligne.get(c, "") for c in colonnes] for ligne in lignes])
        connexion.commit()
    finally:
        connexion.close()


def ecrire(chemin, lignes, colonnes=None, format_force=None):
    """Ecrit la sortie dans le format demande. Format inconnu = erreur nette."""
    colonnes = colonnes or CHAMPS_SORTIE
    fmt = format_force or detecter_format(chemin)
    if fmt == "tsv":
        _ecrire_delimite(chemin, lignes, colonnes, "\t")
    elif fmt == "csv":
        _ecrire_delimite(chemin, lignes, colonnes, ",")
    elif fmt == "json":
        with open(chemin, "w", encoding="utf-8") as flux:
            json.dump([{c: l.get(c, "") for c in colonnes} for l in lignes],
                      flux, ensure_ascii=False, indent=2)
    elif fmt == "jsonl":
        with open(chemin, "w", encoding="utf-8") as flux:
            for ligne in lignes:
                flux.write(json.dumps({c: ligne.get(c, "") for c in colonnes},
                                      ensure_ascii=False) + "\n")
    elif fmt == "sqlite":
        _ecrire_sqlite(chemin, lignes, colonnes)
    else:
        raise ErreurContrat("format de sortie non pris en charge: %r" % fmt)
    return len(lignes)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("usage: contrat.py <source> [--format tsv|csv|json|jsonl|sqlite]")
        sys.exit(2)
    force = None
    if "--format" in sys.argv:
        force = sys.argv[sys.argv.index("--format") + 1]
    try:
        ok, ko = lire(sys.argv[1], force)
    except ErreurContrat as erreur:
        print("REFUS DE PRISE EN CHARGE : %s" % erreur, file=sys.stderr)
        sys.exit(1)
    print("valides : %d" % len(ok))
    print("rejets  : %d" % len(ko))
    for rejet in ko[:10]:
        print("  ligne %s : %s" % (rejet.get("_ligne"), rejet.get("motif")))
