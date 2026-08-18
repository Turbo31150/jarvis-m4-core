#!/usr/bin/env python3
"""
JARVIS MULTI-MINI-BASH AUTO-DETECT DAEMON (SQL & BIBLIOTHÈQUE)
1. Analyse périodiquement les requêtes, logs et tâches stockées en SQLite.
2. Auto-détecte les blocs de commandes (bloc.sh) et mots-clés système.
3. Exécute en parallèle les mini-bash correspondants pour pré-mâcher le travail.
4. Met à jour les résultats et le score dans SQLite.
"""
import os, sys, time, json, sqlite3, subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT = "/home/pamerys/jarvis"
DB_MASTER = f"{ROOT}/jarvis_master.db"
DB_LOGS = f"{ROOT}/jarvis_logs.db"

def execute_mini_bash(kw, query):
    res_bash = ""
    try:
        if kw in ["gpu", "nvidia", "vram"]:
            res_bash = subprocess.check_output(["nvidia-smi", "--query-gpu=index,name,temperature.gpu,memory.used", "--format=csv,noheader"], text=True, timeout=5).strip()
        elif kw in ["cpu", "systeme", "load", "uptime"]:
            res_bash = subprocess.check_output(["uptime"], text=True, timeout=5).strip()
        elif kw in ["reseau", "ping", "m6", "ip"]:
            res_bash = subprocess.check_output(["ping", "-c", "1", "10.42.0.230"], text=True, timeout=5).strip()
        elif kw in ["docker", "container"]:
            res_bash = subprocess.check_output(["docker", "ps", "--format", "{{.Names}} {{.Status}}"], text=True, timeout=5).strip()[:200]
        else:
            # Fallback consultation bibliothèque bloc.sh
            res_bash = subprocess.check_output(["bash", f"{ROOT}/bin/bloc.sh", kw], text=True, timeout=5).strip()[:200]
    except Exception as e:
        res_bash = f"Info {kw}: {e}"
    return kw, res_bash

def run_multi_bash_cycle():
    print("🔄 [MULTI-BASH DAEMON] Analyse SQLite & Auto-détection Mots-Clés...")
    
    # 1. Extraction des intentions récentes depuis SQLite
    queries_to_process = []
    try:
        conn = sqlite3.connect(DB_LOGS)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS multi_bash_results (ts TEXT, kw TEXT, output TEXT);")
        cur.execute("SELECT prompt FROM single_request_logs ORDER BY rowid DESC LIMIT 5;")
        rows = cur.fetchall()
        conn.close()
        for r in rows:
            queries_to_process.append(r[0])
    except Exception:
        pass

    if not queries_to_process:
        queries_to_process = ["audit gpu nvidia", "charge systeme cpu", "statut docker container", "reseau ping m6"]

    # 2. Détection des mots-clés à traiter en parallèle
    keywords_set = set()
    for q in queries_to_process:
        for word in q.lower().split():
            if len(word) > 2:
                keywords_set.add(word)

    print(f"🎯 Mots-clés extraits pour détection multi-bash : {list(keywords_set)[:8]}")

    # 3. Exécution parallèle multi mini-bash
    results = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(execute_mini_bash, kw, q) for kw in list(keywords_set)[:8] for q in queries_to_process[:1]]
        for f in futures:
            kw, out = f.result()
            results[kw] = out

    # 4. Ingestion des résultats pré-mâchés dans SQLite
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_LOGS)
    cur = conn.cursor()
    for kw, out in results.items():
        cur.execute("INSERT INTO multi_bash_results VALUES (?, ?, ?);", (ts, kw, out[:300]))
    conn.commit()
    conn.close()

    print(f"✅ [MULTI-BASH DAEMON] Cycle exécuté avec succès ({len(results)} mini-bash pré-mâchés dans SQLite) !")

if __name__ == "__main__":
    run_multi_bash_cycle()
