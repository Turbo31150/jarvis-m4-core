#!/usr/bin/env python3
"""Banque de modèles administratifs prêts à l'emploi (0-IA, production immédiate).
Devance les tâches récurrentes : mails parents, ordres du jour de réunion, absences,
autorisations. Placeholders {prenom},{date},{heure},{motif}… à adapter.
Écrit dans ecole.db (table `modeles`) + génère un classeur HTML copiable/imprimable.
Idempotent (UPSERT sur titre)."""

import sqlite3
import os
import html

WEBAPP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(WEBAPP, "ecole.db")
OUT = os.path.join(WEBAPP, "static", "modeles")

# (categorie, titre, corps)
MODELES = [
    # ── MAILS / MOTS AUX PARENTS ──
    (
        "Mail parents",
        "Information sortie scolaire",
        "Bonjour,\n\nLa classe de {classe} participera à une sortie à {lieu} le {date}. Départ {heure_depart}, retour prévu {heure_retour}. Prévoir une tenue adaptée et un pique-nique.\nMerci de signer et retourner l'autorisation ci-jointe avant le {date_limite}.\n\nBien cordialement,\n{enseignante}",
    ),
    (
        "Mail parents",
        "Demande de rendez-vous",
        "Bonjour,\n\nJe souhaiterais échanger avec vous au sujet de {prenom}. Seriez-vous disponible le {date} à {heure}, ou préférez-vous une autre proposition ?\nVous pouvez me répondre par le cahier de liaison ou par mail.\n\nBien cordialement,\n{enseignante}",
    ),
    (
        "Mail parents",
        "Comportement positif / progrès",
        "Bonjour,\n\nJe tenais à vous partager une belle réussite : {prenom} a fait de réels progrès en {domaine} cette période. {precisions}\nBravo à lui/elle, et merci pour votre soutien à la maison.\n\nBien cordialement,\n{enseignante}",
    ),
    (
        "Mail parents",
        "Difficulté rencontrée (bienveillant)",
        "Bonjour,\n\nJe reviens vers vous concernant {prenom}. J'observe depuis quelque temps {difficulte}. Rien d'inquiétant, mais je préfère vous en informer pour que nous puissions l'accompagner ensemble.\nJe reste disponible pour en discuter.\n\nBien cordialement,\n{enseignante}",
    ),
    (
        "Mail parents",
        "Objet / vêtement oublié",
        "Bonjour,\n\n{prenom} a oublié {objet} en classe / à la cantine. Vous pouvez le récupérer auprès de moi aux heures d'entrée et de sortie.\nPensez à noter le prénom sur les affaires, cela facilite les retrouvailles !\n\nBien cordialement,\n{enseignante}",
    ),
    (
        "Mail parents",
        "Rappel matériel / équipement",
        "Bonjour,\n\nPetit rappel : merci de prévoir {materiel} pour {prenom} d'ici le {date}. {precisions}\nMerci de votre aide.\n\nBien cordialement,\n{enseignante}",
    ),
    (
        "Mail parents",
        "Invitation réunion de rentrée",
        "Bonjour,\n\nJe vous invite à la réunion de rentrée de la classe de {classe}, le {date} à {heure} en salle {salle}. Nous y présenterons le fonctionnement de la classe, les projets de l'année et le matériel.\nVotre présence est importante ; en cas d'empêchement, n'hésitez pas à me solliciter.\n\nBien cordialement,\n{enseignante}",
    ),
    # ── ABSENCES ──
    (
        "Absences",
        "Relance absence non justifiée",
        "Bonjour,\n\n{prenom} était absent(e) le {date} et je n'ai pas reçu de justificatif. Merci de m'indiquer le motif par écrit (mot dans le cahier ou mail), conformément au règlement.\nPrenez soin de vous.\n\nBien cordialement,\n{enseignante}",
    ),
    (
        "Absences",
        "Demande de justificatif médical",
        "Bonjour,\n\nSuite à l'absence de {prenom} du {date_debut} au {date_fin}, merci de fournir un justificatif (mot des parents ou certificat médical si absence de plus de 3 jours).\n\nBien cordialement,\n{enseignante}",
    ),
    (
        "Absences",
        "Signalement absentéisme (direction)",
        "Objet : signalement — {prenom} {nom}, classe {classe}\n\nJe signale des absences répétées et non justifiées : {liste_dates}. Total : {nb} demi-journées sur la période.\nDémarches déjà effectuées : {demarches}. Je sollicite un suivi.\n\n{enseignante}",
    ),
    # ── RÉUNIONS — ORDRES DU JOUR ──
    (
        "Réunions",
        "Ordre du jour — Conseil des maîtres",
        "CONSEIL DES MAÎTRES — {date}\n\n1. Organisation de la période / calendrier\n2. Projets d'école en cours\n3. Répartition des services (récréations, décloisonnements)\n4. Élèves à besoins particuliers (PPRE, PAP, PPS)\n5. Sécurité / PPMS / exercices\n6. Questions diverses\n\nSecrétaire de séance : {secretaire}",
    ),
    (
        "Réunions",
        "Ordre du jour — Conseil de cycle 1",
        "CONSEIL DE CYCLE 1 — {date}\n\n1. Harmonisation des progressions (5 domaines BO 2026)\n2. Évaluation positive / carnet de suivi\n3. Continuité PS→MS→GS et liaison GS/CP\n4. Coins d'apprentissage et ateliers autonomes\n5. Projets communs (spectacle, sorties)\n6. Questions diverses",
    ),
    (
        "Réunions",
        "Ordre du jour — Équipe éducative",
        "ÉQUIPE ÉDUCATIVE — {prenom} {nom} — {date}\n\n1. Présentation de la situation de l'élève\n2. Observations de l'enseignant(e) (points d'appui / difficultés)\n3. Parole des parents\n4. Bilans des intervenants ({intervenants})\n5. Propositions d'aménagements / d'aides\n6. Décisions et prochaines étapes\n\nParticipants : {participants}",
    ),
    (
        "Réunions",
        "Compte-rendu — trame vierge",
        "COMPTE-RENDU — {titre} — {date}\nPrésents : {presents}\nExcusés : {excuses}\n\nPoints abordés :\n1. {point1}\n2. {point2}\n\nDécisions prises :\n- {decision1}\n\nActions à suivre (qui / quoi / quand) :\n- {action1}\n\nProchaine réunion : {date_prochaine}",
    ),
    # ── AUTORISATIONS ──
    (
        "Autorisations",
        "Autorisation de sortie scolaire",
        "AUTORISATION DE SORTIE SCOLAIRE\n\nJe soussigné(e) {parent}, responsable légal de {prenom} {nom} (classe {classe}),\nautorise mon enfant à participer à la sortie à {lieu} le {date} (départ {heure_depart}, retour {heure_retour}), encadrée par {encadrants}.\n☐ J'autorise   ☐ Je n'autorise pas\nParticularités de santé / PAI : {sante}\n\nDate : ................   Signature : ................",
    ),
    (
        "Autorisations",
        "Autorisation droit à l'image",
        "AUTORISATION DE DROIT À L'IMAGE — année {annee}\n\nJe soussigné(e) {parent}, responsable de {prenom} {nom},\n☐ autorise   ☐ n'autorise pas la prise de photos/vidéos de mon enfant dans le cadre scolaire et leur utilisation pour : {usages} (blog de classe, journal, exposition — usage strictement pédagogique, jamais commercial).\n\nDate : ................   Signature : ................",
    ),
    (
        "Autorisations",
        "Autorisation sortie régulière (piscine/biblio)",
        "AUTORISATION — ACTIVITÉ RÉGULIÈRE\n\nJe soussigné(e) {parent}, responsable de {prenom} {nom} (classe {classe}),\nautorise mon enfant à participer à l'activité « {activite} » se déroulant à {lieu} chaque {jour} de la période, avec déplacement {transport}.\n\nDate : ................   Signature : ................",
    ),
    (
        "Autorisations",
        "Autorisation intervention extérieure",
        "AUTORISATION — INTERVENANT EXTÉRIEUR\n\nDans le cadre du projet « {projet} », {intervenant} interviendra en classe le(s) {dates}.\nJe soussigné(e) {parent}, responsable de {prenom} {nom}, autorise mon enfant à participer à cette activité encadrée.\n\nDate : ................   Signature : ................",
    ),
]


