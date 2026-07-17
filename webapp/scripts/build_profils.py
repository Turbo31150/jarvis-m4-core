#!/usr/bin/env python3
"""Base d'ADAPTATIONS PAR PROFIL D'ÉLÈVE — différenciation, actions rapides (0-IA).
Pour chaque profil (dys, TDAH, TSA, allophone, HPI, PPRE…) : besoins, aménagements
pédagogiques, matériel, évaluation adaptée. Pré-généré → l'enseignante pioche vite.
Table `adaptations` dans ecole.db + support HTML copiable/imprimable dans static/profils/."""

import os
import sqlite3
import html

WEBAPP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(WEBAPP, "ecole.db")
OUT = os.path.join(WEBAPP, "static", "profils")

# (profil, besoins, aménagements, matériel, évaluation)
PROFILS = [
    (
        "Dyslexie / Dysorthographie",
        "Décodage lent et coûteux, fatigue en lecture, orthographe instable.",
        "Textes aérés (police Arial/OpenDyslexic 14, interligne 1.5) ; lire les consignes à voix haute ; ne pas faire lire à voix haute devant la classe sans accord ; segmenter les tâches ; valoriser l'oral.",
        "Règle-cache / fenêtre de lecture, surligneurs, dictée à trous, cartes-sons, ordinateur avec correcteur si PAP.",
        "Ne pas pénaliser l'orthographe hors dictée ; barème allégé ; tiers-temps ; consigne relue.",
    ),
    (
        "Dyspraxie",
        "Geste moteur et coordination difficiles, écriture lente/illisible, repérage spatial fragile.",
        "Limiter la copie (fournir les traces écrites) ; agrandir les supports ; cases/lignes repères ; privilégier le clavier ; éviter les tableaux à double entrée complexes.",
        "Cahier à gros carreaux/lignes Seyès agrandies, guide-doigt, ciseaux adaptés, plan incliné, gabarits.",
        "Évaluer les connaissances, pas le geste ; oral ou QCM ; ne pas noter le soin ; tiers-temps.",
    ),
    (
        "Dyscalculie",
        "Sens du nombre fragile, mémorisation des faits numériques difficile, procédures instables.",
        "Manipulation systématique avant l'abstrait ; autoriser table de multiplication et bandes numériques ; décomposer les problèmes ; verbaliser les étapes.",
        "Jetons, réglettes Cuisenaire, bande numérique, boulier, table de Pythagore, calculatrice si PAP.",
        "Évaluer le raisonnement, pas le calcul mental ; problèmes lus ; outils autorisés.",
    ),
    (
        "TDAH (attention / hyperactivité)",
        "Attention labile, impulsivité, difficulté à rester en place et à s'organiser.",
        "Consignes courtes et une à la fois ; place au calme, près de l'enseignante ; pauses motrices ; time-timer visible ; renforcement positif immédiat ; routines claires.",
        "Time-timer, sablier, casque anti-bruit, sous-main avec étapes, balle anti-stress, ceinture lestée.",
        "Fractionner l'évaluation ; temps supplémentaire ; environnement calme ; consignes rappelées.",
    ),
    (
        "TSA (trouble du spectre autistique)",
        "Besoin de prévisibilité, sensibilité sensorielle, communication et implicite difficiles.",
        "Emploi du temps visuel (pictos), anticiper les changements, consignes explicites et littérales, espace refuge, éviter le second degré, séquentialiser.",
        "Pictogrammes/PECS, emploi du temps visuel, timer, casque anti-bruit, coin calme, scénarios sociaux.",
        "Consignes explicites, éviter les doubles sens, format habituel, temps adapté, valoriser les intérêts spécifiques.",
    ),
    (
        "Allophone (EANA — élève nouvellement arrivé)",
        "Français en cours d'acquisition, lexique scolaire limité, culture scolaire différente.",
        "Appui visuel systématique (images, gestes) ; lexique bilingue ; tutorat par un pair ; simplifier la langue des consignes sans appauvrir le contenu ; valoriser la langue d'origine.",
        "Imagiers thématiques, dictionnaire bilingue/traducteur, étiquettes-mots, supports visuels, cahier de sons.",
        "Évaluer les compétences non-langagières à part ; consignes illustrées ; oral privilégié ; ne pas sanctionner la langue.",
    ),
    (
        "HPI / élève à haut potentiel",
        "Rapidité, besoin de sens et de défi, ennui possible, perfectionnisme.",
        "Approfondissement et enrichissement (pas plus du même) ; projets autonomes ; tutorat d'un pair ; questions ouvertes ; droit à l'erreur travaillé.",
        "Fichiers d'approfondissement, défis logiques, projets de recherche, accès documentaire, jeux de stratégie.",
        "Tâches complexes et ouvertes ; valoriser la démarche ; éviter la répétition.",
    ),
    (
        "Trouble du langage oral (dysphasie)",
        "Expression et/ou compréhension orale altérées, lexique et syntaxe fragiles.",
        "Phrases courtes, débit lent, reformulation, appui gestuel et visuel ; laisser le temps de répondre ; ne pas finir les phrases à sa place.",
        "Pictogrammes, Makaton/gestes, imagiers, supports visuels de consigne, coin langage.",
        "Privilégier le pointage/QCM ; ne pas évaluer la forme orale ; temps de latence accepté.",
    ),
    (
        "Déficience visuelle",
        "Fatigue visuelle, accès aux supports écrits limité.",
        "Agrandir (A3, police 18-24), fort contraste, placer près du tableau, verbaliser ce qui est écrit, éviter le bleu/vert peu contrasté.",
        "Supports agrandis, contraste renforcé, loupe, pupitre, matériel tactile, plage braille si besoin.",
        "Supports adaptés fournis ; tiers-temps ; oral possible ; consignes verbalisées.",
    ),
    (
        "Difficulté scolaire (PPRE / élève fragile)",
        "Acquis fragiles, lenteur, faible estime de soi, découragement.",
        "Objectifs prioritaires ciblés, étayage rapproché, réussite garantie au départ, valorisation, aide des pairs, quantité réduite mais exigence maintenue.",
        "Fiches de soutien (niveau Soutien de la banque !), affichages d'aide, sous-main, cahier de réussites.",
        "Évaluer les objectifs prioritaires ; barème adapté ; valoriser les progrès ; évaluation positive.",
    ),
]


