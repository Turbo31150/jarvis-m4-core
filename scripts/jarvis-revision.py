#!/usr/bin/env python3
"""
jarvis-revision.py — Système de révision MAMS pour oral concours
Modes: interactif (menu), thème, all, timer
Dépendances: stdlib uniquement (json, re, sys, time, signal)
"""

import json
import re
import sys
import signal
import select
from pathlib import Path

# ==================== CONFIG ====================
MAMS_DIR = Path.home() / "jarvis" / "multiagent"
QUESTIONS_FILE = MAMS_DIR / "mams_questions_jury.json"
REPONSES_FILE = MAMS_DIR / "mams_reponses_type.md"

# ANSI Colors
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"
GRAY = "\033[90m"

# ==================== DONNÉES ====================


def load_questions():
    """Charge les questions depuis le JSON"""
    try:
        with open(QUESTIONS_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"\033[31m✗ Fichier non trouvé: {QUESTIONS_FILE}\033[0m")
        sys.exit(1)


def load_reponses():
    """Charge les réponses depuis le markdown"""
    try:
        with open(REPONSES_FILE) as f:
            return f.read()
    except FileNotFoundError:
        print(f"\033[31m✗ Fichier non trouvé: {REPONSES_FILE}\033[0m")
        sys.exit(1)


def group_by_theme(questions):
    """Groupe les questions par thème"""
    themes = {}
    for q in questions:
        theme = q["theme"]
        if theme not in themes:
            themes[theme] = []
        themes[theme].append(q)
    return themes


def find_reponse(reponses_text, question_text):
    """
    Cherche la réponse pour une question donnée.
    Stratégie: trouve la ligne "### Q: <question_text>" et prend les 3-5 lignes suivantes.
    """
    # Échappe les caractères spéciaux pour regex
    q_escaped = re.escape(question_text)
    pattern = rf"###\s+Q:\s*{q_escaped}.*?(?=\n###|$)"

    match = re.search(pattern, reponses_text, re.IGNORECASE | re.DOTALL)
    if not match:
        return None

    block = match.group(0)
    lines = block.split("\n")

    # Ligne avec Q:, puis prend les 3-5 lignes de réponse
    response_lines = []
    in_response = False
    for line in lines[1:]:
        if line.strip().startswith("**R:**"):
            in_response = True
            # Extrait le texte après **R:**
            r_text = line.replace("**R:**", "").strip()
            if r_text:
                response_lines.append(r_text)
        elif in_response:
            if line.strip() and not line.startswith("###"):
                response_lines.append(line)
            if len(response_lines) >= 3:
                break

    return " ".join(response_lines) if response_lines else None


def print_question(num, total, theme, question_text):
    """Affiche la question formatée"""
    print(f"\n{YELLOW}{'━' * 60}{RESET}")
    print(f"{YELLOW}QUESTION {num}/{total} — {theme}{RESET}")
    print(f"{YELLOW}{'━' * 60}{RESET}")
    print(f"\n{CYAN}{BOLD}{question_text}{RESET}\n")


def print_reponse(reponse_text):
    """Affiche la réponse formatée"""
    if reponse_text:
        print(f"{GREEN}{reponse_text}{RESET}\n")
    else:
        print(f"{GRAY}[Réponse à préparer]{RESET}\n")


def timer_prompt(duration_sec=120):
    """
    Attend input avec timeout. Retourne True si Entrée, False si timeout.
    Non-bloquant : utilisateur peut interrompre avec Entrée.
    """
    print(
        f"\033[33m⏱  {duration_sec}s — Appuyez Entrée pour continuer...\033[0m ",
        end="",
        flush=True,
    )
    for remaining in range(duration_sec, 0, -1):
        print(
            f"\r\033[33m⏱  {remaining:3d}s — Appuyez Entrée...\033[0m ",
            end="",
            flush=True,
        )
        rlist, _, _ = select.select([sys.stdin], [], [], 1)
        if rlist:
            sys.stdin.readline()
            print()
            return True
    print()
    return False


