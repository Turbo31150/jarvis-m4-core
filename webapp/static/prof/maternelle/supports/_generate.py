#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère tous les supports imprimables A4 de la semaine maternelle « La chenille qui fait des trous ».
Sortie: HTML prêts à imprimer dans ce dossier. PDF générés ensuite via Chrome headless."""

import pathlib

OUT = pathlib.Path(__file__).resolve().parent

CSS = """
@page { size: A4; margin: 12mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI','Helvetica Neue',Arial,sans-serif; color:#222; margin:0; }
.page { page-break-after: always; padding: 4mm; }
.page:last-child { page-break-after: auto; }
h1 { color:#2e7d32; font-size:24px; margin:0 0 4px; }
h2 { color:#1b5e20; font-size:16px; margin:10px 0 6px; }
.sub { color:#666; font-size:12px; margin:0 0 14px; }
.consigne { background:#f1f8e9; border-left:5px solid #8bc34a; padding:8px 12px; font-size:13px; border-radius:6px; margin-bottom:12px; }
.foot { margin-top:14px; font-size:10px; color:#999; text-align:center; }
/* étiquettes lettres */
.lettres { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; }
.lettre { width:78px; height:96px; border:3px dashed #66bb6a; border-radius:10px; display:flex; align-items:center; justify-content:center;
  font-size:60px; font-weight:800; color:#2e7d32; background:#fafffa; }
/* cartes fruits */
.cartes { display:flex; flex-wrap:wrap; gap:14px; justify-content:center; }
.carte { width:165px; border:3px solid #66bb6a; border-radius:14px; padding:10px; text-align:center; background:#fff; }
.carte .fruits { font-size:34px; line-height:1.1; min-height:80px; }
.carte .chiffre { font-size:46px; font-weight:800; color:#ef6c00; }
.de { display:inline-grid; grid-template-columns:repeat(3,14px); grid-template-rows:repeat(3,14px); gap:3px; margin-top:4px; }
.de span { width:14px; height:14px; border-radius:50%; }
.de .on { background:#333; }
/* cycle de vie */
.cycle { display:flex; gap:12px; justify-content:center; flex-wrap:wrap; }
.etape { width:150px; height:170px; border:3px solid #aed581; border-radius:14px; display:flex; flex-direction:column; align-items:center; justify-content:center; background:#fff; }
.etape .ico { font-size:54px; }
.etape .lbl { margin-top:8px; font-size:15px; font-weight:700; color:#1b5e20; }
.etape .num { width:26px;height:26px;border:2px solid #ef6c00;border-radius:50%;color:#ef6c00;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:14px;margin-top:6px;}
/* frise jours */
table.frise { width:100%; border-collapse:collapse; }
table.frise th, table.frise td { border:2px solid #c5e1a5; padding:10px; text-align:center; font-size:15px; }
table.frise th { background:#66bb6a; color:#fff; }
table.frise td .f { font-size:30px; }
/* papillon */
.papillon-wrap { text-align:center; }
.axe { border-left:3px dashed #ef6c00; height:0; }
.pap { font-size:150px; }
/* graphisme */
.bande { border:2px solid #c5e1a5; border-radius:8px; height:54px; margin:10px 0; display:flex; align-items:center; padding:0 10px;
  background:repeating-linear-gradient(90deg,#fff,#fff 38px,#f1f8e9 38px,#f1f8e9 40px); font-size:30px; color:#8bc34a; letter-spacing:6px; overflow:hidden; }
.start { font-size:26px; margin-right:8px; }
/* grille eval */
table.grille { width:100%; border-collapse:collapse; font-size:12px; }
table.grille th, table.grille td { border:1px solid #cfe8c9; padding:6px 8px; }
table.grille th { background:#66bb6a; color:#fff; text-align:left; }
table.grille td.code { text-align:center; width:42px; }
.legende { font-size:11px; color:#555; margin-top:8px; }
/* affiche */
.affiche { text-align:center; }
.affiche .big { font-size:40px; color:#2e7d32; font-weight:800; margin:10px 0; }
.affiche .papillons { font-size:60px; }
.materiel li { margin:4px 0; font-size:13px; }
"""


def de_html(n):
    # constellation de dé (positions classiques pour 1..6)
    pos = {
        1: [4],
        2: [0, 8],
        3: [0, 4, 8],
        4: [0, 2, 6, 8],
        5: [0, 2, 4, 6, 8],
        6: [0, 2, 3, 5, 6, 8],
    }
    cells = "".join(
        f'<span class="{"on" if i in pos.get(n, []) else ""}"></span>' for i in range(9)
    )
    return f'<div class="de">{cells}</div>'


def wrap(title, body):
    return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style></head><body>{body}
<div class="foot">La chenille qui fait des trous — atelier maternelle MS/GS · à plastifier</div></body></html>"""


FRUITS = [
    (1, "🍎", "pomme"),
    (2, "🍐🍐", "poires"),
    (3, "🍇🍇🍇", "prunes"),
    (4, "🍓🍓🍓🍓", "fraises"),
    (5, "🍊🍊🍊🍊🍊", "oranges"),
]
JOURS = [
    ("Lundi", "🍎", "1 pomme"),
    ("Mardi", "🍐🍐", "2 poires"),
    ("Mercredi", "🍇🍇🍇", "3 prunes"),
    ("Jeudi", "🍓🍓🍓🍓", "4 fraises"),
    ("Vendredi", "🍊🍊🍊🍊🍊", "5 oranges"),
    ("Samedi", "🍰🍦🥧", "trop de gâteaux !"),
    ("Dimanche", "🍃", "1 belle feuille"),
]
CYCLE = [
    ("🥚", "l'œuf"),
    ("🐛", "la chenille"),
    ("🛡️", "la chrysalide"),
    ("🦋", "le papillon"),
]

supports = {}

# 1. Étiquettes lettres CHENILLE
lettres = "".join(f'<div class="lettre">{c}</div>' for c in "CHENILLE")
supports["01_etiquettes-CHENILLE"] = wrap(
    "Étiquettes CHENILLE",
    f"""
<div class="page"><h1>Le mot CHENILLE</h1><p class="sub">Langage écrit · reconstituer le mot en lettres capitales</p>
<div class="consigne">✂️ Découpe les lettres, mélange-les, puis remets-les dans l'ordre sous le modèle <b>CHENILLE</b>. Entoure la lettre de ton prénom.</div>
<div class="lettres">{lettres}</div>
<h2>Modèle</h2><div class="lettres" style="justify-content:flex-start">{"".join(f'<div class="lettre" style="width:54px;height:64px;font-size:38px;border-style:solid">{c}</div>' for c in "CHENILLE")}</div>
</div>""",
)

# 2. Cartes-fruits 1->5 + constellation
cartes = "".join(
    f'<div class="carte"><div class="fruits">{ic}</div><div class="chiffre">{n}</div>{de_html(n)}</div>'
    for n, ic, _ in FRUITS
)
supports["02_cartes-fruits-1a5"] = wrap(
    "Cartes fruits 1 à 5",
    f"""
<div class="page"><h1>Combien de trous ?</h1><p class="sub">Nombres · associer quantité ↔ chiffre ↔ constellation du dé</p>
<div class="consigne">🔢 Compte les fruits, pose le bon chiffre et la bonne carte-dé. (PS : jusqu'à 3 · GS : écris le chiffre.)</div>
<div class="cartes">{cartes}</div></div>""",
)

# 3. Cycle de vie à ordonner
etapes = "".join(
    f'<div class="etape"><div class="ico">{ic}</div><div class="lbl">{lbl}</div><div class="num"></div></div>'
    for ic, lbl in CYCLE
)
supports["03_cycle-de-vie"] = wrap(
    "Cycle de vie",
    f"""
<div class="page"><h1>De l'œuf au papillon</h1><p class="sub">Explorer le vivant · remettre les 4 étapes dans l'ordre</p>
<div class="consigne">🔄 Découpe les 4 images. Colle-les dans l'ordre : <b>d'abord… ensuite… puis… enfin…</b> Écris 1, 2, 3, 4 dans les ronds.</div>
<div class="cycle">{etapes}</div></div>""",
)

# 4. Frise des 7 jours
rows_h = "".join(f"<th>{j}</th>" for j, _, _ in JOURS)
rows_f = "".join(f'<td><div class="f">{ic}</div>{txt}</td>' for _, ic, txt in JOURS)
supports["04_frise-7-jours"] = wrap(
    "Frise des 7 jours",
    f"""
<div class="page"><h1>Les 7 jours de la chenille</h1><p class="sub">Se repérer dans le temps · chaque jour, la chenille mange…</p>
<div class="consigne">📅 Récite les jours dans l'ordre et associe ce que mange la chenille chaque jour.</div>
<table class="frise"><tr>{rows_h}</tr><tr>{rows_f}</tr></table></div>""",
)

# 5. Papillon symétrique
supports["05_papillon-symetrie"] = wrap(
    "Papillon symétrique",
    """
<div class="page papillon-wrap"><h1>Mon papillon symétrique</h1><p class="sub">Arts · peinture par pliage (effet miroir)</p>
<div class="consigne">🎨 Plie la feuille sur le trait orange. Dépose des gouttes de gouache sur une moitié, replie, ouvre : les deux ailes sont pareilles !</div>
<div class="pap">🦋</div>
<div style="border-top:3px dashed #ef6c00; margin:6px 30px;"></div>
<p class="sub">— trait de pliage —</p></div>""",
)

# 6. Graphisme ondulations
bandes = "".join(
    '<div class="bande"><span class="start">🐛</span>～～～～～～～～～～～～～<span style="margin-left:auto">🍎</span></div>'
    for _ in range(5)
)
supports["06_graphisme-ondulations"] = wrap(
    "Graphisme : lignes ondulées",
    f"""
<div class="page"><h1>Le chemin de la chenille</h1><p class="sub">Graphisme · tracer des lignes ondulées de gauche à droite</p>
<div class="consigne">✏️ Repasse puis continue le chemin ondulé de la chenille 🐛 jusqu'au fruit 🍎, sans lever le crayon.</div>
{bandes}</div>""",
)

# 7. Grilles d'évaluation
comp = [
    ("Langage oral", "Raconter l'histoire dans l'ordre (d'abord/ensuite/enfin)"),
    ("Langage écrit", "Reconstituer le mot CHENILLE / écrire son prénom"),
    ("Nombres", "Dénombrer une collection jusqu'à 5 (PS : 3)"),
    ("Nombres", "Associer quantité / chiffre / constellation"),
    ("Explorer le vivant", "Ordonner le cycle de vie (œuf→papillon)"),
    ("Le temps", "Ranger les jours de la semaine dans l'ordre"),
    ("Graphisme", "Tracer des lignes ondulées maîtrisées"),
    ("Arts", "Réaliser la symétrie par pliage"),
]
rows = "".join(
    f'<tr><td>{d}</td><td>{c}</td><td class="code">NA</td><td class="code">EA</td><td class="code">A</td></tr>'
    for d, c in comp
)
supports["07_grille-evaluation"] = wrap(
    "Grille d'évaluation",
    f"""
<div class="page"><h1>Grille d'observation — compétences</h1><p class="sub">Élève : ____________________  ·  Classe : ______  ·  Période : ______</p>
<div class="consigne">Cocher le niveau atteint pour chaque compétence observée pendant la semaine.</div>
<table class="grille"><tr><th>Domaine</th><th>Compétence visée</th><th>NA</th><th>EA</th><th>A</th></tr>{rows}</table>
<p class="legende"><b>NA</b> = non acquis · <b>EA</b> = en cours d'acquisition · <b>A</b> = atteint — exploitable pour le carnet de suivi des apprentissages.</p></div>""",
)

# 8. Affiche bilan + matériel
mat = [
    "Album <i>La chenille qui fait des trous</i> + marotte chenille",
    "Étiquettes-lettres et étiquettes-jours",
    "Cartes-fruits 1→5, chiffres mobiles, dés-constellations",
    "Images du cycle de vie + roue à attache parisienne",
    "Gouache, papiers, colle, ciseaux",
    "Pâte à modeler",
    "Graines (lentilles/haricot) + petits pots",
    "Grilles d'observation par compétence (NA-EA-A)",
]
supports["08_affiche-bilan-materiel"] = wrap(
    "Affiche bilan & matériel",
    f"""
<div class="page affiche"><h1>Notre semaine de la chenille 🐛</h1>
<div class="big">D'abord l'œuf 🥚 … puis la chenille 🐛 … la chrysalide 🛡️ … enfin le papillon 🦋 !</div>
<div class="papillons">🦋 🦋 🦋 🦋 🦋</div>
<p class="sub">Affiche-bilan collective — exposition pour les familles dans le couloir.</p></div>
<div class="page"><h1>Matériel à préparer</h1><p class="sub">Liste pour la semaine complète</p>
<ul class="materiel">{"".join(f"<li>{m}</li>" for m in mat)}</ul></div>""",
)

# 9. Étiquettes-mots (étapes + jours) pour les GS
mots = [
    w
    for w in [
        "ŒUF",
        "CHENILLE",
        "CHRYSALIDE",
        "PAPILLON",
        "LUNDI",
        "MARDI",
        "MERCREDI",
        "JEUDI",
        "VENDREDI",
    ]
]
mots_h = "".join(
    f'<div class="lettre" style="width:auto;min-width:120px;height:54px;font-size:24px;padding:0 12px;border-style:solid">{w}</div>'
    for w in mots
)
supports["09_etiquettes-mots"] = wrap(
    "Étiquettes-mots (GS)",
    f"""
<div class="page"><h1>Étiquettes-mots à légender</h1><p class="sub">Langage écrit (GS) · associer chaque mot à son image</p>
<div class="consigne">🔤 Place chaque étiquette-mot sous la bonne image (étapes du cycle, jours de la semaine).</div>
<div class="lettres" style="justify-content:flex-start">{mots_h}</div></div>""",
)

for name, html in supports.items():
    (OUT / f"{name}.html").write_text(html, encoding="utf-8")
    print("écrit:", name + ".html")
print(f"\n{len(supports)} supports HTML générés dans {OUT}")
