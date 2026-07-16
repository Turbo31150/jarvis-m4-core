#!/usr/bin/env python3
"""Banque annuelle — génère, stocke et imprime une année complète de fiches
d'exercices différenciées pour la maternelle et l'élémentaire, TOUTES matières.

Principe (anti-surchauffe M4) : on ne génère JAMAIS tout d'un coup. Chaque fiche
est produite à la demande (cache SQL → cascade ai_local), ou par petits lots via
`/api/banque/batch` que le job de nuit appelle — l'année se remplit progressivement,
0 token, sans pic thermique. Sortie PDF imprimable via export_pdf.

Branché par server.py via register(app). Réutilise les helpers de prof_routes
(require_token) + le garde global @before_request.
"""

import sqlite3
from pathlib import Path

from flask import jsonify, request, send_file

import ai_local
from programme_maternelle_2026 import cells_2026 as _maternelle_cells_2026

ECOLE_DB = str(Path(__file__).resolve().parent / "ecole.db")
_TEMP_MAX = 86  # au-dessus, pas de génération (cf. protocole anti-surchauffe)

# ── CURRICULUM (squelette B.O., notions clés réparties en 5 périodes) ───────
# Compact volontairement : ~5 notions par (niveau, matière). L'enseignante peut
# régénérer/compléter. Période = (index // ceil) + 1, réparti sur P1→P5.
PROGRAMME = {
    # ───── MATERNELLE ─────
    "PS": {
        "Langage oral": [
            "Se présenter, nommer",
            "Comptines et jeux de doigts",
            "Raconter une histoire connue",
            "Vocabulaire du corps",
            "Décrire une image",
        ],
        "Langage écrit": [
            "Reconnaître son prénom",
            "Manipuler un livre",
            "Graphisme : traits",
            "Graphisme : les ronds",
            "Reconnaître des lettres",
        ],
        "Nombres": [
            "Reconnaître 1, 2, 3",
            "Beaucoup / pas beaucoup",
            "Dénombrer jusqu'à 3",
            "Plus / moins",
            "Rituel des présents",
        ],
        "Formes et grandeurs": [
            "Trier par couleur",
            "Trier par taille",
            "Ranger petit→grand",
            "Rond et carré",
            "Encastrements",
        ],
        "Explorer le monde": [
            "Les parties du corps",
            "La journée (matin/soir)",
            "Les 5 sens",
            "Les animaux familiers",
            "L'eau",
        ],
        "Activités physiques": [
            "Courir et s'arrêter",
            "Sauter à pieds joints",
            "Rouler, ramper",
            "Lancer une balle",
            "Rondes et jeux dansés",
        ],
        "Activités artistiques": [
            "Peindre avec les mains",
            "Coller des gommettes",
            "Modeler la pâte",
            "Chanter une comptine",
            "Écouter un son",
        ],
    },
    "MS": {
        "Langage oral": [
            "Décrire et expliquer",
            "Syllabes (frapper les mots)",
            "Raconter avec des images séquentielles",
            "Vocabulaire des émotions",
            "Poser une question",
        ],
        "Langage écrit": [
            "Écrire son prénom en capitales",
            "Graphisme : ponts et boucles",
            "Reconnaître l'alphabet",
            "Rimes et sons",
            "Sens de l'écrit",
        ],
        "Nombres": [
            "Dénombrer jusqu'à 6",
            "Comparer des collections",
            "Le nombre juste après",
            "Constellations du dé",
            "Suites numériques",
        ],
        "Formes et grandeurs": [
            "Reconnaître les formes",
            "Algorithmes simples",
            "Mesurer (long/court)",
            "Se repérer (sur/sous)",
            "Reproduire un assemblage",
        ],
        "Explorer le monde": [
            "Le vivant : la plante",
            "Les saisons",
            "Le jour et la nuit",
            "Flotte / coule",
            "La frise de la semaine",
        ],
        "Activités physiques": [
            "Parcours de motricité",
            "Sauter loin, sauter haut",
            "Lancer et attraper",
            "Se déplacer en rythme",
            "Jeux collectifs à règles",
        ],
        "Activités artistiques": [
            "Peinture au pinceau",
            "Dessiner un bonhomme",
            "Modelage en volume",
            "Percussions corporelles",
            "Jeu dramatique (marionnettes)",
        ],
    },
    "GS": {
        "Langage oral": [
            "Raconter seul une histoire",
            "Segmenter en syllabes",
            "Phonologie : sons d'attaque",
            "Argumenter, justifier",
            "Lexique thématique",
        ],
        "Langage écrit": [
            "Écriture cursive : préparation",
            "Reconnaître les 3 écritures",
            "Encoder des syllabes simples",
            "Copier un mot",
            "Phonologie : sons-voyelles",
        ],
        "Nombres": [
            "Dénombrer jusqu'à 10",
            "Décomposer 5 et 10",
            "Écrire les chiffres",
            "Ajouter / retirer 1",
            "Résoudre un petit problème",
        ],
        "Formes et grandeurs": [
            "Solides et figures",
            "Algorithmes complexes",
            "Tracer à la règle",
            "Se repérer sur quadrillage",
            "Comparer des longueurs",
        ],
        "Explorer le monde": [
            "Le corps et l'hygiène",
            "Cycle de vie",
            "Le temps : la frise",
            "Espace : plan de la classe",
            "Objets techniques",
        ],
        "Activités physiques": [
            "Parcours d'équilibre",
            "Courses et relais",
            "Viser une cible",
            "Danse et chorégraphie",
            "Jeux d'opposition",
        ],
        "Activités artistiques": [
            "Composition plastique",
            "Dessin d'observation",
            "Sculpture et assemblage",
            "Chant et rythme structuré",
            "Mise en scène d'une histoire",
        ],
    },
    # ───── ÉLÉMENTAIRE — CYCLE 2 ─────
    "CP": {
        "Français": [
            "Correspondance graphème-phonème",
            "Lire des syllabes simples",
            "Écriture cursive des lettres",
            "Compréhension de phrases",
            "Les sons complexes (ch, ou, on)",
        ],
        "Mathématiques": [
            "Nombres jusqu'à 10",
            "Addition simple",
            "Comparer et ranger",
            "Formes planes",
            "Se repérer dans l'espace",
        ],
        "Questionner le monde": [
            "Le vivant / non-vivant",
            "Les saisons et le temps",
            "Se repérer dans l'espace proche",
            "Hygiène et santé",
            "Les objets du quotidien",
        ],
        "EMC": [
            "Les règles de la classe",
            "Respecter les autres",
            "Émotions et besoins",
            "Le rôle de délégué",
            "La politesse",
        ],
        "Arts": [
            "Le portrait",
            "Les couleurs primaires",
            "Chant et rythme",
            "Land art / nature",
            "Découverte d'une œuvre",
        ],
    },
    "CE1": {
        "Français": [
            "Lecture fluide",
            "Le verbe et son sujet",
            "Les accords dans le groupe nominal",
            "Le présent des verbes",
            "Produire un texte court",
        ],
        "Mathématiques": [
            "Nombres jusqu'à 100",
            "Addition posée avec retenue",
            "Soustraction",
            "Tables de multiplication (2,5,10)",
            "Lire l'heure",
        ],
        "Questionner le monde": [
            "Cycle de vie des animaux",
            "États de l'eau",
            "La frise historique",
            "Se repérer sur un plan",
            "Trier les déchets",
        ],
        "EMC": [
            "Les droits et devoirs",
            "La coopération",
            "Gérer un conflit",
            "Les symboles de la République",
            "L'égalité filles-garçons",
        ],
        "Arts": [
            "Le paysage",
            "Couleurs chaudes/froides",
            "Percussions corporelles",
            "Volume et modelage",
            "Une œuvre du patrimoine",
        ],
    },
    "CE2": {
        "Français": [
            "Nature et fonction des mots",
            "Passé / présent / futur",
            "L'imparfait et le passé composé",
            "Les homophones (a/à, et/est)",
            "Rédiger un récit",
        ],
        "Mathématiques": [
            "Nombres jusqu'à 10 000",
            "Multiplication posée",
            "Division : approche",
            "Périmètre et mesures",
            "Problèmes à étapes",
        ],
        "Questionner le monde": [
            "Le système solaire",
            "Les régimes alimentaires",
            "La préhistoire",
            "Lire une carte",
            "Circuits électriques simples",
        ],
        "EMC": [
            "La laïcité",
            "Le harcèlement",
            "L'engagement (éco-délégué)",
            "La justice et la loi",
            "Solidarité et entraide",
        ],
        "Arts": [
            "Composition et cadrage",
            "Le mélange des couleurs",
            "Lecture d'un tableau",
            "Musique : familles d'instruments",
            "Théâtre et expression",
        ],
    },
    # ───── ÉLÉMENTAIRE — CYCLE 3 ─────
    "CM1": {
        "Français": [
            "Classes grammaticales",
            "Compléments (COD/COI/CC)",
            "Les temps du récit",
            "Accord du participe passé (être)",
            "Rédiger un texte descriptif",
        ],
        "Mathématiques": [
            "Nombres décimaux",
            "Les fractions simples",
            "Multiplication et division posées",
            "Aires et périmètres",
            "Proportionnalité (approche)",
        ],
        "Sciences et technologie": [
            "Le squelette et les muscles",
            "Les états de la matière",
            "Énergies et circuits",
            "Le système solaire",
            "Classer le vivant",
        ],
        "Histoire-Géographie": [
            "La Gaule et les Romains",
            "Le Moyen Âge",
            "Se nourrir / habiter",
            "Lire un paysage",
            "Les grandes villes",
        ],
        "EMC": [
            "La démocratie",
            "Les médias et l'info",
            "Le respect de l'environnement",
            "Les discriminations",
            "Le débat argumenté",
        ],
        "Anglais": [
            "Se présenter (greetings)",
            "Les nombres et l'âge",
            "La famille",
            "Les couleurs et objets",
            "Les goûts (I like)",
        ],
    },
    "CM2": {
        "Français": [
            "Phrase simple / complexe",
            "Propositions et conjonctions",
            "Concordance des temps",
            "Tous les accords du PP",
            "Rédiger un texte argumentatif",
        ],
        "Mathématiques": [
            "Opérations sur les décimaux",
            "Fractions : addition",
            "Pourcentages",
            "Volumes et conversions",
            "Problèmes de proportionnalité",
        ],
        "Sciences et technologie": [
            "La digestion et la respiration",
            "Mélanges et solutions",
            "Énergie : sources et usages",
            "La Terre dans l'Univers",
            "Programmer un robot (algorithmes)",
        ],
        "Histoire-Géographie": [
            "Temps modernes et Révolution",
            "Le XXe siècle et les guerres",
            "La France et l'Europe",
            "Mondialisation et échanges",
            "Développement durable",
        ],
        "EMC": [
            "Les valeurs de la République",
            "Liberté d'expression",
            "Le citoyen et le vote",
            "Égalité et fraternité",
            "Sécurité et numérique",
        ],
        "Anglais": [
            "Décrire sa journée",
            "L'heure et l'emploi du temps",
            "La météo et les saisons",
            "Donner son chemin",
            "Parler de ses loisirs",
        ],
    },
}