def run_questions_sequence(questions, with_timer=False):
    """
    Parcourt une liste de questions et affiche réponses.
    Gère Ctrl+C, retourne nombre de questions parcourues.
    """
    reponses_text = load_reponses()
    count = 0

    try:
        for i, q in enumerate(questions, 1):
            q_text = q["q"]
            theme = q["theme"]

            print_question(i, len(questions), theme, q_text)
            print(f"{GRAY}Appuyez Entrée pour voir la réponse...{RESET}")

            try:
                input()
            except (KeyboardInterrupt, EOFError):
                return count

            reponse = find_reponse(reponses_text, q_text)
            print_reponse(reponse)

            if with_timer:
                result = timer_prompt(duration_sec=120)
                if not result:
                    # Timeout, on continue auto
                    count += 1
                    continue

            print(f"{GRAY}Appuyez Entrée pour continuer (q=quitter)...{RESET}")
            try:
                user_input = input()
                if user_input.lower() == "q":
                    return count + 1
            except (KeyboardInterrupt, EOFError):
                return count + 1

            count += 1

    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Révision interrompue.{RESET}")
        return count

    return len(questions)


def show_themes_menu(themes_dict):
    """Affiche le menu des thèmes et retourne le choix"""
    themes_list = sorted(themes_dict.keys())

    print(f"\n{YELLOW}{'━' * 60}{RESET}")
    print(f"{YELLOW}{BOLD}RÉVISION MAMS — Sélection de thème{RESET}")
    print(f"{YELLOW}{'━' * 60}{RESET}\n")

    for i, theme in enumerate(themes_list, 1):
        count = len(themes_dict[theme])
        print(f"  {i}. {theme} ({count} questions)")

    print("\n  a. Aléatoire (tous thèmes)")
    print("  q. Quitter\n")

    while True:
        choice = (
            input(f"{CYAN}Choisir thème (1-{len(themes_list)}, a, q): {RESET}")
            .strip()
            .lower()
        )

        if choice == "q":
            return None
        elif choice == "a":
            # Retourne toutes les questions
            all_qs = []
            for theme in themes_list:
                all_qs.extend(themes_dict[theme])
            return all_qs
        elif choice.isdigit() and 1 <= int(choice) <= len(themes_list):
            theme = themes_list[int(choice) - 1]
            return themes_dict[theme]
        else:
            print(f"{YELLOW}Choix invalide. Réessayez.{RESET}")


def print_score(count, total):
    """Affiche le score final"""
    pct = int(100 * count / total) if total > 0 else 0
    print(f"\n{YELLOW}{'━' * 60}{RESET}")
    print(f"{GREEN}Révision complétée: {count}/{total} questions ({pct}%){RESET}")
    print(f"{YELLOW}{'━' * 60}{RESET}\n")


def handle_signal(sig, frame):
    """Gère Ctrl+C proprement"""
    print(f"\n\n{YELLOW}Révision interrompue par l'utilisateur.{RESET}")
    sys.exit(0)


# ==================== MAIN ====================


def main():
    signal.signal(signal.SIGINT, handle_signal)

    questions = load_questions()
    themes_dict = group_by_theme(questions)

    # Parsing arguments
    if len(sys.argv) == 1:
        # Mode menu interactif
        selected_questions = show_themes_menu(themes_dict)
        if selected_questions is None:
            print(f"{YELLOW}Au revoir!{RESET}")
            return
        with_timer = False
    elif len(sys.argv) == 2:
        arg = sys.argv[1].lower()

        if arg == "themes":
            # Affiche les thèmes (mode test)
            print(f"\n{YELLOW}Thèmes disponibles:{RESET}")
            for theme in sorted(themes_dict.keys()):
                count = len(themes_dict[theme])
                print(f"  - {theme}: {count} questions")
            return

        elif arg == "all":
            # Toutes les questions
            selected_questions = questions
            with_timer = False

        elif arg == "timer":
            # Mode aléatoire avec timer
            selected_questions = show_themes_menu(themes_dict)
            if selected_questions is None:
                print(f"{YELLOW}Au revoir!{RESET}")
                return
            with_timer = True

        elif arg in themes_dict:
            # Thème spécifique
            selected_questions = themes_dict[arg]
            with_timer = False

        else:
            print(f"{YELLOW}Argument invalide: {arg}{RESET}")
            print("Usage: jarvis-revision [thème|all|timer|themes]")
            sys.exit(1)
    else:
        print("Usage: jarvis-revision [thème|all|timer|themes]")
        sys.exit(1)

    # Exécution
    count = run_questions_sequence(selected_questions, with_timer=with_timer)
    print_score(count, len(selected_questions))


if __name__ == "__main__":
    main()
