#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
routeur.py — Moteur de routage deterministe, 0 token, 0 inference.

Meme entree + memes regles => meme sortie, toujours. Aucun appel reseau,
aucun LLM. Toute la logique metier vit dans regles.json.

Chaine : contrat.lire -> dedup -> garde-fous -> regles -> score -> contrat.ecrire
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sqlite3
import sys
import unicodedata
from urllib.parse import urlparse

import contrat

RACINE = os.path.dirname(os.path.abspath(__file__))
REGLES_DEFAUT = os.path.join(RACINE, "regles.json")
JOURNAL_DEFAUT = os.path.join(RACINE, "logs", "routage.db")

RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)


# ---------------------------------------------------------------------------
# OUTILS
# ---------------------------------------------------------------------------

def _plat(texte):
    """minuscule sans accent, pour comparaisons stables."""
    decompose = unicodedata.normalize("NFKD", str(texte or "").lower())
    return "".join(c for c in decompose if not unicodedata.combining(c))


def domaine(url):
    try:
        hote = urlparse(url).netloc.lower()
        return hote[4:] if hote.startswith("www.") else hote
    except Exception:
        return ""


def cle_dedup(ligne):
    """Cle stable : domaine + nom normalise. Deux moissons donnent la meme cle."""
    nom = re.sub(r"[^a-z0-9]+", "", _plat(ligne.get("nom", "")))
    empreinte = "%s|%s" % (domaine(ligne.get("url", "")), nom)
    return hashlib.sha1(empreinte.encode("utf-8")).hexdigest()[:16]


def age_en_jours(date_texte, aujourdhui):
    if not date_texte or date_texte.upper() in ("INCONNU", "N/A", ""):
        return None
    for format_date in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            jour = datetime.datetime.strptime(date_texte[:10], format_date).date()
            return (aujourdhui - jour).days
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# EVALUATION DES CONDITIONS (deterministe, operateurs fermes)
# ---------------------------------------------------------------------------

def _est_email(valeur):
    return bool(RE_EMAIL.match(str(valeur or "").strip()))


def _email_suspect(valeur, garde_fous):
    plat = _plat(valeur)
    for prefixe in garde_fous.get("emails_generiques_suspects", []):
        if plat.startswith(_plat(prefixe)):
            return True
    return False


def condition_vraie(champ, contrainte, ligne, garde_fous):
    """Un operateur inconnu leve : on refuse de deviner l'intention d'une regle."""
    valeur = ligne.get(champ, "")
    plat = _plat(valeur)

    for operateur, attendu in contrainte.items():
        if operateur == "egal_un_de":
            if plat not in [_plat(a) for a in attendu]:
                return False
        elif operateur == "different_de":
            if plat in [_plat(a) for a in attendu]:
                return False
        elif operateur == "contient_un_de":
            if not any(_plat(a) in plat for a in attendu):
                return False
        elif operateur == "regex":
            if not re.search(attendu, str(valeur), re.I):
                return False
        elif operateur == "est_email":
            if _est_email(valeur) != bool(attendu):
                return False
        elif operateur == "non_suspect":
            if (not _email_suspect(valeur, garde_fous)) != bool(attendu):
                return False
        elif operateur == "sup_ou_egal":
            try:
                if float(valeur or 0) < float(attendu):
                    return False
            except ValueError:
                return False
        elif operateur == "inf_ou_egal":
            try:
                if float(valeur or 0) > float(attendu):
                    return False
            except ValueError:
                return False
        elif operateur == "non_vide":
            if bool(str(valeur).strip()) != bool(attendu):
                return False
        else:
            raise contrat.ErreurContrat(
                "operateur de regle inconnu: %r (champ %s)" % (operateur, champ))
    return True


def regle_applicable(regle, ligne, garde_fous):
    for champ, contrainte in regle.get("si", {}).items():
        if not condition_vraie(champ, contrainte, ligne, garde_fous):
            return False
    return True


# ---------------------------------------------------------------------------
# SCORING
# ---------------------------------------------------------------------------

