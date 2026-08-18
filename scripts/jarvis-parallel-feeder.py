#!/usr/bin/env python3
"""
JARVIS Parallel Task Feeder (Alimentation continue & simultanée des 2 modèles/GPU)
- RTX 3080 : Reçoit les tâches complexes, analyse de code et raisonnement.
- RTX 2060 : Reçoit les tâches légères, résumés et classifications.
"""

import urllib.request
import json
import time
import concurrent.futures

ROUTER_URL = "http://127.0.0.1:9765/v1/chat/completions"

TASKS_HEAVY = [
    "Écris une fonction Python optimisée pour calculer le plus grand commun diviseur (PGCD) de deux nombres.",
    "Explique en 3 points clés le fonctionnement du mécanisme d'attention (Attention Mechanism) dans les Transformers.",
    "Rédige un script Bash pour surveiller l'utilisation du disque et envoyer une alerte si elle dépasse 85%."
]

TASKS_LIGHT = [
    "Résume en une phrase : La physique quantique étudie le comportement de la matière à l'échelle atomique.",
    "Classe ce mot-clé dans une catégorie : 'Apprentissage supervisé'. Réponds en 1 mot.",
    "Traduis en anglais : 'Le cluster local fonctionne parfaitement sur plusieurs cartes graphiques.'"
]

def execute_task(task_text: str, client_name: str, forced_model: str) -> dict:
    start_time = time.time()
    payload = {
        "model": forced_model,
        "messages": [
            {"role": "user", "content": task_text}
        ],
        "temperature": 0.3,
        "max_tokens": 512
    }
    headers = {
        "Content-Type": "application/json",
        "X-Client-Name": client_name
    }
    req = urllib.request.Request(ROUTER_URL, data=json.dumps(payload).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            elapsed = time.time() - start_time
            content = data['choices'][0]['message']['content'].strip()
            return {
                "success": True,
                "client": client_name,
                "model": forced_model,
                "elapsed": round(elapsed, 2),
                "preview": content[:120].replace('\n', ' ')
            }
    except Exception as e:
        return {
            "success": False,
            "client": client_name,
            "model": forced_model,
            "error": str(e)
        }

def run_parallel_batch():
    print("🚀 [Parallel Feeder] Alimentation simultanée des 2 modèles Bi-GPU...")
    futures = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        # Soumettre les tâches complexes (RTX 3080 / Qwen 9B)
        for t in TASKS_HEAVY:
            futures.append(executor.submit(execute_task, t, "claude-client", "qwen/qwen3.5-9b"))
        
        # Soumettre les tâches rapides (RTX 2060 / Hermes 7B)
        for t in TASKS_LIGHT:
            futures.append(executor.submit(execute_task, t, "openclaw-client", "hermes-2-pro-mistral-7b"))

        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res["success"]:
                print(f"✅ [{res['client']}] Modèle: {res['model']} | Temps: {res['elapsed']}s | Extrait: {res['preview']}")
            else:
                print(f"❌ [{res['client']}] Erreur sur {res['model']} : {res['error']}")

if __name__ == "__main__":
    run_parallel_batch()
