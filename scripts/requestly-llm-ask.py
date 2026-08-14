#!/usr/bin/env python3
"""
requestly-llm-ask.py — Connecteur terminal pour ChatGPT, Gemini & Perplexity via Requestly.
Permet d'exécuter directement les requêtes et endpoints configurés dans Requestly.

Usage:
  requestly-ask gemini "Explique le fonctionnement des MCP"
  requestly-ask chatgpt "Donne-moi un snippet Python pour FastAPI"
  requestly-ask perplexity "Dernières actualités IA"
  requestly-ask --list
"""

import sys
import json
import argparse
from pathlib import Path

REQUESTLY_SCRIPT = Path("/home/pamerys/IA/Core/jarvis/scripts/mcp_requestly.py")
if not REQUESTLY_SCRIPT.exists():
    REQUESTLY_SCRIPT = Path("/home/pamerys/jarvis/scripts/mcp_requestly.py")

sys.path.insert(0, str(REQUESTLY_SCRIPT.parent))
import mcp_requestly as req

MAPPING = {
    "chatgpt": ("IA Web — ChatGPT", "API-chat-gpt4o"),
    "gpt": ("IA Web — ChatGPT", "API-chat-gpt4o"),
    "o1": ("IA Web — ChatGPT", "API-chat-o1"),
    "gemini": ("IA Web — Gemini", "API-generate-flash"),
    "gemini-pro": ("IA Web — Gemini", "API-generate-pro"),
    "perplexity": ("IA Web — Perplexity", "API-chat-sonar"),
    "sonar": ("IA Web — Perplexity", "API-chat-sonar"),
    "sonar-reasoning": ("IA Web — Perplexity", "API-chat-sonar-reasoning"),
}

def list_targets():
    cols = req.list_collections()
    print("=== Collections et Endpoints Requestly IA disponibles ===")
    for target in ['IA Web — ChatGPT', 'IA Web — Gemini', 'IA Web — Perplexity', 'JARVIS — Perplexity', 'JARVIS — AI Studio']:
        if target in cols:
            print(f"\n📂 {target}:")
            for r in cols[target]:
                print(f"  • {r['name']} [{r['method']}] -> {r['url']}")

def execute_llm(provider: str, prompt: str, timeout: int = 30):
    prov = provider.lower()
    if prov not in MAPPING:
        print(f"Provider inconnu '{provider}'. Choix possibles: {', '.join(MAPPING.keys())}")
        sys.exit(1)
    
    col, req_name = MAPPING[prov]
    
    # Préparer la payload selon le provider
    req_details = req.get_request(col, req_name)
    if "error" in req_details:
        print(f"Erreur chargement endpoint: {req_details['error']}")
        sys.exit(1)
    
    print(f"🚀 [Requestly] Exécution via {col} / {req_name}...")
    res = req.execute_request(col, req_name, timeout=timeout)
    print(json.dumps(res, indent=2, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="Connecteur Requestly pour ChatGPT, Gemini, Perplexity")
    parser.add_argument("provider", nargs="?", help="Provider (chatgpt, gemini, perplexity, o1, etc.)")
    parser.add_argument("prompt", nargs="?", help="Prompt / Question à envoyer")
    parser.add_argument("--list", action="store_true", help="Lister les collections et requêtes IA")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout en secondes")

    args = parser.parse_args()

    if args.list or not args.provider:
        list_targets()
        return

    execute_llm(args.provider, args.prompt or "", timeout=args.timeout)

if __name__ == "__main__":
    main()
