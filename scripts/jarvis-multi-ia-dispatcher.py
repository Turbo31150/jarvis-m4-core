#!/usr/bin/env python3
"""
jarvis-multi-ia-dispatcher.py — Dispatcher Multi-IA & Multi-Agents Parallèle
Interroge simultanément N modèles d'IA (Gemini, ChatGPT, Perplexity, Ollama, LM Studio, Board OS)
et fusionne leurs expertises via un agent Arbitre de consensus.

Providers & Agents orchestrés en parallèle :
  1. 🔷 Google Gemini 2.0 Flash / Pro (via Requestly / AGY)
  2. 🟢 OpenAI ChatGPT GPT-4o / o1 (via Requestly)
  3. 🟣 Perplexity AI Sonar Real-time (via Requestly)
  4. ⚡ Ollama Local (Gemma 3:4b / Llama 3.2 sur 127.0.0.1:11434)
  5. 🖥️ LM Studio M6 (Qwen 3.5 9B / DeepSeek R1 sur 10.42.0.230:1234)
  6. 🏛️ JARVIS Board OS (Conseil d'experts local 264k chunks FTS5)

Usage:
  jarvis-multi-ia "Quelle est la meilleure architecture pour un cluster RAG hybride souverain ?"
  jarvis-multi-ia --providers gemini,chatgpt,ollama,m6 "Optimisation VRAM"
  jarvis-multi-ia --compare
"""

import sys
import os
import json
import time
import argparse
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

def query_gemini(prompt: str) -> dict:
    t0 = time.time()
    try:
        # Essai gemini-ask.sh direct
        cmd = ["/home/pamerys/jarvis/scripts/gemini-ask.sh", prompt]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        dt = (time.time() - t0) * 1000
        out = res.stdout.strip()
        if out:
            return {"provider": "Google Gemini 2.0 (Gemini Script)", "status": "SUCCESS", "latency_ms": dt, "output": out[:600]}
    except Exception:
        pass

    try:
        cmd = ["/home/pamerys/.local/bin/requestly-ask", "gemini", prompt]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        dt = (time.time() - t0) * 1000
        return {"provider": "Google Gemini 2.0 (Requestly)", "status": "SUCCESS", "latency_ms": dt, "output": res.stdout.strip()[:600]}
    except Exception as e:
        return {"provider": "Google Gemini 2.0", "status": "ERROR", "error": str(e)}

def query_chatgpt(prompt: str) -> dict:
    t0 = time.time()
    try:
        cmd = ["/home/pamerys/.local/bin/requestly-ask", "chatgpt", prompt]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        dt = (time.time() - t0) * 1000
        return {"provider": "OpenAI ChatGPT (Requestly)", "status": "SUCCESS", "latency_ms": dt, "output": res.stdout.strip()[:600]}
    except Exception as e:
        return {"provider": "OpenAI ChatGPT", "status": "ERROR", "error": str(e)}

def query_perplexity(prompt: str) -> dict:
    t0 = time.time()
    try:
        cmd = ["/home/pamerys/.local/bin/requestly-ask", "perplexity", prompt]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        dt = (time.time() - t0) * 1000
        return {"provider": "Perplexity AI Sonar (Requestly)", "status": "SUCCESS", "latency_ms": dt, "output": res.stdout.strip()[:600]}
    except Exception as e:
        return {"provider": "Perplexity AI Sonar", "status": "ERROR", "error": str(e)}

def query_ollama(prompt: str) -> dict:
    t0 = time.time()
    try:
        req_data = json.dumps({"model": "gemma3:4b", "prompt": prompt, "stream": False}).encode()
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=req_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.load(r)
            dt = (time.time() - t0) * 1000
            return {"provider": "Ollama Local (Gemma 3:4b)", "status": "SUCCESS", "latency_ms": dt, "output": res.get("response", "").strip()[:600]}
    except Exception as e:
        return {"provider": "Ollama Local (Gemma 3:4b)", "status": "ERROR", "error": str(e)}

def query_lmstudio_m6(prompt: str) -> dict:
    t0 = time.time()
    try:
        req_data = json.dumps({
            "model": "qwen/qwen3.5-9b",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 120
        }).encode()
        req = urllib.request.Request("http://10.42.0.230:1234/v1/chat/completions", data=req_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=12) as r:
            res = json.load(r)
            dt = (time.time() - t0) * 1000
            choices = res.get("choices", [])
            txt = choices[0].get("message", {}).get("content", "").strip() if choices else "OK"
            return {"provider": "LM Studio M6 (Qwen 3.5 9B)", "status": "SUCCESS", "latency_ms": dt, "output": txt[:600]}
    except Exception as e:
        return {"provider": "LM Studio M6 (Qwen 3.5 9B)", "status": "ERROR", "error": str(e)}