NIVEAUX = list(PROGRAMME.keys())

# ── PROGRAMME MATERNELLE 2026 (BO n°19 du 7 mai 2026, rentrée 2026-2027) ──────
# Squelette officiel des 5 domaines. On NE régénère pas le contenu déjà produit :
# on le remappe. Une réforme future = éditer ce seul bloc puis relancer _tag_domaines().
DOMAINES_2026 = [
    "Développement et structuration du langage oral et écrit",
    "Acquisition des premiers outils mathématiques",
    "Agir, s'exprimer, comprendre à travers l'activité physique",
    "Agir, s'exprimer, comprendre à travers les activités artistiques",
    "Explorer le monde",  # volets : « Se repérer dans le temps et l'espace » + « le vivant, la matière, les objets »
]
# Correspondance matière interne (grille de génération) → domaine officiel 2026.
MATIERE_TO_DOMAINE_2026 = {
    "Langage oral": DOMAINES_2026[0],
    "Langage écrit": DOMAINES_2026[0],
    "Phonologie": DOMAINES_2026[0],
    "Graphisme": DOMAINES_2026[0],
    "Nombres": DOMAINES_2026[1],
    "Formes et grandeurs": DOMAINES_2026[1],
    "Explorer le monde": DOMAINES_2026[4],
    "Activités physiques": DOMAINES_2026[2],
    "Motricité": DOMAINES_2026[2],
    "Activités artistiques": DOMAINES_2026[3],
}


