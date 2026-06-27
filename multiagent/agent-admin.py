#!/usr/bin/env python3
"""Agent JARVIS — Démarches administratives (MDPH, DALO, CAF, Académie...)"""
import sys, requests, os, glob

DEMARCHES = os.path.expanduser("~/Documents/Windows-Import/demarches/")
M1 = "http://192.168.1.85:1234"

def get_context():
    """Charge les démarches disponibles"""
    docs = glob.glob(DEMARCHES + "*.md")
    return f"Démarches disponibles: {[os.path.basename(d) for d in docs[:10]]}"

def ask(q):
    ctx = get_context()
    prompt = f"""Tu es un assistant spécialisé en démarches administratives françaises.
Tu aides Claire Domingues-Delmas avec ses démarches: MDPH31, DALO, CAF, Académie Toulouse, HLM, CapEmploi31, Agefiph.
{ctx}

Question: {q}

Donne une réponse précise et pratique. Si tu connais une démarche spécifique, explique les étapes."""
    r = requests.post(f"{M1}/v1/chat/completions", json={
        "model": "qwen/qwen3.5-9b",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800, "temperature": 0.2
    }, timeout=45)
    return r.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Quelles démarches sont en cours?"
    print(ask(q))