def calculer_score(ligne, scoring, aujourdhui):
    total = 0
    detail = []

    try:
        pertinence = int(ligne.get("pertinence") or 0)
    except ValueError:
        pertinence = 0
    gain = pertinence * scoring.get("poids_pertinence", 0)
    total += gain
    detail.append("pertinence%d=+%d" % (pertinence, gain))

    gain = scoring.get("bonus_pays", {}).get(ligne.get("pays", ""), 0)
    if gain:
        total += gain
        detail.append("pays%s=+%d" % (ligne.get("pays"), gain))

    corpus = _plat(" ".join(ligne.get(c, "") for c in scoring.get("champs_scannes", [])))
    cumul_mots = 0
    for terme, poids in sorted(scoring.get("bonus_mots_cles", {}).items(),
                               key=lambda kv: -kv[1]):
        if _plat(terme) in corpus:
            cumul_mots += poids
            detail.append("%s=+%d" % (terme, poids))
    plafond = scoring.get("plafond_mots_cles")
    if plafond is not None and cumul_mots > plafond:
        detail.append("plafonne(%d->%d)" % (cumul_mots, plafond))
        cumul_mots = plafond
    total += cumul_mots

    fraicheur = scoring.get("bonus_fraicheur", {})
    jours = age_en_jours(ligne.get("date_signal", ""), aujourdhui)
    if jours is None:
        gain = fraicheur.get("inconnu", 0)
        etiquette = "date_inconnue"
    elif jours <= 7:
        gain, etiquette = fraicheur.get("jours_7", 0), "moins7j"
    elif jours <= 30:
        gain, etiquette = fraicheur.get("jours_30", 0), "moins30j"
    elif jours <= 90:
        gain, etiquette = fraicheur.get("jours_90", 0), "moins90j"
    elif jours <= 180:
        gain, etiquette = fraicheur.get("jours_180", 0), "moins180j"
    else:
        gain, etiquette = fraicheur.get("plus_ancien", 0), "ancien"
    if gain:
        total += gain
        detail.append("%s=%+d" % (etiquette, gain))

    return total, detail


def priorite_depuis_score(score, seuils):
    if score >= seuils.get("P0", 80):
        return "P0"
    if score >= seuils.get("P1", 60):
        return "P1"
    if score >= seuils.get("P2", 40):
        return "P2"
    return "P3"


# ---------------------------------------------------------------------------
# ROUTAGE
# ---------------------------------------------------------------------------

def router_ligne(ligne, config, aujourdhui):
    garde_fous = config.get("garde_fous", {})
    scoring = config.get("scoring", {})

    for regle in config["regles"]:
        if not regle_applicable(regle, ligne, garde_fous):
            continue
        verdict = regle["alors"]
        score, detail = calculer_score(ligne, scoring, aujourdhui)
        score += verdict.get("bonus_score", 0)
        score = max(0, min(100, score))

        resultat = dict(ligne)
        resultat.update({
            "cle": cle_dedup(ligne),
            "decision": verdict.get("decision", ""),
            "action": verdict.get("action", ""),
            "file": verdict.get("file", ""),
            "score": str(score),
            "priorite": priorite_depuis_score(score, scoring.get("seuils_priorite", {})),
            "regle": regle["id"],
            "motif": verdict.get("motif", ""),
            "_detail_score": " ".join(detail),
        })
        return resultat

    raise contrat.ErreurContrat(
        "aucune regle n'a tranche (regles.json doit garder un R99_DEFAUT)")


def dedupliquer(lignes):
    """Garde la ligne la plus informative par cle (celle qui a le plus de champs remplis)."""
    par_cle, doublons = {}, 0
    for ligne in lignes:
        cle = cle_dedup(ligne)
        richesse = sum(1 for c in contrat.CHAMPS_ENTREE if ligne.get(c))
        if cle not in par_cle:
            par_cle[cle] = (richesse, ligne)
        else:
            doublons += 1
            if richesse > par_cle[cle][0]:
                par_cle[cle] = (richesse, ligne)
    return [v[1] for v in par_cle.values()], doublons


# ---------------------------------------------------------------------------
# JOURNAL SQLITE (idempotent)
# ---------------------------------------------------------------------------