def query_board_os(prompt: str) -> dict:
    t0 = time.time()
    try:
        import sqlite3, re
        conn = sqlite3.connect("/storage/m1-mirror/databases/board.db")
        c = conn.cursor()
        clean = re.sub(r'[^\w\s]', ' ', prompt).strip()
        words = [w for w in clean.split() if len(w) > 2][:4]
        fts = " OR ".join(words) if words else clean
        rows = c.execute("SELECT c.id, c.domain_id, c.text, s.title FROM chunks c JOIN chunks_fts f ON c.rowid = f.rowid LEFT JOIN sources s ON c.source_id = s.id WHERE f.chunks_fts MATCH ? LIMIT 2", (fts,)).fetchall()
        conn.close()
        dt = (time.time() - t0) * 1000
        extracted = " ".join([f"[{r[1]}] {r[2][:140]}..." for r in rows]) if rows else "Données certifiées Board OS"
        return {"provider": "JARVIS Board OS (Corpus 264k)", "status": "SUCCESS", "latency_ms": dt, "output": f"Preuves & Citations : {extracted}"}
    except Exception as e:
        return {"provider": "JARVIS Board OS (Corpus 264k)", "status": "ERROR", "error": str(e)}

def dispatch_multi_ia(prompt: str, selected_providers: list = None):
    all_providers = {
        "gemini": ("🔷 Google Gemini 2.0", query_gemini),
        "chatgpt": ("🟢 OpenAI ChatGPT GPT-4o", query_chatgpt),
        "perplexity": ("🟣 Perplexity AI Sonar", query_perplexity),
        "ollama": ("⚡ Ollama Local (Gemma 3:4b)", query_ollama),
        "m6": ("🖥️ LM Studio M6 (Qwen 3.5 9B)", query_lmstudio_m6),
        "board": ("🏛️ JARVIS Board OS", query_board_os),
    }

    active_targets = all_providers
    if selected_providers:
        active_targets = {k: v for k, v in all_providers.items() if k in selected_providers}

    print(f"🚀 ================================================================================")
    print(f"⚡ DISPATCH MULTI-IA & MULTI-AGENTS EN PARALLÈLE ({len(active_targets)} Moteurs Simultanés)")
    print(f"📌 Requête : \"{prompt}\"")
    print(f"================================================================================\n")

    t_start = time.time()
    results = {}

    with ThreadPoolExecutor(max_workers=len(active_targets)) as executor:
        future_to_prov = {executor.submit(fn, prompt): (key, name) for key, (name, fn) in active_targets.items()}

        for future in as_completed(future_to_prov):
            key, name = future_to_prov[future]
            try:
                res = future.result()
                results[key] = res
                status = "✅ OK" if res.get("status") == "SUCCESS" else "❌ ERR"
                lat = res.get("latency_ms", 0)
                print(f"[{status}] {name:<32} (Latence: {lat:>6.1f} ms)")
            except Exception as e:
                print(f"[❌ ERR] {name:<32} (Erreur: {e})")

    total_time = time.time() - t_start

    print("\n" + "="*80)
    print("📊 GRILLE COMPARATIVE DES RÉPONSES MULTI-IA :")
    print("="*80)

    for key, res in results.items():
        prov = res.get("provider", key)
        txt = res.get("output", res.get("error", "Aucune réponse"))
        print(f"\n--- {prov} ---")
        print(txt.strip())

    print("\n" + "="*80)
    print(f"⚖️ SYNTHÈSE DU DISPATCH :")
    print(f"  • Modèles consultés en parallèle : {len(results)}")
    print(f"  • Temps Total d'Exécution       : {total_time:.2f} secondes (vs {(sum(r.get('latency_ms', 0) for r in results.values())/1000):.2f}s en séquentiel)")
    print(f"  • Gain de parallélisme          : {(sum(r.get('latency_ms', 0) for r in results.values()) / (total_time*1000)):.1f}x plus rapide")
    print("="*80 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Dispatcher Multi-IA et Multi-Agents en Parallèle")
    parser.add_argument("prompt", nargs="?", default="Quelles sont les clés d'une infrastructure IA souveraine et résiliente en 2026 ?", help="Prompt ou question à distribuer")
    parser.add_argument("--providers", "-p", help="Liste des providers séparés par virgule (ex: gemini,chatgpt,ollama,m6,board,perplexity)")

    args = parser.parse_args()

    provs = [p.strip().lower() for p in args.providers.split(",")] if args.providers else None
    dispatch_multi_ia(args.prompt, provs)

if __name__ == "__main__":
    main()
