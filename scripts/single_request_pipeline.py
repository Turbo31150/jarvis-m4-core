#!/usr/bin/env python3
"""
JARVIS SINGLE REQUEST PIPELINE (1 Demande -> 1 Action -> Log -> Scoring -> Feedback -> Biblio -> Bash -> Mots-clés)
"""
import os, sys, json, sqlite3, time, subprocess

def process_single_request(prompt):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # 1. Détection Mots-clés
    keywords = [w for w in prompt.lower().split() if len(w) > 3]
    
    # 2. Exécution Mini-Bash
    bash_out = ""
    if any(k in prompt.lower() for k in ["gpu", "nvidia", "vram"]):
        bash_out += os.popen("nvidia-smi --query-gpu=index,name,temperature.gpu,memory.used --format=csv,noheader 2>/dev/null").read().strip()
    if any(k in prompt.lower() for k in ["cpu", "systeme", "charge", "load"]):
        bash_out += "\n" + os.popen("uptime").read().strip()
        
    # 3. Consultation Bibliothèque
    biblio_match = ""
    try:
        b_res = subprocess.run(["bash", "/home/pamerys/jarvis/bin/bloc.sh", keywords[0] if keywords else "systeme"], capture_output=True, text=True, timeout=5)
        biblio_match = b_res.stdout.strip()[:150]
    except Exception:
        pass
        
    # 4. Scoring & Feedback
    score = 99.0 if bash_out or biblio_match else 85.0
    
    # 5. Log SQLite (jarvis_logs.db)
    log_db = '/home/pamerys/jarvis/jarvis_logs.db'
    conn = sqlite3.connect(log_db)
    conn.execute('CREATE TABLE IF NOT EXISTS single_request_logs (ts TEXT, prompt TEXT, keywords TEXT, bash_summary TEXT, score REAL);')
    conn.execute('INSERT INTO single_request_logs VALUES (?, ?, ?, ?, ?);', (ts, prompt, json.dumps(keywords), bash_out[:200], score))
    conn.commit()
    conn.close()
    
    result = {
        "demande": prompt,
        "mots_cles": keywords,
        "bash_machage": bash_out,
        "feedback_biblio": biblio_match,
        "score_execution": score,
        "log_status": "Enregistré dans jarvis_logs.db"
    }
    return result

if __name__ == "__main__":
    req = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Vérifier la charge CPU et GPU"
    res = process_single_request(req)
    print(json.dumps(res, indent=2, ensure_ascii=False))
