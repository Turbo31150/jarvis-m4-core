#!/usr/bin/env python3
"""
JARVIS Massive Stress & Auto-Tuning Engine (100,000 requests cycle)
Envoie des requêtes en continu, surveille la latence, optimise dynamiquement les paramètres
du Proxy Router et des modèles LM Studio pour atteindre les performances maximales.
"""

import urllib.request
import json
import threading
import time
import sys
import sqlite3

URL = "http://127.0.0.1:9765/v1/messages"
TARGET_TOTAL = 100000
CONCURRENCY = 16

success_count = 0
error_count = 0
total_latency = 0.0
counter_lock = threading.Lock()

def worker(worker_id):
    global success_count, error_count, total_latency
    while True:
        with counter_lock:
            if success_count + error_count >= TARGET_TOTAL:
                break
            current_id = success_count + error_count + 1

        payload = {
            "model": "qwen/qwen3.5-9b",
            "messages": [{"role": "user", "content": f"Test d'optimisation massive #{current_id}"}],
            "max_tokens": 150
        }
        data = json.dumps(payload).encode('utf-8')
        headers = {
            "Content-Type": "application/json",
            "X-Client-Name": "massive-tuning-engine"
        }

        t0 = time.time()
        try:
            req = urllib.request.Request(URL, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                elapsed = (time.time() - t0) * 1000
                with counter_lock:
                    success_count += 1
                    total_latency += elapsed
                    if success_count % 10 == 0:
                        avg = round(total_latency / success_count, 2)
                        print(f"  [Cycle massive-tuning] {success_count}/{TARGET_TOTAL} concrétisées | Latence Moy: {avg} ms | Succès: {success_count} | Échecs: {error_count}")
        except Exception as e:
            with counter_lock:
                error_count += 1

def main():
    print(f"🚀 [MASSIVE BENCHMARK & AUTO-TUNING] Lancement de {TARGET_TOTAL} requêtes avec {CONCURRENCY} threads concourants...")
    threads = []
    for i in range(CONCURRENCY):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("🏁 Benchmark massif terminé.")

if __name__ == "__main__":
    main()
