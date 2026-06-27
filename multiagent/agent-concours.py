#!/usr/bin/env python3
"""JARVIS Agent Concours MAMS — préparation oral 2 juin 2026."""

import json
import random
import sys
from pathlib import Path

import requests

QUESTIONS_FILE = Path("/home/pamerys/jarvis/multiagent/mams_questions_jury.json")
M1 = "http://192.168.1.85:1234"
M2 = "http://192.168.1.26:1234"
MODEL = "qwen3.5-27b-claude-4.6-opus-distilled"


def load_questions():
    if QUESTIONS_FILE.exists():
        return json.loads(QUESTIONS_FILE.read_text())
    return []


def ask_llm(prompt: str, model: str = MODEL) -> str:
    for host in [M1, M2]:
        try:
            r = requests.post(
                f"{host}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Tu es un coach expert pour le concours MAMS "
                                "(secrétaire général d'EPLE). Tu prépares une candidate "
                                "à l'oral du 2 juin 2026. Réponds de façon précise, "
                                "structurée et adaptée au niveau attendu par le jury."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 800,
                    "temperature": 0.7,
                },
                timeout=30,
            )
            return r.json()["choices"][0]["message"]["content"]
        except Exception:
            continue
    return "[Erreur: cluster LLM indisponible]"


def cmd_question(args: list[str]) -> None:
    questions = load_questions()
    if not questions:
        print("Aucune question trouvée.")
        return
    theme_filter = " ".join(args).lower() if args else None
    pool = (
        [q for q in questions if theme_filter in q["theme"].lower()]
        if theme_filter
        else questions
    )
    if not pool:
        print(f"Aucune question pour le thème: {theme_filter}")
        return
    q = random.choice(pool)
    print(f"\n🎯 QUESTION JURY ({q['theme']})")
    print(f"   « {q['q']} »\n")
    answer = ask_llm(
        f"Question du jury MAMS: {q['q']}\n\nDonne une réponse-type concise (5-8 lignes) adaptée pour un oral de concours."
    )
    print("💡 RÉPONSE TYPE:")
    print(answer)


def cmd_simulation(args: list[str]) -> None:
    questions = load_questions()
    sample = random.sample(questions, min(5, len(questions)))
    print("\n🎭 SIMULATION ORAL BLANC — 5 questions\n" + "=" * 50)
    for i, q in enumerate(sample, 1):
        print(f"\n[{i}/5] ({q['theme']})")
        print(f"Jury: « {q['q']} »")
        ans = ask_llm(f"Réponds brièvement (3-5 lignes): {q['q']}")
        print(f"Réponse: {ans}")


def cmd_liste_themes(_: list[str]) -> None:
    questions = load_questions()
    themes: dict[str, int] = {}
    for q in questions:
        themes[q["theme"]] = themes.get(q["theme"], 0) + 1
    print(f"\n📚 {len(questions)} questions — {len(themes)} thèmes:\n")
    for t, n in sorted(themes.items(), key=lambda x: -x[1]):
        print(f"  {n:3d}q  {t}")


def cmd_free(args: list[str]) -> None:
    prompt = " ".join(args)
    if not prompt:
        print("Usage: jarvis-concours <question libre>")
        return
    print(ask_llm(prompt))


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("jarvis-concours [question|simulation|themes|<question libre>]")
        return
    cmd = args[0].lower()
    rest = args[1:]
    if cmd in ("question", "q", "questions_jury"):
        cmd_question(rest)
    elif cmd in ("simulation", "oral", "simulation_jury"):
        cmd_simulation(rest)
    elif cmd in ("themes", "liste_themes"):
        cmd_liste_themes(rest)
    else:
        cmd_free(args)


if __name__ == "__main__":
    main()
