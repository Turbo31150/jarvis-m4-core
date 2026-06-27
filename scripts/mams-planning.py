#!/usr/bin/env python3
"""JARVIS MAMS Planning — Programme de révision J-10 au J-1.
Usage: mams-planning [--full | --today | --theme <n>]
"""

import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

# ── Constantes ────────────────────────────────────────────────────────────────
ORAL_DATE = date(2026, 6, 2)
QUESTIONS_FILE = Path.home() / "jarvis/multiagent/mams_questions_jury.json"
REPONSES_FILE = Path.home() / "jarvis/multiagent/mams_reponses_type.md"

# ── ANSI ──────────────────────────────────────────────────────────────────────
R, G, Y, C, M, B, Z = (
    "\033[31m",
    "\033[32m",
    "\033[33m",
    "\033[36m",
    "\033[35m",
    "\033[1m",
    "\033[0m",
)

# ── Planning thématique J-10 → J-1 ───────────────────────────────────────────
PLANNING = {
    10: {
        "theme": "Parcours professionnel",
        "focus": "Posture, équipe de direction, positionnement",
    },
    9: {
        "theme": "Fonction publique",
        "focus": "Droits/obligations, statut, loi transfo FP",
    },
    8: {
        "theme": "Comptabilité",
        "focus": "AE/CP, titre 2, MRCF, OP@LE, responsabilité",
    },
    7: {
        "theme": "Gouvernance EPLE",
        "focus": "CA, commission permanente, PPMS, lycée pro",
    },
    6: {
        "theme": "Politiques éducatives",
        "focus": "ORE, EGAlim, laïcité, inclusion, SNU",
    },
    5: {
        "theme": "Mise en situation",
        "focus": "Management de crise, conduite du changement",
    },
    4: {
        "theme": "Révision globale",
        "focus": "Simulation orale — tous thèmes aléatoires",
    },
    3: {"theme": "Réponses-type", "focus": "Reformulation, fluidité, concision"},
    2: {
        "theme": "Simulation finale",
        "focus": "Oral blanc complet + logistique déplacement",
    },
    1: {
        "theme": "Repos & relecture légère",
        "focus": "Dernière relecture + préparer affaires",
    },
}


def load_questions() -> list[dict]:
    try:
        return json.loads(QUESTIONS_FILE.read_text())
    except FileNotFoundError:
        return []


def days_left() -> int:
    return (ORAL_DATE - date.today()).days


def header(title: str) -> None:
    line = "═" * 52
    print(f"\n{B}{C}╔{line}╗{Z}")
    print(f"{B}{C}║  {title:<50}║{Z}")
    print(f"{B}{C}╚{line}╝{Z}")


def show_today() -> None:
    j = days_left()
    today = date.today()

    if j <= 0:
        print(f"\n{B}{G}🎯 Bonne chance pour l'oral MAMS !{Z}\n")
        return
    if j > 10:
        print(f"\n{Y}Oral MAMS dans {j} jours — planning actif à J-10.{Z}\n")
        return

    plan = PLANNING.get(j, {"theme": "Révision libre", "focus": "À ta convenance"})
    questions = load_questions()
    theme_qs = [q for q in questions if plan["theme"].lower() in q["theme"].lower()]

    header(f"JARVIS MAMS — {today.strftime('%A %d %B')} — J-{j}")

    print(f"\n  {B}🎯 Thème du jour:{Z} {C}{plan['theme']}{Z}")
    print(f"  {B}💡 Focus:{Z} {plan['focus']}")
    print(f"  {B}📅 Oral:{Z} {ORAL_DATE.strftime('%A %d %B %Y')} (J-{j})")

    if theme_qs:
        print(f"\n  {B}❓ Questions du thème ({len(theme_qs)} disponibles):{Z}")
        sample = random.sample(theme_qs, min(3, len(theme_qs)))
        for i, q in enumerate(sample, 1):
            print(f"  {Y}{i}.{Z} {q['q']}")
    else:
        print(f"\n  {Y}Pas de questions spécifiques — révision libre{Z}")

    if j <= 3:
        print(f"\n  {R}{B}⚠️  DERNIERS JOURS — simulation orale recommandée !{Z}")
        print(f"  {C}→ jarvis-concours simulation{Z}")

    print()


def show_full_planning() -> None:
    header("PLANNING COMPLET — RÉVISION MAMS 2026")
    j_now = days_left()
    print()
    for j in sorted(PLANNING.keys(), reverse=True):
        plan = PLANNING[j]
        d = ORAL_DATE - timedelta(days=j)
        marker = f"{G}◀ AUJOURD'HUI{Z}" if j == j_now else ""
        past = f"{R}(passé){Z}" if j > j_now else ""
        color = G if j <= j_now else Y
        print(
            f"  {color}J-{j:2d}{Z}  {d.strftime('%d/%m')}  "
            f"{B}{plan['theme']:<30}{Z}  {plan['focus'][:35]}  {marker}{past}"
        )
    print()
    print(f"  {B}{G}  2 JUIN: ORAL MAMS 🎯{Z}\n")


def show_theme(n: int) -> None:
    plan = PLANNING.get(n)
    if not plan:
        print(f"{R}J-{n} non trouvé (valeurs: 1-10){Z}")
        sys.exit(1)
    questions = load_questions()
    theme_qs = [q for q in questions if plan["theme"].lower() in q["theme"].lower()]
    header(f"J-{n} — {plan['theme']}")
    print(f"\n  {B}Focus:{Z} {plan['focus']}")
    print(f"\n  {B}Questions ({len(theme_qs)}):{Z}")
    for i, q in enumerate(theme_qs, 1):
        print(f"  {Y}{i:2d}.{Z} {q['q']}")
    print()


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] == "--today":
        show_today()
    elif args[0] == "--full":
        show_full_planning()
    elif args[0] == "--theme" and len(args) > 1:
        try:
            show_theme(int(args[1]))
        except ValueError:
            print(f"{R}Usage: mams-planning --theme <1-10>{Z}")
            sys.exit(1)
    elif args[0] in ("-h", "--help"):
        print("Usage: mams-planning [--today | --full | --theme <1-10>]")
    else:
        show_today()


if __name__ == "__main__":
    main()
