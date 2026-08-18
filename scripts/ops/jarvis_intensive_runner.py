#!/usr/bin/env python3
"""
JARVIS Ultra-Intensive Mega Runner v2
Exécute la chaîne complète des 7 briques en mode ULTRA-GROSSIER (multi-requêtes, multi-domaines, multi-scopes).
Logue l'ensemble des étapes et sous-étapes dans jarvis_master.db.
"""
import sys
import os
import subprocess
import json
import time
import sqlite3

DB_PATH = "/home/pamerys/jarvis/jarvis_master.db"

def run_step(cmd, env_extra=None):
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    start_time = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    elapsed_ms = int((time.time() - start_time) * 1000)
    try:
        data = json.loads(res.stdout)
    except Exception:
        data = {"stdout": res.stdout, "stderr": res.stderr}
    return res.returncode, data, elapsed_ms

def log_run(conn, step_name, returncode, latency_ms):
    conn.execute(
        "INSERT INTO pipeline_log (task_id, step, machine, model, latency_ms, quality_score) VALUES (?,?,?,?,?,?)",
        (9999, f"mega_{step_name}", "M1", "jarvis-brique-mega-v2", latency_ms, 1.0 if returncode == 0 else 0.0)
    )
    conn.commit()

def run_mega_cycle():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🚀 DÉMARRAGE DU MEGA-CYCLE ULTRA-INTENSIF (7 BRIQUES)...")
    # WAL : un seul écrivain à la fois sur une base très sollicitée,
    # il faut attendre au lieu d'échouer sur "database is locked".
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")

    # 1. WEB (A3) — Multi-sources
    urls = ["https://example.com", "https://example.org", "https://httpbin.org/get"]
    for i, url in enumerate(urls, 1):
        code, data, ms = run_step(["/home/pamerys/jarvis/bin/jarvis-web", "grab", url])
        log_run(conn, f"web_grab_{i}", code, ms)
        print(f"  [1.1-{i}] Web Grab ({url}): code {code} ({ms}ms)")

    code, data, ms = run_step(["/home/pamerys/jarvis/bin/jarvis-web", "search", "Intelligence Artificielle Souveraine 2026"])
    log_run(conn, "web_search", code, ms)
    print(f"  [1.2] Web Search: code {code} ({ms}ms)")

    # 2. MEDIA (Extraire) — Multi-médias
    code, data, ms = run_step(["/home/pamerys/jarvis/bin/jarvis-media", "grab", "https://youtube.com/watch?v=jarvis2026"])
    log_run(conn, "media_grab", code, ms)
    print(f"  [2.1] Media Grab: code {code} ({ms}ms)")

    code, data, ms = run_step(["/home/pamerys/jarvis/bin/jarvis-media", "summary", "https://youtube.com/watch?v=jarvis2026"])
    log_run(conn, "media_summary", code, ms)
    print(f"  [2.2] Media Summary: code {code} ({ms}ms)")

    # 3. BOARD (Délibérer) — Multi-domaines
    domains = ["tech", "business", "souveraineté"]
    for d in domains:
        code, data, ms = run_step(["/home/pamerys/jarvis/bin/jarvis-board", "ask", f"Stratégie et délibération sur domaine {d}", "--domain", d])
        log_run(conn, f"board_ask_{d}", code, ms)
        print(f"  [3.1-{d}] Board Ask ({d}): code {code} ({ms}ms)")

    # 4. AGENT (A1) — Multi-modèles / Multi-providers
    providers = ["cascade", "ollama"]
    for p in providers:
        args = ["/home/pamerys/jarvis/bin/jarvis-agent", "delegate", f"Synthèse et arbitrage pour {p}"]
        if p == "ollama":
            args.append("--local")
        code, data, ms = run_step(args)
        log_run(conn, f"agent_delegate_{p}", code, ms)
        print(f"  [4.1-{p}] Agent Delegate ({p}): code {code} ({ms}ms)")

    # 5. PUBLISH (A4) — Stage & Commit
    code, data, ms = run_step(["/home/pamerys/jarvis/bin/jarvis-publish", "stage", "Payload d'action à effet de bord validé"])
    log_run(conn, "publish_stage", code, ms)
    print(f"  [5.1] Publish Stage: code {code} ({ms}ms)")

    # 6. MAIL (Communiquer) — Gated Check
    code, data, ms = run_step(["/home/pamerys/jarvis/bin/jarvis-mail", "list"])
    log_run(conn, "mail_list", code, ms)
    print(f"  [6.1] Mail List: code {code} ({ms}ms)")

    # 7. MEM (A2) — Multi-scopes
    scopes = ["global", "system_audit", "mega_cycle"]
    for s in scopes:
        code, data, ms = run_step(["/home/pamerys/jarvis/bin/jarvis-mem", "write", f"Empreinte mémoire pour scope {s}", "--scope", s])
        log_run(conn, f"mem_write_{s}", code, ms)
        print(f"  [7.1-{s}] Mem Write ({s}): code {code} ({ms}ms)")

    conn.close()
    print("🔥 MEGA-CYCLE ULTRA-INTENSIF TERMINÉ AVEC SUCCÈS !\n")

if __name__ == "__main__":
    run_mega_cycle()
