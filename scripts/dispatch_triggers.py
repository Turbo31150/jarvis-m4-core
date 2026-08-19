#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dispatch_triggers.py — genere en masse les mots-cles de declenchement manquants
des skills run-*, et les fusionne dans skill-triggers.json.

Applique la recette dispatch-generation-masse, MAIS avec les plafonds reellement
mesures sur cette machine le 2026-08-19 :

  - Backend depporte M6 (10.42.0.230:1234)  : ECHOUE MEME A CONCURRENCE 1.
    Ecarte. Ce n'est pas un choix de style, c'est une mesure.
  - Backend cloud `kimi-k2.5:cloud`         : RETIRE par Ollama le 2026-07-31.
    Ecarte. L'erreur serveur le dit mot pour mot.
  - Ollama local qwen2.5:7b                 : 4 requetes concurrentes -> 4/4 OK.
    Retenu, avec garde-fou thermique puisqu'il chauffe le M4.

La recette recommande un backend deporte pour ne pas chauffer. Aucun n'est
disponible aujourd'hui : on assume le calcul local et on surveille la
temperature, plutot que de faire semblant d'avoir un cloud.

Idempotent : relançable sans doublon (fusion par nom de skill).
"""
import json
import os
import pathlib
import re
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

OLLAMA = "http://127.0.0.1:11434/api/chat"
MODELE = "qwen2.5:7b"
REGISTRE = pathlib.Path.home() / ".claude/skills/run-jarvis-autoheal/skill-triggers.json"
SKILL_DIRS = [pathlib.Path.home() / ".claude/skills",
              pathlib.Path.home() / "jarvis/.claude/skills"]
JOURNAL = pathlib.Path.home() / "jarvis/logs/dispatch_triggers.log"

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 4
SEUIL_C = 82.0          # garde-fou : au-dela on reporte, on ne casse pas
MARGE = 6.0             # il faut redescendre a 76 °C pour repartir (anti-yoyo)
PAUSE_CHAUD = 10        # granularite de la boucle d'attente
PAUSE_MAX = 300         # plafond : on n'attend pas indefiniment
ESSAIS = 4
MIN_MOTS = 4            # plancher de qualite : en dessous, on refuse et on rejoue

_verrou = threading.Lock()
_faits = {"n": 0}


def log(msg):
    ligne = "%s %s" % (time.strftime("%H:%M:%S"), msg)
    print(ligne, flush=True)
    with _verrou:
        with open(JOURNAL, "a", encoding="utf-8") as f:
            f.write(ligne + "\n")


def temperature():
    """Temperature paquet CPU, ou None si illisible."""
    for p in pathlib.Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try:
            v = int(p.read_text()) / 1000.0
            if 20 < v < 120:
                return v
        except Exception:
            pass
    return None


def attendre_si_chaud():
    """Attend REELLEMENT le retour sous le seuil, au lieu de dormir une fois.

    Version precedente : un sleep(25) puis on repartait sans revérifier — la
    machine tenait 91 °C en continu, le seuil de throttling de ce chassis.
    """
    attendu = 0
    prevenu = False
    while attendu < PAUSE_MAX:
        t = temperature()
        if not t or t < SEUIL_C - MARGE:
            if prevenu:
                log("  [thermique] retombe a %.1f °C apres %ds — reprise"
                    % (t or 0, attendu))
            return prevenu
        if not prevenu:
            log("  [thermique] %.1f °C >= %.0f — attente du refroidissement"
                % (t, SEUIL_C))
            prevenu = True
        time.sleep(PAUSE_CHAUD)
        attendu += PAUSE_CHAUD
    log("  [thermique] toujours chaud apres %ds — on avance quand meme" % attendu)
    return True


def description_skill(nom):
    """Lit la description du SKILL.md — frontmatter d'abord, sinon premieres lignes."""
    for base in SKILL_DIRS:
        f = base / nom / "SKILL.md"
        if not f.is_file():
            continue
        txt = f.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"^description:\s*(?:\|[^\n]*\n)?((?:[ \t]+.*\n|[^\n]*\n))",
                      txt, re.M)
        if m:
            d = re.sub(r"\s+", " ", m.group(1)).strip()
            if len(d) > 40:
                return d[:900]
        corps = re.sub(r"^---.*?---", "", txt, flags=re.S)
        corps = re.sub(r"[#`*>|]", " ", corps)
        corps = re.sub(r"\s+", " ", corps).strip()
        if corps:
            return corps[:900]
    return ""


