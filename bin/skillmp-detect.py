#!/usr/bin/env python3
"""skillmp-detect.py — auto-detection par mots-cles -> cascade skills.

Lit un texte (prompt), en deduit la ou les FAMILLES d'agents concernees, remonte
les skills du catalogue correspondants (FTS5, 0 token) et rend la commande de
cascade prete a l'emploi.

Deux usages :
  skillmp-detect.py "<texte>"          -> rapport lisible (CLI)
  skillmp-detect.py --hook             -> lit .prompt sur stdin, sort le JSON du hook

Contrat hook : ne bloque JAMAIS. Toute erreur -> '{}' et code 0.
"""

import json
import os
import re
import sqlite3
import sys

DB = os.path.expanduser("~/jarvis/jarvis_master.db")

# Memes signaux que implantation.py : une seule verite lexicale pour tout le pipeline.
FAMILLES = [
    ("openclaw", r"openclaw|clawd|clawsweeper|discrawl|gitcrawl|clawtributor"),
    ("trading", r"\btrading\b|crypto|backtest|march[eé]|portfolio|binance|mexc|bourse"),
    (
        "omega",
        r"s[eé]curit|security|vuln[eé]rab|pentest|hardening|menace|owasp|exploit|cve|audit",
    ),
    (
        "ai",
        r"\bllm\b|embedding|\brag\b|prompt|inf[eé]rence|fine-?tun|mod[eè]le|ollama|lmstudio",
    ),
    ("data", r"sqlite|postgres|database|base de donn|\bsql\b|etl|pandas|sch[eé]ma"),
    (
        "monitoring",
        r"monitor|observab|m[eé]trique|grafana|prometheus|alerte|surveillance|log",
    ),
    ("comms", r"telegram|slack|discord|mail|gmail|smtp|notification|newsletter"),
    (
        "business",
        r"marketing|vente|\bcrm\b|facture|billing|seo|contenu|linkedin|prospect",
    ),
    (
        "automation",
        r"browser|playwright|puppeteer|scrap|selenium|crawl|automatis|workflow|n8n",
    ),
    (
        "ops",
        r"docker|kubernetes|d[eé]ploi|\bci/?cd\b|terraform|ansible|systemd|nginx|devops|service",
    ),
    (
        "dev",
        r"react|vue|angular|svelte|typescript|python|rust|golang|refactor|\btest|debug|\bapi\b",
    ),
    ("run", r"\blance\b|\brun\b|ex[eé]cut|pipeline|orchestr|scheduler|cron|vague"),
    ("chef", r"\bplan\b|architect|design|strat[eé]gie|d[eé]cision|revue|coordonn"),
    (
        "cowork",
        r"collabor|[eé]quipe|agent|multi-agent|d[eé]l[eè]gue|dispatch|distribue",
    ),
]

# Declencheurs explicites : le texte demande la cascade, pas seulement un theme.
DECLENCHEURS = r"cascade|implante|implanter|sortie plan mode|dispatch massif|vague d'implantation|distribue aux agents"


def familles_de(texte):
    bas = (texte or "").lower()
    trouvees = [nom for nom, motif in FAMILLES if re.search(motif, bas)]
    return trouvees


def skills_pour(cx, texte, famille, limite=5):
    """Top skills du catalogue pour ces mots-cles, restreints a la famille."""
    mots = [m for m in re.split(r"\W+", texte.lower()) if len(m) > 3][:6]
    if not mots:
        return []
    requete = " OR ".join(mots)
    try:
        lignes = cx.execute(
            """SELECT s.slug, s.nom, a.famille
               FROM skillsmp_fts f
               JOIN skillsmp_skills s ON s.rowid = f.rowid
               LEFT JOIN skillsmp_affectation a ON a.url = s.url
               WHERE skillsmp_fts MATCH ? AND (a.famille = ? OR a.famille IS NULL)
               LIMIT ?""",
            (requete, famille, limite),
        ).fetchall()
    except sqlite3.Error:
        return []
    return [{"slug": r[0], "nom": r[1], "famille": r[2]} for r in lignes]


def analyse(texte):
    familles = familles_de(texte)
    explicite = bool(re.search(DECLENCHEURS, (texte or "").lower()))
    resultat = {"familles": familles, "cascade_demandee": explicite, "skills": []}
    if not familles:
        return resultat
    if not os.path.exists(DB):
        return resultat
    try:
        cx = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=3)
        for fam in familles[:3]:
            resultat["skills"].extend(skills_pour(cx, texte, fam))
        # file en attente pour ces familles
        marques = ",".join("?" * len(familles[:3]))
        resultat["en_file"] = cx.execute(
            f"""SELECT COUNT(*) FROM skillmp_cascade_taches
                WHERE statut='pending' AND famille IN ({marques})""",
            familles[:3],
        ).fetchone()[0]
        cx.close()
    except sqlite3.Error:
        pass
    return resultat


def mode_hook():
    try:
        brut = sys.stdin.read()
        prompt = json.loads(brut).get("prompt", "") if brut.strip() else ""
    except (json.JSONDecodeError, ValueError):
        prompt = ""
    if not prompt:
        print("{}")
        return 0

    r = analyse(prompt)
    if not r["familles"]:
        print("{}")
        return 0

    fam = r["familles"][0]
    bouts = [f"SKILLS CASCADE — familles detectees : {', '.join(r['familles'][:3])}"]
    if r.get("en_file"):
        bouts.append(f"{r['en_file']} taches en file pour ces familles")
    if r["skills"]:
        bouts.append("skills : " + ", ".join(s["slug"] for s in r["skills"][:5]))
    bouts.append(f"commande : skillmp cascade --mode validated --famille {fam}")
    if r["cascade_demandee"]:
        bouts.append("→ cascade explicitement demandee : appliquer, ne pas replanifier")

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": " | ".join(bouts),
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


def main():
    if "--hook" in sys.argv:
        try:
            return mode_hook()
        except Exception:  # fail-safe absolu : un hook ne bloque jamais
            print("{}")
            return 0

    texte = " ".join(a for a in sys.argv[1:] if not a.startswith("--"))
    if not texte:
        print(__doc__)
        return 2
    r = analyse(texte)
    print(f"familles         : {', '.join(r['familles']) or '(aucune)'}")
    print(f"cascade demandee : {r['cascade_demandee']}")
    print(f"taches en file   : {r.get('en_file', 0)}")
    for s in r["skills"]:
        print(f"  - {s['slug']:45s} [{s['famille'] or '?'}]")
    if r["familles"]:
        print(f"\n→ skillmp cascade --mode validated --famille {r['familles'][0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
