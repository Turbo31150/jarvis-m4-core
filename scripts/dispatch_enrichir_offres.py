#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dispatch_enrichir_offres.py — enrichit chaque offre de emploi_rqth.db avec sa
fiche detaillee France Travail, puis re-note sur des donnees reelles.

POURQUOI : le drapeau `grand_employeur` posé à la moisson est une HEURISTIQUE
appliquée au résumé de la carte (quelques lignes). Un cabinet de recrutement y
apparaît « grand » parce qu'il cite son client. La fiche détaillée porte, elle,
le secteur, l'effectif et le texte intégral — de quoi confirmer ou infirmer.

Applique la recette dispatch-generation-masse, avec une différence qui compte :
**aucun LLM**. Extraction déterministe par expressions régulières.
  → 0 token facturé ET 0 chaleur sur le M4 (le run précédent, lui, a tenu 91 °C).
Le plafond n'est donc ni thermique ni tarifaire : c'est la politesse envers
la source. 4 workers, temporisation entre appels.

Idempotent : ne retraite que les offres dont `texte_detail` est NULL.
"""
import argparse
import html
import os
import re
import sqlite3
import sys
import threading
import time
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

DB = os.path.expanduser("~/jarvis/data/emploi_rqth.db")
JOURNAL = os.path.expanduser("~/jarvis/logs/dispatch_enrichir.log")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
BASE = "https://candidat.francetravail.fr/offres/recherche/detail"

ESSAIS = 3
TEMPO = 0.7            # politesse : on n'inonde pas une source publique
_verrou = threading.Lock()
_faits = {"n": 0}

# Repris de l'agent, pour re-noter sur le texte integral
GRANDS_EMPLOYEURS = {
    "airbus", "atr", "thales", "safran", "continental", "liebherr",
    "latecoere", "actia", "sopra", "steria", "capgemini", "atos", "eviden",
    "cgi", "orange", "sfr", "bouygues", "free", "iliad", "berger-levrault",
    "pierre fabre", "sanofi", "cnes", "meteo-france", "chu", "onera", "cnrs",
    "toulouse metropole", "conseil departemental", "region occitanie",
    "alten", "expleo", "scalian", "akkodis", "sogeti", "ibm", "dell",
    "infotel", "neurones", "econocom", "inetum", "inserm", "universite",
    "la poste", "sncf", "edf", "enedis", "engie", "veolia", "suez",
    "carrefour", "leclerc", "decathlon", "credit agricole", "bnp",
    "societe generale", "caisse d'epargne", "banque populaire", "harmonie",
    "cpam", "urssaf", "assurance maladie", "collins", "honeywell",
    "altran", "assystem", "segula", "ausy", "modis", "randstad", "manpower",
    "adecco", "derichebourg", "onet", "spie", "vinci", "eiffage", "nxp",
    "siemens", "schneider",
}
SIGNAUX_HANDICAP = [
    "rqth", "travailleur handicape", "travailleurs handicapes",
    "mission handicap", "situation de handicap", "oeth", "agefiph",
    "handicap", "diversite et inclusion", "obligation d'emploi",
]


def sans_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "")
                   if unicodedata.category(c) != "Mn").lower()


def log(msg):
    ligne = "%s %s" % (time.strftime("%H:%M:%S"), msg)
    print(ligne, flush=True)
    with _verrou:
        with open(JOURNAL, "a", encoding="utf-8") as f:
            f.write(ligne + "\n")


def db():
    c = sqlite3.connect(DB, timeout=30)
    c.execute("PRAGMA journal_mode=WAL")
    for col, typ in (("texte_detail", "TEXT"), ("secteur", "TEXT"),
                     ("effectif", "TEXT"), ("score_verifie", "INTEGER"),
                     ("grand_confirme", "INTEGER"), ("enrichi_le", "TEXT")):
        try:
            c.execute("ALTER TABLE offres ADD COLUMN %s %s" % (col, typ))
        except sqlite3.OperationalError:
            pass   # colonne deja presente : relance idempotente
    c.commit()
    return c


def http(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def texte_utile(page):
    """Isole la description de CETTE offre — surtout pas la page entiere.

    Lecon du premier passage (2026-08-19) : lire toute la page a detruit le
    pouvoir discriminant du score. Deux pollutions, mesurees :
      - « handicap » apparait sur 98 pages sur 98, via un avertissement de
        navigation (« carte Mappy non accessible aux personnes en situation
        de handicap ») — rien a voir avec l'employeur.
      - Un encart « deja vu » liste D'AUTRES offres : le nom « Thales » y
        figurait, faisant passer 69 offres pour de grands comptes.
    Le bloc itemprop="description" ne contient que l'offre courante.
    """
    m = re.search(r'itemprop="description"[^>]*>(.*?)</(?:div|section|p)>', page, re.S)
    brut = m.group(1) if m else ""
    if len(re.sub(r"<[^>]+>", "", brut)) < 200:
        # repli : le bloc principal, sans pied de page ni encarts lateraux
        m2 = re.search(r'(?is)<main\b.*?</main>', page)
        brut = m2.group(0) if m2 else page
    p = re.sub(r"(?is)<(script|style|noscript|aside|footer|nav).*?</\1>", " ", brut)
    p = re.sub(r"<[^>]+>", " ", p)
    return re.sub(r"\s+", " ", html.unescape(p)).strip()


def champ(page, motifs):
    for m in motifs:
        x = re.search(m, page, re.I | re.S)
        if x:
            v = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x.group(1)))).strip()
            if v:
                return v[:160]
    return ""


def worker(rid, oid, employeur_carte, total):
    for essai in range(1, ESSAIS + 1):
        try:
            page = http("%s/%s" % (BASE, oid))
            txt = texte_utile(page)
            if len(txt) < 200:
                raise ValueError("description trop maigre (%d car.)" % len(txt))
            plat = sans_accents(txt)

            secteur = champ(page, [r"Secteur d.activit[^<]*</\w+>\s*<[^>]*>([^<]{3,120})",
                                   r"itemprop=\"industry\"[^>]*>([^<]{3,120})"])
            effectif = champ(page, [r"(\d+\s*(?:à|a)\s*\d+\s*salari[^<]{0,30})",
                                    r"(\d{2,6}\s*salari[^<]{0,20})"])

            grand = any(g in plat for g in GRANDS_EMPLOYEURS)
            signaux = [s for s in SIGNAUX_HANDICAP if s in plat]
            cdi = "cdi" in plat or "duree indeterminee" in plat

            score = 0
            if grand:
                score += 40
            if signaux:
                score += 30
            if cdi:
                score += 15
            if "toulouse" in plat:
                score += 10

            with _verrou:
                c = sqlite3.connect(DB, timeout=30)
                c.execute("""UPDATE offres SET texte_detail=?, secteur=?, effectif=?,
                             signal_handicap=?, score_verifie=?, grand_confirme=?,
                             enrichi_le=datetime('now') WHERE id_offre=?""",
                          (txt[:20000], secteur, effectif, ", ".join(signaux[:5]),
                           score, int(grand), oid))
                c.commit()
                c.close()
                _faits["n"] += 1
                n = _faits["n"]

            marque = ""
            if grand and not employeur_carte:
                marque = " (grand employeur confirme au texte)"
            log("[%d/%d %d%%] %s score=%d%s"
                % (n, total, 100 * n // total, oid, score, marque))
            time.sleep(TEMPO)
            return True
        except Exception as e:
            if essai == ESSAIS:
                log("  [%s] ABANDON apres %d essais : %s" % (oid, ESSAIS, str(e)[:80]))
                return False
            time.sleep(2 * essai)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workers", nargs="?", type=int, default=4)
    a = ap.parse_args()

    c = db()
    trous = c.execute("""SELECT rowid, id_offre, grand_employeur FROM offres
                         WHERE texte_detail IS NULL ORDER BY score DESC""").fetchall()
    c.close()
    if not trous:
        log("Toutes les offres sont deja enrichies — rien a faire.")
        return

    t0 = time.time()
    log("=== ENRICHISSEMENT : %d offres, %d workers, 0 LLM (extraction deterministe) ==="
        % (len(trous), a.workers))
    ok = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futurs = [ex.submit(worker, r, o, g, len(trous)) for r, o, g in trous]
        for f in as_completed(futurs):
            if f.result():
                ok += 1
    log("=== TERMINE en %.0fs : %d enrichies, %d en echec ==="
        % (time.time() - t0, ok, len(trous) - ok))


if __name__ == "__main__":
    main()
