import urllib.request
import json
import threading
import time

URL = "http://127.0.0.1:9765/v1/messages"
CONCURRENCY = 8

def send_req(thread_id):
    payload = {
        "model": "qwen/qwen3.5-9b",
        "messages": [{"role": "user", "content": f"Génère un rapport de charge maximal pour le thread {thread_id}"}],
        "max_tokens": 500
    }
    data = json.dumps(payload).encode('utf-8')
    headers = {"Content-Type": "application/json", "X-Client-Name": "max-stress-tester"}
    try:
        t0 = time.time()
        req = urllib.request.Request(URL, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            elapsed = round((time.time() - t0) * 1000, 2)
            print(f"  [Thread {thread_id}] ✅ 200 OK en {elapsed} ms")
    except Exception as e:
        print(f"  [Thread {thread_id}] ❌ Erreur: {e}")

threads = []
print(f"🔥 Lancement de la charge GPU maximale avec {CONCURRENCY} requêtes parallèles concourantes...")
for i in range(1, CONCURRENCY + 1):
    t = threading.Thread(target=send_req, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("⚡ Test de charge maximale sur les 2 GPU achevé.")
