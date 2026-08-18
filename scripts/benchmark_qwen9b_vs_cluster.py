#!/usr/bin/env python3
"""
benchmark_qwen9b_vs_cluster.py — Benchmark comparatif Qwen 3.5 9B vs Qwen 3.5 27B vs Gemma 3
"""

import time
import json
import urllib.request
import os

ENDPOINTS = [
    {"name": "Qwen 3.5 9B (M2)", "url": "http://192.168.1.26:1234/v1/chat/completions", "model": "qwen3.5-9b", "type": "openai"},
    {"name": "Qwen 3.5 27B (M1)", "url": "http://192.168.1.85:1234/v1/chat/completions", "model": "qwen3.5-27b-claude-distill", "type": "openai"},
    {"name": "Gemma 3 4B (OL1)", "url": "http://127.0.0.1:11434/v1/chat/completions", "model": "gemma3:4b", "type": "openai"}
]

PROMPT_TEST = "Explique en 3 points concis pourquoi une architecture IA 100% on-premise est essentielle pour un cabinet d'avocats ou M&A."

print("==========================================================")
print("⚡ BENCHMARK COMPARATIF : QWEN 3.5 9B vs CLUSTER")
print("==========================================================")

results = []

for ep in ENDPOINTS:
    print(f"\n🧪 Test en cours sur : {ep['name']}...")
    payload = {
        "model": ep["model"],
        "messages": [{"role": "user", "content": PROMPT_TEST}],
        "temperature": 0.2,
        "max_tokens": 300
    }
    
    t0 = time.time()
    try:
        req = urllib.request.Request(ep["url"], data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=12) as response:
            t1 = time.time()
            res = json.loads(response.read().decode("utf-8"))
            elapsed = t1 - t0
            content = res.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = res.get("usage", {})
            completion_tokens = usage.get("completion_tokens", len(content.split()))
            tps = completion_tokens / elapsed if elapsed > 0 else 0
            
            print(f"  ✓ Temps de réponse : {elapsed:.2f}s")
            print(f"  ✓ Débit estimé     : {tps:.1f} tokens/s")
            print(f"  ✓ Extrait : {content[:100].strip()}...")
            
            results.append({
                "model": ep["name"],
                "time": f"{elapsed:.2f}s",
                "tps": f"{tps:.1f} t/s",
                "status": "SUCCÈS",
                "output": content
            })
    except Exception as e:
        print(f"  ⚠️ Nœud non joignable ou timeout ({e})")
        results.append({
            "model": ep["name"],
            "time": "N/A",
            "tps": "0 t/s",
            "status": f"FAIL ({type(e).__name__})",
            "output": ""
        })

print("\n==========================================================")
print("📊 RÉSULTATS DU BENCHMARK")
print("==========================================================")
for r in results:
    print(f"• {r['model']:<25} | {r['time']:<8} | {r['tps']:<10} | {r['status']}")
print("==========================================================")
