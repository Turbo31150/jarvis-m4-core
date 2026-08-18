#!/usr/bin/env python3
"""
JARVIS Bi-GPU Continuous Dual Feeder
Envoie simultanément des flux de tâches aux 2 modèles/GPU pour OpenClaw et Claude Code.
"""

import urllib.request
import json
import time
import concurrent.futures

ROUTER_URL = "http://127.0.0.1:9765/v1/chat/completions"

TASKS = [
    ("claude-client", "qwen/qwen3.5-9b", "Écris un script Python de tri rapide (QuickSort) optimisé avec commentaires."),
    ("openclaw-client", "hermes-2-pro-mistral-7b", "Résume en 10 mots : Le routage dynamique permet d'utiliser plusieurs cartes graphiques simultanément."),
    ("claude-client", "qwen/qwen3.5-9b", "Analyse cette structure SQL et propose 3 index pour accélérer les requêtes SELECT."),
    ("openclaw-client", "hermes-2-pro-mistral-7b", "Traduis en anglais : 'Le système de dispatch bi-GPU fonctionne à 100%.'"),
    ("claude-client", "hermes-2-pro-mistral-7b", "Donne 3 conseils pour optimiser un script Bash sous Linux."),
    ("openclaw-client", "qwen/qwen3.5-9b", "Rédige une fonction Python pour vérifier si une chaîne de caractères est un palindrome.")
]

def send_request(client_name, model_name, prompt):
    start_time = time.time()
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 512
    }
    headers = {
        "Content-Type": "application/json",
        "X-Client-Name": client_name
    }
    req = urllib.request.Request(ROUTER_URL, data=json.dumps(payload).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            elapsed = time.time() - start_time
            content = res['choices'][0]['message']['content'].strip()
            return {
                "success": True,
                "client": client_name,
                "model": model_name,
                "elapsed": round(elapsed, 2),
                "preview": content[:100].replace('\n', ' ')
            }
    except Exception as e:
        return {"success": False, "client": client_name, "model": model_name, "error": str(e)}

def main():
    print("🔥 [Dual-GPU Stream] Alimentation croisée en double flux simultané...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(send_request, client, model, prompt) for client, model, prompt in TASKS]
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r["success"]:
                gpu_name = "RTX 3080" if "qwen" in r["model"] else "RTX 2060"
                print(f"⚡ [{r['client']}] -> {r['model']} ({gpu_name}) | {r['elapsed']}s | Output: {r['preview']}")
            else:
                print(f"❌ Erreur sur {r['client']}: {r['error']}")

if __name__ == "__main__":
    main()
