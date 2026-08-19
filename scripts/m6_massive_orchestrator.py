#!/usr/bin/env python3
"""
m6_massive_orchestrator.py — Distribution Massive des Tâches Agent & Table Ronde sur M6 GPU via RJ45 Direct.
Lien prioritaire : 10.42.0.230:1234 (1.4 ms) avec bascule automatique.
"""

import concurrent.futures
import json
import os
import sqlite3
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

# Priorité absolue au lien direct RJ45 ASIX M4<->M6
M6_DIRECT_URL = "http://10.42.0.230:1234/v1"
M6_TS_URL = "http://100.112.114.32:1234/v1"

EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"
CHAT_MODEL = "qwen2.5-coder-14b-instruct"
FALLBACK_CHAT_MODEL = "deepseek-r1-0528-qwen3-8b"

MASTER_DB = "/home/pamerys/jarvis/databases/jarvis_master.db"
PLAN_DB = "/home/pamerys/jarvis/databases/unified_plan.db"
BIBLIO_DB = "/home/pamerys/jarvis/databases/bibliotheque.db"
LOGS_DB = "/home/pamerys/jarvis/databases/jarvis_logs.db"

def get_active_m6_url():
    for url in [M6_DIRECT_URL, M6_TS_URL]:
        try:
            req = urllib.request.Request(f"{url}/models")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
                models = [m["id"] for m in data.get("data", [])]
                return url, models
        except Exception:
            continue
    return None, []

def embed_text(url, text):
    try:
        payload = {"model": EMBED_MODEL, "input": text}
        req = urllib.request.Request(
            f"{url}/embeddings",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data["data"][0]["embedding"]
    except Exception:
        return None

def infer_table_ronde(url, task_title, task_context=""):
    system_prompt = (
        "Tu es l'Orchestrateur Suprême de la Table Ronde JARVIS sur GPU M6. "
        "Pour chaque tâche, génère une décision d'exécution découpée, précise et immédiatement actionnable en français (40 mots max)."
    )
    user_prompt = f"Tâche : {task_title}\nContexte : {task_context}"
    
    for model in [CHAT_MODEL, FALLBACK_CHAT_MODEL, "qwen/qwen3.5-9b"]:
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 120
            }
            req = urllib.request.Request(
                f"{url}/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                res = json.loads(resp.read().decode())
                return res["choices"][0]["message"]["content"].strip(), model
        except Exception:
            continue
            
    return "Appliquer la doctrine SWAN / LUMIÈRE 2 : exécution fluide immédiate sur le cluster.", "fallback-deterministic"

def process_single_task(task_item, m6_url):
    task_id, title, context = task_item
    t0 = time.time()
    
    # 1. Délibération / Arbitrage GPU M6
    verdict, model_used = infer_table_ronde(m6_url, title, context or "")
    
    # 2. Vectorisation 768D GPU M6
    vec = embed_text(m6_url, f"{title} - {verdict}")
    
    elapsed = time.time() - t0
    
    # 3. Enregistrement Base
    try:
        # Stockage dans Bibliotheque Stream
        conn_b = sqlite3.connect(BIBLIO_DB)
        cur_b = conn_b.cursor()
        vec_blob = sqlite3.Binary(json.dumps(vec).encode()) if vec else None
        cur_b.execute("""
        INSERT INTO elements_stream (mots_cles, titre, contenu, vecteur_768d)
        VALUES (?, ?, ?, ?);
        """, ("table-ronde,m6-gpu,swan", f"Task #{task_id}: {title[:80]}", verdict, vec_blob))
        conn_b.commit()
        conn_b.close()
    except Exception:
        pass
        
    return task_id, title, verdict, model_used, elapsed

def run_mass_distribution(limit=25):
    print("=" * 80)
    print(f"🚀 DISTRIBUTION MASSIVE TABLE RONDE ➔ M6 GPU ({datetime.now():%F %T})")
    print("=" * 80)
    
    m6_url, models = get_active_m6_url()
    if not m6_url:
        print("✗ ERREUR CRITIQUE : Nœud M6 / LMStudio inaccessible sur 10.42.0.230 et Tailscale !")
        return
        
    link_type = "RJ45 Direct ASIX (10.42.0.230)" if "10.42.0.230" in m6_url else "Tailscale Mesh"
    print(f"⚡ Lien Actif : {link_type} | URL : {m6_url}")
    print(f"🧠 Modèles GPU M6 Détectés : {', '.join(models)}")
    print("-" * 80)
    
    # Récupération des tâches en attente dans jarvis_master.db
    tasks = []
    try:
        conn = sqlite3.connect(MASTER_DB)
        cur = conn.cursor()
        tasks = cur.execute("""
            SELECT id, title, context FROM tasks 
            WHERE status = 'pending' OR status = 'todo'
            ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
    except Exception as e:
        print(f"⚠ Erreur lecture tasks master: {e}")
        
    if not tasks:
        print("Aucune tâche en attente directe dans jarvis_master.db. Test de charge synthétique...")
        tasks = [
            (i, f"Optimisation pipeline #{i} : Distribution de flux M4-M6 à latence minimale", "Contrôle d'intégrité et streaming zéro rétention")
            for i in range(1, 11)
        ]
        
    print(f"📦 Volume de Tâches à Traiter en Parallèle : {len(tasks)}")
    
    t_start = time.time()
    completed_count = 0
    
    # Exécution Parallèle Multi-Threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {executor.submit(process_single_task, t, m6_url): t for t in tasks}
        for future in concurrent.futures.as_completed(future_map):
            try:
                task_id, title, verdict, model, dur = future.result()
                completed_count += 1
                print(f"[{completed_count:02d}/{len(tasks):02d}] 🏛️ Task #{task_id} [{model}] ({dur:.2f}s)")
                print(f"     ➔ Titre   : {title[:75]}")
                print(f"     👉 Décision: {verdict[:100]}...\n")
            except Exception as e:
                print(f"⚠ Erreur traitement tâche : {e}")
                
    total_time = time.time() - t_start
    throughput = completed_count / total_time if total_time > 0 else 0
    
    print("=" * 80)
    print(f"✅ RÉSULTAT DU BATCH GPU M6 :")
    print(f"   • Tâches traitées avec succès : {completed_count} / {len(tasks)}")
    print(f"   • Temps total d'exécution     : {total_time:.2f}s")
    print(f"   • Débit d'inférence Table R.  : {throughput:.2f} tâches / seconde (0 token payant)")
    print("=" * 80)

if __name__ == "__main__":
    limit_val = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    run_mass_distribution(limit_val)