def domaine_2026(matiere):
    """Domaine officiel 2026 d'une matière interne (défaut: Explorer le monde)."""
    return MATIERE_TO_DOMAINE_2026.get(matiere, DOMAINES_2026[4])


def _conn():
    c = sqlite3.connect(ECOLE_DB)
    c.row_factory = sqlite3.Row
    return c


def _init():
    c = _conn()
    try:
        c.execute(
            """CREATE TABLE IF NOT EXISTS banque(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 niveau TEXT, matiere TEXT, periode INTEGER, notion TEXT,
                 contenu_md TEXT, backend TEXT,
                 created_at TEXT DEFAULT (datetime('now')),
                 UNIQUE(niveau, matiere, notion)
               )"""
        )
        c.commit()
    finally:
        c.close()


def _cpu_temp():
    import glob

    t = 0
    for p in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            with open(p) as f:
                t = max(t, int(f.read().strip()) // 1000)
        except Exception:
            pass
    return t


def _periode(idx, total):
    """Répartit l'index d'une notion sur 5 périodes."""
    import math

    per_p = max(1, math.ceil(total / 5))
    return min(5, idx // per_p + 1)


def _cells(niveau, matiere=None):
    """Liste des cellules attendues (squelette) pour un niveau (et matière).

    Maternelle (PS/MS/GS) → programme officiel 2026 (BO n°19) : 5 domaines ×
    5 périodes × 4-6 notions. Élémentaire → grille PROGRAMME historique.
    """
    if niveau in ("PS", "MS", "GS"):
        cells = _maternelle_cells_2026(niveau)
        return [c for c in cells if c["matiere"] == matiere] if matiere else cells
    out = []
    prog = PROGRAMME.get(niveau, {})
    mats = [matiere] if matiere else list(prog.keys())
    for m in mats:
        notions = prog.get(m, [])
        for i, n in enumerate(notions):
            out.append(
                {
                    "niveau": niveau,
                    "matiere": m,
                    "notion": n,
                    "periode": _periode(i, len(notions)),
                }
            )
    return out


def _generate_cell(niveau, matiere, notion, periode):
    """Génère (ou récupère du cache) une fiche pour une cellule. Anti-surchauffe."""
    if _cpu_temp() >= _TEMP_MAX:
        raise ai_local.AIUnavailable(
            f"Surchauffe ({_cpu_temp()}°C) — génération reportée"
        )
    prompt = (
        f"Crée une fiche d'exercices pour le niveau {niveau} en {matiere}, "
        f"sur la notion « {notion} » (période {periode}, école française).\n"
        "Donne TROIS versions séparées et leur corrigé :\n"
        "## SOUTIEN (étayé, plus simple)\n## STANDARD\n## APPROFONDISSEMENT\n"
        "Consignes claires, adaptées à l'âge. Markdown, prêt à imprimer."
    )
    # repli=False : le dispatch veut de VRAIES fiches (retry si cascade KO),
    # pas une trame hors-ligne. Les routes interactives gardent le repli par défaut.
    res = ai_local.generate(prompt, max_tokens=1100, cache=True, repli=False)
    c = _conn()
    try:
        c.execute(
            "INSERT INTO banque(niveau,matiere,periode,notion,contenu_md,backend) "
            "VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(niveau,matiere,notion) DO UPDATE SET "
            "contenu_md=excluded.contenu_md, backend=excluded.backend",
            (niveau, matiere, periode, notion, res["text"], res["backend"]),
        )
        c.commit()
    finally:
        c.close()
    return res


def register(app):
    _init()
    try:
        from prof_routes import require_token as _rt
    except Exception:  # pragma: no cover

        def _rt(f):
            return f

    def _body():
        return request.get_json(force=True, silent=True) or {}

    @_rt
    def plan():
        niveau = request.args.get("niveau", "CE2")
        matiere = request.args.get("matiere") or None
        cells = _cells(niveau, matiere)
        done = {
            (r["matiere"], r["notion"])
            for r in _conn().execute(
                "SELECT matiere, notion FROM banque WHERE niveau=?", (niveau,)
            )
        }
        for c in cells:
            c["fait"] = (c["matiere"], c["notion"]) in done
        return jsonify(
            {
                "niveau": niveau,
                "matieres": list(PROGRAMME.get(niveau, {}).keys()),
                "cellules": cells,
                "total": len(cells),
                "faits": sum(1 for c in cells if c["fait"]),
            }
        )

    @_rt
    def generer():
        d = _body()
        niveau, matiere = d.get("niveau"), d.get("matiere")
        notion = d.get("notion")
        periode = int(d.get("periode", 1) or 1)
        if not (niveau and matiere and notion):
            return jsonify({"error": "niveau, matiere, notion requis"}), 400
        try:
            res = _generate_cell(niveau, matiere, notion, periode)
        except ai_local.AIUnavailable as e:
            return jsonify({"error": str(e)}), 503
        return jsonify(
            {
                "contenu_md": res["text"],
                "backend": res["backend"],
                "cached": res["cached"],
            }
        )

    @_rt
    def liste():
        niveau = request.args.get("niveau")
        matiere = request.args.get("matiere")
        q = "SELECT id,niveau,matiere,periode,notion,backend,created_at FROM banque WHERE 1=1"
        a = []
        if niveau:
            q += " AND niveau=?"
            a.append(niveau)
        if matiere:
            q += " AND matiere=?"
            a.append(matiere)
        q += " ORDER BY niveau, matiere, periode, id"
        rows = [dict(r) for r in _conn().execute(q, a)]
        return jsonify(rows)

    @_rt
    def cellule():
        """Contenu d'une fiche déjà générée (par id)."""
        cid = request.args.get("id")
        r = _conn().execute("SELECT * FROM banque WHERE id=?", (cid,)).fetchone()
        if not r:
            return jsonify({"error": "introuvable"}), 404
        return jsonify(dict(r))

    @_rt
    def batch():
        """Génère les N prochaines fiches manquantes (appelé par le job de nuit).
        Borné + garde thermique : remplit l'année progressivement, sans pic."""
        d = _body()
        maxi = max(1, min(int(d.get("max", 3) or 3), 20))
        only_niveau = d.get("niveau")
        prepared, errors = [], []
        niveaux = [only_niveau] if only_niveau else NIVEAUX
        done = 0
        for niv in niveaux:
            for cell in _cells(niv):
                if done >= maxi:
                    break
                exists = (
                    _conn()
                    .execute(
                        "SELECT 1 FROM banque WHERE niveau=? AND matiere=? AND notion=?",
                        (cell["niveau"], cell["matiere"], cell["notion"]),
                    )
                    .fetchone()
                )
                if exists:
                    continue
                if _cpu_temp() >= _TEMP_MAX:
                    return jsonify(
                        {
                            "ok": False,
                            "raison": f"surchauffe {_cpu_temp()}°C",
                            "prepares": prepared,
                            "temp": _cpu_temp(),
                        }
                    )
                try:
                    _generate_cell(
                        cell["niveau"], cell["matiere"], cell["notion"], cell["periode"]
                    )
                    prepared.append(
                        f"{cell['niveau']}/{cell['matiere']}/{cell['notion']}"
                    )
                    done += 1
                except Exception as e:
                    errors.append(str(e)[:120])
            if done >= maxi:
                break
        return jsonify(
            {"ok": True, "prepares": prepared, "erreurs": errors, "temp": _cpu_temp()}
        )

    @_rt
    def pdf():
        """Compile toutes les fiches générées d'un niveau (option matière) en un PDF."""
        niveau = request.args.get("niveau", "CE2")
        matiere = request.args.get("matiere")
        q = "SELECT matiere,periode,notion,contenu_md FROM banque WHERE niveau=?"
        a = [niveau]
        if matiere:
            q += " AND matiere=?"
            a.append(matiere)
        q += " ORDER BY matiere, periode"
        rows = list(_conn().execute(q, a))
        if not rows:
            return jsonify({"error": "Aucune fiche générée pour ce niveau"}), 400
        parts = []
        cur_mat = None
        for r in rows:
            if r["matiere"] != cur_mat:
                cur_mat = r["matiere"]
                parts.append(f"\n# {cur_mat} — {niveau}\n")
            parts.append(
                f"\n## P{r['periode']} · {r['notion']}\n\n{r['contenu_md'] or ''}\n\n---\n"
            )
        md = "".join(parts)
        titre = f"Banque {niveau}" + (f" {matiere}" if matiere else "")
        try:
            from export_pdf import md_to_pdf_path

            path = md_to_pdf_path(md, titre)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        return send_file(
            path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=titre.replace(" ", "_") + ".pdf",
        )

    @_rt
    def domaines2026():
        """Contenu existant regroupé par les 5 domaines officiels du programme 2026.
        Ne régénère rien : remappe banque + programmations sur le squelette 2026."""
        niveau = request.args.get("niveau", "MS")
        c = _conn()
        fiches = c.execute(
            "SELECT id,matiere,notion,periode FROM banque WHERE niveau=? ORDER BY matiere,periode",
            (niveau,),
        ).fetchall()
        progs = c.execute(
            "SELECT matiere FROM programmations WHERE niveau=? AND portee='annuelle'",
            (niveau,),
        ).fetchall()
        out = []
        for d in DOMAINES_2026:
            df = [
                {"id": r["id"], "matiere": r["matiere"], "notion": r["notion"]}
                for r in fiches
                if domaine_2026(r["matiere"]) == d
            ]
            pc = sum(1 for p in progs if domaine_2026(p["matiere"]) == d)
            out.append(
                {"domaine": d, "fiches": df, "nb_fiches": len(df), "nb_prog": pc}
            )
        return jsonify(
            {
                "niveau": niveau,
                "source": "BO n°19 du 7 mai 2026 — rentrée 2026-2027",
                "domaines": out,
            }
        )

    app.add_url_rule(
        "/api/programme2026", "banque_domaines2026", domaines2026, methods=["GET"]
    )
    app.add_url_rule("/api/banque/plan", "banque_plan", plan, methods=["GET"])
    app.add_url_rule("/api/banque/generer", "banque_generer", generer, methods=["POST"])
    app.add_url_rule("/api/banque", "banque_liste", liste, methods=["GET"])
    app.add_url_rule("/api/banque/cellule", "banque_cellule", cellule, methods=["GET"])
    app.add_url_rule("/api/banque/batch", "banque_batch", batch, methods=["POST"])
    app.add_url_rule("/api/banque/pdf", "banque_pdf", pdf, methods=["GET"])
    print("[Pousseline] Banque annuelle chargée (/api/banque/*)")
