#!/usr/bin/env python3
"""Vague CASCADE — simulation d'une année de classe (PE maternelle/primaire).
Pour chaque scénario récurrent de l'année, un modèle prêt à l'emploi (0-IA).
Étend la table `modeles` (ecole.db), puis régénère le support HTML via build_modeles.
Idempotent (UPSERT sur titre). But : devancer TOUTES les tâches, maximiser l'automatisation."""

import os
import sqlite3
import importlib.util

WEBAPP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(WEBAPP, "ecole.db")

# Scénarios de l'année → (categorie, titre, corps). Placeholders {..} à adapter.
ANNEE = [
    # ── RENTRÉE / DÉBUT D'ANNÉE ──
    (
        "Rentrée",
        "Mot de bienvenue (rentrée)",
        "Bonjour à tous,\n\nBienvenue en classe de {classe} ! Je suis {enseignante} et j'accompagnerai votre enfant cette année. Nous allons vivre une belle année d'apprentissages et de découvertes.\nN'hésitez pas à me solliciter via le cahier de liaison. Une réunion de rentrée aura lieu le {date}.\n\nBien cordialement,\n{enseignante}",
    ),
    (
        "Rentrée",
        "Liste de fournitures",
        "FOURNITURES — classe de {classe} — année {annee}\n\nMerci de prévoir pour la rentrée :\n- {item1}\n- {item2}\n- {item3}\nTout doit être marqué au prénom de l'enfant. La coopérative fournit {fourni_coop}.\nMerci de votre collaboration.\n{enseignante}",
    ),
    (
        "Rentrée",
        "Règles de vie de la classe",
        "NOS RÈGLES DE VIE — classe de {classe}\n\n1. Je respecte les autres (paroles et gestes doux).\n2. J'écoute et je lève le doigt pour parler.\n3. Je prends soin du matériel.\n4. Je range après une activité.\n5. Je me déplace calmement.\nAffiché en classe et co-construit avec les élèves.",
    ),
    (
        "Rentrée",
        "Appel cotisation coopérative",
        "Bonjour,\n\nLa coopérative scolaire finance les sorties, le matériel et les projets de la classe. La cotisation (libre et facultative) est de {montant} € par famille pour l'année.\nMerci de votre participation selon vos possibilités (chèque à l'ordre de {ordre}).\n{enseignante}",
    ),
    # ── SANTÉ ──
    (
        "Santé",
        "Information poux",
        "Bonjour,\n\nDes poux ont été signalés dans la classe. Merci de vérifier la tête de votre enfant et de traiter si nécessaire. Un traitement simultané de toute la famille évite les récidives.\nMerci de votre vigilance.\n{enseignante}",
    ),
    (
        "Santé",
        "Mise en place d'un PAI",
        "Objet : Projet d'Accueil Individualisé — {prenom} {nom}\n\nSuite à {situation}, je vous propose de mettre en place un PAI avec le médecin scolaire. Merci de me retourner l'ordonnance / le protocole afin d'organiser une rencontre.\nCela permettra d'accueillir votre enfant en toute sécurité.\n{enseignante}",
    ),
    (
        "Santé",
        "Signalement épidémie / gastro",
        "Bonjour,\n\nPlusieurs cas de {maladie} ont été constatés. Par précaution, nous renforçons le lavage des mains. Gardez votre enfant à la maison en cas de symptômes (fièvre, vomissements) au moins {duree}.\nMerci de votre compréhension.\n{enseignante}",
    ),
    # ── ÉVÉNEMENTS / PROJETS ──
    (
        "Événements",
        "Information photos scolaires",
        "Bonjour,\n\nLes photos scolaires (individuelle et de classe) auront lieu le {date}. Aucun achat n'est obligatoire. Les pochettes seront distribuées ensuite ; vous choisirez librement.\n{enseignante}",
    ),
    (
        "Événements",
        "Appel aux parents accompagnateurs",
        "Bonjour,\n\nPour la sortie du {date} à {lieu}, j'ai besoin de {nb} parents accompagnateurs (départ {heure}, retour {heure_retour}). Merci de vous signaler via le coupon ci-dessous. Votre aide est précieuse !\n{enseignante}",
    ),
    (
        "Événements",
        "Invitation spectacle / kermesse",
        "Bonjour,\n\nLes élèves vous présenteront {evenement} le {date} à {heure} ({lieu}). Ils ont hâte de vous montrer leur travail !\nEntrée libre — venez nombreux.\n{enseignante}",
    ),
    (
        "Événements",
        "Remerciement parents accompagnateurs",
        "Bonjour,\n\nUn grand merci à {parents} qui ont accompagné la sortie du {date}. Grâce à vous, la journée a été une réussite et les enfants ont adoré.\nAvec toute ma reconnaissance,\n{enseignante}",
    ),
    # ── ÉVALUATION / LIVRET ──
    (
        "Livret / LSU",
        "Remise du livret scolaire",
        "Bonjour,\n\nLe livret scolaire de {prenom} pour la période {periode} sera remis le {date}. Il valorise ses réussites et ses progrès. Je reste disponible pour un rendez-vous si vous souhaitez en échanger.\n{enseignante}",
    ),
    (
        "Livret / LSU",
        "Invitation remise de bulletin en main propre",
        "Bonjour,\n\nJe vous propose un temps d'échange autour du bilan de {prenom}, le {date} entre {heure} et {heure_fin}. Merci d'indiquer votre créneau. En cas d'empêchement, le livret sera transmis par le cahier.\n{enseignante}",
    ),
    # ── VIE DE CLASSE (maternelle) ──
    (
        "Vie de classe",
        "Rappel horaires / ponctualité",
        "Bonjour,\n\nPetit rappel : la classe ouvre à {heure_ouverture} et les apprentissages commencent dès l'accueil. Merci d'arriver à l'heure — les retards répétés perturbent le groupe et votre enfant.\nMerci de votre compréhension.\n{enseignante}",
    ),
    (
        "Vie de classe",
        "Doudou / objet transitionnel (mater)",
        "Bonjour,\n\nVotre enfant peut apporter son doudou pour la sieste / les moments calmes. Il sera rangé dans sa case le reste du temps et repartira chaque {jour} pour être lavé. Merci de le marquer à son prénom.\n{enseignante}",
    ),
    (
        "Vie de classe",
        "Change / propreté (PS)",
        "Bonjour,\n\nPour accompagner votre enfant, merci de laisser dans son sac un change complet (culotte, pantalon, chaussettes) marqué à son prénom. Les petits accidents sont normaux à cet âge et gérés avec bienveillance.\n{enseignante}",
    ),
    (
        "Vie de classe",
        "Emprunt bibliothèque de classe",
        "Bonjour,\n\nVotre enfant a emprunté « {livre} » dans la bibliothèque de classe. Merci d'en prendre soin et de le rapporter le {date_retour}. Bonne lecture partagée !\n{enseignante}",
    ),
    (
        "Vie de classe",
        "Organisation anniversaire en classe",
        "Bonjour,\n\nNous fêterons l'anniversaire de {prenom} le {date}. Si vous le souhaitez, vous pouvez apporter {gouter} (sans allergène majeur, gâteau du commerce avec étiquette de préférence). Merci de me prévenir.\n{enseignante}",
    ),
    # ── FIN D'ANNÉE ──
    (
        "Fin d'année",
        "Mot de fin d'année",
        "Chers parents,\n\nCette année s'achève. Quel plaisir d'avoir accompagné vos enfants ! Ils ont tant grandi et progressé. Je vous remercie pour votre confiance et votre collaboration tout au long de l'année.\nBel été à tous,\n{enseignante}",
    ),
    (
        "Fin d'année",
        "Information passage classe supérieure",
        "Bonjour,\n\n{prenom} passera en {classe_sup} à la rentrée. Le dossier a été transmis à l'équipe. Je reste disponible pour toute question sur cette continuité.\nBonnes vacances,\n{enseignante}",
    ),
    # ── RÉUNIONS COMPLÉMENTAIRES ──
    (
        "Réunions",
        "Ordre du jour — Conseil d'école",
        "CONSEIL D'ÉCOLE — {date}\n\n1. Règlement intérieur / charte laïcité\n2. Sécurité (PPMS, exercices) et travaux\n3. Projets et sorties de l'année\n4. Bilan et budget de la coopérative\n5. Restauration et périscolaire\n6. Questions des parents élus\n\nSecrétaire : {secretaire}",
    ),
    (
        "Réunions",
        "Ordre du jour — Conseil de maîtres (répartition)",
        "CONSEIL DES MAÎTRES — Répartition {annee} — {date}\n\n1. Effectifs prévisionnels par niveau\n2. Propositions de répartition des classes\n3. Décloisonnements / échanges de service\n4. Élèves à suivre (dossiers, PPS, maintiens)\n5. Commandes et budget\n6. Calendrier des temps forts",
    ),
    # ── ABSENCES / DISCIPLINE ──
    (
        "Absences",
        "Accusé de réception justificatif",
        "Bonjour,\n\nJ'accuse réception du justificatif d'absence de {prenom} pour le(s) {dates}. Je vous en remercie.\nBonne journée,\n{enseignante}",
    ),
    (
        "Vie de classe",
        "Signalement incident (mot mesuré)",
        "Bonjour,\n\nAujourd'hui, {prenom} a {incident}. Nous en avons discuté ensemble calmement. Je préfère vous en informer pour que nous soyons cohérents. Rien de grave, mais un point d'attention.\nBien cordialement,\n{enseignante}",
    ),
]


def load_build():
    spec = importlib.util.spec_from_file_location(
        "build_modeles", os.path.join(os.path.dirname(__file__), "build_modeles.py")
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS modeles(
        id INTEGER PRIMARY KEY AUTOINCREMENT, categorie TEXT, titre TEXT UNIQUE, corps TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')))""")
    n = 0
    for cat, titre, corps in ANNEE:
        c.execute(
            """INSERT INTO modeles(categorie,titre,corps) VALUES(?,?,?)
                     ON CONFLICT(titre) DO UPDATE SET categorie=excluded.categorie, corps=excluded.corps""",
            (cat, titre, corps),
        )
        n += 1
    c.commit()
    c.close()
    print(f"✅ +{n} modèles-scénarios de l'année insérés")
    # régénère le support HTML depuis TOUTE la table
    load_build().build()


if __name__ == "__main__":
    main()
