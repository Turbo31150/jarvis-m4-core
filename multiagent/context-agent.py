#!/usr/bin/env python3
"""
Context Agent - Explique texte adapté au niveau scolaire
Reçoit texte stdin ou argv --text "..." --niveau [primaire|college|lycee|adulte]
Niveau par défaut: college
Fallback M1 -> M2
"""

import sys
import argparse
import requests
import json
from typing import Optional

# Configuration
M1_ENDPOINT = "http://192.168.1.85:1234/v1/chat/completions"
M2_ENDPOINT = "http://192.168.1.26:1234/v1/chat/completions"
TIMEOUT = 30
MODEL = "qwen3.5-9b"

SYSTEM_PROMPTS = {
    "primaire": "Tu es assistant pour enfants de 6-10 ans. Explique simplement avec des exemples du quotidien.",
    "college": "Tu es assistant pédagogique pour collégiens. Explique clairement avec exemples concrets.",
    "lycee": "Tu es assistant pour lycéens. Explique avec rigueur et exemples académiques.",
    "adulte": "Tu es assistant expert. Réponse directe et précise.",
}


def get_args():
    """Parse arguments stdin + argv."""
    parser = argparse.ArgumentParser(description="Context agent")
    parser.add_argument("--text", type=str, default=None, help="Texte à expliquer")
    parser.add_argument(
        "--niveau",
        type=str,
        default="college",
        choices=list(SYSTEM_PROMPTS.keys()),
        help="Niveau scolaire (primaire|college|lycee|adulte)",
    )
    args = parser.parse_args()

    text = args.text
    niveau = args.niveau

    # Lire depuis stdin si pas de --text
    if not text and not sys.stdin.isatty():
        text = sys.stdin.read().strip()

    if not text:
        print("Usage: echo 'texte' | python3 context-agent.py [--niveau college]", file=sys.stderr)
        print(
            "   ou: python3 context-agent.py --text 'texte' --niveau lycee",
            file=sys.stderr,
        )
        sys.exit(1)

    return text, niveau


def call_llm(text: str, endpoint: str, system_prompt: str) -> Optional[str]:
    """Appelle LLM via endpoint OpenAI-compatible."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "temperature": 0.7,
        "max_tokens": 500,
    }

    try:
        response = requests.post(
            endpoint,
            json=payload,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return None


def main():
    text, niveau = get_args()
    system_prompt = SYSTEM_PROMPTS[niveau]

    # Essai M1
    result = call_llm(text, M1_ENDPOINT, system_prompt)

    # Fallback M2
    if result is None:
        result = call_llm(text, M2_ENDPOINT, system_prompt)

    if result is None:
        print("Erreur: impossible contacter M1 ou M2", file=sys.stderr)
        sys.exit(1)

    print(result)


if __name__ == "__main__":
    main()