def demander(prompt, timeout=180):
    charge = {"model": MODELE,
              "messages": [{"role": "user", "content": prompt}],
              "stream": False,
              "options": {"num_predict": 320, "temperature": 0.2}}
    req = urllib.request.Request(OLLAMA, json.dumps(charge).encode("utf-8"),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["message"]["content"]


GABARIT = """Voici la description d'un outil en ligne de commande nommé "{nom}".

{desc}

Donne les mots-clés qui doivent déclencher cet outil quand un utilisateur les
emploie. Réponds UNIQUEMENT par un objet JSON, sans texte autour, de la forme :
{{"keywords_fr": ["...", "..."], "keywords_en": ["...", "..."]}}

Exemple de réponse attendue, pour un outil qui pilote AnyDesk entre machines :
{{"keywords_fr": ["anydesk", "réveil", "fond noir", "mesh", "wake on lan", "accès distant"], "keywords_en": ["anydesk", "wake", "mesh", "privacy", "wol", "unattended"]}}

Règles impératives : EXACTEMENT 6 mots-clés par langue, ni plus ni moins.
Minuscules, courts, distinctifs. Pas de mot générique isolé comme "lance",
"run", "test", "outil" ou "jarvis". Privilégie ce qui identifie CET outil."""


def extraire_json(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        raise ValueError("pas de JSON dans la reponse")
    d = json.loads(m.group())
    fr = [str(x).strip().lower() for x in d.get("keywords_fr", []) if str(x).strip()]
    en = [str(x).strip().lower() for x in d.get("keywords_en", []) if str(x).strip()]
    fr = [k for k in dict.fromkeys(fr) if len(k) > 2]
    en = [k for k in dict.fromkeys(en) if len(k) > 2]
    if len(fr) < MIN_MOTS or len(en) < MIN_MOTS:
        raise ValueError("qualite insuffisante (fr=%d en=%d, minimum %d)"
                         % (len(fr), len(en), MIN_MOTS))
    return fr[:8], en[:8]


def worker(nom, total):
    desc = description_skill(nom)
    if not desc:
        log("  [%s] IGNORE — aucun SKILL.md lisible" % nom)
        return None
    for essai in range(1, ESSAIS + 1):
        attendre_si_chaud()
        try:
            fr, en = extraire_json(demander(GABARIT.format(nom=nom, desc=desc)))
            with _verrou:
                _faits["n"] += 1
                n = _faits["n"]
            log("[%d/%d %d%%] OK %-34s fr=%d en=%d"
                % (n, total, 100 * n // total, nom, len(fr), len(en)))
            return {"skill": nom, "priority": 5,
                    "keywords_fr": fr, "keywords_en": en}
        except Exception as e:
            if essai == ESSAIS:
                log("  [%s] ABANDON apres %d essais : %s" % (nom, ESSAIS, str(e)[:70]))
                return None
            time.sleep(3 * essai)
    return None


def manquants():
    """Trous = tous les run-* moins ceux deja couverts. SQL-like, 0 token."""
    d = json.loads(REGISTRE.read_text(encoding="utf-8"))
    couverts = {e.get("skill") for e in d["triggers"]}
    runs = set()
    for base in SKILL_DIRS:
        if base.is_dir():
            runs |= {p.name for p in base.iterdir()
                     if p.is_dir() and p.name.startswith("run-")}
    return d, sorted(runs - couverts)


def fusionner(registre, nouvelles):
    """Fusion idempotente : une entree par skill, les nouvelles gagnent."""
    par_nom = {e["skill"]: e for e in registre["triggers"]}
    for e in nouvelles:
        par_nom[e["skill"]] = e
    registre["triggers"] = sorted(par_nom.values(), key=lambda e: e["skill"])
    sauvegarde = REGISTRE.with_suffix(".json.bak-%s" % time.strftime("%Y%m%d-%H%M%S"))
    sauvegarde.write_text(REGISTRE.read_text(encoding="utf-8"), encoding="utf-8")
    REGISTRE.write_text(json.dumps(registre, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    return sauvegarde


def main():
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    registre, trous = manquants()
    if not trous:
        log("Aucun skill run-* sans trigger — rien a faire.")
        return
    t0 = time.time()
    log("=== DISPATCH TRIGGERS : %d skills, %d workers, backend %s ==="
        % (len(trous), WORKERS, MODELE))
    t = temperature()
    log("    thermique au depart : %s" % ("%.1f °C" % t if t else "illisible"))

    produites = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futurs = [ex.submit(worker, n, len(trous)) for n in trous]
        for f in as_completed(futurs):
            r = f.result()
            if r:
                produites.append(r)

    abandons = len(trous) - len(produites)
    sauvegarde = fusionner(registre, produites) if produites else None
    log("=== TERMINE en %.0fs : %d generees, %d abandonnees ==="
        % (time.time() - t0, len(produites), abandons))
    if abandons:
        log("    (les abandons sont journalises ci-dessus, aucune troncature silencieuse)")
    if sauvegarde:
        log("    registre mis a jour — sauvegarde : %s" % sauvegarde.name)
    t = temperature()
    log("    thermique en fin : %s" % ("%.1f °C" % t if t else "illisible"))


if __name__ == "__main__":
    main()
