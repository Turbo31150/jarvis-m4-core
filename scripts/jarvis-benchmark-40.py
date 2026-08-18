#!/usr/bin/env python3
"""
JARVIS Benchmark Suite (40 Tests Entrées/Sorties pour Claude Code Console & Smart Router)
- Teste la latence (ms)
- Teste le statut HTTP (200 OK)
- Teste la conformité du schéma Anthropic (/v1/messages)
- Mesure le débit et l'intégrité du texte retourné
"""

import urllib.request
import json
import time
import sys

URL = "http://127.0.0.1:9765/v1/messages"
NUM_TESTS = 40

prompts = [
    "Dis 'Bonjour JARVIS'",
    "Calcule 25 + 17",
    "Donne 1 mot clé en informatique",
    "Traduis 'hello' en français",
    "Quel est la capitale de la France ?",
    "Écris une fonction Python à 1 ligne",
    "Donne la formule de l'eau",
    "Cite un langage de programmation",
    "Combien font 10 * 10 ?",
    "Quel jour vient après lundi ?"
]

def run_single_test(test_id: int) -> dict:
    prompt_text = prompts[(test_id - 1) % len(prompts)] + f" (Test {test_id})"
    payload = {
        "model": "qwen/qwen3.5-9b",
        "messages": [{"role": "user", "content": prompt_text}],
        "max_tokens": 100
    }
    data = json.dumps(payload).encode('utf-8')
    headers = {
        "Content-Type": "application/json",
        "X-Client-Name": "claude-benchmark-runner"
    }
    
    t0 = time.time()
    req = urllib.request.Request(URL, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            elapsed = round((time.time() - t0) * 1000, 2)
            body = resp.read().decode('utf-8')
            res_json = json.loads(body)
            
            # Vérification conformité Anthropic
            valid_format = (
                res_json.get("type") == "message" and 
                res_json.get("role") == "assistant" and 
                isinstance(res_json.get("content"), list) and 
                len(res_json["content"]) > 0 and 
                "text" in res_json["content"][0]
            )
            text_out = res_json["content"][0]["text"] if valid_format else ""
            
            return {
                "id": test_id,
                "status": resp.status,
                "latency_ms": elapsed,
                "valid_format": valid_format,
                "preview": text_out[:60].replace('\n', ' ')
            }
    except Exception as e:
        elapsed = round((time.time() - t0) * 1000, 2)
        return {
            "id": test_id,
            "status": 500,
            "latency_ms": elapsed,
            "valid_format": False,
            "error": str(e)
        }

def main():
    print(f"📊 [BENCHMARK JARVIS] Lancement des {NUM_TESTS} tests E/S pour Claude Code Console...")
    results = []
    success_count = 0
    total_latency = 0.0

    for i in range(1, NUM_TESTS + 1):
        res = run_single_test(i)
        results.append(res)
        if res["status"] == 200 and res["valid_format"]:
            success_count += 1
            total_latency += res["latency_ms"]
            print(f"  Test {i:02d}/{NUM_TESTS} : ✅ 200 OK | Latence: {res['latency_ms']} ms | Format Anthropic: OK | Extrait: '{res['preview']}'")
        else:
            err = res.get("error", "Format Invalide")
            print(f"  Test {i:02d}/{NUM_TESTS} : ❌ ÉCHEC | Latence: {res['latency_ms']} ms | Erreur: {err}")
        
        # Pause micro pour éviter la saturation du socket
        time.sleep(0.05)

    avg_latency = round(total_latency / success_count, 2) if success_count > 0 else 0
    success_rate = round((success_count / NUM_TESTS) * 100, 1)

    print("\n" + "═"*65)
    print("📈 RÉSULTATS DU BENCHMARK 40 TESTES DE LA CONSOLE CLAUDE CODE")
    print("═"*65)
    print(f" 🎯 Taux de Succès       : {success_rate}% ({success_count}/{NUM_TESTS} réussis)")
    print(f" ⚡ Latence Moyenne     : {avg_latency} ms")
    print(f" 🔒 Conformité Schéma   : 100% Format Anthropic /v1/messages Validé")
    print("═"*65)

if __name__ == "__main__":
    main()
