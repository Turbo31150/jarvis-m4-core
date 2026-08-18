import sqlite3
import os
import json
import time

db_path = "/home/pamerys/jarvis/jarvis_master.db"
# WAL : un seul écrivain à la fois sur une base très sollicitée,
# il faut attendre au lieu d'échouer sur "database is locked".
conn = sqlite3.connect(db_path, timeout=120)
conn.execute("PRAGMA busy_timeout=120000")
cur = conn.cursor()

# 10 Légions OMEGA x 25 Tâches Dominos = 250 Nouvelles chaînes dominos générées
domino_templates = [
    ("L1_architectes", "Architectural Refactoring & Module Graph Optimization", "m1-qwen35-9b"),
    ("L1_architectes", "API Schema Validation & OpenAPI Spec Sync", "m1-gpt-oss-20b"),
    ("L2_forgeurs", "Stubs Auto-Generation & Type Hints Enforcer", "ol1-gemma3-4b"),
    ("L2_forgeurs", "Rust & C++ Extensions Micro-compilation", "ol1-deepseek-r1-7b"),
    ("L3_sentinelles", "Continuous Threat Detection & Port Sentinel", "m4-qwen35-9b"),
    ("L3_sentinelles", "CVE Dependency Scanner & Patch Auto-apply", "m1-qwen35-9b"),
    ("L4_analystes", "Cluster Telemetry & Inference Latency Bench", "m1-gpt-oss-20b"),
    ("L4_analystes", "VRAM Fragmentation & Thermal Guard Patrol", "m4-qwen35-9b"),
    ("L5_automates", "CI/CD Auto-git Committer & Production Push", "ol1-gemma3-4b"),
    ("L5_automates", "Systemd User Services Auto-healer", "ol1-llama32"),
    ("L6_traders", "Market Data Stream Aspirator & Signal Processing", "m1-qwen35-9b"),
    ("L6_traders", "Crypto Portfolio Risk Manager & Volatility Alert", "m4-qwen35-9b"),
    ("L7_communicateurs", "Telegram Bot Multi-LLM Router Digest", "m1-qwen35-9b"),
    ("L7_communicateurs", "LinkedIn Post Generator & Engagement Pipeline", "m1-gpt-oss-20b"),
    ("L8_optimiseurs", "SQLite WAL Journal Optimizer & Vacuum Sweep", "ol1-gemma3-4b"),
    ("L8_optimiseurs", "ZRAM Memory Swap Compact & Kernel Drop Caches", "ol1-llama32"),
    ("L9_erudits", "Vector RAG Indexing & Embedding Refresh", "m1-qwen35-9b"),
    ("L9_erudits", "Prompts Multi-IA Library Catalog Ingester", "m4-qwen35-9b"),
    ("L10_debuggers", "Traceback Parser & Dynamic Code Patching", "m1-qwen35-9b"),
    ("L10_debuggers", "Docker Log Error Watchdog & Auto-restart", "ol1-deepseek-r1-7b")
]

created_count = 0
for idx in range(1, 26):
    for legion, title_prefix, model in domino_templates:
        chain_name = f"domino-{legion.lower()}-batch-{idx:02d}"
        task_title = f"[DOMINO-{legion.upper()}-{idx:02d}] {title_prefix} (Batch #{idx})"
        context = f"Exécution automatique massive du domino {chain_name} via modèle {model} sur cluster JARVIS."
        
        try:
            # Table tasks
            cur.execute("""
            INSERT INTO tasks (title, context, status, progress, agent, machine)
            VALUES (?, ?, 'pending', 0, ?, 'M1')
            """, (task_title, context, legion))
            created_count += 1
        except Exception:
            pass

conn.commit()
conn.close()

print(f"Succès : {created_count} nouvelles chaînes Domino de tâches ont été insérées et planifiées en masse !")
