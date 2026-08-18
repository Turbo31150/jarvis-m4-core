#!/usr/bin/env python3
"""
JARVIS Multi-GPU Task Dispatcher
Achemine intelligemment les requêtes vers le bon modèle / GPU selon la complexité :
- Tâches complexes / Code / Raisonnement / Claude Code -> RTX 3080 (qwen/qwen3.5-9b)
- Tâches simples / Résumés / Classification / Routine  -> RTX 2060 (hermes-2-pro-mistral-7b)
"""

import sys
import json
import urllib.request
import argparse

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"

MODEL_HEAVY = "qwen/qwen3.5-9b"         # RTX 3080 (10 Go)
MODEL_LIGHT = "hermes-2-pro-mistral-7b"  # RTX 2060 (12 Go)

def query_model(model_name: str, prompt: str, system_prompt: str = "Tu es un assistant IA précis et concis.") -> str:
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2048
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(LM_STUDIO_URL, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            return res['choices'][0]['message']['content']
    except Exception as e:
        return f"Erreur lors de l'appel au modèle {model_name} : {e}"

def is_complex_task(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    keywords_heavy = [
        "code", "python", "script", "refactor", "bug", "debug", "architecture", 
        "analyse", "raisonne", "expliquer en détail", "optimis", "erreur", "sql", "math"
    ]
    if len(prompt) > 400:
        return True
    return any(kw in prompt_lower for kw in keywords_heavy)

def main():
    parser = argparse.ArgumentParser(description="JARVIS Multi-GPU Task Dispatcher")
    parser.add_argument("prompt", type=str, help="Prompt de la tâche à exécuter")
    parser.add_argument("--force-heavy", action="store_true", help="Forcer l'utilisation de la RTX 3080 (Qwen 9B)")
    parser.add_argument("--force-light", action="store_true", help="Forcer l'utilisation de la RTX 2060 (Hermes 7B)")
    args = parser.parse_args()

    if args.force_heavy:
        selected_model = MODEL_HEAVY
        target_gpu = "RTX 3080 (GPU 4)"
    elif args.force_light:
        selected_model = MODEL_LIGHT
        target_gpu = "RTX 2060 (GPU 0)"
    else:
        if is_complex_task(args.prompt):
            selected_model = MODEL_HEAVY
            target_gpu = "RTX 3080 (GPU 4)"
        else:
            selected_model = MODEL_LIGHT
            target_gpu = "RTX 2060 (GPU 0)"

    print(f"🔀 [Dispatcher] Acheminement vers {selected_model} sur {target_gpu}")
    response = query_model(selected_model, args.prompt)
    print("\n--- Réponse ---")
    print(response)

if __name__ == "__main__":
    main()