def build():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS modeles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categorie TEXT, titre TEXT UNIQUE, corps TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')))""")
    for cat, titre, corps in MODELES:
        c.execute(
            """INSERT INTO modeles(categorie,titre,corps) VALUES(?,?,?)
                     ON CONFLICT(titre) DO UPDATE SET categorie=excluded.categorie, corps=excluded.corps""",
            (cat, titre, corps),
        )
    c.commit()
    n = c.execute("SELECT COUNT(*) FROM modeles").fetchone()[0]
    cats = c.execute(
        "SELECT categorie,COUNT(*) FROM modeles GROUP BY categorie"
    ).fetchall()
    # ── support HTML copiable/imprimable ──
    os.makedirs(OUT, exist_ok=True)
    rows = c.execute(
        "SELECT categorie,titre,corps FROM modeles ORDER BY categorie,titre"
    ).fetchall()
    body, curcat = [], None
    for cat, titre, corps in rows:
        if cat != curcat:
            curcat = cat
            body.append(f"<h2>{html.escape(cat)}</h2>")
        body.append(
            f'<div class="m"><h3>{html.escape(titre)} <button onclick="cp(this)">📋 Copier</button></h3><pre>{html.escape(corps)}</pre></div>'
        )
    css = (
        "body{font-family:system-ui,sans-serif;max-width:860px;margin:auto;padding:28px;background:#f7f5ef;color:#222}"
        "h1{color:#1a6a4a}h2{color:#1a6a4a;margin-top:28px;border-bottom:2px solid #d9d4c7;padding-bottom:4px}"
        ".m{background:#fff;border:1px solid #e2ddd0;border-radius:10px;padding:16px;margin:12px 0}"
        "h3{color:#c0693a;font-size:15px;display:flex;justify-content:space-between;align-items:center;margin:0 0 8px}"
        "button{font-size:12px;border:1px solid #1a6a4a;background:#fff;color:#1a6a4a;border-radius:6px;padding:3px 8px;cursor:pointer}"
        "pre{white-space:pre-wrap;font-family:inherit;font-size:14px;line-height:1.5;margin:0}"
        "@media print{button{display:none}.m{page-break-inside:avoid}}"
    )
    js = "function cp(b){const t=b.closest('.m').querySelector('pre').innerText;navigator.clipboard.writeText(t);b.textContent='✅ Copié';setTimeout(()=>b.textContent='📋 Copier',1500);}"
    doc = (
        f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Classeur de modèles — Pousseline</title>'
        f"<style>{css}</style></head><body><h1>🗂️ Classeur de modèles prêts à l'emploi</h1>"
        f"<p>{n} modèles — mails parents, réunions, absences, autorisations. Clique « Copier », colle, remplace les {{champs}}. Ctrl+P pour imprimer.</p>"
        f"{''.join(body)}<script>{js}</script></body></html>"
    )
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(doc)
    c.close()
    print(f"✅ {n} modèles en base ecole.db (table modeles)")
    for cat, k in cats:
        print(f"   {cat}: {k}")
    print("📄 support : static/modeles/index.html")


if __name__ == "__main__":
    build()
