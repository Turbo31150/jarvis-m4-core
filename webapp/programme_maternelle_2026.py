#!/usr/bin/env python3
"""Programme maternelle 2026 (BO n°19 du 7 mai 2026, rentrée 2026-2027).

Détail PS/MS/GS × 5 domaines officiels × 5 périodes × 4-6 notions (titres de fiches).
Autonome (pas d'import de banque_annuelle → pas de cycle). Les clés de domaine sont
IDENTIQUES à DOMAINES_2026 de banque_annuelle.py → mapping 1:1.
Explorer le monde : 2 volets balisés en préfixe — [T/E] temps-espace, [V/M/O] vivant-matière-objets.
"""

DOM = [
    "Développement et structuration du langage oral et écrit",
    "Acquisition des premiers outils mathématiques",
    "Agir, s'exprimer, comprendre à travers l'activité physique",
    "Agir, s'exprimer, comprendre à travers les activités artistiques",
    "Explorer le monde",
]

PROGRAMME_MATERNELLE_2026 = {
    "PS": {
        DOM[0]: {
            "P1": [
                "Se présenter, nommer",
                "Comptines et jeux de doigts",
                "Écouter une histoire courte",
                "Reconnaître son prénom (photo)",
                "Vocabulaire de la classe",
            ],
            "P2": [
                "Nommer les objets du quotidien",
                "Répéter une comptine",
                "Manipuler un livre (sens)",
                "Graphisme : traits verticaux",
                "Vocabulaire du corps",
            ],
            "P3": [
                "Décrire une image simple",
                "Raconter une histoire connue",
                "Reconnaître son prénom en capitales",
                "Graphisme : traits horizontaux",
                "Les mots de la politesse",
            ],
            "P4": [
                "Dire ce que l'on fait",
                "Nouveaux jeux de doigts",
                "Reconnaître quelques lettres",
                "Graphisme : les ronds",
                "Vocabulaire des émotions de base",
            ],
            "P5": [
                "Formuler une demande",
                "Redire une comptine longue",
                "Repérer l'initiale de son prénom",
                "Graphisme : traits et ronds combinés",
                "Vocabulaire des animaux",
            ],
        },
        DOM[1]: {
            "P1": [
                "Reconnaître 1 et 2",
                "Beaucoup / pas beaucoup",
                "Trier par couleur",
                "Rituel des présents",
                "Un et plusieurs",
            ],
            "P2": [
                "Reconnaître 1, 2, 3",
                "Dénombrer jusqu'à 2",
                "Trier par taille",
                "La correspondance terme à terme",
                "Ranger deux tailles",
            ],
            "P3": [
                "Dénombrer jusqu'à 3",
                "Plus / moins",
                "Rond et carré",
                "Encastrements",
                "Autant que",
            ],
            "P4": [
                "Constellations 1-2-3",
                "Comparer deux collections",
                "Ranger petit → grand",
                "Rythme à 2 couleurs",
                "La file numérique jusqu'à 3",
            ],
            "P5": [
                "Associer quantité et doigts",
                "Donner juste ce qu'il faut",
                "Les formes dans l'espace",
                "Puzzle 4-6 pièces",
                "Compter les marches",
            ],
        },
        DOM[2]: {
            "P1": [
                "Courir et s'arrêter au signal",
                "Marcher sur un chemin",
                "Rondes et jeux dansés",
                "Investir la salle de motricité",
                "Ramper sous un obstacle",
            ],
            "P2": [
                "Sauter à pieds joints",
                "Rouler sur un tapis",
                "Lancer une balle",
                "Se déplacer à quatre pattes",
                "Danser avec un foulard",
            ],
            "P3": [
                "Grimper et descendre",
                "Franchir des obstacles bas",
                "Attraper un ballon",
                "Jeux dansés à consignes",
                "Pousser, tirer un objet",
            ],
            "P4": [
                "Sauter d'un petit banc",
                "Parcours simple enchaîné",
                "Lancer dans une cible large",
                "Se déplacer en rythme",
                "Jeu de poursuite (le loup)",
            ],
            "P5": [
                "Enchaîner deux actions",
                "Équilibre sur une poutre basse",
                "Viser un panier",
                "Ronde collective",
                "Jeu collectif à règle simple",
            ],
        },
        DOM[3]: {
            "P1": [
                "Peindre avec les mains",
                "Écouter un son",
                "Coller des gommettes",
                "Chanter une comptine",
                "Explorer les feutres",
            ],
            "P2": [
                "Peindre au rouleau",
                "Modeler la pâte",
                "Assembler des formes",
                "Frapper un rythme simple",
                "Traces avec les doigts",
            ],
            "P3": [
                "Empreintes et tampons",
                "Boudins et boules en pâte",
                "Collage libre",
                "Bouger sur la musique",
                "Les couleurs primaires",
            ],
            "P4": [
                "Peindre au pinceau large",
                "Déchirer-coller du papier",
                "Comptine à gestes",
                "Jouer des maracas",
                "Découvrir une image d'artiste",
            ],
            "P5": [
                "Composer avec des gommettes",
                "Modeler un objet simple",
                "Chanter en groupe",
                "Reproduire un rythme corporel",
                "Dessiner un bonhomme (têtard)",
            ],
        },
        DOM[4]: {
            "P1": [
                "[V/M/O] Les parties du corps",
                "[T/E] La journée : matin / soir",
                "[T/E] Se repérer dans la classe",
                "[V/M/O] Les 5 sens : découvrir",
                "[T/E] L'école : les lieux",
            ],
            "P2": [
                "[V/M/O] Nommer le visage",
                "[T/E] Les moments de la journée",
                "[T/E] Se situer : sur / sous",
                "[V/M/O] Le toucher : doux / rugueux",
                "[V/M/O] Les animaux familiers",
            ],
            "P3": [
                "[V/M/O] Le schéma corporel",
                "[T/E] Hier, aujourd'hui, demain",
                "[T/E] Le coin, le tapis (espace)",
                "[V/M/O] Le goût : sucré / salé",
                "[V/M/O] L'eau : jouer et transvaser",
            ],
            "P4": [
                "[V/M/O] Se laver les mains (hygiène)",
                "[T/E] La frise de la semaine",
                "[T/E] Un parcours dans l'école",
                "[V/M/O] L'ouïe : fort / doux",
                "[V/M/O] Flotte / coule (découverte)",
            ],
            "P5": [
                "[V/M/O] Prendre soin de son corps",
                "[T/E] Les saisons : découvrir",
                "[T/E] Le plan du coin jeux",
                "[V/M/O] La vue : les couleurs",
                "[V/M/O] Les plantes : semer une graine",
            ],
        },
    },
    "MS": {
        DOM[0]: {
            "P1": [
                "Se présenter au groupe",
                "Comptines nouvelles",
                "Raconter sa fin de semaine",
                "Écrire son prénom en capitales",
                "Vocabulaire des rituels",
            ],
            "P2": [
                "Décrire et expliquer",
                "Frapper les syllabes",
                "Images séquentielles (2-3)",
                "Graphisme : les ponts",
                "Reconnaître les lettres de son prénom",
            ],
            "P3": [
                "Poser une question",
                "Repérer une syllabe",
                "Raconter une histoire connue",
                "Graphisme : les boucles",
                "Sens de l'écrit (gauche → droite)",
            ],
            "P4": [
                "Vocabulaire des émotions",
                "Jouer avec les rimes",
                "Reformuler une consigne",
                "Reconnaître l'alphabet (capitales)",
                "Distinguer lettre / mot",
            ],
            "P5": [
                "Décrire une image riche",
                "Compter les syllabes d'un mot",
                "Inventer une courte histoire",
                "Graphisme : ponts et boucles enchaînés",
                "Copier son prénom en capitales",
            ],
        },
        DOM[1]: {
            "P1": [
                "Dénombrer jusqu'à 4",
                "Comparer deux collections",
                "Le dé : constellations 1-3",
                "Trier selon un critère",
                "La file numérique jusqu'à 5",
            ],
            "P2": [
                "Dénombrer jusqu'à 6",
                "Autant / plus / moins",
                "Constellations du dé (1-6)",
                "Algorithme à 2 couleurs",
                "Le nombre juste après",
            ],
            "P3": [
                "Le nombre juste avant / après",
                "Associer chiffre et quantité",
                "Reconnaître les formes planes",
                "Reproduire un assemblage",
                "Mesurer : long / court",
            ],
            "P4": [
                "Décomposer 3 et 4",
                "Réaliser une collection donnée",
                "Algorithme à 3 éléments",
                "Se repérer : sur / sous / à côté",
                "Ranger 3 tailles",
            ],
            "P5": [
                "Dénombrer jusqu'à 10",
                "Résoudre un petit problème (ajouter)",
                "Suites numériques",
                "Reproduire une figure sur points",
                "Comparer des longueurs",
            ],
        },
        DOM[2]: {
            "P1": [
                "Parcours de motricité",
                "Courir vite",
                "Rondes et danses",
                "S'orienter dans la salle",
                "Jeux de poursuite",
            ],
            "P2": [
                "Sauter loin, sauter haut",
                "Lancer et attraper",
                "Se déplacer en rythme",
                "Franchir des obstacles",
                "Rouler, tourner",
            ],
            "P3": [
                "Ramper, grimper, sauter (parcours)",
                "Viser une cible",
                "Chorégraphie simple",
                "Jeux collectifs à règles",
                "Équilibre sur banc",
            ],
            "P4": [
                "Enchaîner un parcours",
                "Lancer loin",
                "Jeux d'opposition (tirer-pousser)",
                "Danse à deux",
                "Courses de relais",
            ],
            "P5": [
                "Parcours chronométré",
                "Viser et marquer",
                "Ronde chorégraphiée",
                "Jeu collectif avec but",
                "Équilibre et déplacements",
            ],
        },
        DOM[3]: {
            "P1": [
                "Peinture au pinceau",
                "Reconnaître un son",
                "Collage thématique",
                "Chanter en chœur",
                "Dessiner un bonhomme",
            ],
            "P2": [
                "Mélanger deux couleurs",
                "Modelage en volume",
                "Percussions corporelles",
                "Reproduire un motif",
                "Empreintes et traces",
            ],
            "P3": [
                "Peindre à la manière de…",
                "Sculpter un objet en pâte",
                "Jouer d'un instrument simple",
                "Comptine à gestes",
                "Composer avec des formes",
            ],
            "P4": [
                "Composition plastique",
                "Assemblage de matériaux",
                "Chant à couplets",
                "Rythme à 2 temps",
                "Dessin d'observation simple",
            ],
            "P5": [
                "Œuvre collective",
                "Modeler un personnage",
                "Jeu dramatique (marionnettes)",
                "Reproduire une mélodie courte",
                "Découvrir une œuvre d'art",
            ],
        },
        DOM[4]: {
            "P1": [
                "[V/M/O] Le vivant : la plante",
                "[T/E] La frise de la semaine",
                "[T/E] Se repérer dans l'école",
                "[V/M/O] Les objets de la classe",
                "[T/E] L'automne",
            ],
            "P2": [
                "[V/M/O] Les besoins des plantes",
                "[T/E] Le jour et la nuit",
                "[T/E] Un parcours codé simple",
                "[V/M/O] Flotte / coule",
                "[V/M/O] Les 5 sens (approfondir)",
            ],
            "P3": [
                "[V/M/O] Le cycle d'une graine",
                "[T/E] Les saisons",
                "[T/E] Le plan de la classe",
                "[V/M/O] Aimants : attire / n'attire pas",
                "[V/M/O] L'hygiène du corps",
            ],
            "P4": [
                "[V/M/O] Les animaux et leur milieu",
                "[T/E] Hier, aujourd'hui, demain",
                "[T/E] Se déplacer sur un quadrillage",
                "[V/M/O] L'air : le vent, souffler",
                "[V/M/O] Le chaud et le froid",
            ],
            "P5": [
                "[V/M/O] Prendre soin du vivant (élevage)",
                "[T/E] La frise de l'année",
                "[T/E] Coder un déplacement",
                "[V/M/O] Manipuler la matière (eau, sable)",
                "[V/M/O] Le monde des objets techniques",
            ],
        },
    },
    "GS": {
        DOM[0]: {
            "P1": [
                "Raconter seul une histoire",
                "Lexique thématique",
                "Écrire son prénom en cursive (approche)",
                "Reconnaître les 3 écritures",
                "Présenter, argumenter (rituels)",
            ],
            "P2": [
                "Segmenter un mot en syllabes",
                "Sons d'attaque (phonologie)",
                "Copier un mot en capitales",
                "Écriture cursive : préparation",
                "Vocabulaire précis : nommer, définir",
            ],
            "P3": [
                "Argumenter, justifier",
                "Localiser un son dans le mot",
                "Encoder des syllabes simples",
                "Reconnaître les voyelles",
                "Les lettres et leur son",
            ],
            "P4": [
                "Décrire précisément",
                "Fusionner des syllabes",
                "Encoder un mot court",
                "Écriture cursive : lettres rondes",
                "Ordre alphabétique (approche)",
            ],
            "P5": [
                "Inventer et dicter une histoire",
                "Manipuler phonèmes (rimes, sons)",
                "Écrire un mot simple seul",
                "Copier une phrase",
                "Comprendre un texte lu",
            ],
        },
        DOM[1]: {
            "P1": [
                "Dénombrer jusqu'à 6",
                "Comparer des collections",
                "Écrire les chiffres 1-3",
                "Constellations et doigts",
                "La bande numérique jusqu'à 10",
            ],
            "P2": [
                "Dénombrer jusqu'à 10",
                "Le nombre d'avant / d'après",
                "Écrire les chiffres 4-6",
                "Décomposer 5",
                "Algorithmes complexes",
            ],
            "P3": [
                "Décomposer 10",
                "Ajouter / retirer 1",
                "Écrire les chiffres 7-9",
                "Solides et figures",
                "Tracer à la règle",
            ],
            "P4": [
                "Résoudre un problème (ajouter / retirer)",
                "Compléter à 5, à 10",
                "Se repérer sur quadrillage",
                "Reproduire une figure",
                "Comparer des longueurs",
            ],
            "P5": [
                "Additionner deux petites quantités",
                "Le nombre jusqu'à 20 (approche)",
                "Écrire les nombres jusqu'à 10",
                "Reproduire un pavage",
                "Mesurer avec un étalon",
            ],
        },
        DOM[2]: {
            "P1": [
                "Parcours d'équilibre",
                "Courses et relais",
                "Danse et chorégraphie",
                "S'orienter dans un espace",
                "Jeux collectifs",
            ],
            "P2": [
                "Viser une cible",
                "Sauter loin et haut",
                "Chorégraphie à plusieurs",
                "Jeux d'opposition",
                "Franchir et enchaîner",
            ],
            "P3": [
                "Lancer avec précision",
                "Vitesse et endurance",
                "Danse structurée (phrases)",
                "Jeux de coopération",
                "Équilibre dynamique",
            ],
            "P4": [
                "Réaliser un enchaînement",
                "Relais chronométrés",
                "Créer une chorégraphie",
                "Jeux à règles complexes",
                "Grimper et se réceptionner",
            ],
            "P5": [
                "Parcours athlétique complet",
                "Viser, marquer, compter les points",
                "Spectacle dansé",
                "Jeu collectif stratégique",
                "Défis d'équilibre",
            ],
        },
        DOM[3]: {
            "P1": [
                "Composition plastique",
                "Dessin d'observation",
                "Chant et rythme structuré",
                "Reconnaître des œuvres",
                "Les nuances de couleurs",
            ],
            "P2": [
                "Mélanges et nuances",
                "Sculpture et assemblage",
                "Jouer un rythme instrumental",
                "Reproduire un motif complexe",
                "Croquis d'un objet",
            ],
            "P3": [
                "Peindre à la manière d'un artiste",
                "Volume et matériaux de récup",
                "Chanter un canon simple",
                "Coder un rythme",
                "Portrait et autoportrait",
            ],
            "P4": [
                "Réaliser une fresque collective",
                "Assembler une sculpture",
                "Percussions à plusieurs voix",
                "Créer un motif décoratif",
                "Lecture d'une œuvre d'art",
            ],
            "P5": [
                "Mettre en scène une histoire",
                "Exposition de la classe",
                "Chorale : un chant appris",
                "Inventer une phrase rythmique",
                "Dessin narratif (BD simple)",
            ],
        },
        DOM[4]: {
            "P1": [
                "[V/M/O] Le corps et l'hygiène",
                "[T/E] La frise du jour",
                "[T/E] Le plan de la classe",
                "[V/M/O] Objets techniques : usage",
                "[V/M/O] Le vivant : classer",
            ],
            "P2": [
                "[V/M/O] Cycle de vie (animal / plante)",
                "[T/E] Frise de la semaine et du mois",
                "[T/E] Se repérer sur un quadrillage",
                "[V/M/O] Aimants et électricité (approche)",
                "[V/M/O] Les états de l'eau",
            ],
            "P3": [
                "[V/M/O] Croissance et alimentation",
                "[T/E] La frise de l'année",
                "[T/E] Coder un déplacement",
                "[V/M/O] Fabriquer un objet simple",
                "[V/M/O] Flotte / coule : expliquer",
            ],
            "P4": [
                "[V/M/O] L'élevage en classe",
                "[T/E] Se repérer dans le temps (avant / après)",
                "[T/E] Lire un plan, un itinéraire",
                "[V/M/O] Leviers et engrenages (jeu)",
                "[V/M/O] Solide, liquide",
            ],
            "P5": [
                "[V/M/O] Protéger le vivant (environnement)",
                "[T/E] Le calendrier et les événements",
                "[T/E] L'espace : maquette du quartier",
                "[V/M/O] Le monde des objets numériques",
                "[V/M/O] Air, eau, matière : expériences",
            ],
        },
    },
}


def cells_2026(niveau):
    """Aplati PROGRAMME_MATERNELLE_2026[niveau] en cellules générables (matiere=domaine)."""
    out = []
    for domaine, periodes in PROGRAMME_MATERNELLE_2026.get(niveau, {}).items():
        for pkey, notions in periodes.items():
            p = int(pkey[1])  # "P3" -> 3
            for n in notions:
                out.append(
                    {"niveau": niveau, "matiere": domaine, "periode": p, "notion": n}
                )
    return out
