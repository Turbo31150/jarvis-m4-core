#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dispatch_adequation.py — mesure, offre par offre, l'ecart entre ce que
l'annonce demande et ce que Franck sait faire.

POURQUOI : l'agent classe les offres sur le LEVIER (grand employeur, mention
handicap, CDI, lieu). Il ne dit rien de l'ADEQUATION technique. Une offre a
100 points de levier mais exigeant VMware + Ansible + Active Directory reste
une mauvaise candidature. Ce script comble ce trou.

AUCUN LLM — et c'est un choix, pas une contrainte :
apparier un vocabulaire technique contre une liste de competences est de
l'appariement exact, pas de la redaction. Le passage precedent (enrichissement)
a montre qu'un LLM sur ce type de tache ajoute du bruit, pas du signal.
  → 0 token, 0 chaleur, resultat instantane et reproductible.

PIEGE EVITE (mesure le 2026-08-19) : chercher les technos en sous-chaine donne
« san » dans 68 offres sur 98 — il capte « sans », « sante », « croissance ».
Toute recherche se fait donc par mots entiers.

Referentiel : CV_Franck_Delmas_INFRASTRUCTURES_20260819.md, section
« Environnement technique maitrise ». Rien n'est ajoute qui n'y figure pas :
une candidature ne se batit pas sur une competence supposee.
"""
import os
import re
import sqlite3
import sys

DB = os.path.expanduser("~/jarvis/data/emploi_rqth.db")

# (motif, libelle, maitrise) — maitrise=True uniquement si la competence
# figure noir sur blanc dans le CV du 19/08.
TECHNOS = [
    # --- maitrisees (CV, section « Environnement technique maitrise ») ---
    (r"\blinux\b|\bubuntu\b|\bdebian\b",        "Linux",            True),
    (r"\bsystemd\b",                            "systemd",          True),
    (r"\bwindows\b",                            "Windows",          True),
    (r"\bdocker\b|\bconteneur",                 "Docker",           True),
    (r"\bpostgres(?:ql)?\b",                    "PostgreSQL",       True),
    (r"\bsqlite\b",                             "SQLite",           True),
    (r"\bredis\b",                              "Redis",            True),
    (r"\belastic(?:search)?\b",                 "Elasticsearch",    True),
    (r"\bpython\b",                             "Python",           True),
    (r"\bbash\b|\bshell\b|\bscripting\b",       "Bash",             True),
    (r"\bsql\b",                                "SQL",              True),
    (r"\bjavascript\b|\btypescript\b",          "JavaScript",       True),
    (r"\bssh\b",                                "SSH",              True),
    (r"\bvpn\b",                                "VPN",              True),
    (r"\bdhcp\b",                               "DHCP",             True),
    (r"\bdns\b",                                "DNS",              True),
    (r"\bgrafana\b",                            "Grafana",          True),
    (r"\bprometheus\b",                         "Prometheus",       True),
    (r"\bsupervision\b|\bmonitoring\b",         "Supervision",      True),
    (r"\bsauvegarde|\bbackup\b",                "Sauvegardes",      True),
    (r"\bgit\b",                                "Git",              True),
    (r"\bnvidia\b|\bcuda\b|\bgpu\b",            "GPU/CUDA",         True),
    # --- NON maitrisees : absentes du CV, donc comptees comme ecart ---
    (r"\bansible\b",                            "Ansible",          False),
    (r"\bvmware\b|\bvsphere\b|\besxi\b",        "VMware",           False),
    (r"\bkubernetes\b|\bk8s\b",                 "Kubernetes",       False),
    (r"\bactive directory\b|\bad ds\b",         "Active Directory", False),
    (r"\bazure\b",                              "Azure",            False),
    (r"\baws\b",                                "AWS",              False),
    (r"\bpowershell\b",                         "PowerShell",       False),
    (r"\bcitrix\b",                             "Citrix",           False),
    (r"\bproxmox\b",                            "Proxmox",          False),
    (r"\bnagios\b|\bzabbix\b|\bcentreon\b",     "Nagios/Zabbix",    False),
    (r"\bitil\b",                               "ITIL",             False),
    (r"\bjenkins\b|\bgitlab.ci\b",              "CI/CD outillé",    False),
    (r"\boracle\b",                             "Oracle",           False),
    (r"\bmysql\b|\bmariadb\b",                  "MySQL",            False),
    (r"\bveeam\b",                              "Veeam",            False),
    (r"\bfirewall\b|\bpare-feu\b|\bfortinet\b", "Pare-feu",         False),
]


def db():
    c = sqlite3.connect(DB, timeout=30)
    for col in ("techs_ok", "techs_manquantes", "couverture_pct"):
        typ = "INTEGER" if col == "couverture_pct" else "TEXT"
        try:
            c.execute("ALTER TABLE offres ADD COLUMN %s %s" % (col, typ))
        except sqlite3.OperationalError:
            pass
    c.commit()
    return c


def analyser(texte):
    t = (texte or "").lower()
    ok, manque = [], []
    for motif, libelle, maitrise in TECHNOS:
        if re.search(motif, t):
            (ok if maitrise else manque).append(libelle)
    total = len(ok) + len(manque)
    couverture = round(100 * len(ok) / total) if total else 0
    return ok, manque, couverture


def main():
    c = db()
    lignes = c.execute("""SELECT id_offre, texte_detail FROM offres
                          WHERE texte_detail IS NOT NULL""").fetchall()
    if not lignes:
        print("Aucune offre enrichie — lance d'abord dispatch_enrichir_offres.py")
        return
    n = 0
    with c:
        for oid, txt in lignes:
            ok, manque, cov = analyser(txt)
            c.execute("""UPDATE offres SET techs_ok=?, techs_manquantes=?,
                         couverture_pct=? WHERE id_offre=?""",
                      (", ".join(ok), ", ".join(manque), cov, oid))
            n += 1
    print("  %d offres analysees (0 token, 0 LLM)" % n)

    print("\n  === REPARTITION DE LA COUVERTURE ===")
    for seuil, lib in ((90, "90-100 % — quasi parfait"),
                       (75, "75-89 %  — tres bon"),
                       (60, "60-74 %  — correct"),
                       (40, "40-59 %  — a evaluer"),
                       (0,  "0-39 %   — trop d'ecart")):
        haut = {90: 101, 75: 90, 60: 75, 40: 60, 0: 40}[seuil]
        k = c.execute("""SELECT count(*) FROM offres
                         WHERE couverture_pct>=? AND couverture_pct<?""",
                      (seuil, haut)).fetchone()[0]
        print("   %-26s %s (%d)" % (lib, "█" * k, k))
    c.close()


if __name__ == "__main__":
    main()