def build():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS adaptations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profil TEXT UNIQUE, besoins TEXT, amenagements TEXT, materiel TEXT, evaluation TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')))""")
    for p in PROFILS:
        c.execute(
            """INSERT INTO adaptations(profil,besoins,amenagements,materiel,evaluation) VALUES(?,?,?,?,?)
                     ON CONFLICT(profil) DO UPDATE SET besoins=excluded.besoins,amenagements=excluded.amenagements,
                       materiel=excluded.materiel,evaluation=excluded.evaluation""",
            p,
        )
    c.commit()
    n = c.execute("SELECT COUNT(*) FROM adaptations").fetchone()[0]
    # support HTML
    os.makedirs(OUT, exist_ok=True)
    e = html.escape
    cards = []
    for pr, be, am, ma, ev in c.execute(
        "SELECT profil,besoins,amenagements,materiel,evaluation FROM adaptations ORDER BY profil"
    ):
        cards.append(
            f'<div class="p"><h3>{e(pr)}</h3>'
            f"<p><b>🎯 Besoins :</b> {e(be)}</p>"
            f"<p><b>🛠️ Aménagements :</b> {e(am)}</p>"
            f"<p><b>🎒 Matériel :</b> {e(ma)}</p>"
            f"<p><b>📝 Évaluation :</b> {e(ev)}</p></div>"
        )
    css = (
        "body{font-family:system-ui,sans-serif;max-width:860px;margin:auto;padding:28px;background:#f7f5ef;color:#222}"
        "h1{color:#1a6a4a}.p{background:#fff;border:1px solid #e2ddd0;border-left:4px solid #1a6a4a;border-radius:10px;padding:16px;margin:14px 0}"
        "h3{color:#c0693a;margin:0 0 10px}p{margin:6px 0;font-size:14px;line-height:1.5}"
        "@media print{.p{page-break-inside:avoid}}"
    )
    doc = (
        f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Adaptations par profil — Pousseline</title>'
        f"<style>{css}</style></head><body><h1>🧩 Adaptations par profil d'élève</h1>"
        f"<p>{n} profils — aménagements pédagogiques prêts à appliquer (dys, TDAH, TSA, allophone, HPI, PPRE…). "
        f"Repère le profil, applique les aménagements. Ctrl+P pour joindre à un PPRE/PAP.</p>{''.join(cards)}</body></html>"
    )
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(doc)
    c.close()
    print(
        f"✅ {n} profils en base (table adaptations) + support static/profils/index.html"
    )


if __name__ == "__main__":
    build()