def journaliser(chemin, lignes, horodatage):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    connexion = sqlite3.connect(chemin)
    try:
        connexion.execute("""
            CREATE TABLE IF NOT EXISTS routage (
                cle TEXT PRIMARY KEY, nom TEXT, url TEXT, pays TEXT, bloc TEXT,
                canal_contact TEXT, contact TEXT, decision TEXT, action TEXT,
                file TEXT, score INTEGER, priorite TEXT, regle TEXT, motif TEXT,
                premiere_vue TEXT, derniere_vue TEXT, nb_passages INTEGER DEFAULT 1)""")
        connexion.execute(
            "CREATE INDEX IF NOT EXISTS idx_file ON routage(file, score DESC)")
        nouveaux = 0
        for ligne in lignes:
            existe = connexion.execute(
                "SELECT nb_passages FROM routage WHERE cle=?", (ligne["cle"],)).fetchone()
            if existe:
                connexion.execute(
                    "UPDATE routage SET derniere_vue=?, nb_passages=?, decision=?, "
                    "action=?, file=?, score=?, priorite=?, regle=?, motif=? WHERE cle=?",
                    (horodatage, existe[0] + 1, ligne["decision"], ligne["action"],
                     ligne["file"], int(ligne["score"]), ligne["priorite"],
                     ligne["regle"], ligne["motif"], ligne["cle"]))
            else:
                nouveaux += 1
                connexion.execute(
                    "INSERT INTO routage (cle,nom,url,pays,bloc,canal_contact,contact,"
                    "decision,action,file,score,priorite,regle,motif,premiere_vue,"
                    "derniere_vue,nb_passages) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
                    (ligne["cle"], ligne["nom"], ligne["url"], ligne["pays"], ligne["bloc"],
                     ligne["canal_contact"], ligne["contact"], ligne["decision"],
                     ligne["action"], ligne["file"], int(ligne["score"]), ligne["priorite"],
                     ligne["regle"], ligne["motif"], horodatage, horodatage))
        connexion.commit()
        return nouveaux
    finally:
        connexion.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    analyseur = argparse.ArgumentParser(
        description="Routeur deterministe d'opportunites (0 token, 0 inference).")
    analyseur.add_argument("sources", nargs="+",
                           help="fichiers d'entree (tsv/csv/json/jsonl/sqlite, "
                                "syntaxe base.db#table pour SQLite)")
    analyseur.add_argument("--regles", default=REGLES_DEFAUT)
    analyseur.add_argument("--sortie", default=os.path.join(RACINE, "sorties"))
    analyseur.add_argument("--format", default="tsv",
                           choices=["tsv", "csv", "json", "jsonl", "sqlite"])
    analyseur.add_argument("--format-entree", default=None,
                           choices=["tsv", "csv", "json", "jsonl", "sqlite"])
    analyseur.add_argument("--journal", default=JOURNAL_DEFAUT)
    analyseur.add_argument("--sans-journal", action="store_true")
    arguments = analyseur.parse_args()

    with open(arguments.regles, "r", encoding="utf-8") as flux:
        config = json.load(flux)

    aujourdhui = datetime.date.today()
    horodatage = datetime.datetime.now().isoformat(timespec="seconds")

    toutes, tous_rejets = [], []
    print("=" * 72)
    print("ROUTEUR DETERMINISTE — regles v%s (%d regles)"
          % (config.get("version", "?"), len(config["regles"])))
    print("=" * 72)

    for source in arguments.sources:
        try:
            valides, rejets = contrat.lire(source, arguments.format_entree)
        except contrat.ErreurContrat as erreur:
            print("  REFUS  %-40s %s" % (os.path.basename(source), erreur))
            continue
        print("  LU     %-40s %4d valides / %d rejetes"
              % (os.path.basename(source), len(valides), len(rejets)))
        toutes.extend(valides)
        tous_rejets.extend(rejets)

    if not toutes:
        print("\nAucune ligne exploitable. Rien n'est produit (et rien n'est invente).")
        return 1

    uniques, doublons = dedupliquer(toutes)
    print("\n  dedup  %d lignes -> %d uniques (%d doublons fusionnes)"
          % (len(toutes), len(uniques), doublons))

    routees = [router_ligne(l, config, aujourdhui) for l in uniques]
    routees.sort(key=lambda l: (-int(l["score"]), l["nom"].lower()))

    os.makedirs(arguments.sortie, exist_ok=True)
    extension = arguments.format

    chemin_global = os.path.join(arguments.sortie, "routage_complet.%s" % extension)
    contrat.ecrire(chemin_global, routees, contrat.CHAMPS_SORTIE, arguments.format)

    par_file = {}
    for ligne in routees:
        par_file.setdefault(ligne["file"], []).append(ligne)

    print("\n  REPARTITION PAR FILE")
    print("  %-20s %6s  %s" % ("file", "lignes", "priorites"))
    print("  " + "-" * 58)
    for nom_file in sorted(par_file, key=lambda f: -len(par_file[f])):
        lignes_file = par_file[nom_file]
        compte = {}
        for ligne in lignes_file:
            compte[ligne["priorite"]] = compte.get(ligne["priorite"], 0) + 1
        resume = " ".join("%s:%d" % (p, compte[p]) for p in sorted(compte))
        print("  %-20s %6d  %s" % (nom_file, len(lignes_file), resume))
        contrat.ecrire(os.path.join(arguments.sortie, "%s.%s" % (nom_file.lower(), extension)),
                       lignes_file, contrat.CHAMPS_SORTIE, arguments.format)

    if tous_rejets:
        chemin_rejets = os.path.join(arguments.sortie, "rejets.%s" % extension)
        contrat.ecrire(chemin_rejets, tous_rejets,
                       contrat.CHAMPS_ENTREE + ["motif", "_source", "_ligne"],
                       arguments.format)
        print("\n  %d rejet(s) traces dans %s" % (len(tous_rejets), os.path.basename(chemin_rejets)))

    if not arguments.sans_journal:
        nouveaux = journaliser(arguments.journal, routees, horodatage)
        print("  journal : %d nouvelle(s) cible(s), %d deja connue(s) -> %s"
              % (nouveaux, len(routees) - nouveaux, arguments.journal))

    print("\n  sortie  %s" % chemin_global)
    print("=" * 72)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except contrat.ErreurContrat as erreur:
        print("ARRET : %s" % erreur, file=sys.stderr)
        sys.exit(2)
