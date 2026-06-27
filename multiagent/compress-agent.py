#!/usr/bin/env python3
"""
Compress Agent - Comprime texte via LM local M2/M1
Reçoit texte stdin ou argv --text "..."
Fallback M2 -> M1
"""

import sys
import argparse
import requests
import json
from typing import Optional

# Configuration
M2_ENDPOINT = "http://192.168.1.26:1234/v1/chat/completions"
M1_ENDPOINT = "http://192.168.1.85:1234/v1/chat/completions"
TIMEOUT = 20
MODEL = "qwen3.5-9b"

SYSTEM_PROMPT = """Compresse ce texte en gardant l'essentiel. Max 3 phrases. Français."""


def get_text() -> str:
    """Récupère texte depuis stdin ou argv."""
    parser = argparse.ArgumentParser(description="Compress agent")
    parser.add_argument("--text", type=str, default=None, help="Texte à compresser")
    args = parser.parse_args()

    if args.text:
        return args.text

    # Lire depuis stdin
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    print("Usage: echo 'texte' | python3 compress-agent.py", file=sys.stderr)
    print("   ou: python3 compress-agent.py --text 'texte'", file=sys.stderr)
    sys.exit(1)


def call_llm(text: str, endpoint: str) -> Optional[str]:
    """Appelle LLM via endpoint OpenAI-compatible."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.7,
        "max_tokens": 150,
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
    text = get_text()

    if not text:
        print("Erreur: aucun texte fourni", file=sys.stderr)
        sys.exit(1)

    # Essai M2
    result = call_llm(text, M2_ENDPOINT)

    # Fallback M1
    if result is None:
        result = call_llm(text, M1_ENDPOINT)

    if result is None:
        print("Erreur: impossible contacter M2 ou M1", file=sys.stderr)
        sys.exit(1)

    print(result)


if __name__ == "__main__":
    main()
